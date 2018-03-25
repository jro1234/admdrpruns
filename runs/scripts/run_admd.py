#!/usr/bin/env/python

'''
    Usage:
           $ python run_admd.py [name] [additional options]

    Timestamp format:
       >>>  TIMER <object> <label> <time>

     - object: single word, what we are monitoring
     - label: a few words, description of timestamp
     - timestamp: float, the time

      $ if 'TIMER' in timestampline:
      $     timestamp = timestampline.split('TIMER')[-1].strip().split()
      $     obj = str(timestamp[0])
      $     label = [str(l) for l in timestamp[1:-1]]
      $     t = float(timestamp[-1])

'''

# Import custom adaptivemd init & strategy functions
from _argparser import argparser
from __run_admd import init_project, strategy_function, get_logger, formatline
from adaptivemd.rp.client import Client
from adaptivemd import Task
import sys
import time

logger = get_logger(logname=__name__)#, logfile='run_admdrp.'+__name__+'.log')


uuid = lambda x: x.__uuid__

# success, cancelled, fail, halted
# -  no need for dummy since it will always
#    be an existing task, and not checked
final_states = Task.FINAL_STATES + Task.RESTARTABLE_STATES
task_done = lambda ta: ta.state in final_states


def calculate_request(size_workload, n_workloads, n_steps, steprate=150):
    '''
    Calculate the parameters for resource request done by RP.
    The workload to execute will be assessed to estimate these
    required parameters.
    -- Function in progress, also requires a minimum time
       and cpus per node. Need to decide how these will be
       calculated and managed in general.

    Parameters
    ----------
    size_workload : <int>
    For now, this is like the number of nodes that will be used.
    With OpenMM Simulations and the 1-node PyEMMA tasks, this is
    also the number of tasks per workload. Clearly a name conflict...

    n_workloads : <int>
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
    rp_cpu_overhead = 16
    cpu_per_node = 16
    cpus = size_workload * cpu_per_node + rp_cpu_overhead
    # nodes is not used
    nodes = size_workload 
    gpus = size_workload
    logger.info(formatline(
        "\nn_steps: {0}\nn_workloads: {1}\nsteprate: {2}".format(
                         n_steps, n_workloads, steprate)))

    # 5 minutes padding for initialization & such
    # as the minimum walltime
    wallminutes = 10 + int(float(n_steps) * n_workloads / steprate)
    return cpus, nodes, wallminutes, gpus 


if __name__ == '__main__':

    project = None

    try:

        parser = argparser()
        args = parser.parse_args()

        logger.info("Initializing Project named: " + args.project_name)
        # send selections and frequencies as kwargs
        #fix1#project = init_project(p_name, del_existing, **freq)
        logger.info(formatline("\n{}".format(args)))
        logger.info(formatline("TIMER Project opening {0:.5f}".format(time.time())))
        project = init_project(args.project_name,
                               args.system_name,
                               args.all,
                               args.prot,
                               args.platform,
                               reinitialize=args.reinitialize,
                               #args.dblocation
                              )

        logger.info(formatline("TIMER Project opened {0:.5f}".format(time.time())))

        logger.info("AdaptiveMD dburl: {}".format(project.storage._db_url))


        if args.init_only:
            logger.info("Leaving project '{}' initialized without tasks".format(project.name))

        else:
            logger.info("Adding event to project from function: {0}, {1}".format(project.name, strategy_function))

            if  args.longts:
                ext = '-5'
            else:
                ext = '-2'

            nm_engine = 'openmm' + ext
            nm_modeller = args.modeller + ext

            engine = project.generators[nm_engine]
            modeller = project.generators[nm_modeller]

            cpus, nodes, walltime, gpus = calculate_request(
                                          args.n_traj+1,
                                          args.n_rounds,
                                          args.length)#, steprate)

            project.request_resource(cpus, walltime, gpus, 'current')

            client = Client(project.storage._db_url, project.name)
            client.start()

            logger.info(formatline("\nResource request arguments: \ncpus: {0}\nwalltime: {1}\ngpus: {2}".format(cpus, walltime, gpus)))
            logger.info("n_rounds: {}".format(args.n_rounds))


            # Tasks not in this list will be checked for
            # a final status before stopping RP Client
            existing_tasks = [uuid(ta) for ta in project.tasks]

            logger.info(formatline("TIMER Project event adding {0:.5f}".format(time.time())))

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

            logger.info(formatline("TIMER Project event added {0:.5f}".format(time.time())))
            logger.info("Triggering project")
            project.wait_until(project.events_done)
            logger.info(formatline("TIMER Project event done {0:.5f}".format(time.time())))

            new_tasks = filter(lambda ta: uuid(ta) not in existing_tasks, project.tasks)

            done = False
            while not done:
                logger.info("Waiting for final state assignments to new states")
                time.sleep(1)
                if all([task_done(ta) for ta in new_tasks]):
                    done = True
                    logger.info("All new tasks finalized")
                    logger.info(formatline("TIMER Project tasks checked {0:.5f}".format(time.time())))

            client.stop()
            project.resources.consume_one()

    except KeyboardInterrupt:
        logger.info("KEYBOARD INTERRUPT")

    finally:

        if project:
            project.close()

        logger.info("Exiting Event Script")
        logger.info(formatline("TIMER Project closed {0:.5f}".format(time.time())))


