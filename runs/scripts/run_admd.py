#!/usr/bin/env/python

'''
    Usage:
           $ python run_admd.py [name] [additional options]

'''

from __future__ import print_function

# Import custom adaptivemd init & strategy functions
from _argparser import argparser
from __run_admd import init_project, strategy_function
from adaptivemd.rp.client import Client
from sys import exit
import time



def calculate_request(n_workload, n_rounds, n_steps, steprate=50):
    '''
    Calculate the parameters for resource request done by RP.
    The workload to execute will be assessed to estimate these
    required parameters.
    -- Function in progress, also requires a minimum time
       and cpus per node. Need to decide how these will be
       calculated and managed in general.

    Parameters
    ----------
    n_workload : <int>
    For now, this is like the number of nodes that will be used.
    With OpenMM Simulations and the 1-node PyEMMA tasks, this is
    also the number of tasks per workload. Clearly a name conflict...

    n_rounds : <int>
    Number of workload iterations or rounds. The model here
    is that the workloads are approximately identical, maybe
    some will not include new modeller tasks but otherwise
    should be the same.

    n_steps : <int>
    Number of simulation steps in each task.

    steprate : <int>
    Number of simulation steps per minute. Use a low-side
    estimate to ensure jobs don't timeout before the tasks
    are completed.
    '''
    # TODO get this from the configuration and send to function
    cpu_per_node = 16
    cpus = n_workload * cpu_per_node
    nodes = n_workload
    gpus = n_workload
    print("n_steps: ", n_steps, "\nn_rounds: ", n_rounds, "\nsteprate: ", steprate)
    # 5 minutes padding for initialization & such
    # as the minimum walltime
    wallminutes = 10 + int(float(n_steps) * n_rounds / steprate)
    return cpus, nodes, wallminutes, gpus 


if __name__ == '__main__':

    parser = argparser()
    args = parser.parse_args()

    print("Initializing Project named: ", args.project_name)
    # send selections and frequencies as kwargs
    #fix1#project = init_project(p_name, del_existing, **freq)
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
        print(strategy_function)

        if  args.longts:
            ext = '-5'
        else:
            ext = '-2'

        nm_engine = 'openmm' + ext
        nm_modeller = args.modeller + ext

        engine = project.generators[nm_engine]
        modeller = project.generators[nm_modeller]

        print("dburl: ", project.storage._db_url)

        cpus, nodes, walltime, gpus = calculate_request(
                                      args.n_traj+1,
                                      args.n_rounds,
                                      args.length)#, steprate)

        print("Resource request arguments: ")
        print("cpus: ", cpus)
        print("walltime: ", walltime)
        print("gpus: ", gpus)

        project.request_resource(cpus, walltime, gpus, 'current')

        client = Client(project.storage._db_url, project.name)
        client.start()

        start_time = time.time()
        print("TIMER Project add event {0:.5f}".format(time.time()))
        project.add_event(strategy_function(
            project, engine, args.n_traj,
            args.n_ext, args.length,
            modeller=modeller,
            fixedlength=True,#args.fixedlength,
            minlength=args.minlength,
            n_rounds=args.n_rounds,
            environment=args.environment,
            activate_prefix=args.activate_prefix,
            virtualenv=args.virtualenv,
            longest=args.all,
            cpu_threads=args.threads,
            ))

        print("Triggering project")
        project.wait_until(project.events_done)

        end_time = time.time()
        print("Start Time: {0}\nEnd Time: {1}"
              .format(start_time, end_time))

        client.stop()

    print("Exiting Event Script")
    project.close()


