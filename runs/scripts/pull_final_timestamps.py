#!/usr/bin/env python


import adaptivemd
import uuid


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
            lambda tae: ids_stamps.update(
                     {uuidfromhex(getproperty(tae, key_trajid)):
                      (tae["_id"], tae["cuid"], tae["_time"]),
                     }),
            filter(filterfunc, cur)
            )
    cur = project.files._set._document.find(
            {"_cls":"Trajectory"}, projection=["_time","created"]
            )
    id_stamps = map(
            lambda tje: (tje["_id"], tje["_time"], ids_stamps[tje["_id"]][1], tje["created"]), cur
            )
    #timestamps.append(sorted(map(lambda t: t - timestamps[0], zip(*id_stamps)[-1])))
    #timestamps.extend(map(lambda t: t[-1] - starttime, zip(*id_stamps)[-2:]))
    timestamps.extend(map(lambda t: (str(t[-2]), t[-1] - starttime) if all(t) else '', id_stamps))
    return timestamps

