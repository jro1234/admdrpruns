#!/usr/bin/env/python

'''
This file contains strategy functions for running adaptivemd simulations
and project initializing function 'init_project'.

'''

from __future__ import print_function
from adaptivemd.scheduler import Scheduler
from adaptivemd import PythonTask
from pprint import pformat
import uuid
import time
import os, sys




# This is used outside of logger context
# for timestamping in task descriptions
_loglevel = os.environ.get('ADMD_PROFILE')

prefixline = '    >>>   '
formatline = lambda l: '\n'.join([prefixline+ls if ls else '' for ls in l.split('\n')] + ( [''] if len(l.split('\n'))>1 else []))
def get_logger(logname, logfile=None):

    import logging

    try:
        if _loglevel.lower() == 'info':
            loglevel = logging.INFO
        elif _loglevel.lower() == 'debug':
            loglevel = logging.DEBUG
        elif _loglevel.lower() == 'warning':
            loglevel = logging.WARNING
        elif _loglevel.lower() == 'error':
            loglevel = logging.ERROR
        # catch attempted set values as WARNING level
        elif hasattr(_loglevel, 'lower'):
            loglevel = logging.WARNING
    # catch None's for not set
    except:
        loglevel = logging.WARNING

    if not logfile:
        logfile = 'run_admdrp.' + logname + '.log'

    formatter = logging.Formatter(
        '%(asctime)s ::::: %(name)s ::::: %(levelname)s |||||   %(message)s'
        )

    logging.basicConfig(level=loglevel)#, format=formatter)
    logger = logging.getLogger(logname)

    ch = logging.StreamHandler()
    #ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.propagate = False

    return logger


logger = get_logger(__name__)




def pythontask_callback(pythontask, scheduler):
    outpath = os.path.expandvars(
        # TODO TODO fix this field query (post[1]) since now
        #           we can't prepend post operations
        pythontask.__dict__['post'][1].target.url.replace(
          'project:///',
          '$ADMDRP_DATA/projects/{}/'.format(scheduler.project.name))
    )

    pythontask._cb_success(scheduler, outpath)


def get_dbentry(project, obj, store):
    #return project.storage.stores[store]._document()
    return project.storage.stores[store]._document.find_one(
                    {"_id": str(uuid.UUID(int=obj.__uuid__))})


def get_task_dbentry(project, obj):
    return get_dbentry(project, obj, store='tasks')


class counter(object):
    def __init__(self, maxcount=0):
        self.n = maxcount
        self.i = 0

    @property
    def done(self):
        #print("I am done: ", not self.i < self.n)
        return not self.i < self.n

    def increment(self):
        self.i += 1


def print_last_model(project):
    try:
        mdat = project.models.last.data
        logger.info("Hopefully model prints below!")
        logger.info("Model created using modeller:".format(project.models.last.name))
        logger.info("attempted using n_microstates: {}".format(mdat['clustering']['k']))
        logger.info("length of cluster populations row: {}".format(len(mdat['msm']['C'][0])))
        logger.info(formatline(pformat(mdat['msm'])))
        logger.info(formatline(mdat['msm']))
        #logger.info(mdat['msm']['P'])
        #logger.info(mdat['msm']['C'])
    except:
        logger.info("tried to print model")
        pass


def randlength(n, incr, length, lengthvariance=0.2):

    import random

    rand = [random.random()*lengthvariance*2-lengthvariance
            for _ in range(n)]

    return [int(length*(1+r)/incr)*incr for r in rand]


def add_task_env(task, environment=None, activate_prefix=None, virtualenv=None, openmm_threads=None):
    if isinstance(task, list):
        [add_task_env(ta, environment, activate_prefix, virtualenv, openmm_threads)
         for ta in task]
    elif task:
        task.pre.append("echo \"CPU THREADS: ${OPENMM_CPU_THREADS}\"")
        if environment:
            task.add_conda_env(environment, activate_prefix)
        if virtualenv:
            task.pre.append('module load python')
            task.add_virtualenv(virtualenv)
        if openmm_threads:
            if len(openmm_threads)==1:
                task.setenv(*openmm_threads.items()[0])

        if _loglevel.lower() == 'info':
            task.pre.append("echo \"   >>>  TIMER Task start \"`date +%s.%3N`")
            task.post.append("echo \"   >>>  TIMER Task stop \"`date +%s.%3N`")


