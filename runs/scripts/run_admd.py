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

#dump_finalize_timestamps = False
dump_finalize_timestamps = True
if dump_finalize_timestamps:
    from __run_tools import pull_final_timestamps
    from pprint import pformat

from adaptivemd import Task, TrajectoryGenerationTask, TrajectoryExtensionTask
import sys
import time

logger = get_logger(logname=__name__)#, logfile='run_admdrp.'+__name__+'.log')


uuid = lambda x: x.__uuid__

# success, cancelled, fail, halted
# -  no need for dummy since it will always
#    be an existing task, and not checked
final_states = Task.FINAL_STATES + Task.RESTARTABLE_STATES
task_done = lambda ta: ta.state in final_states


def calculate_request(size_workload, n_workloads, n_steps, steprate=1000):
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
    wallminutes = 15 + int(float(n_steps) * n_workloads / steprate)

    return cpus, nodes, wallminutes, gpus 


if __name__ == '__main__':

    project = None
    sleeptime = 1

    try:

        parser   = argparser()
        args     = parser.parse_args()

        using_rp = args.rp

        if using_rp:
            from adaptivemd.rp.client import Client

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

        steprate = 1000
        if args.system_name.startswith('chignolin'):
            steprate = 15000
        elif args.system_name.startswith('ntl9'):
            steprate = 11000
        if  args.longts:
            steprate *= 2

        if args.init_only:
            logger.info("Leaving project '{}' initialized without tasks".format(project.name))

        else:
            logger.info("Adding event to project: {0}".format(project.name))

            if  args.longts:
                ext = '-5'
            else:
                ext = '-2'

            nm_engine = 'openmm' + ext
            engine = project.generators[nm_engine]

            # implement `get` method on `Bundle` and return None if no match
            n_traj   = args.n_traj
            n_rounds = args.n_rounds
            length   = args.length
            modeller = None
            if args.modeller:
                nm_modeller = args.modeller + ext
                modeller = project.generators[nm_modeller]

            if not n_traj:
                if not modeller:
                    # TODO FIXME this is not acceptable for general use...
                    #fixit_states = {'pending','running','cancelled'}
                    fixit_states = {'pending','running'}
                    while fixit_states:
                        fix_state = fixit_states.pop()
                        project.tasks._set._document.update_many({"state": fix_state,"_cls":"TrajectoryGenerationTask"}, {"$set":{"state":"created","__dict__.state":"created"}})
                    new_tasks = list(project.tasks.c(TrajectoryGenerationTask).m('state','created')) \
                                +  list(project.tasks.c(TrajectoryExtensionTask).m('state','created'))
                    if not new_tasks:
                        print ("Nothing to clean up, exiting")
                        sys.exit(0)
                    n_rounds  = 1
                    n_traj    = len(new_tasks)
                    length    = max(map(lambda ta: ta.trajectory.length, new_tasks))
                else:
                    # FIXME TODO need a 'held' state for tasks so holdovers in 'created'
                    #            state don't start when we're looking to do a model task
                    pass


            # TODO add rp definition
            print "CALCULATING REQUEST"
            #print args.n_traj, args.modeller, int(bool(args.modeller))
            cpus, nodes, walltime, gpus = calculate_request(
                                          n_traj + int(bool(modeller)),
                                          n_rounds,
                                          length,
                                          steprate,
                                          )

            sfkwargs = dict()
            sfkwargs['num_macrostates'] = 25

            logger.info(formatline("\nResource request arguments: \ncpus: {0}\nwalltime: {1}\ngpus: {2}".format(cpus, walltime, gpus)))
            logger.info("n_rounds: {}".format(args.n_rounds))


            if args.n_traj or args.modeller:
                # Tasks not in this list will be checked for
                # a final status before stopping RP Client
                existing_tasks = [uuid(ta) for ta in project.tasks]

                logger.info("Project event adding from {}".format(strategy_function))
                logger.info(formatline("TIMER Project event adding {0:.5f}".format(time.time())))

                project.add_event(strategy_function(
                    project, engine, n_traj,
                    args.n_ext, length,
                    modeller=modeller,
                    fixedlength=True,#args.fixedlength,
                    minlength=args.minlength,
                    n_rounds=n_rounds,
                    environment=args.environment,
                    activate_prefix=args.activate_prefix,
                    virtualenv=args.virtualenv,
                    longest=args.all,
                    cpu_threads=args.threads,
                    sampling_method=args.sampling_method,
                    batchsleep=args.batchsleep,
                    batchsize=args.batchsize,
                    batchwait=args.batchwait,
                    progression=args.progression,
                    sfkwargs=sfkwargs,
                    ))

                new_tasks = filter(lambda ta: uuid(ta) not in existing_tasks, project.tasks)
            else:
                logger.info("Project event adding from incomplete tasks\n{}".format(new_tasks))
                sleeptime = 20
                # FIXME this event finishes immediately for some reason...
                #         - event usage description needed
                project.add_event(all([ta.is_done() for ta in new_tasks]))

            if using_rp:
                logger.info("starting RP client for workflow execution")
                project.request_resource(cpus, walltime, gpus, 'current')
                client = Client(project.storage._db_url, project.name)
                client.start()

            logger.info(formatline("TIMER Project event added {0:.5f}".format(time.time())))
            logger.info("TRIGGERING PROJECT")
            project.wait_until(project.events_done)
            logger.info(formatline("TIMER Project event done {0:.5f}".format(time.time())))
            done = False
            while not done:
                logger.info("Waiting for final state assignments to new states")
                time.sleep(sleeptime)
                if all([task_done(ta) for ta in new_tasks]):
                    done = True
                    logger.info("All new tasks finalized")
                    logger.info(formatline("TIMER Project tasks checked {0:.5f}".format(time.time())))

            if using_rp:
                client.stop()
            else:
                logger.info("TRYING TO SHUTDOWN WORKERS")
                logger.info(project.workers.all)
                project.workers.all.execute('shutdown')
                #[setattr(w,'state','down') for w in project.workers]
                logger.info(project.workers.all)

            project.resources.consume_one()

    except KeyboardInterrupt:
        logger.info("KEYBOARD INTERRUPT- Quitting Workflow Execution")

    finally:

        if project:
            project.resources.consume_one()
            project.close()
            if not args.init_only and dump_finalize_timestamps:
                final_timestamps = pull_final_timestamps(project)
                logger.info(pformat(final_timestamps))

        logger.info("Exiting Event Script")
        logger.info(formatline("TIMER Project closed {0:.5f}".format(time.time())))


