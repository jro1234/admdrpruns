
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

  $ python runmaker.py test11 ntl9 -P CUDA -M pyemma-ionic -N 10 -x 1 -b 1 -l 10000 -p 500 -m 1000
