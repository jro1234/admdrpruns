

from __future__ import print_function

import numpy as np
from __run_tools import get_logger
LOGGER = get_logger(__name__)

oty = lambda d: d['input']['modeller'].outtype
stride = lambda d: d['input']['modeller'].engine.types[oty(d)].stride
dfti = lambda d, fi: fi/stride(d)


# TODO update this documentation...
'''
Available Sampling Functions:

 long_trajectories
 random_sampling_trajectories
 random_sampling_microstates
 uniform_sampling_microstates
 explore_microstates
 explore_macrostates

This file contains functions that sample from trajectory data
using a model. One sampling function is special "randomm_restart",
this one does not use a model and provides a random selection
of restarting frames. It is used as a backup sampling function
incase no model is available. To create a new sampling function,
see the examples. 

The requirements for a full-fledged sampling function:

 0. Call signature: project, number, additional arguments

 1. Get a model with function 'get_model'
    - currently returns last model, can expand functionality later
    - it checks that each microstate in the model is populated
    - then returns a tuple of: model data, count matrix

 2. Query some attribute of the model
    - only the count matrix, transition matrix, dtrajs,
      and a couple other MSM elements are available
      in the model data object. Can add more at our
      liesure.

 3. Weights based on analysis of this attribute

 4. Sample a selection of frames from trajectories
    - use something like the np.choice shown in
      xplor_microstates. here the weights were given
      by a vector with probability for each state i.

 5. Returns these frames
    - these frames are converted to trajectories for execution
      by the sampling interface component, no need to do

'''



def long_trajectories(project, number=1, trajectories=None, uselast=True, **kwargs):
    '''
    Continually grow the same trajectories to longer total
    length.
    '''
    #Note -- This currently does not make TrajectoryExtensionTasks
    #        which would be the expected output...
    #TODO -- have this function return or indicate to interface 
    #        that extension tasks should be made, and use the
    #        restart file from previous stopping point.
    trajlist = list()

    if trajectories is None:
        # TODO could also use first, maybe use
        #      argument "selection" to choose option
        if uselast:
            trajectories = list(reversed(list(
                             project.trajectories.sorted(
                             lambda t: t.created))))[:number]

        else:
            trajectories = [t for n,t in enumerate(project.trajectories) if n < number]

    if len(trajectories) > 0:

        LOGGER.info("Extending the trajectory selection")

        for traj in trajectories:
            trajlist.append(traj[len(traj)])

    return trajlist


def random_sampling_trajectories(project, number=1, **kwargs):
    '''
    Randomly sample frames from the body of trajectory data.
    Low energy regions will be heavily sampled, since most
    simulation time is presumably in these regions.
    '''

    trajlist = list()

    if len(project.trajectories) > 0:
        LOGGER.info("Random selection of new frames from trajectory data")
        [trajlist.append(project.trajectories.pick().pick()) for _ in range(number)]

    return trajlist


def uniform_sampling_microstates(project, number=1, **kwargs):
    trajlist = list()
    data, c = get_model(project)

    filelist = data['input']['trajectories']
    frame_state_list = list_microstate_frames(data)
    states = frame_state_list.keys()
    # remove states that do not have at least one frame
    # can't iterate over states while also changing states
    # so using len(c), states is same range
    for state in states:
        if len(frame_state_list[state]) == 0:
            states.remove(state)

    LOGGER.info("Uniformly sampling {0} frames across {1} microstates".format(number, c.shape[0]))
    _states = iter(states)
    while len(trajlist) < number:
        try:
            state = next(_states)
            pick = frame_state_list[state][np.random.randint(0,
                    # why shouldn't this be len()-1?
                    # ALSO this should be done by get_picks
                    len(frame_state_list[state]))]
            trajlist.append(filelist[pick[0]][pick[1]])
            state_from_dtrajs = data['clustering']['dtrajs'][pick[0]][dfti(data, pick[1])]
            LOGGER.info("For state {0}, picked this frame: {1}  {2}   --  {3}".format(
                    state, state_from_dtrajs, trajlist[-1], pick
            ))
        except StopIteration:
            _states = iter(states)

    return trajlist


def random_sampling_microstates(project, number=1, **kwargs):
    '''
    Randomly sample frames across microstates from the
    clustered trajectory data. This should result in a
    roughly uniform exploration of the already simulated
    space..
    '''

    trajlist = list()
    data, c = get_model(project)

    filelist = data['input']['trajectories']
    frame_state_list = list_microstate_frames(data)
    states = frame_state_list.keys()
    # remove states that do not have at least one frame
    # can't iterate over states while also changing states
    # so using len(c), states is same range
    for state in states:
        if len(frame_state_list[state]) == 0:
            LOGGER.info("This state was empty: {}".format(state))
            states.remove(state)

    nstates = len(states)
    w = 1./nstates
    q = [w if state in states else 0 for state in frame_state_list]
    trajlist = get_picks(frame_state_list, filelist, number, pvec=q, data=None)
    #trajlist = get_picks(frame_state_list, filelist, number, pvec=q, data=data)

    return trajlist


