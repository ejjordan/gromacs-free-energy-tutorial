#!/usr/env python

import shlex,os,modulecmd,subprocess,tarfile,shutil
import urllib.request

#allow use of modules
module=modulecmd.Modulecmd()
#load gromacs module
module.load('gromacs/2019')

#simple terminal functionality
def terminal_call(command_string, directory):
    command=shlex.split(command_string)
    proc=subprocess.run(command,cwd=directory,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(proc.stdout.decode())

#simple function to write mdp files
def write_mdp(mdp_string, mdp_name, directory):
    mdp_filename=os.path.join(directory,mdp_name)
    mdp_filehandle=open(mdp_filename,'w')
    mdp_filehandle.write(mdp)
    mdp_filehandle.close()

#get the path to the working directory
pwd=os.getcwd()

#fetch the files
tutorial_name='gromacs-free-energy-tutorial'
url=f'http://www.gromacs.org/@api/deki/files/261/={tutorial_name}.tgz'
tar_name=f'{tutorial_name}.tgz'
urllib.request.urlretrieve(url,tar_name)

#untar the archive but discard some wonky mac junk
tar=tarfile.open(tar_name,'r:gz')
[tar.extract(member) for member in tar.getnames() if '_' not in member];
tar.close()

#path to gromacs files
files_path=os.path.join(pwd,tutorial_name)

editconf_string="gmx editconf -f ethanol.gro -o box.gro -bt dodecahedron -d 1"
terminal_call(editconf_string,files_path)

solvate_string="gmx solvate -cp box.gro -cs -o solvated.gro -p topol.top"
terminal_call(solvate_string,files_path)

em_mdp="""integrator               = steep
nsteps                   = 500
coulombtype              = pme
vdw-type                 = pme
"""
write_mdp(em_mdp,'em.mdp',files_path)

em_grompp_string='gmx grompp -f em.mdp -c solvated.gro -o em.tpr'
terminal_call(em_grompp_string,files_path)

em_md_string='gmx mdrun -v -deffnm em -ntmpi 1'
terminal_call(em_md_string,files_path)

equil_mdp="""integrator               = md
nsteps                   = 20000
dt                       = 0.002
nstenergy                = 100
rlist                    = 1.0
nstlist                  = 10
vdw-type                 = pme
rvdw                     = 1.0
coulombtype              = pme
rcoulomb                 = 1.0
fourierspacing           = 0.12
constraints              = all-bonds
tcoupl                   = v-rescale
tc-grps                  = system
tau-t                    = 0.2
ref-t                    = 300
pcoupl                   = berendsen
ref-p                    = 1
compressibility          = 4.5e-5
tau-p                    = 5
gen-vel                  = yes
gen-temp                 = 300
"""
write_mdp(equil_mdp,'equil.mdp',files_path)

equil_grompp_string='gmx grompp -f equil.mdp -c em.gro -o equil.tpr'
equil_grompp_call=shlex.split(equil_grompp_string)
terminal_call(equil_grompp_call,files_path)

equil_md_string='gmx mdrun -deffnm equil -v -ntmpi 1'
equil_md_call=shlex.split(equil_md_string)
terminal_call(equil_md_call,files_path)

run_mdp=f"""; we'll use the sd integrator with 100000 time steps (200ps)
integrator               = sd
nsteps                   = 100000
dt                       = 0.002
nstenergy                = 1000
nstlog                   = 5000
; cut-offs at 1.0nm
rlist                    = 1.0
dispcorr                 = EnerPres
vdw-type                 = pme
rvdw                     = 1.0
; Coulomb interactions
coulombtype              = pme
rcoulomb                 = 1.0
fourierspacing           = 0.12
; Constraints
constraints              = all-bonds
; set temperature to 300K
tcoupl                   = v-rescale
tc-grps                  = system
tau-t                    = 0.2
ref-t                    = 300
; set pressure to 1 bar with a thermostat that gives a correct
; thermodynamic ensemble
pcoupl                   = parrinello-rahman
ref-p                    = 1
compressibility          = 4.5e-5
tau-p                    = 5

; and set the free energy parameters
free-energy              = yes
couple-moltype           = ethanol
; these 'soft-core' parameters make sure we never get overlapping
; charges as lambda goes to 0
sc-power                 = 1
sc-sigma                 = 0.3
sc-alpha                 = 1.0
; we still want the molecule to interact with itself at lambda=0
couple-intramol          = no
couple-lambda1           = vdwq
couple-lambda0           = none
init-lambda-state        = {lambda_number}
; These are the lambda states at which we simulate
; for separate LJ and Coulomb decoupling, use
fep-lambdas              = 0.0 0.2 0.4 0.6 0.8 0.9 1.0
"""

number_of_lambdas=2
for lambda_number in range(number_of_lambdas):
    lambda_directory=os.path.join(files_path,'lambda_%2d'%lambda_number)
    os.mkdir(lambda_directory)
    gro_file=os.path.join(files_path,'equil.gro')
    top_file=os.path.join(files_path,'topol.top')
    shutil.copy(gro_file,lambda_directory)
    shutil.copy(top_file,lambda_directory)
    write_mdp(run_mdp,'run.mdp',lambda_directory)
    run_grompp_string='gmx grompp'
    terminal_call(run_grompp_string,files_path)
    run_mdrun_string='gmx mdrun -nt 1'
    terminal_call(run_mdrun_string)
