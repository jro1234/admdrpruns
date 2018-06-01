#!/bin/bash


# del #module load python
CWD=`pwd`

INSTALL_CONDA=$PROJWORK/bip149/$USER/
CONDA_ENV_NAME=admdenv
CONDA_ENV_PYTHON=2.7
CONDA_VERSION=2
CONDA_PKG_VERSION=
OPENMM_VERSION=7.0
ADMD_TASK_PKG="openmm=$OPENMM_VERSION mdtraj"
if [ -z ${TASKCONDAPATH+x} ]; then
  cd $INSTALL_CONDA
  curl -O https://repo.continuum.io/miniconda/Miniconda$CONDA_VERSION-latest-Linux-x86_64.sh
  bash Miniconda$CONDA_VERSION-latest-Linux-x86_64.sh -p ${INSTALL_CONDA}miniconda$CONDA_VERSION/
  echo "Miniconda conda executable here: "
  echo "export TASKCONDAPATH=${INSTALL_CONDA}miniconda$CONDA_VERSION/bin" >> ~/.bashrc
  echo "export TASKCONDAACTIVATE=\$TASKCONDAPATH/activate" >> ~/.bashrc
  source ~/.bashrc
  PATH=$TASKCONDAPATH:$PATH
  conda config --append channels conda-forge
  conda config --append channels omnia
  conda install conda=$CONDA_PKG_VERSION
  rm Miniconda$CONDA_VERSION-latest-Linux-x86_64.sh
fi
which conda
if [[ ! -z "$CONDA_ENV_NAME" ]]; then
  ENVS=`$TASKCONDAPATH/conda env list`
  if ! echo "$ENVS" | grep -q "$CONDA_ENV_NAME"; then
    echo "Creating and Activating new conda env: $CONDA_ENV_NAME"
    conda create -n $CONDA_ENV_NAME python=$CONDA_ENV_PYTHON
    echo "ADMD_ENV_NAME=$CONDA_ENV_NAME"
  fi
  source $TASKCONDAPATH/activate $CONDA_ENV_NAME
fi
echo "Installing these Packages in AdaptiveMD Task Layer"
echo $ADMD_TASK_PKG
conda install $ADMD_TASK_PKG
echo "Deactivating conda env: $CONDA_ENV_NAME"
source deactivate

