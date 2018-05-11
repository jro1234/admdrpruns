#!/bin/bash

# Sort out some stuff
NTRAJ={ntraj}
NSTEPS={nsteps}
BATCHSLEEP=5
BATCHSIZE={batchsize}
BATCHWAIT={batchwait}
PROGRESS={progress}

MFREQ=250
PFREQ=50

RUNNAME=trials_$NTRAJ
SCRIPT_NAME=run_admd_Q.py
ADMD_SCRIPT=${{ADMDRP_RUNS}}/scripts/$SCRIPT_NAME

# Initialize the run
python $ADMD_SCRIPT $RUNNAME ntl9 --reinit --init_only -P CPU -p $PFREQ -m $MFREQ

# Execute the run
python $ADMD_SCRIPT $RUNNAME ntl9  -s $BATCHSLEEP -c $BATCHSIZE -u $BATCHWAIT --progress $PROGRESS  -w /lustre/atlas/proj-shared/bip149/jrossyra/admdrp/admdrpenv/bin/activate  -t 16 -l $NSTEPS -k $NSTEPS -N $NTRAJ -b 2 -x 1 -M pyemma-ionic

deactivate
