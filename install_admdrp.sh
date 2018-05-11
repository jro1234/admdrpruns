#!/bin/bash


# TODO Fix for this, exit won't
#      work currently because
#      the mkdir's below will
#      fail when directory is
#      already made (some are
#      duplicates)
# Exit if anything goes wrong
#set -e

# If installing on Mac, the echo'd files contain
# an erroneous '-e'. This is used by to create
# newlines from the "\n" string, but for some
# reason is also getting printed to the files.

# If you're on Titan (or other system
# who has python < 2.7.x) you will need
# to do something like this due to syntax
# changes.
module load python

CWD=`pwd`

# The only check is that the system does (not)
# match "linux", otherwise assumes it is a Mac
# even if you type "Linux", etc.
SYSTEM=linux
#SYSTEM=Mac

# TODO see when this is necessary...
RP_ENV_PRELOAD=true
#RP_ENV_PRELOAD=false

# Use these to change what layers are installed
# if the DB is already installed then nothing
# will happen even if the INSTALL_DB=true
INSTALL_DB=true
INSTALL_APP=true
INSTALL_TASKS=true

## Paths for different installer components
#   - modify however you like...
PREFIX_ALL=$PROJWORK/bip149/$USER/admdrp/
#PREFIX_ALL=$HOME/admdrp/

# Subdirectories to make for runtime data
# and run scripts/io
FOLDER_ADMDRP_DATA=
FOLDER_ADMDRP_DB=mongodb/
FOLDER_ADMDRP_RUNS=
FOLDER_ADMDRP_ENV=admdrpenv/

# CONDA is used to provide the Task environment
#   - AdaptiveMD is not installed here
#     in the current AdaptiveMD-RP setup
INSTALL_CONDA=$PREFIX_ALL/../

# VirtualEnv is used to provide the Application Environment
#   - AdaptiveMD & RP Client, as well as RP Instance
#     run in this environment
INSTALL_ENV=$PREFIX_ALL
INSTALL_ADAPTIVEMD=$PREFIX_ALL
INSTALL_ADMDRP_DATA=$PREFIX_ALL$FOLDER_ADMDRP_DATA
INSTALL_ADMDRP_RUNS=$PREFIX_ALL$FOLDER_ADMDRP_RUNS
INSTALL_ADMDRP_DB=$PREFIX_ALL

## Options & Versions:
ADAPTIVEMD_VERSION=jrossyra/adaptivemd.git
ADAPTIVEMD_BRANCH=rp_integration
ADAPTIVEMD_INSTALLMETHOD="--editable"

CONDA_ENV_NAME=admdtaskenv
CONDA_ENV_PYTHON=2.7
CONDA_VERSION=2
CONDA_PKG_VERSION=4.3.23

NUMPY_VERSION_TASK=1.12
NUMPY_VERSION_APP=1.12
OPENMM_VERSION=7.0
MONGODB_VERSION=3.3.0
PYMONGO_VERSION=3.5


##################################
#                                #
#   End of Settings              #
#                                #
##################################
# TODO something a bit better...
if [ "$SYSTEM" == "linux" ]; then
  echo "configuring for Linux"
  CONDA_SYSTEM=Linux
  MONGODB_SYSTEM=linux
else
  echo "configuring for Mac"
  CONDA_SYSTEM=MacOSX
  MONGODB_SYSTEM=osx
  ADAPTIVEMD_INSTALLMETHOD=
fi

# TODO format conda vs virtualenv
#      equal signs for versioning
#
#

# Application Package dependencies
ADMD_APP_PKG="pyyaml zmq six ujson numpy==$NUMPY_VERSION_APP"

# Task Package dependencies
ADMD_TASK_PKG="numpy=$NUMPY_VERSION_TASK openmm=$OPENMM_VERSION mdtraj pyemma"

# CONDA tries to upgrade itself at every turn
# - must stop it if installing in the outer conda
# - inside an env, conda won't update so its ok
if [[ -z "$CONDA_ENV_NAME" ]]; then
  ADMD_TASK_PKG+=" conda=$CONDA_PKG_VERSION"
fi