def get_picks(frame_state_list, filelist, npicks, pvec=None, data=None, state_picks=None):

    LOGGER.info("Using probability vector for states q:\n{}".format(pvec))
    nstates = len(frame_state_list)
    if state_picks is None:
        state_picks = np.random.choice(np.arange(nstates), size=npicks, p=pvec)
    elif pvec is not None:
        LOGGER.info("Discarding the given probability vector when state_picks recieved")

    LOGGER.info("Selecting from these states:\n{}".format(state_picks))

    LOGGER.debug("{}".format(filelist))
    trajlist = list()
    picks = list()
    for state in state_picks:
        LOGGER.debug("LOOKING AT STATE: ".format(state))
        LOGGER.debug("{}".format(frame_state_list[state]))
        pick = frame_state_list[state][np.random.randint(0,
                # FIXME should this be len()-1?
                len(frame_state_list[state]))]
        picks.append(pick)
        if data:
            #state_from_dtrajs = data['clustering']['dtrajs'][pick[0]][dfti(data, pick[1])]
            LOGGER.debug("DTRAJ {}".format(data['clustering']['dtrajs'][pick[0]]))
        LOGGER.info("For state {0}, picked this frame: {1}  {2} from traj  {3}  --  {4}".format(state, picks[-1], filelist[pick[0]][pick[1]], filelist[pick[0]], pick))

    [trajlist.append(filelist[pick[0]][pick[1]]) for pick in picks]

    return trajlist


def explore_microstates(project, number=1, **kwargs):
    '''
    This one is the same as project.new_ml_trajectory
    '''

    d = get_model(project)
    if not d:
        return None
    data, c = d
    filelist = data['input']['trajectories']
    # TODO verify axis 0 is the columns
    # TODO dont' do above todo, but ...
    #      do ceiling(average(rowcount, colcount)) as weight
    #q = 1/np.sum(c, axis=1)
    q = 1/c
    trajlist = list()

    frame_state_list = list_microstate_frames(data)
    # remove states that do not have at least one frame
    for k in range(len(q)):
        if len(frame_state_list[k]) == 0:
            q[k] = 0.0
    # and normalize the remaining ones
    q /= np.sum(q)
    #trajlist = get_picks(frame_state_list, filelist, number, pvec=q, data=data)
    trajlist = get_picks(frame_state_list, filelist, number, pvec=q, data=None)

    LOGGER.info("Trajectory picks list:\n{}".format(trajlist))
    return trajlist


def list_microstate_frames(data):
    '''
    This function returns a dict with items that contain the frames
    belonging to each microstate. While the trajectories analyzed for
    the data might have a more frequent stride than the all-atoms
    trajectory, only the all-atoms trajectory can be used for sampling
    since the restart frame must contain the whole system. So the
    returned lists only contain frames that are saved in the all-atoms
    trajectory data.

    keys :: int
    microstate index

    values :: list
    frames belonging to this microstate

    '''
    # not a good method to get n_states
    # populated clusters in
    # data['msm']['C'] may be less than k
    #n_states = data['clustering']['k']
    n_states = len(data['msm']['C'])
    modeller = data['input']['modeller']
    outtype = modeller.outtype
    # the stride of the analyzed trajectories
    used_stride = modeller.engine.types[outtype].stride
    # all stride for full trajectories
    full_strides = modeller.engine.full_strides
    frame_state_list = {n: [] for n in range(n_states)}
    for nn, dt in enumerate(data['clustering']['dtrajs']):
        for mm, state in enumerate(dt):
            # if there is a full traj with existing frame, use it
            if any([(mm * used_stride) % stride == 0 for stride in full_strides]):
                frame_state_list[state].append((nn, mm * used_stride))
                #print("Appended frame: TJidx {0} Fidx {1} State {2} to framestatelist".format(
                #        nn, mm, state))
    return frame_state_list



def select_restart_state(values, select_type, microstates, nparallel=1, parameters=None):
    if select_type == 'sto_inv_linear':
        if not isinstance(values, np.ndarray):
            values = np.array(values)
        inv_values = 1.0 / values
        p = inv_values / np.sum(inv_values)
        LOGGER.info("Values: {}".format(values))
        LOGGER.info("Problt: {}".format(p))
    return np.random.choice(microstates, p = p, size=nparallel)


