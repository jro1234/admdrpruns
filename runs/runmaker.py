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
    args = parser.parse_args()

    run_filename = args.template
    run_template = 'runpackage/{0}.template'.format(run_filename)
    print("Reading run script template from:\n", run_template)

    run_name = '{0}'.format(args.project_name)
    run_folder = 'runs/{0}/'.format(run_name)

    print("Job will be located in directory:\n", run_folder)
    run_file = run_folder + run_filename

    os.mkdir(run_folder)

    ## TODO args to build run script here
    run_scripts = ['configuration.cfg']
    for runscript in run_scripts:
        shutil.copy('runpackage/'+runscript, run_folder+runscript)

    with open(run_template, 'r') as f_in, open(run_file, 'w') as f_out:
        text = ''.join([line for line in f_in])
        f_out.write(text.format(
            project_name=args.project_name,
            system_name=args.system_name,
            longts='--longts' if args.longts else '',
            randomly='-R' if args.randomly else '',
            strategy=args.strategy,
            dblocation=args.dblocation
            platform=args.platform,
            n_rounds=args.n_rounds,
            minlength=args.minlength if args.minlength > args.length else args.length,
            n_ext=args.n_ext,
            mk_model= '-M' if args.model else '',
            n_traj=args.n_traj,
            prot=args.prot if not args.longts else args.prot * 2 / 5,
            all=args.all if not args.longts else args.all * 2 / 5,
            length=args.length,))