echo "AdaptiveMD Task Stack Installer: ", $ADMD_TASK_PKG

################################################################################
#  Create Root folder                                                          #
################################################################################
if [ ! -d $PREFIX_ALL ]; then
  mkdir -p $PREFIX_ALL
fi

if [ $INSTALL_DB = true ]; then
  ################################################################################
  #  Install MongoDB                                                             #
  ################################################################################
  if [ ! -x "$(command -v mongod)" ]; then
    mkdir -p $INSTALL_ADMDRP_DB
    cd $INSTALL_ADMDRP_DB
    echo "Installing Mongo in: $INSTALL_ADMDRP_DB"
    curl -O https://fastdl.mongodb.org/$MONGODB_SYSTEM/mongodb-$MONGODB_SYSTEM-x86_64-$MONGODB_VERSION.tgz
    tar -zxvf mongodb-$MONGODB_SYSTEM-x86_64-$MONGODB_VERSION.tgz
    mv mongodb-$MONGODB_SYSTEM-x86_64-$MONGODB_VERSION/ $FOLDER_ADMDRP_DB
    mkdir -p $INSTALL_ADMDRP_DB${FOLDER_ADMDRP_DB}data/db
    rm mongodb-$MONGODB_SYSTEM-x86_64-$MONGODB_VERSION.tgz
    echo "# APPENDING PATH VARIABLE with AdaptiveMD Environment" >> ~/.bashrc
    echo "export ADMDRP_DB=$INSTALL_ADMDRP_DB$FOLDER_ADMDRP_DB" >> ~/.bashrc
    echo "export PATH=$INSTALL_ADMDRP_DB${FOLDER_ADMDRP_DB}bin:\$PATH" >> ~/.bashrc
    echo "Done installing Mongo, appended PATH with mongodb bin folder"
    # Mongo should default to using /tmp/mongo-27017.sock as socket
    echo -e "net:\n   unixDomainSocket:\n      pathPrefix: ${INSTALL_ADMDRP_DB}${FOLDER_ADMDRP_DB}data/\n   bindIp: 0.0.0.0" > ${INSTALL_ADMDRP_DB}${FOLDER_ADMDRP_DB}/mongo.cfg
    source ~/.bashrc
    echo "MongoDB daemon installed here: "
  else
    echo "Found MongoDB already installed at: "
  fi
  which mongod
fi


