#!/bin/bash


#rp_uid=$1
#postfix=$2
#
#mv run_admdrp.__*  $rp_uid
#
#session_dest=~/workflow-analysis/rawdata/testrun_$postfix/$rp_uid
#agent_dest=$session_dest/pilot.0000
#
#mkdir $session_dest
#mkdir $agent_dest
#cp $rp_uid/*prof $session_dest
#cp $rp_uid/pilot.0000/*prof $agent_dest
#
#cp $rp_uid/*json $session_dest

rp_uid=$1
group=$2

mv run_admdrp.__*  $rp_uid

session_dest=./$group/$rp_uid
agent_dest=$session_dest/pilot.0000

mkdir $session_dest
mkdir $agent_dest

cp $rp_uid/*json $session_dest
cp $rp_uid/*prof $session_dest
cp $rp_uid/run_admdrp.__* $session_dest
cp $rp_uid/pilot.0000/*prof $agent_dest