def check_trajectory_minlength(project, minlength, n_steps=None, n_run=None, trajectories=None,
                               environment=None, activate_prefix=None, virtualenv=None,
                               openmm_threads=None, resource_requirements=None):

    if not trajectories:
        trajectories = project.trajectories

    tasks = list()
    for t in trajectories:

        tlength = t.length
        xlength = 0

        if n_steps:
            if tlength % n_steps > n_steps / 2:
                tlength += n_steps - tlength % n_steps

        if tlength < minlength:
            if n_steps:
                xlength += n_steps
            else:
                xlength += minlength - tlength

        if xlength > n_steps / 2:
            tasks.append(t.extend(xlength, **resource_requirements))

    if n_run is not None and len(tasks) > n_run:
        tasks = tasks[:n_run]

    add_task_env(tasks, environment, activate_prefix, virtualenv, openmm_threads)

    return tasks


def model_task(project, modeller, margs, trajectories=None,
               resource_requirements=None, taskenv=None):

    # model task goes last to ensure (on first one) that the
    # previous round of trajectories is done
    #print("Using these in the model:\n", list(project.trajectories))
    if trajectories is None:
        trajectories = project.trajectories

    #print(project, modeller, margs, trajectories, resource_requirements)

    kwargs = margs.copy()
    kwargs.update(resource_requirements)
    #kwargs.update({"est_exec_time": 7})
    mtask = modeller.execute(list(trajectories), **kwargs)

    add_task_env(mtask, **taskenv)

    project.queue(mtask)

    #logger.info(formatline("\nModeller Pre-task:\n" + pformat(mtask.pre)))
    #logger.info(formatline("\nModeller Main-task:\n" + pformat(mtask.main)))
    #logger.info(formatline("\nModeller Post-task:\n" + pformat(mtask.post)))

    return mtask



