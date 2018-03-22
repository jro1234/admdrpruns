#!/usr/bin/env/ python



from __future__ import print_function
from datetime import datetime
from subprocess import call
from shlex import split
import shutil
import sys, os

from scripts._argparser import argparser



if __name__ == "__main__":

    parser = argparser()
    args   = parser.parse_args()


    runs           = 'runpackage/'
    run_filename   = args.template
    margs_filename = 'margs.cfg'
    margs_template = runs + '{0}.template'.format(margs_filename)
    ## TODO args to build run script here
    run_scripts = ['configuration.cfg']
    if args.launch:
        run_scripts += ['launch1.sh', 'launch2.sh', 'startclient.sh', 'startdb.sh']
        run_filename = 'launch_admdrp.pbs'

    run_template   = runs + '{0}.template'.format(run_filename)

    print("Reading run script template from:\n", run_template)

    run_name   = '{0}'.format(args.project_name)
    run_folder = 'runs/{0}/'.format(run_name)

    print("Job will be located in directory:\n", run_folder)
    run_file   = run_folder + run_filename
    margs_file = run_folder + margs_filename

    if not os.path.isdir(run_folder):
        os.mkdir(run_folder)

        with open(margs_template, 'r') as f_in, open(margs_file, 'w') as f_out:
            text = ''.join([line for line in f_in])
            f_out.write(text.format(
                project_name = args.project_name,
                clust_stride = args.clust_stride,
                tica_stride  = args.tica_stride,
                tica_lag     = args.tica_lag,
                tica_dim     = args.tica_dim,
                msm_states   = args.msm_states,
                msm_lag      = args.msm_lag))

        for runscript in run_scripts:
            shutil.copy('runpackage/'+runscript, run_folder+runscript)

        with open(run_template, 'r') as f_in, open(run_file, 'w') as f_out:
            text = ''.join([line for line in f_in])
            f_out.write(text.format(
                project_name = args.project_name,
                system_name  = args.system_name,
                longts       = '--longts' if args.longts else '',
                strategy     = args.strategy,
                dblocation   = args.dblocation,
                platform     = args.platform,
                environment  = '-e '+args.environment if args.environment else '',
                activate_prefix = '-A '+args.activate_prefix if args.activate_prefix else '',
                virtualenv   = '-w '+args.virtualenv if args.virtualenv else '',
                n_rounds     = args.n_rounds,
                minlength    = args.minlength if args.minlength > args.length else args.length,
                n_ext        = args.n_ext,
                modeller     = '-M {0}'.format(args.modeller) if args.modeller else '',
                n_traj       = args.n_traj,
                threads      = args.threads,
                prot         = args.prot if not args.longts else args.prot * 2 / 5,
                all          = args.all if not args.longts else args.all * 2 / 5,
                length       = args.length,))

    else:
        print("\nExiting runmaker script\nA run already exists in folder called:\n", run_folder)
        sys.exit(0)
