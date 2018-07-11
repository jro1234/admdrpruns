

import traceback
import sampling_functions

from __run_tools import get_logger
logger = get_logger(__name__)

'''
This file provides an interface for using sampling functions.
The sampling scheme should be programmed in such a function by
the user and saved in sampling_functions.py. These are called
through sampling_function defined in get_one, which handles
the arguments and provides the routines that should be replicated
for all sampling functions, currently this is simply converting
them to a runnable form, ie trajectory objects.
'''

def get_one(name_func, **sfkwargs): 

    name_backup_func = 'random_sampling_trajectories'
 
    _sampling_function = getattr(sampling_functions, name_func)
    logger.info("Retrieved sampling function: {}".format(_sampling_function) )
    backup_sampling_function = getattr(sampling_functions, name_backup_func) 
    logger.info("Backup sampling function: {}".format(backup_sampling_function) )

    assert callable(_sampling_function)
    assert callable(backup_sampling_function)
 
    # Use Sampled Frames to make New Trajectories 
    def sampling_function(project, engine, length, number, *args, **skwargs): 
 
        trajectories = list() 
        skwargs.update(sfkwargs)

        if number == 0:
             return trajectories
 
        if isinstance(length, int): 
            assert(isinstance(number, int)) 
            length = [length] * number 
 
        if isinstance(length, list): 
            if number is None: 
                number = len(length) 
 
            if len(project.models) == 0: 
                sf = backup_sampling_function 
            else: 
                sf = _sampling_function 
             
            sampled_frames = None

            # Sampling 0 frames will go through this loop
            #  - eg workflow with only model task
            #  - should be caught above though.
            while sampled_frames is None:

                try:
                    sampled_frames = sf(project, number, *args, **skwargs)

                except Exception as e:
                    logger.error("Sampling was unsuccessful due to this error:")
                    logger.error(traceback.print_exc())

                    if sf == backup_sampling_function:
                        logger.error("This error must be fixed to generate sampled frames")
                        return []

                    else:
                        sf = backup_sampling_function

            logger.info("frames sampled from function: {0}".format(name_func))
            logger.info(sampled_frames)
            for i,frame in enumerate(sampled_frames): 
                trajectories.append( 
                    project.new_trajectory(
                    frame, length[i], engine) 
                ) 
 
        return trajectories 
 
 
    return sampling_function 

