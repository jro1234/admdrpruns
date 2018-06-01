#!/bin/bash

#ntraj=(10 10)
#nsteps=(2000 2000)
#batchsize=(2 2)
#batchwait=(5 5)
#progress=("any" "all")
#run_folder=("trial_" "trial_")

# NOTE "once" will default to any
#      because of the argument type...
#      and this will have no effect when
#      including all tasks in first batch
ntraj=(2000    2000   2000   2000   2000   2000)
nsteps=(1000  1000  1000  1000  1000  1000)
batchsize=(500   500    500   500   2000   2000)
batchwait=("any" "any" "all" "all" "once" "once")
progress=("any"  "all" "any" "all" "any"  "all")
#run_prefix="WAIT_${batchwait}_PROGRESS_${progress}"

for ((i=0; i<${#batchsize[@]}; i++)); do
  python format_runtemplate.py  TPT ${ntraj[$i]} ${nsteps[$i]} ${batchsize[$i]} ${batchwait[$i]} ${progress[$i]} "WAIT_${batchwait[$i]}_PROGRESS_${progress[$i]}"
done



