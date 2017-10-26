#!/bin/bash

CWD=`pwd`

## Paths for different installer components
#taskstack#INSTALL_CONDA=$PROJWORK/bip149/$USER/
INSTALL_ENV=$PROJWORK/bip149/$USER/admdrp/
INSTALL_ADAPTIVEMD=$PROJWORK/bip149/$USER/admdrp/adaptivemd/
INSTALL_ADMDRP_DATA=$PROJWORK/bip149/$USER/admdrp/
INSTALL_ADMDRP_RUNS=$PROJWORK/bip149/$USER/admdrp/runs

## Options & Versions:
ADAPTIVEMD_VERSION=jrossyra/adaptivemd.git
ADAPTIVEMD_BRANCH=rp_integration
#del#ADAPTIVEMD_INSTALLMETHOD=install

# This has given trouble !to only me! when loading
# inside of a job on Titan, so currently
# we have everything install under the
# *root* conda
#taskstack#CONDA_ENV_NAME=py27
#taskstack#CONDA_ENV_VERSION=2.7
#taskstack#CONDA_VERSION=2
#taskstack#CONDA_PKG_VERSION=4.3.23

NUMPY_VERSION=1.12
#taskstack#OPENMM_VERSION=7.0
MONGODB_VERSION=3.3.0
PYMONGO_VERSION=3.3

# Application Package dependencies
ADMD_APP_PKG="pyyaml six ujson numpy=$NUMPY_VERSION"
# Task Package dependencies
#taskstack#ADMD_TASK_PKG="openmm=$OPENMM_VERSION mdtraj pyemma"

# CONDA tries to upgrade itself at every turn
# - must stop it if installing in the outer conda
# - inside an env, conda won't update so its ok
if [[  -z "$CONDA_ENV_NAME" ]]; then
  ADMD_APP_PKG+=" conda=$CONDA_PKG_VERSION"
  #taskstack#ADMD_TASK_PKG+=" conda=$CONDA_PKG_VERSION"
fi


###############################################################################
#  Install Env, RP, AdaptiveMD
###############################################################################
mkdir $INSTALL_ENV
cd $INSTALL_ENV
module load python/2.7.9
virtualenv $INSTALL_ENV/admdrpenv

echo "export ADMDRP_ENV=${INSTALL_ENV}admdrpenv/" >> ~/.bashrc

echo "# MORE ENVIRONMENT VARIABLES" >> ${INSTALL_ENV}/admdrpenv/bin/activate
echo "export LD_PRELOAD=/lib64/librt.so.1" >> ${INSTALL_ENV}/admdrpenv/bin/activate
echo "export RP_ENABLE_OLD_DEFINES=True" >> ${INSTALL_ENV}/admdrpenv/bin/activate
echo "export RADICAL_PILOT_DBURL='mongodb://admin:v3ry2r4d1c4l@openshift.ccs.ornl.gov:30008/rp'" >> ${INSTALL_ENV}/admdrpenv/bin/activate

source ~/.bashrc
source ${ADMDRP_ENV}bin/activate

#mkdir $INSTALL_ADAPTIVEMD
#cd $INSTALL_ADAPTIVEMD
git clone https://github.com/$ADAPTIVEMD_VERSION
cd adaptivemd
git checkout $ADAPTIVEMD_BRANCH
pip install numpy==$NUMPY_VERSION
pip install pyyaml
pip install six
pip install zmq

deactivate
source ${ADMDRP_ENV}bin/activate

pip install .
python -c "import adaptivemd" || echo "something wrong with adaptivemd install"

mkdir $INSTALL_ADMDRP_DATA
cd $INSTALL_ADMDRP_DATA
cp -r $CWD/runs/ ./

echo "export ADMDRP_DATA=${INSTALL_ADMDRP_DATA}" >> ~/.bashrc
echo "export ADMDRP_RUNS=${INSTALL_ADMDRP_RUNS}" >> ~/.bashrc

cd $CWD
echo "if no errors then AdaptiveMD & dependencies installed"

source ~/.bashrc

deactivate

module unload python/2.7.9
###################
#
# AdaptiveMD Task Stack
#
###################

#pip install ujson pyyaml numpy cython pymongo==$PYMONGO_VERSION
#pip install pyemma==$PYEMMA_VERSION openmm==$OPENMM_VERSION mdtraj

