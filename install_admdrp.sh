#!/bin/bash

CWD=`pwd`
### Paths for different installer components
#INSTALL_CONDA=$PROJWORK/bip149/$USER/
INSTALL_ENV=$PROJWORK/bip149/$USER/admdrp/
## these ones saved to environment variables
INSTALL_ADAPTIVEMD=$PROJWORK/bip149/$USER/adaptivemd/
INSTALL_ADMDRP_DATA=$MEMBERWORK/bip149/admdrp/
INSTALL_ADMDRP_RUNS=$MEMBERWORK/bip149/admdrp/runs
#INSTALL_ADMD_DB=$PROJWORK/bip149/$USER/


## Options & Version configuration stuff:
ADAPTIVEMD_VERSION=jrossyra/adaptivemd.git
ADAPTIVEMD_BRANCH=rp_compat
GPU_ENV=cudatoolkit
#CONDA_VERSION=2
OPENMM_VERSION=7.0
#MONGODB_VERSION=3.3.0
PYMONGO_VERSION=3.3
PYEMMA_VERSION=2.4

## Environment preparation:
module load $GPU_ENV

###############################################################################
#
#  Install Env, RP, AdaptiveMD
#
###############################################################################
mkdir $INSTALL_ENV
cd $INSTALL_ENV
module load python/2.7.9
#pip install virtualenv
virtualenv --python=`which python` $INSTALL_ENV/admdrpenv
echo "export ADMDRP_ENV=${INSTALL_ENV}admdrpenv/" >> ~/.bashrc

source ~/.bashrc
source ${ADMDRP_ENV}bin/activate
which python
mkdir rp
cd rp/

git clone https://github.com/radical-cybertools/saga-python.git
git clone https://github.com/radical-cybertools/radical.pilot.git
git clone https://github.com/radical-cybertools/radical.utils.git

pip install radical.utils/ saga-python/ radical.pilot/
# what to do for this on titan?
#cd ~ && "/bin/cp" -v  "/tmp/rs_pty_staging_4rWMPI.tmp" ".saga/adaptors/shell_job//wrapper.sh"

cd $INSTALL_ADAPTIVEMD
#git clone https://github.com/$ADAPTIVEMD_VERSION
git checkout $ADAPTIVEMD_BRANCH
#python setup.py develop
pip install ujson pyyaml numpy pymongo==$PYMONGO_VERSION
pip install .
python -c "import adaptivemd" || echo "something wrong with adaptivemd install"
#echo "export ADAPTIVEMD=${INSTALL_ADAPTIVEMD}adaptivemd/" >> ~/.bashrc

mkdir $INSTALL_ADMDRP_DATA
cd $INSTALL_ADMDRP_DATA
cp -r $CWD/runs/ ./
echo "export ADMDRP_DATA=${INSTALL_ADMDRP_DATA}">> ~/.bashrc
echo "export ADMDRP_RUNS=${INSTALL_ADMDRP_RUNS}" >> ~/.bashrc

cd $CWD
echo "if no errors then AdaptiveMD & dependencies installed"

deactivate

###################
#
# AdaptiveMD Task Stack
#
###################

#pip install ujson pyyaml numpy cython pymongo==$PYMONGO_VERSION
#pip install pyemma==$PYEMMA_VERSION openmm==$OPENMM_VERSION mdtraj

