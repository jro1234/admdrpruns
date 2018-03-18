#!/bin/bash


echo "db got args: "
echo "$@"

WHICHDB=$1
RUNNAME=$2

# Parse the ip address of this node on Gemini
# high-speed interconnect.
DB_HOSTNAME=`ip addr show ipogif0 | grep -Eo '(addr:)?([0-9]*\.){3}[0-9]*'`
DB_CONFIG=$ADMD_DB/mongo.$RUNNAME.$WHICHDB.cfg
DB_LOCATION=$ADMD_DB/data/$RUNNAME.$WHICHDB.db/
DB_SOCKET=$ADMD_DB/data/$DB_HOSTNAME/
DB_LOGFILE=mongo.$RUNNAME.$WHICHDB.log
export OMP_NUM_THREADS=16
# Making config file specific to each database
# so each has own socket. Can run concurrent DB
# independently (for different jobs, etc).
mkdir $DB_SOCKET
echo -e "net:\n   unixDomainSocket:\n      pathPrefix: $DB_SOCKET\n   bindIp: 0.0.0.0" > $DB_CONFIG 
mkdir $DB_LOCATION
#echo "Hopefully ulimit is large enough (10k+) ..."
#ulimit -n

# Store database location for other connections
echo "$DB_HOSTNAME" > $RUNNAME.$WHICHDB.hostname

# Making database (ie directory) for this mongod instance
numactl --interleave=all mongod --config $DB_CONFIG --dbpath $DB_LOCATION &> $DB_LOGFILE