# TODO snowball all environment stuff AND resource requirements
#      into variable "taskenv", which gets sent as kwargs to the
#      add_task_env function for application to tasks
#       - maybe not, resolve this considering late-binding of
#         of task env attributes and traj.run(**res_reqs)
#
#       --> not using resource_requirements in task env
#
def strategy_function(project, engine, n_run, n_ext, n_steps,
                   modeller=None, fixedlength=True, longest=5000,
                   continuing=True, minlength=None, randomly=False,
                   n_rounds=0, environment=None,
                   activate_prefix=None, virtualenv=None,
                   cpu_threads=16, gpu_contexts=1, mpi_rank=0,
                   **kwargs):

    logger.info(formatline("TIMER Brain enter {0:.5f}".format(time.time())))

    taskenv = {'environment': environment,
               'activate_prefix': activate_prefix,
               'virtualenv': virtualenv}

    logger.info("Got {0} for `cpu_threads`".format(cpu_threads))
    openmm_threads = {'OPENMM_CPU_THREADS': cpu_threads}
    resource_name = project._current_configuration.resource_name

    resource_requirements = {'resource_name': resource_name,
                             'cpu_threads': cpu_threads,
                             'gpu_contexts': gpu_contexts,
                             'mpi_rank': mpi_rank}

    c = counter(n_rounds)
    tasks = list()

    if n_rounds:
        assert(n_rounds > 0)
        logger.info("Going to do n_rounds:  {}".format(c.n))

    # PREPARATION - Preprocess task setups
    logger.info("Using MD Engine: {0} {1}".format(engine, engine.name))#, project.generators[engine.name].__dict__)
    logger.info("Using fixed length? {}".format(fixedlength))

    lengthvariance=0.2

    if fixedlength:
        randbreak = [n_steps]*n_run

    else:
        randbreak = randlength(n_run, longest, n_steps, lengthvariance)

    if minlength is None:
        minlength = n_steps

    logger.info(formatline("\nProject models\n - Number: {n_model}"
          .format(n_model=len(project.models))))

    logger.info(formatline("\nProject trajectories\n - Number: {n_traj}\n - Lengths:\n{lengths}"
          .format(n_traj=len(project.trajectories),
                  lengths=[t.length for t in project.trajectories])))

    # ROUND 1 - No pre-existing data
    #         - will skip if revisiting project
    if len(project.trajectories) == 0:

        notfirsttime = False

        logger.info(formatline("TIMER Brain first tasks define {0:.5f}".format(time.time())))
        [tasks.append(project.new_trajectory(
         engine['pdb_file'], rb, engine).run(**resource_requirements))
         for rb in randbreak]

        add_task_env(tasks, environment, activate_prefix, virtualenv, openmm_threads)

        logger.info(formatline("TIMER Brain first tasks queue {0:.5f}".format(time.time())))
        if not n_rounds or not c.done:
            project.queue(tasks)
            c.increment()

        #print("Number of tasks: ", len(tasks))
        logger.info(formatline("TIMER Brain first tasks queued {0:.5f}".format(time.time())))
        logger.info("Queued First Tasks in new project")
        logger.info(formatline("\nTrajectory lengths were: \n{0}".format(randbreak)))

        yield lambda: any([ta.is_done() for ta in tasks])

        logger.info("First Tasks are done")
        logger.info(formatline("TIMER Brain first tasks done {0:.5f}".format(time.time())))

    else:
        notfirsttime = True


    logger.info("Starting Trajectory Extensions")
    logger.info(formatline("TIMER Brain main loop enter {0:.5f}".format(time.time())))

    def model_extend(modeller, randbreak, mtask=None, c=None):
        #print("c_ext is ", c_ext, "({0})".format(n_ext))
        #print("length of extended is: ", len(extended))

        # FIRST workload including a model this execution
        if c_ext == 0:
            if len(tasks) == 0:
                if not randbreak and not fixedlength:
                    randbreak += randlength(n_run, longest, n_steps)
                    lengtharg = randbreak
                    
                else:
                    # this may already be set if new project
                    # was created in this run of adaptivemd
                    #locals()['randbreak'] = [n_steps]*n_run
                    lengtharg = n_steps

                # this will randomly sample the existing
                # trajectories for starting frames
                # if no pre-existing data
                #trajectories = [project.new_trajectory(engine['pdb_file'], lengtharg, engine) for _ in range(n_run)]
                logger.info(formatline("TIMER Brain fresh tasks define {0:.5f}".format(time.time())))
                trajectories = project.new_ml_trajectory(engine, lengtharg, n_run)
                #trajectories = project.new_ml_trajectory(engine, lengtharg, n_run, randomly)

                # could use the initial PDB for next round
                #trajectories = project.new_trajectory(engine['pdb_file'],
                #                                      engine, n_steps, n_run-1)

                #print(trajectories)
                if not n_rounds or not c.done:
                    #[tasks.append(t.run(export_path=export_path)) for t in trajectories]
                    [tasks.append(t.run(**resource_requirements)) for t in trajectories]
                    add_task_env(tasks, environment, activate_prefix, virtualenv, openmm_threads)

                    logger.info(formatline("TIMER Brain fresh tasks queue {0:.5f}".format(time.time())))
                    for task in tasks:
                        project.queue(task)
                        time.sleep(0.1)

                    c.increment()
                    logger.info(formatline("TIMER Brain fresh tasks queued {0:.5f}".format(time.time())))

                # wait for all initial trajs to finish
                waiting = True
                while waiting:
                    # OK condition because we're in first
                    #    extension, as long as its a fresh
                    #    project.
                    logger.info("len(project.trajectories), n_run: {0} {1}".format(
                          len(project.trajectories), n_run))
                    if notfirsttime or len(project.trajectories) >= n_run:
                        logger.info("adding first/next modeller task")
                        mtask = model_task(project, modeller, margs,
                            taskenv=taskenv,
                            resource_requirements=resource_requirements)
    
                        logger.info(formatline("\nQueued Modelling Task\nUsing these modeller arguments:\n" + pformat(margs)))

                        tasks.append(mtask)
                        waiting = False
                    else:
                        time.sleep(3)

            #print(tasks)
            #print("First Extensions' status':\n", [ta.state for ta in tasks])
            return any([ta.is_done() for ta in tasks[:-1]])

        # LAST workload in this execution
        elif c_ext == n_ext:
            if len(tasks) < n_run and mtask.is_done():
                # breaking convention of mtask last
                # is OK because not looking for mtask
                # after last round, only task.done
                if continuing:
                    mtask = model_task(project, modeller, margs,
                            taskenv=taskenv,
                            resource_requirements=resource_requirements)

                    tasks.append(mtask)
                    logger.info(formatline("\nQueued Modelling Task\nUsing these modeller arguments:\n" + pformat(margs)))
                    
                logger.info(formatline("TIMER Brain last tasks define {0:.5f}".format(time.time())))
                logger.info("Queueing final extensions after modelling done")
                logger.info(formatline("\nFirst MD Task Lengths: \n".format(randbreak)))
                unrandbreak = [2*n_steps - rb for rb in randbreak]
                unrandbreak.sort()
                unrandbreak.reverse()
                logger.info(formatline("\nFinal MD Task Lengths: \n".format(unrandbreak)))

                trajectories = project.new_ml_trajectory(engine, unrandbreak, n_run)
                #trajectories = [project.new_trajectory(engine['pdb_file'], urb, engine) for urb in unrandbreak]

                #print(trajectories)
                [tasks.append(t.run(**resource_requirements)) for t in trajectories]
                add_task_env(tasks, environment, activate_prefix, virtualenv, openmm_threads)

                logger.info(formatline("TIMER Brain last tasks queue {0:.5f}".format(time.time())))
                if not n_rounds or not c.done:
                    c.increment()
                    project.queue(tasks)

                logger.info(formatline("TIMER Brain last tasks queued {0:.5f}".format(time.time())))
            return any([ta.is_done() for ta in tasks])

        else:
            # MODEL TASK MAY NOT BE CREATED
            #  - timing is different
            #  - just running trajectories until
            #    prior model finishes, then starting
            #    round of modelled trajs along
            #    with mtask
            if len(tasks) == 0:
                logger.info("Queueing new round of modelled trajectories")
                logger.info(formatline("TIMER Brain new tasks define {0:.5f}".format(time.time())))
                trajectories = project.new_ml_trajectory(engine, n_steps, n_run)
                #trajectories = [project.new_trajectory(engine['pdb_file'], n_steps, engine) for _ in range(n_run)]

                if not n_rounds or not c.done:
                    c.increment()
                    [tasks.append(t.run(**resource_requirements)) for t in trajectories]
                    add_task_env(tasks, environment, activate_prefix, virtualenv, openmm_threads)
                    logger.info(formatline("TIMER Brain new tasks queue {0:.5f}".format(time.time())))
                    project.queue(tasks)
                    logger.info(formatline("TIMER Brain new tasks queued {0:.5f}".format(time.time())))

                if mtask.is_done():
                    mtask = model_task(project, modeller, margs,
                            taskenv=taskenv,
                            resource_requirements=resource_requirements)

                    tasks.append(mtask)

                    return any([ta.is_done() for ta in tasks[:-1]])

                else:
                    return any([ta.is_done() for ta in tasks])

            else:
                #print("not restarting with existing tasks")
                return any([ta.is_done() for ta in tasks])

    c_ext = 0
    mtask = None
    frac_ext_final_margs = 0.75

    #start_margs = dict(tica_stride=10, tica_lag=50, tica_dim=4,
    #    clust_stride=10, msm_states=50, msm_lag=5)
     
    #final_margs = dict(tica_stride=10, tica_lag=50, tica_dim=6,
    #    clust_stride=10, msm_states=100, msm_lag=5)

    start_margs = dict(tica_stride=2, tica_lag=20, tica_dim=2,
        clust_stride=1, msm_states=50, msm_lag=20)

    final_margs = dict(tica_stride=2, tica_lag=20, tica_dim=2,
        clust_stride=1, msm_states=50, msm_lag=20)

    def update_margs():
        margs=dict()
        progress = c_ext/float(n_ext)

        if c_ext == 1:
            progress_margs = 0
        elif progress < frac_ext_final_margs:
            progress_margs = progress/frac_ext_final_margs
        else:
            progress_margs = 1

        for key,baseval in start_margs.items():
            if key in final_margs:
                finalval = final_margs[key]
                val = int( progress_margs*(finalval-baseval) + baseval )
            else:
                val = baseval

            margs.update({key: val})

        return margs

    # this will be used to update the models
    # into database after `mtask` completion
    scd = Scheduler(project.resources.one)
    scd.enter(project)

    mtime = 0
    mtimes = list()
    # Start of CONTROL LOOP
    # when on final c_ext ( == n_ext), will
    # grow trajs to minlength before
    # strategy terminates
    while c_ext <= n_ext and (not n_rounds or not c.done):

        logger.info("Checking Extension Lengths")

        done = False
        lastcheck = True
        priorext = 0
        # TODO fix, this isn't a consistent name "trajectories"
        trajectories = set()
        while not done and ( not n_rounds or not c.done ):

            #print("looking for too-short trajectories")
            if c.done:
                xtasks = list()
            else:
                #logger.info(formatline("TIMER Brain ext tasks define {0:.5f}".format(time.time())))
                xtasks = check_trajectory_minlength(project, minlength,
                    n_steps, n_run, environment=environment,
                    activate_prefix=activate_prefix, virtualenv=virtualenv,
                    openmm_threads=openmm_threads, resource_requirements=resource_requirements)

            tnames = set()
            if len(trajectories) > 0:
                [tnames.add(_) for _ in set(zip(*trajectories)[0])]

            #if xtasks:
            #    logger.info(formatline("TIMER Brain ext tasks queue {0:.5f}".format(time.time())))
            for xta in xtasks:
                tname = xta.trajectory.basename

                if tname not in tnames:
                    tnames.add(tname)
                    trajectories.add( (tname, xta) )
                    project.queue(xta)

            #if xtasks:
            #    logger.info(formatline("TIMER Brain ext tasks queued {0:.5f}".format(time.time())))
            removals = list()
            for tname, xta in trajectories:
                if xta.state in {"fail","halted","success","cancelled"}:
                    removals.append( (tname, xta) )

            for removal in removals:
                trajectories.remove(removal)

            if len(trajectories) == n_run and priorext < n_run:
                logger.info("Have full width of extensions")
                c.increment()

            # setting this to look at next round
            priorext = len(trajectories)

            if len(trajectories) == 0:
                if lastcheck:
                    logger.info("Extensions last check")
                    lastcheck = False
                    time.sleep(15)

                else:
                    logger.info("Extensions are done")
                    #logger.info(formatline("TIMER Brain ext tasks done {0:.5f}".format(time.time())))
                    done = True

            else:
                if not lastcheck:
                    lastcheck = True

                time.sleep(15)

        logger.info("----------- Extension #{0}".format(c_ext))

        # when c_ext == n_ext, we just wanted
        # to use check_trajectory_minlength above
        if c_ext < n_ext and not c.done:
            logger.info(formatline("TIMER Brain main loop enter {0:.5f}".format(time.time())))
            if modeller:
                margs = update_margs()

                logger.info("Extending project with modeller")
                tasks = list()

                if mtask is None:

                    mtime -= time.time()
                    yield lambda: model_extend(modeller, randbreak, c=c)

                    logger.info(formatline("TIMER Brain main loop1 done {0:.5f}".format(time.time())))
                    logger.info("Set a current modelling task")
                    mtask = tasks[-1]
                    logger.info("First model task is: {}".format(mtask))

                # TODO don't assume mtask not None means it
                #      has is_done method. outer loop needs
                #      upgrade
                elif mtask.is_done():

                    mtime += time.time()
                    mtimes.append(mtime)
                    mtime = -time.time()
                    logger.info("Current modelling task is done")
                    logger.info("It took {0} seconds".format(mtimes[-1]))
                    c_ext += 1

                    yield lambda: model_extend(modeller, randbreak, mtask, c=c)
                    logger.info(formatline("TIMER Brain main loop2 done {0:.5f}".format(time.time())))

                    pythontask_callback(mtask, scd)
                    #mpath = os.path.expandvars(mtask.__dict__['post'][1].target.url.replace('project:///','$ADMDRP_DATA/projects/{}/'.format(project.name)))
                    #mtask._cb_success(scd, mpath)
                    logger.info("Added another model to project, now have: {}".format(len(project.models)))

                    print_last_model(project)
                    mtask = tasks[-1]
                    logger.info("Set a new current modelling task")

                elif not mtask.is_done():
                    logger.info("Continuing trajectory tasks, waiting on model")
                    yield lambda: model_extend(modeller, randbreak, mtask, c=c)
                    logger.info(formatline("TIMER Brain main loop3 done {0:.5f}".format(time.time())))

                else:
                    logger.info("Not sure how we got here")
                    pass

            # don't currently have a modeller-less workload function
            else:
                pass

        # End of CONTROL LOOP
        # need to increment c_ext to exit the loop
        else:
            c_ext += 1

    # we should not arrive here until the final round
    # of extensions are queued and at least one of them
    # is complete.
    def all_done(mtask):
        '''
        Need to make sure all tasks are in a final state, ie
        either cancelled or success.
        '''         

        #print("Checking if all done")
        idle_time = 20

        # First can check the mtask
        # - if it's not done, then we're not all_done anyway
        project.tasks._set.load(mtask.__uuid__, force_load=True)
        #print("MTASK IS::::::::", mtask, mtask.state)
        if mtask:
            if mtask:
                _mtask = get_task_dbentry(project, mtask)

            #logger.info("mtask is {0} {1} {2}".format(mtask, mtask.state, mtask.is_done()))
            #logger.info("MTASK OUTPUT STORED::::: {}".format(mtask.output_stored))
            #logger.info(formatline("_MTASK OUTPUT STORED:::::\n"+pformat(_mtask['_dict'])))
            if mtask.is_done():
                if not _mtask['_dict']['output_stored']:
                    #print("ADDING FINAL MODEL TO PROJECT DATABASE")
                    logger.info("Adding final model to project database")
                    logger.info("Had {} models".format(len(project.models)))
                    #pprint(mtask.__dict__)
                    #pprint(_mtask)

                    pythontask_callback(mtask, scd)

                    logger.info("MTASK OUTPUT STORED::::: {}".format(mtask.output_stored))

                    #print("NOW HAVE: ", len(project.models))
                    #pprint(mtask.__dict__)
                    #pprint(_mtask)
                    #mtask = None

            else:
                logger.info("Waiting on mtask first")
                time.sleep(idle_time)
                return False

        n_waiting = len(project.tasks) - len(list(filter(
            # TODO establish / utilize FINAL_STATES
            lambda ta: ta.state in {'dummy','cancelled', 'success'},
            project.tasks)))
            #lambda ta: ta['state'] in {'dummy','cancelled', 'success'},
            #project.storage.tasks._document.find())))

        if n_waiting > 0:
            logger.info("Waiting on {} tasks".format(n_waiting))
            time.sleep(idle_time)
            return False
        else:
            logger.info("All Tasks in Final States")
            return True

    #
    # It's really only imperative we have a PythonTask as mtask
    # when we get here, since above only check was the is_done
    # method
    #
    #
    # TODO TODO find out why sometimes mtask is wrong from above
    #
    mtasks = sorted( filter(lambda x: x.__class__ is PythonTask, tasks),
                     key=lambda x: x.__time__)

    if len(mtasks) > 0:
        if mtask != mtasks[-1]:
            # TODO TODO find out why sometimes mtask is wrong
            if not isinstance(mtask, PythonTask): 
                logger.info("Changing mtask to last PythonTask of tasks list")
                logger.info("Changing mtask to last PythonTask of tasks list: was:: {}".format(mtask))
                mtask = mtasks[-1]
                logger.info("Changing mtask to last PythonTask of tasks list: is:: {}".format(mtask))

    logger.info("Waiting for all done")
    logger.info(formatline("TIMER Brain finishing enter {0:.5f}".format(time.time())))
    yield lambda: all_done(mtask)
    logger.info(formatline("TIMER Brain finishing done {0:.5f}".format(time.time())))
    time.sleep(5)

    logger.info("Simulation Event Finished")



