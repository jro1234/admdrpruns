'''
This file contains the various runtime tools used
during a workflow to manage and report on it.
'''

import adaptivemd
import uuid
import os

# This is used outside of logger context
# for timestamping in task descriptions
_loglevel = os.environ.get('ADMD_PROFILE',"WARNING")

prefixline = '    >>>   '
formatline = lambda l: '\n'.join(
    [prefixline+ls if ls else '' for ls in l.split('\n')] +
    ( [''] if len(l.split('\n'))>1 else [])
    )

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



# e,p ~ entry, property
getproperty   = lambda e,p: reduce(lambda x,y: x.get(y,dict()),
                                   [e]+[k for k in p.split('.')])
uuidfromhex   = lambda   h: str(uuid.UUID(int=long(h,16)))
onlytrajtasks = lambda tae: tae["_cls"] not in {'PythonTask','DummyTask'}
onlyexectasks = lambda tae: tae["_cls"] not in {'DummyTask'}

def pull_final_timestamps(projectname, onlytrajs=True, starttime=0):
    timestamps = list()
    if isinstance(projectname, adaptivemd.Project):
        project = projectname
    elif isinstance(projectname, str) and projectname in adaptivemd.Project.list():
        project  = adaptivemd.Project(projectname)
    else:
        print "Provide an existing adaptivemd.Project instance or name"
        return timestamps
    if onlytrajs:
        filterfunc = onlytrajtasks
    else:
        filterfunc = onlyexectasks
    key_trajid = "_dict.trajectory._hex_uuid"
    cur = project.tasks._set._document.find(
            projection=["_time", "_cls", "cuid", key_trajid])
    ids_stamps = dict()
    _ids_stamps = map(
            lambda tae: ids_stamps.update({uuidfromhex(getproperty(tae, key_trajid)): (tae["_id"], tae["cuid"], tae["_time"])}), filter(lambda tae: 'cuid' in tae, filter(filterfunc, cur)))
    cur = project.files._set._document.find(
            {"_cls":"Trajectory"}, projection=["_time","created"]
            )
    id_stamps = map(
            lambda tje: (tje["_id"], tje["_time"], ids_stamps[tje["_id"]][1], tje["created"]), filter(lambda tje: tje["_id"] in ids_stamps, cur)
            )
    #timestamps.append(sorted(map(lambda t: t - timestamps[0], zip(*id_stamps)[-1])))
    #timestamps.extend(map(lambda t: t[-1] - starttime, zip(*id_stamps)[-2:]))
    timestamps.extend(map(lambda t: (str(t[-2]), t[-1] - starttime) if all(t) else '', id_stamps))
    return timestamps

