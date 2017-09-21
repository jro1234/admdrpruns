#!/usr/bin/env/python

'''
    Usage:
           $ python run_admd.py [name] [additional options]

'''

from __future__ import print_function

# Import custom adaptivemd init & strategy functions
from _argparser import argparser
from __run_admd import init_project, strategy_pllMD
from adaptivemd.rp.client import Client
from sys import exit
import time



def calculate_request(n_workload, n_rounds, n_steps, steprate):

    cpus = n_workload * 16
    gpus = n_workload
    wallminutes = int(n_steps * n_rounds / steprate / 60)

    return cpus, wallminutes, gpus 


if __name__ == '__main__':

    parser = argparser()
    args = parser.parse_args()

    print("Initializing Project named: ", args.project_name)
    # send selections and frequencies as kwargs
    #fix1#project = init_project(p_name, del_existing, **freq)
    print("Worker threads: {0}".format(args.w_threads))
    print(args)
    project = init_project(args.project_name,
                           args.system_name,
                           args.all,
                           args.prot,
                           args.platform,
                           args.dblocation)

    if args.init_only:
        print("Leaving project initialized without tasks")
        exit(0)

    else:
        print("Adding event to project from function:")
        print(strategy_pllMD)

        if  args.longts:
            ext = '-5'
        else:
            ext = '-2'

        nm_engine = 'openmm' + ext
        nm_modeller_1 = 'pyemma-ca' + ext
        nm_modeller_2 = 'pyemma-ionic' + ext

        engine = project.generators[nm_engine]

        if args.model:
            modellers = list()
            modellers.append(project.generators[nm_modeller_1])
            modellers.append(project.generators[nm_modeller_2])

        else:
            modellers = None


        client = Client(project.storage._db_url, project.name)
        cpus, wallminutes, gpus = calculate_request(
                                      args.n_traj+1,
                                      args.n_rounds,
                                      args.length,
                                      steprate=250)

        project.request_resource(cpus, wallminutes, gpus, 'current')
        client.start()

        start_time = time.time()
        print("TIMER Project add event {0:.5f}", time.time())
        project.add_event(strategy_pllMD(
            project, engine, args.n_traj,
            args.n_ext, args.length,
            modellers=modellers,
            fixedlength=args.fixedlength,
            minlength=args.minlength,
            n_rounds=args.n_rounds,
            randomly=args.randomly,
            longest=args.all))

        print("Triggering project")
        project.wait_until(project.events_done)

        end_time = time.time()
        print("Start Time: {0}\nEnd Time: {1}"
              .format(start_time, end_time))

    print("Exiting Event Script")
    project.close()