def explore_macrostates(project, n_frames=1, num_macrostates = 30, reversible=True, **kwargs):

  # TODO   MOVE TO analysis task: adaptivemd.analysis.pyemma._remote
  #         -----  now, how to deal with multiple analyses?
  import time
  import pyemma
  import msmtools
  def MinMaxScale(X, min=-1, max=1):
    X_std = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0))
    X_scaled = X_std * (max - min) + min
    return X_scaled

  pyemma.config.show_progress_bars = False
  starttime = time.time()
  LOGGER.info("USING EXPLORE MACROSTATES STRATEGY")
  LOGGER.info("Starting Timer at: {}".format(starttime))
  data, _c  = get_model(project)
  c         = data['msm']['C']
  counts    = np.sum(c, axis=1)
  array_ok  = msmtools.estimation.largest_connected_set(c)
  num_macrostates = min(num_macrostates, array_ok.shape[0]/3)
  connected = msmtools.estimation.is_connected(c[array_ok,:][:,array_ok])
  LOGGER.info("Coarse Graining to {} macrostates".format(num_macrostates))
  LOGGER.info("c.shape: {}".format(c.shape))
  LOGGER.info("array_ok: {}".format(array_ok))
  LOGGER.debug("array_ok.__len__: {}".format(len(array_ok)))
  LOGGER.info("Connected Dataset: {0} {1}".format(connected, len(array_ok)))
  #if connected:
  #else:
  p = msmtools.estimation.transition_matrix(c[array_ok,:][:,array_ok], reversible=reversible)
  # Should be identical to not reversible esimate above
  #p = data['msm']['P'][array_ok,:][:,array_ok]
  # Does it make a difference specifying reversible here?
  current_MSM_obj    = pyemma.msm.markov_model(p)
  # different from below?
  #current_MSM_obj = pyemma.msm.MSM(p)
  current_timescales = current_MSM_obj.timescales()
  LOGGER.debug("Timescales from microstate MSM: {}".format(current_timescales))
  #num_macrostates = max(cut.shape[0],1)
 # TODO implement option for macrostate method
 # #  
 # #  k-means Macrostates
 # #  
 # current_eigenvecs  = np.real(current_MSM_obj.eigenvectors_right())#num_eigenvecs_to_compute)
 # #current_eigenvals  = np.real(current_MSM_obj.eigenvalues())
 # #num_eigenvecs_to_compute = current_eigenvecs.shape[0]
 # num_eigenvecs_to_compute = 6
 # projected_microstate_coords_scaled = MinMaxScale(current_eigenvecs[:,1:num_eigenvecs_to_compute])
 # projected_microstate_coords_scaled *= np.sqrt(current_timescales[:num_eigenvecs_to_compute-1] / current_timescales[0]).reshape(1, num_eigenvecs_to_compute-1)
 # LOGGER.info("projected_microstate_coords_scaled.shape: {}".format(projected_microstate_coords_scaled.shape))
 # LOGGER.debug("projected_microstate_coords_scaled: {}".format(projected_microstate_coords_scaled))
 # #kin_cont = np.cumsum(-1./np.log(np.abs(current_eigenvals[1:])))/2.
 # #frac_kin_content=0.9
 # #cut = kin_cont[kin_cont < kin_cont.max()*frac_kin_content]
 # LOGGER.info("Number macrostates: {}".format(num_macrostates))
 # num_kmeans_iter = 15
 # kmeans_obj      = pyemma.coordinates.cluster_kmeans(data=projected_microstate_coords_scaled, k=num_macrostates, max_iter=num_kmeans_iter)
 # macrostate_assignment_of_visited_microstates = kmeans_obj.assign()[0]
 # LOGGER.info("Macrostate mapping: {}".format(macrostate_assignment_of_visited_microstates))
 # macrostate_assignments = dict()
 # for mi,ma in enumerate(macrostate_assignment_of_visited_microstates):
 #   if ma not in macrostate_assignments:
 #     macrostate_assignments[ma] = set()
 #   macrostate_assignments[ma].add(mi)
  #  
  #   PCCA  Macrostates
  #  
  current_MSM_obj.pcca(num_macrostates)
  macrostate_assignments = { k:v for k,v in enumerate(current_MSM_obj.metastable_sets) }
  macrostate_assignment_of_visited_microstates = current_MSM_obj.metastable_assignments
  corrected       = np.zeros(c.shape[0])
  corrected[array_ok] = macrostate_assignment_of_visited_microstates
  not_connected_macrostates = [i for i in range(c.shape[0]) if i not in array_ok]
  for n,i in enumerate(not_connected_macrostates):
    #print(i)
    # an unpopulated macrostate label
    corrected[i]=n+num_macrostates
  LOGGER.info("Macrostates including unassigned (index over num_macrostates): {}".format(corrected))
  #del#counts=np.sum(c,axis=1)
  #[array_ok,:][:,array_ok]
  LOGGER.debug("Macrostate summer: {}".format([counts[corrected == macrostate_label] for macrostate_label in range(num_macrostates+len(not_connected_macrostates))]))
  macrostate_counts   = np.array([np.sum(counts[corrected == macrostate_label])      for macrostate_label in range(num_macrostates+len(not_connected_macrostates))])
  macrostate_counts[num_macrostates:] = 0
  LOGGER.info("Macrostate Assignments: {}".format('\n'.join(["{0}: {1}".format(k,v)  for k,v in macrostate_assignments.items()])))
  LOGGER.info("Microstate Counts: {}".format(counts))
  LOGGER.info("Macrostate Counts: {}".format(macrostate_counts))
  selected_macrostate = select_restart_state(macrostate_counts[macrostate_counts > 0], 'sto_inv_linear', np.arange(num_macrostates+len(not_connected_macrostates))[macrostate_counts > 0], nparallel=n_frames)
  LOGGER.info("Selected Macrostates: {}".format(selected_macrostate))
  restart_state = np.empty((0))
  for i in range(n_frames):
    selected_macrostate_mask      = (corrected == selected_macrostate[i])
    LOGGER.debug("Macrostate Selection Mask: ({0})\n{1}".format(selected_macrostate[i], selected_macrostate_mask))
    #counts_in_selected_macrostate = counts[selected_macrostate_mask]
    counts_in_selected_macrostate = np.ones(len(counts))[selected_macrostate_mask]
    add_microstate                = select_restart_state(counts_in_selected_macrostate, 'sto_inv_linear', np.arange(c.shape[0])[selected_macrostate_mask], nparallel=1)
    LOGGER.info("Selected Macrostate, microstate: {0}, {1}".format(selected_macrostate[i], add_microstate))
    restart_state                 = np.append(restart_state, add_microstate)
  state_picks  = restart_state.astype('int')
  frame_state_list = list_microstate_frames(data)
  filelist = data['input']['trajectories']
  trajlist = get_picks(frame_state_list, filelist, n_frames, data=None, state_picks=state_picks)
  #trajlist = get_picks(frame_state_list, filelist, n_frames, data=data, state_picks=state_picks)
  stoptime = time.time()
  LOGGER.info("Stopping Timer at: {}".format(stoptime))
  LOGGER.info("Explore Macrostates duration: {}".format(stoptime - starttime))
  return trajlist


