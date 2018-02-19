#!/bin/bash



# Nothing will work if this is False
# or these aren't already given by 
# a prior installation
### For each install
APPEND_BASHRC=True

### Only on first install
ADD_ENVIRONMENT=False

#DEBUG
#TIMESTAMPS

CWD=`pwd`
ENV_BASE=ADMDRP
ENV_HOME=`echo $ENV_BASE | tr '[:upper:]' '[:lower:]'`

INSTALL_HOME=$PROJWORK/bip149/$USER/$ENV_HOME/
FOLDER_ADMDRP_ENV=admdrpenv/
FOLDER_ADMDRP=admdrp/

ADAPTIVEMD_PKG=jrossyra/adaptivemd.git
ADAPTIVEMD_BRANCH=rp_integration
RCT_DEDICATED_ADAPTIVEMD_BRANCH=project/adaptivemd
RUTILS_PKG=radical-cybertools/radical.utils.git
RUTILS_BRANCH=$RCT_DEDICATED_ADAPTIVEMD_BRANCH
SAGA_PKG=radical-cybertools/saga-python.git
SAGA_BRANCH=$RCT_DEDICATED_ADAPTIVEMD_BRANCH
RPILOT_PKG=radical-cybertools/radical.pilot.git
RPILOT_BRANCH=$RCT_DEDICATED_ADAPTIVEMD_BRANCH

# User must download OpenMM-Linux precompiled binaries
# and untar it. This just tells the script where these
# are located on the filesystem.
# This one came from:
#https://simtk.org/frs/download_confirm.php/file/4904/OpenMM-7.0.1-Linux.zip?group_id=161
OPENMM_LOC=$PROJWORK/bip149/$USER/
FOLDER_OPENMM=OpenMM-7.0.1-Linux

OPENMM_LIBRARY_PREFIX=lib/
OPENMM_PLUGIN_PREFIX=lib/plugins/
OPENMM_INSTALL_LOC=$INSTALL_HOME$FOLDER_ADMDRP/openmm/


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
  echo "export ${ENV_BASE}_ENV=$INSTALL_HOME$FOLDER_ADMDRP_ENV" >> ~/.bashrc
  echo "export ${ENV_BASE}_ENV_ACTIVATE=\${${ENV_BASE}_ENV}bin/activate" >> ~/.bashrc
  echo "export ${ENV_BASE}_RUNS=$INSTALL_HOME${FOLDER_ADMDRP}runs/" >> ~/.bashrc
  echo "export ${ENV_BASE}_ADAPTIVEMD=$INSTALL_HOME${FOLDER_ADMDRP}adaptivemd/" >> ~/.bashrc
  echo "export ${ENV_BASE}_DATA=$INSTALL_HOME$FOLDER_ADMDRP" >> ~/.bashrc
fi

source ~/.bashrc
#eval echo \$${ENV_BASE}_ENV_ACTIVATE
eval source \$${ENV_BASE}_ENV_ACTIVATE

# DEPENDENCY INSTALL
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

# RADICAL UTILS INSTALL
git clone https://github.com/$RUTILS_PKG
cd radical.utils
git checkout $RUTILS_BRANCH
pip install .
cd ../

# SAGA PYTHON INSTALL
git clone https://github.com/$SAGA_PKG
cd saga-python
git checkout $SAGA_BRANCH
pip install .
cd ../

# RADICAL PILOT INSTALL
git clone https://github.com/$RPILOT_PKG
cd radical.pilot
git checkout $RPILOT_BRANCH
pip install .
cd ../

# ADAPTIVEMD INSTALL
git clone https://github.com/$ADAPTIVEMD_PKG
cd adaptivemd
git checkout $ADAPTIVEMD_BRANCH
pip install .

# OPENMM INSTALL
cd $OPENMM_LOC$FOLDER_OPENMM
module load cudatoolkit
pwd
ls -grth
expect -c "
    spawn sh install.sh
    expect "Enter?install?location*"
    send  \"$OPENMM_INSTALL_LOC\r\"
    expect "Enter?path?to?Python*"
    send  \"\r\"
    expect eof
    "
echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$OPENMM_INSTALL_LOC$OPENMM_PLUGIN_PREFIX" >> ~/.bashrc
echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$OPENMM_INSTALL_LOC$OPENMM_LIBRARY_PREFIX" >> ~/.bashrc

cd $CWD

