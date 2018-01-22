#!/bin/bash

CWD=`pwd`

INSTALL_HOME=$PROJWORK/bip149/$USER/admdrp2/
FOLDER_ADMDRP_ENV=admdrpenv/
FOLDER_ADMDRP=admdrp/

ADAPTIVEMD_PKG=jrossyra/adaptivemd.git
ADAPTIVEMD_BRANCH=rp_integration

RUTILS_PKG=radical-cybertools/radical.utils.git
RUTILS_BRANCH=

SAGA_PKG=radical-cybertools/saga-python.git
SAGA_BRANCH=

RPILOT_PKG=radical-cybertools/radical.pilot.git
RPILOT_BRANCH=fix/ompi_on_titan

# User must download OpenMM-Linux precompiled binaries
# and untar it. This just tells the script where these
# are located on the filesystem.
# This one came from:
#https://simtk.org/frs/download_confirm.php/file/4904/OpenMM-7.0.1-Linux.zip?group_id=161
OPENMM_LOC=$PROJWORK/bip149/$USER/
FOLDER_OPENMM=OpenMM-7.0.1-Linux

# Nothing will work if this is False
# or these aren't already given by 
# a prior installation
APPEND_BASHRC=True
ADD_ENVIRONMENT=True
#DEBUG
#TIMESTAMPS


module load python
virtualenv $INSTALL_HOME$FOLDER_ADMDRP_ENV

if [ $ADD_ENVIRONMENT = True ]
then
  #echo "Appending virtualenv activate script"
  echo "Appending bashrc with RP Environment Vars for DEBUG"
  #RP_VARSLOC=$INSTALL_HOME$FOLDER_ADMDRP_ENV/bin/activate
  RP_VARSLOC=~/.bashrc
  echo -e "\n# MORE ENVIRONMENT VARIABLES" >> $RP_VARSLOC
  echo "export LD_PRELOAD=/lib64/librt.so.1" >> $RP_VARSLOC
  echo "export RP_ENABLE_OLD_DEFINES=True" >> $RP_VARSLOC
  echo "export RADICAL_PILOT_DBURL='mongodb://rp:rp@ds015335.mlab.com:15335/rp'" >> $RP_VARSLOC
fi

if [ $APPEND_BASHRC = True ]
then
  echo "Adding AdaptiveMD-RP Environment Variables to bashrc"
  echo "export ADMDRP_ENV=$INSTALL_HOME$FOLDER_ADMDRP_ENV" >> ~/.bashrc
  echo "export ADMDRP_ENV_ACTIVATE=\${ADMDRP_ENV}bin/activate" >> ~/.bashrc
  echo "export ADMDRP_RUNS=$INSTALL_HOME${FOLDER_ADMDRP}runs/" >> ~/.bashrc
  echo "export ADMDRP_ADAPTIVEMD=$INSTALL_HOME${FOLDER_ADMDRP}adaptivemd/" >> ~/.bashrc
  echo "export ADMDRP_DATA=$INSTALL_HOME$FOLDER_ADMDRP" >> ~/.bashrc
fi

source ~/.bashrc
source $ADMDRP_ENV_ACTIVATE

cat requirements.txt | xargs -n 1 -L 1 pip install

cd $INSTALL_HOME
if [ ! -d "$FOLDER_ADMDRP" ]
then
  mkdir $FOLDER_ADMDRP
  cd $FOLDER_ADMDRP
  mkdir runs/
  cp -rp $CWD/runs/* runs/
else
  cd $FOLDER_ADMDRP
fi


git clone https://github.com/$RUTILS_PKG
cd radical.utils
git checkout $RUTILS_BRANCH
pip install .
cd ../

git clone https://github.com/$SAGA_PKG
cd saga-python
git checkout $SAGA_BRANCH
pip install .
cd ../

git clone https://github.com/$RPILOT_PKG
cd radical.pilot
git checkout $RPILOT_BRANCH
pip install .
cd ../

git clone https://github.com/$ADAPTIVEMD_PKG
cd adaptivemd
git checkout $ADAPTIVEMD_BRANCH
pip install .

cd $OPENMM_LOC$FOLDER_OPENMM
module load cudatoolkit
sh install.sh

cd $CWD