# TODO make get_model able to search the model data with a
#      list of keys to query data from 'model.data'
# TODO model data check feature to check something about model
#      before returning it. 
#def get_model(project):
#    models = sorted(project.models, reverse=True, key=lambda m: m.__time__)
#    for model in models:
#        # Would have to import Model class
#        # definition for this check
#        #assert(isinstance(model, Model))
#        data = model.data
#        c = data['msm']['C']
#        # TODO verify axis 0 is the columns
#        s =  np.sum(c, axis=1)
#        #s =  np.sum(c, axis=0)
#        assert len(c.shape) == 2
#        assert c.shape[0] == c.shape[1]
#        if 0 not in s:
#            return data, c

def get_model(project, filter=dict()):
    LOGGER.info(str(len(project.models)))
    if len(project.models) == 0:
        return None

    models = sorted(project.models, reverse=True,
                    key=lambda m: m.__time__)

    for model in models:
        # best thing & somewhat erroneous check is
        # isinstance(model,p.models._set.content_class)
        #assert(isinstance(model, Model))
        data = model.data
        n_microstates = data['clustering']['k']
        if not n_microstates:
            n_microstates = data['msm']['C'].shape[0]
        c = np.zeros(n_microstates)
        for dtraj in data['clustering']['dtrajs']:
            for f in dtraj:
                c[f] += 1
        return data, c
    ## Uses rowsum of transition count matrix
    ##for model in models:
    ##    # best thing & somewhat erroneous check is
    ##    # isinstance(model,p.models._set.content_class)
    ##    #assert(isinstance(model, Model))
    ##    data = model.data
    ##    c = data['msm']['C']
    ##    print(c)
    ##    s =  np.sum(c, axis=1)
    ##    print(np.sort(s))
    ##    if 0 not in s:
    ##        return data, c
    else:
        return None

