# gromacs-free-energy-tutorial
## Workstation

On the workstations these can be run with the following commands

`bash setup-environment.sh`

`source env/bin/activate`

`jupyter notebook`

Note that on the workstations the command:

`module load gromacs/2018.2`

does not load gromacs but that gromacs 5.1 is in the path so the notebook should still work.

## Tegner

For Tegner, getting the notebook running will be more complicated, but will look something
like the following.

`module load anaconda/py36/5.0.1`

`source activate pyemma`

`jupyter notebook --no-browser --port=XXXX`

`pdc-ssh -N -L YYYY:localhost:XXXX <username>@<your assigned node>.pdc.kth.se`
