#!/bin/bash

CWD=`pwd`

INSTALL_HOME=$PROJWORK/bip149/
FOLDER_ADMDRP_ENV=$USER/admdrpenv/
FOLDER_ADMDRP=admdrp/
ADAPTIVEMD_PKG=jrossyra/adaptivemd.git
ADAPTIVEMD_BRANCH=rp_integration

# Nothing will work if this is False
APPEND_BASHRC=True

module load python
virtualenv $INSTALL_HOME$FOLDER_ADMDRP_ENV

echo "Appending virtualenv activate script"
echo -e "\n# MORE ENVIRONMENT VARIABLES" >> $INSTALL_HOME$FOLDER_ADMDRP_ENV/bin/activate
echo "export LD_PRELOAD=/lib64/librt.so.1" >> $INSTALL_HOME$FOLDER_ADMDRP_ENV/bin/activate
echo "export RP_ENABLE_OLD_DEFINES=True" >> $INSTALL_HOME$FOLDER_ADMDRP_ENV/bin/activate
echo "export RADICAL_PILOT_DBURL='mongodb://rp:rp@ds015335.mlab.com:15335/rp'" >> $INSTALL_HOME$FOLDER_ADMDRP_ENV/bin/activate

if [ $APPEND_BASHRC = True ]
then
  echo "Adding AdaptiveMD Environment Variables to bashrc"
  echo "export ADMDRP_ENV=$INSTALL_HOME$FOLDER_ADMDRP_ENV" >> ~/.bashrc
  echo "export ADMDRP_ENV_ACTIVATE=\${ADMDRP_ENV}bin/activate" >> ~/.bashrc
  echo "export ADMDRP_RUNS=$INSTALL_HOME${FOLDER_ADMDRP}runs/" >> ~/.bashrc
  echo "export ADMDRP_ADAPTIVEMD=$INSTALL_HOME${FOLDER_ADMDRP}adaptivemd/" >> ~/.bashrc
  echo "export ADMDRP_DATA=$INSTALL_HOME$FOLDER_ADMDRP" >> ~/.bashrc
  echo "export ADMDRP_RUNS=$INSTALL_HOME${FOLDER_ADMDRP}runs/" >> ~/.bashrc
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
fi

git clone https://github.com/$ADAPTIVEMD_PKG
cd adaptivemd
git checkout $ADAPTIVEMD_BRANCH

pip install .

cd $CWD