def init_project(p_name, sys_name, m_freq, p_freq,
                 platform, dblocation=None):
#def init_project(p_name, **freq):

    from adaptivemd import Project

    #if p_name in Project.list(): 
    #    print("Deleting existing version of this test project") 
    #    Project.delete(p_name)

    if dblocation is not None:

        Project.set_dblocation(dblocation)

    #project = Project(p_name)

    if p_name in Project.list():
        logger.info("Project {0} exists, reading it from database"
              .format(p_name))

        project = Project(p_name)

    else:

        project = Project(p_name)

        from adaptivemd import File, OpenMMEngine
        from adaptivemd.analysis.pyemma import PyEMMAAnalysis

        #####################################
        # NEW initialize sequence
        configuration_file = 'configuration.cfg'
        project.initialize(configuration_file)
        #
        # OLD initialize sequence
        #from adaptivemd import LocalResource
        #resource = LocalResource('/lustre/atlas/scratch/jrossyra/bip149/admd/')
        #project.initialize(resource)
        #####################################

        f_name = '{0}.pdb'.format(sys_name)

        # only works if filestructure is preserved as described in 'jro_ntl9.ipynb'
        # and something akin to job script in 'admd_workers.pbs' is used
        f_base = 'file:///$ADMDRP_ADAPTIVEMD/examples/files/{0}/'.format(sys_name)

        f_structure = File(f_base + f_name).load()

        f_system_2 = File(f_base + 'system-2.xml').load()
        f_integrator_2 = File(f_base + 'integrator-2.xml').load()

        f_system_5 = File(f_base + 'system-5.xml').load()
        f_integrator_5 = File(f_base + 'integrator-5.xml').load()

        sim_args = '-r -p {0}'.format(platform)

        engine_2 = OpenMMEngine(f_system_2, f_integrator_2,
                              f_structure, sim_args).named('openmm-2')

        engine_5 = OpenMMEngine(f_system_5, f_integrator_5,
                              f_structure, sim_args).named('openmm-5')

        m_freq_2 = m_freq
        p_freq_2 = p_freq
        m_freq_5 = m_freq * 2 / 5
        p_freq_5 = p_freq * 2 / 5

        engine_2.add_output_type('master', 'allatoms.dcd', stride=m_freq_2)
        engine_2.add_output_type('protein', 'protein.dcd', stride=p_freq_2,
                               selection='protein')

        engine_5.add_output_type('master', 'allatoms.dcd', stride=m_freq_5)
        engine_5.add_output_type('protein', 'protein.dcd', stride=p_freq_5,
                               selection='protein')

        ca_features = {'add_distances_ca': None}
        #features = {'add_inverse_distances': {'select_Backbone': None}}
        ca_modeller_2 = PyEMMAAnalysis(engine_2, 'protein', ca_features
                                 ).named('pyemma-ca-2')

        ca_modeller_5 = PyEMMAAnalysis(engine_5, 'protein', ca_features
                                 ).named('pyemma-ca-5')

        pos = ['(rescode K and mass > 13) ' +
               'or (rescode R and mass > 13) ' + 
               'or (rescode H and mass > 13)']
        neg = ['(rescode D and mass > 13) ' +
               'or (rescode E and mass > 13)']

        ionic_features = {'add_distances': {'select': pos},
                          'kwargs': {'indices2': {'select': neg}}}

        all_features = [ca_features, ionic_features]

        #ok#ionic_modeller = {'add_distances': {'select':
        #ok#                                   ['rescode K or rescode R or rescode H']},
        #ok#                  'kwargs': {'indices2': {'select':
        #ok#                                   'rescode D or rescode E']}}}
        #contact_features = [ {'add_inverse_distances':
        #                         {'select_Backbone': None}},
        #                     {'add_residue_mindist': None,
        #                      'kwargs': {'threshold': 0.6}}
        #                   ]

        all_modeller_2 = PyEMMAAnalysis(engine_2, 'protein', all_features
                                 ).named('pyemma-ionic-2')

        all_modeller_5 = PyEMMAAnalysis(engine_5, 'protein', all_features
                                 ).named('pyemma-ionic-5')

        project.generators.add(ca_modeller_2)
        project.generators.add(all_modeller_2)
        project.generators.add(ca_modeller_5)
        project.generators.add(all_modeller_5)
        project.generators.add(engine_2)
        project.generators.add(engine_5)

        #[print(g) for g in project.generators]


    return project

