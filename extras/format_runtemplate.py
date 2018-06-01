#!/usr/bin/env/python


import sys, os
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file
from distutils.errors import DistutilsFileError



if __name__ == "__main__":

    print sys.argv
    run_template,ntraj,nsteps,batchsize,batchwait,progress,run_folder = sys.argv[1:]

    run_files    = os.listdir(run_template)
    f_exec       = "run_admdrp.sh"
    run_execfile = os.path.join(run_template, f_exec)

    if not os.path.exists(run_folder):

        os.mkdir(run_folder)

        for f in run_files:
            src = os.path.join(run_template,f)
            dest = os.path.join(run_folder,f)
            if f == f_exec:
                with open(src, 'r') as tpt, open(dest, 'w') as out:
                    _tpt = tpt.read()
                    out.write(_tpt.format(
                            ntraj=ntraj,
                            nsteps=nsteps,
                            batchsize=batchsize,
                            batchwait=batchwait,
                            progress=progress,
                            ))

            else:
                try:
                    copy_file(src, dest)
                except DistutilsFileError:
                    copy_tree(src, dest)

    else:
        print "This folder already exists: {}".format(run_folder)
