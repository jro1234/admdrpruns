#!/bin/bash


function installeroutput {
  echo "INSTALLER-   $1"
}


###############################################################################
#  Install MongoDB                                                            #
#   - this is treated as a different unit than the Python-based               #
#     workflow packages installed below. You can leave the vars               #
#     made here, and the MongoDB installation, when reinstalling              #
#     the other workflow software                                             #
###############################################################################
# these ones saved to environment variables
INSTALL_ADMD_DB=$PROJWORK/bip149/$USER/
# Folder names for our installed components
FOLDER_ADMD_DB=mongodb
MONGODB_VERSION=3.3.0
if [ ! -x "$(command -v mongod)" ]; then
  cd $INSTALL_ADMD_DB
  installeroutput "Installing Mongo in: $INSTALL_ADMD_DB"
  installeroutput "Appending .bashrc with mongo environment for AdaptiveMD Workflows"
  curl -O https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-$MONGODB_VERSION.tgz
  tar -zxvf mongodb-linux-x86_64-$MONGODB_VERSION.tgz
  mkdir mongodb
  mv mongodb-linux-x86_64-$MONGODB_VERSION/ $FOLDER_ADMD_DB
  rm mongodb-linux-x86_64-$MONGODB_VERSION.tgz
  echo -e "\n\n# >> START OF MONGODB ENVIRONMENT VARIABLES" >> ~/.bashrc
  echo "# APPENDING PATH VARIABLE with MongoDB Binary folder" >> ~/.bashrc
  echo "export PATH=${INSTALL_ADMD_DB}${FOLDER_ADMD_DB}/mongodb-linux-x86_64-$MONGODB_VERSION/bin/:\$PATH" >> ~/.bashrc
  echo "#on titan, this gets the head node ip address." >> ~/.bashrc
  echo "# - for production runs, more appropriate db hosts should be used" >> ~/.bashrc
  echo "#   and the corresponding DBURL variables should be overwritten" >> ~/.bashrc
  echo "export LOGIN_HOSTNAME=`ip addr show bond0 | grep -Eo '(addr:)?([0-9]*\.){3}[0-9]*' | head -n1`" >> ~/.bashrc
  echo "export ADMD_DB=${INSTALL_ADMD_DB}${FOLDER_ADMD_DB}/" >> ~/.bashrc
  echo -e "# >> END OF MONGODB ENVIRONMENT VARIABLES\n\n" >> ~/.bashrc
  echo "# NOTE These should be overwritten according to the" >> ~/.bashrc
  echo "#      actual `mongod` instance host ip. Using the" >> ~/.bashrc
  echo "#      launched-method of workflow, these will be" >> ~/.bashrc
  echo "#      configured automatically at runtime and" >> ~/.bashrc
  echo "#      overwrite with correct locations." >> ~/.bashrc
  echo "export RADICAL_PILOT_DBURL=\"mongodb://\${LOGIN_HOSTNAME}:27777/rp\"" >> ~/.bashrc
  echo "export ADMD_DBURL=\"mongodb://\${LOGIN_HOSTNAME}:27017/\"" >> ~/.bashrc
  installeroutput "Done installing Mongo, appended PATH with mongodb bin folder"
  source ~/.bashrc
  installeroutput "MongoDB daemon installed here: "
else
  installeroutput "Found MongoDB already installed at: "
fi
installeroutput `which mongod`
###############################################################################
#   Done installing MongoDB                                                   #
###############################################################################




###############################################################################
#  Installing Workflow Components                                             #
#   - mostly using pip install of package list                                #
#   - OpenMM is separately downloaded from the location:                      #
#https://simtk.org/frs/download_confirm.php/file/4904/OpenMM-7.0.1-Linux.zip  #
#     requiring a login. Unzip it in the directory $OPENMM_LOC                #
#     and this installer will create an instance in the                       #
#     virtualenv.                                                             #
###############################################################################

# TODO use an ADMDRP_PACKAGES variable
#      to give $ADMDRP_DATA/admdrp/
# Nothing will work if this is False
# or these vars aren't already given by 
# a prior installation
### For each install
APPEND_BASHRC=True
# Turn this off to prevent env copies
# appended to bashrc with reinstalls
ADD_ENVIRONMENT=True

# Configuring the installation
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

# Start Installation
module load python
virtualenv $INSTALL_HOME$FOLDER_ADMDRP_ENV

if [ $ADD_ENVIRONMENT = True ]
then
  #installeroutput "Appending virtualenv activate script"
  #RP_VARSLOC=$INSTALL_HOME$FOLDER_ADMDRP_ENV/bin/activate
  installeroutput "Appending bashrc with Environment Vars for Workflow"
  RP_VARSLOC=~/.bashrc

  echo "# This is home to the execution working directories" >> $RP_VARSLOC
  echo "# ie the Radical Pilot Sandbox" >> $RP_VARSLOC
  echo "export RADICAL_SANDBOX=$MEMBERWORK/bip149/radical.pilot.sandbox/" >> $RP_VARSLOC

  echo "#ENVIRONMENT VARIABLES to Workflow control output" >> $RP_VARSLOC
  echo "#export RADICAL_PILOT_PROFILE=\"True\"" >> $RP_VARSLOC
  echo "#export RADICAL_PROFILE=\"True\"" >> $RP_VARSLOC
  echo "export ADMD_PROFILE=\"INFO\"" >> $RP_VARSLOC
  echo "# These ones are for RP DEBUG verbosity" >> $RP_VARSLOC
  echo "#export RADICAL_SAGA_PTY_VERBOSE=\"DEBUG\"" >> $RP_VARSLOC
  echo "#export RADICAL_VERBOSE=\"DEBUG\"" >> $RP_VARSLOC
  echo -e "\n# REQUIRED ENVIRONMENT VARIABLES" >> $RP_VARSLOC
  echo "export LD_PRELOAD=/lib64/librt.so.1" >> $RP_VARSLOC
  echo "export RP_ENABLE_OLD_DEFINES=True" >> $RP_VARSLOC
fi

if [ $APPEND_BASHRC = True ]
then
  echo "Adding AdaptiveMD-RP Environment Variables to bashrc"
  echo "export ${ENV_BASE}_ENV=$INSTALL_HOME$FOLDER_ADMDRP_ENV" >> ~/.bashrc
  echo "export ${ENV_BASE}_ENV_ACTIVATE=\${${ENV_BASE}_ENV}bin/activate" >> ~/.bashrc
  echo "export ${ENV_BASE}_RUNS=$INSTALL_HOME${FOLDER_ADMDRP}runs/" >> ~/.bashrc
  echo "export ${ENV_BASE}_ADAPTIVEMD=$INSTALL_HOME${FOLDER_ADMDRP}adaptivemd/" >> ~/.bashrc
  echo "export ${ENV_BASE}_DATA=$INSTALL_HOME$FOLDER_ADMDRP" >> ~/.bashrc
  installeroutput "FOR YOUR WORKFLOW TO RUN PROPERLY, UNCOMMENT THIS"
  installeroutput "LINE IN YOUR .bashrc FILE"
  installeroutput "source \$ADMDRP_ENV_ACTIVATE"
  echo "#source \$ADMDRP_ENV_ACTIVATE" >> ~/.bashrc
fi

source ~/.bashrc
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

installeroutput "Appending library path with OpenMM libraries"
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:$OPENMM_INSTALL_LOC$OPENMM_PLUGIN_PREFIX" >> ~/.bashrc
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:$OPENMM_INSTALL_LOC$OPENMM_LIBRARY_PREFIX" >> ~/.bashrc

cd $CWD

