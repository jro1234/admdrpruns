#!/bin/bash


echo "client got args: "
echo "$@"

RUNNAME=$1
ADMD_SCRIPT=$2
SYSTEMNAME=$3
PLATFORM=$4
CONDAENV=$5
ACTIVATEPFX=$6
VIRTUALENV=$7
LONGTS=$8
THREADS=$9
LENGTH=${10}
MINLENGTH=${11}
N_TRAJ=${12}
N_ROUNDS=${13}
N_EXT=${14}
MODELLER=${15}
P_FRAMES=${16}
M_FRAMES=${17}
#VIRTUALENV=$4
#LONGTS=$5
#THREADS=$6
#LENGTH=$7
#MINLENGTH=$8
#N_TRAJ=$9
#N_ROUNDS=$10
#N_EXT=$11
#MODELLER=$12
#P_FRAMES=$13
#M_FRAMES=$14

OMP_NUM_THREADS=16
EXT_RP_DB=rp
EXT_ADMD_DB=admd
FILE_RP_HOSTNAME=$RUNNAME.$EXT_RP_DB.hostname
FILE_ADMD_HOSTNAME=$RUNNAME.$EXT_ADMD_DB.hostname

echo "RECIEVED CLIENT ARGSTRING"
echo "\$RUNNAME=$RUNNAME \$ADMD_SCRIPT=$ADMD_SCRIPT \$SYSTEMNAME=$SYSTEMNAME \$PLATFORM=$PLATFORM \$CONDAENV=$CONDAENV \$ACTIVATEPFX=$ACTIVATEPFX \$VIRTUALENV=$VIRTUALENV \$LONGTS=$LONGTS \$THREADS=$THREADS \$LENGTH=$LENGTH \$MINLENGTH=$MINLENGTH \$N_TRAJ=$N_TRAJ \$N_ROUNDS=$N_ROUNDS \$N_EXT=$N_EXT \$MODELLER=$MODELLER \$P_FRAME=$P_FRAMES \$M_FRAMES=$M_FRAMES"

echo "Reading ${EXT_ADMD_DB} DB Hostname from: ${FILE_ADMD_HOSTNAME}"
echo "Reading ${EXT_RP_DB} DB Hostname from: ${FILE_RP_HOSTNAME}"

waitfor=15
waits=0
while [ $waits -lt $waitfor ]
do
  echo "Waiting for both databases ${waits}"
  if [[ -f $FILE_ADMD_HOSTNAME && -f $FILE_RP_HOSTNAME ]]
  then
    echo "Both databases are up"
    waits=15
  elif [ $waits -eq $waitfor ]
  then
    echo "Waited for both databases too long, exiting!"
    exit 1
  else
    waits=$((waits+1))
    sleep 5
  fi
done

RP_DB_HOSTNAME=`cat $FILE_RP_HOSTNAME`
ADMD_DB_HOSTNAME=`cat $FILE_ADMD_HOSTNAME`

export ADMD_DBURL="mongodb://${ADMD_DB_HOSTNAME}:27017/"
export RADICAL_PILOT_DBURL="mongodb://${RP_DB_HOSTNAME}:27017/rp"

echo "Database URLS: "
echo "ADMD_DBURL=${ADMD_DBURL}"
echo "RADICAL_PILOT_DBURL=${RADICAL_PILOT_DBURL}"
####
####mod=`echo "$N_TRAJ*0.2" | bc`
####delay=`echo "$j*0.1+$j%$mod" | bc`
####echo "Delay of $delay"
####sleep $delay
####
echo "Initializing simulation project for workflow"
python $ADMD_SCRIPT $RUNNAME $SYSTEMNAME --init_only -P $PLATFORM -p $P_FRAMES -m $M_FRAMES

echo "WORKFLOW CALL SIGNATURE"
echo $ADMD_SCRIPT $RUNNAME $SYSTEMNAME $CONDAENV $ACTIVATEPFX $VIRTUALENV $LONGTS -t $THREADS -l $LENGTH -k $MINLENGTH -N $N_TRAJ -b $N_ROUNDS -x $N_EXT $MODELLER -p $P_FRAMES -m $M_FRAMES

echo "Adding simulation workflow events"
python $ADMD_SCRIPT $RUNNAME $SYSTEMNAME $CONDAENV $ACTIVATEPFX $VIRTUALENV $LONGTS -t $THREADS -l $LENGTH -k $MINLENGTH -N $N_TRAJ -b $N_ROUNDS -x $N_EXT $MODELLER -p $P_FRAMES -m $M_FRAMES & EVENT_PID=$!

echo "Waiting for event scripts to terminate"
wait "$EVENT_PID"

sleep 1