#TODO some of these variables need to be moved to bashrc by default
#      and away from the virtualenv activate script
if [ $INSTALL_APP = true ]; then
  ################################################################################
  #  Install Env                                                                 #
  ################################################################################
  if [ ! -d "$INSTALL_ENV$FOLDER_ADMDRP_ENV" ]; then
    mkdir -p $INSTALL_ENV
    cd $INSTALL_ENV
    virtualenv $INSTALL_ENV$FOLDER_ADMDRP_ENV
    echo "export ADMDRP_ENV=$INSTALL_ENV$FOLDER_ADMDRP_ENV" >> ~/.bashrc
    echo "export ADMDRP_ENV_ADAPTIVEMD=\${ADMDRP_ENV}/lib/python2.7/site-package/adaptivemd/" >> ~/.bashrc
    echo "export ADMDRP_ENV_ACTIVATE=\${ADMDRP_ENV}bin/activate" >> ~/.bashrc
    echo -e "\n# MORE ENVIRONMENT VARIABLES" >> $INSTALL_ENV$FOLDER_ADMDRP_ENV/bin/activate
    if [ $RP_ENV_PRELOAD = true ]; then
      echo "ADDING PRELOAD LINE TO ENV ACTIVATE SCRIPT"
      echo "export LD_PRELOAD=/lib64/librt.so.1" >> $INSTALL_ENV$FOLDER_ADMDRP_ENV/bin/activate
    fi
    echo "export RP_ENABLE_OLD_DEFINES=True" >> $INSTALL_ENV$FOLDER_ADMDRP_ENV/bin/activate
    echo "export RADICAL_PILOT_DBURL='mongodb://rp:rp@ds015335.mlab.com:15335/rp'" >> $INSTALL_ENV$FOLDER_ADMDRP_ENV/bin/activate
    source ~/.bashrc
  else
    echo "Found VirtualEnv already installed at: "
    echo $INSTALL_ENV$FOLDER_ADMDRP_ENV
  fi

  ################################################################################
  #  Install AdaptiveMD (and RP via AdaptiveMD package specifications)           #
  ################################################################################
  source $ADMDRP_ENV_ACTIVATE
  if [ ! -d "$INSTALL_ADAPTIVEMD/adaptivemd" ]; then
    mkdir -p $INSTALL_ADAPTIVEMD
    cd $INSTALL_ADAPTIVEMD
    git clone https://github.com/$ADAPTIVEMD_VERSION
    cd adaptivemd
    git checkout $ADAPTIVEMD_BRANCH
    pip install $ADMD_APP_PKG
    pip install $ADAPTIVEMD_INSTALLMETHOD .
    python -W ignore -c "import adaptivemd" || echo "something wrong with adaptivemd install"
    echo "if no errors then AdaptiveMD & dependencies installed"
    echo "export ADMDRP_ADAPTIVEMD=$INSTALL_ADAPTIVEMD/adaptivemd/" >> ~/.bashrc
  else
    echo "Seems AdaptiveMD is already installed, source located here:"
    echo $INSTALL_ADAPTIVEMD/adaptivemd
    python -W ignore -c "import adaptivemd; print adaptivemd.__version__"
  fi
  deactivate

  ################################################################################
  #   Copy the running scripts over and make data directory                      #
  ################################################################################
  mkdir -p $INSTALL_ADMDRP_DATA
  mkdir -p $INSTALL_ADMDRP_RUNS
  cp -r $CWD/runs/ $INSTALL_ADMDRP_RUNS
  
  echo "export ADMDRP_DATA=$INSTALL_ADMDRP_DATA" >> ~/.bashrc
  echo "export ADMDRP_RUNS=${INSTALL_ADMDRP_RUNS}runs/" >> ~/.bashrc
fi


if [ $INSTALL_TASKS = true ]; then
  ################################################################################
  #  Install Miniconda                                                           #
  ################################################################################
  if [ -z ${CONDAPATH+x} ]; then
    mkdir -p $INSTALL_CONDA
    cd $INSTALL_CONDA
    curl -O https://repo.continuum.io/miniconda/Miniconda$CONDA_VERSION-latest-Linux-x86_64.sh
    bash Miniconda$CONDA_VERSION-latest-Linux-x86_64.sh -p ${INSTALL_CONDA}miniconda$CONDA_VERSION/
    echo "Miniconda conda executable here: "
    echo "export CONDAPATH=${INSTALL_CONDA}miniconda$CONDA_VERSION/bin/" >> ~/.bashrc
    source ~/.bashrc
    PATH=$CONDAPATH:$PATH
    conda config --append channels conda-forge
    conda config --append channels omnia
    conda install conda=$CONDA_PKG_VERSION
    rm Miniconda$CONDA_VERSION-latest-Linux-x86_64.sh
  else
    echo "Conda is already installed, binaries folder located here:"
    PATH=$CONDAPATH:$PATH
    echo $CONDAPATH
  fi
  
  ################################################################################
  #  Install Conda Environment for AdaptiveMD                                    #
  ################################################################################
  if [[ ! -z "$CONDA_ENV_NAME" ]]; then
    ENVS=`conda env list`
    if ! echo "$ENVS" | grep -q "$CONDA_ENV_NAME"; then
      echo "Creating and Activating new conda env: $CONDA_ENV_NAME"
      conda create -n $CONDA_ENV_NAME python=$CONDA_ENV_PYTHON
  ################################################################################
  #   Install AdaptiveMD Task Stack in Conda Environment                         #
  ################################################################################
      source $CONDAPATH/activate $CONDA_ENV_NAME
      echo "Installing these Packages in AdaptiveMD Task Layer"
      echo $ADMD_TASK_PKG
      conda install $ADMD_TASK_PKG
      source deactivate
    fi
  fi
fi

  
################################################################################
#  Finalize & Cleanup                                                          #
################################################################################
cd $CWD

module unload python/2.7.9

