
Distributed AdaptiveMD Application Installer

There are 3 AdaptiveMD layers. Radical Pilot (EnsembleTK)  may be utilized as 
an execution manager and 

AdaptiveMD Application
AdaptiveMD Storage
AdaptiveMD Resource

The user-side application may be located on the resource filesystem, and the 
storage must be accessible to both the application and resource. Currently


Type `python runmaker.py [ --help || -h ]` to see all options available.



Usage: 

\###########################################################
\#   Not sure if these will work ... , see env ones below  #
\###########################################################
\#  $ python runmaker.py testagain ntl9 -P CUDA -M pyemma-ionic -N 10 -x 1 -b 1 -l 10000 -p 500 -m 1000
\#
\#
\# # This one is good for very short tests
\#  $ python runmaker.py testagain ntl9 -P CUDA -M pyemma-ionic -N 5 -x 1 -b 1 -l 100 -p 2 -m 10
\###########################################################

 With conda based task-execution environment that is not in the path
  - the "-A" option appends the conda binary folder location, here it is given as an
    environment variable "$CONDAPATH". Leave it off if the PATH knows the location.
  - the "-e" option gives the name of the conda environment, "py27" in this case.

  $ python runmaker.py testagain ntl9 -e py27 -A $CONDAPATH -P CUDA -M pyemma-ionic -N 10 -x 1 -b 1 -l 10000 -p 500 -m 1000


 With virtualenv containing coinstallation of AdaptiveMD application and task environments, and Radical Pilot.
  - the "-w" option gives the full file location of the virtualenv activate script

 \# CPU Platform
 > $ python runmaker.py test01 ntl9 -w $ADMDRP_ENV_ACTIVATE -P CPU -M pyemma-ionic -N 5 -x 1 -b 1 -l 100 -p 2 -m 10

 \# CUDA Platform
 > $ python runmaker.py test01 ntl9 -w $ADMDRP_ENV_ACTIVATE -P CUDA -M pyemma-ionic -N 5 -x 1 -b 1 -l 100 -p 2 -m 10


