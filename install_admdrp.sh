#!/bin/bash

CWD=`pwd`
### Paths for different installer components
INSTALL_ENV=$PROJWORK/bip149/$USER/admdrp/
INSTALL_ADAPTIVEMD=$PROJWORK/bip149/$USER/admdrp/adaptivemd/
INSTALL_ADMDRP_DATA=$MEMBERWORK/bip149/admdrp/
INSTALL_ADMDRP_RUNS=$MEMBERWORK/bip149/admdrp/runs


## Options & Version configuration stuff:
ADAPTIVEMD_VERSION=jrossyra/adaptivemd.git
ADAPTIVEMD_BRANCH=rp_integration

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
echo "export ADMDRP_DATA=${INSTALL_ADMDRP_DATA}">> ~/.bashrc
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

