


from __future__ import print_function


import adaptivemd
import mdtraj
import os


# TODO
# upgrade to handle id cacheing
# for the MongoDB Collections

long_fromuuid = lambda x: int(adaptivemd.mongodb.base.uuid.UUID(x))
hex_fromuuid  = lambda x: hex(long_fromuuid(x))
uuid_fromlong = lambda x: str(adaptivemd.mongodb.base.uuid.UUID(int=x))
long_fromhex  = lambda x: adaptivemd.mongodb.base.long_t(x, 16)
uuid_fromhex  = lambda x: uuid_fromlong(long_fromhex(x))


def reset_failed_tasks(taskstore, idlist=None):
    reset_fields = {
            "state": "created",
            "stderr": None,
            "stdout": None,
            "worker": None
            }
    if idlist:
        for _id in idlist:
            taskstore.update_one(
                    {"_id": _id},
                    {"$set": reset_fields}
                    )
    else:
        failedtaskentries = taskstore.update_many(
                {"state": "fail"},
                {"$set": reset_fields}
                )


def convert_to_uuid(obj):
    uuid = None
    if isinstance(obj, long):
        uuid = uuid_fromlong(obj)
    elif hasattr(obj, '__uuid__'):
        uuid = obj.__uuid__
    elif isinstance(obj, (unicode, str)):
        if obj.startswith("0x"):
            uuid = uuid_fromhex(obj)
        else:
            try:
                adaptivemd.mongodb.base.uuid.UUID(obj)
                uuid = obj
            except ValueError:
                pass
    return uuid


def traj_source_id_from_taskentry(taskentry):
    sourcetrajid = None
    mainops = taskentry["_dict"]["_main"]
    for op in mainops:
        try:
            if op["_cls"] == 'Link':
                # This will catch source trajs since
                # the link target will be a traj
                if op["_dict"]["target"]["_cls"] == 'Trajectory':
                    sourcetrajid = convert_to_uuid(
                            op["_dict"]["source"]["_hex_uuid"]
                            )
        except TypeError:
            # skip mainops list elements that either don't
            # support indexing or need integer index
            pass
    return sourcetrajid


def traj_id_from_taskentry(taskentry):
    trajid = convert_to_uuid(
             taskentry["_dict"]["trajectory"]["_hex_uuid"]
             )
    return trajid


def traj_location_from_taskentry(taskentry, filestore, datadrive):
    location = None
    trajentry = trajentry_from_taskentry(taskentry, filestore)
    if trajentry:
        location = traj_location_from_entry(trajentry, datadrive)
    return location

def traj_location_from_entry(trajentry, datadrive):
    return trajentry["_dict"]["location"].replace(*datadrive)


def trajentry_from_taskentry(taskentry, filestore):
    # TODO generalize to entry from entry
    # TODO check for same functionality in AdaptiveMD
    trajuuid = convert_to_uuid(
            traj_id_from_taskentry(taskentry)
            )
    trajentry = filestore.find_one({"_id":trajuuid})
    return trajentry


def traj_length_from_entry(trajentry):
    trajlength = trajentry["_dict"]["length"]
    return trajlength


def update_entry_state(entryid, store, newstate):
    entryuuid = convert_to_uuid(entryid)
    store.find_one_and_update(
            {"_id": entryuuid},
            {"$set": {"state":newstate}}
            )


def path_to_basename(path):
    locsplit = path.split('/')
    return locsplit[-1] if locsplit[-1] else locsplit[-2]


def traj_basename_from_entry(trajentry):
    location = trajentry["_dict"]["location"]
    basename = path_to_basename(location)
    return basename


def load_project(project_name):
    p = adaptivemd.Project(project_name)
    return p


def makedirs(location):
    if location.find('$') >= 0 \
    or isinstance(location, list):
        location = eval_path(location)
    try:
        os.makedirs(location)
    except OSError:
        pass
    if not os.path.exists(location):
        print("Unable to find or create this directory:")
        print(location)
        raise Exception


def entries_by_state(cursor):
    entries = dict()
    try:
        for entry in cursor:
            state = entry['state']
            if state not in entries:
                updict = {state: list()}
                entries.update(updict)
            entries[state].append(entry)
    except KeyError:
        print("\"state\" key not found in some entries")
        print(entry)
    return entries


def find_dups(trajs):
    assert isinstance(trajs, adaptivemd.bundle.BaseBundle)
    ts = list()
    _dups = list()
    dups = list()
    for t in trajs:
        tbn = t.basename
        if tbn in ts:
            _dups.append(tbn)
        else:
            ts.append(tbn)
    [dups.append(list(trajs.m('basename', tbn))) for tbn in _dups]
    return dups


def get_strides(engine):
    strides = dict()
    [strides.update({otnm: otd.stride})
     for otnm, otd in engine.types.items()]
    return strides


def find_dup_names(trajs, get_dups=False):
    dups = find_dups(trajs)
    return [dupset[0].basename for dupset in dups]


def find_all_of_basename(files, basename):
    assert isinstance(files, adaptivemd.bundle.BaseBundle)
    return list(files.m('basename', basename).sorted(lambda x: x.length))


def get_correct_traj_length(p):
    ls = list()
    for t in p.trajectories:
        ls.append(t.length)
    mostcommonl = max(set(ls), key=ls.count)
    if ls.count(mostcommonl) > len(ls)/2:
        return mostcommonl
    else:
        print("Could not determine the most common length to use")
        print("as the correct trajectory length.")
        return None


def trim_traj_data(traj, final_length):
    pass


def eval_path(*location):
    '''
    Provide multiple arguments who will
    be concatenated and ENV variables
    expanded.
    '''
    varpath = make_path(*location)
    return os.path.expandvars(varpath)


def make_path(*location):
    return os.path.join(*location)


# TODO this one should probably be replaced
#      with more specific functionality
#      and not used.
def get_paths(prefix, filename, **kwargs):
    '''
    ---> UPDATE this docstring
    Get all the traj filepaths that are under
    the directory given by trajs_prefix. If the
    traj_files argument is used, any folder
    without files matching all entries will
    not be included for listing all trajectory
    files.

    Expects a structure similar to:
      ./trajs_prefix/*many_trajdirs*/traj_file1
                                    traj_file2

    kwargs
    return_dirs

    Returns 

    trajs_prefix :: str
      String giving the prefix for all the 
      trajectory data folders. 

    traj_files :: list
      List of all filenames expected for a
      trajectory folder.

    '''
    pfx = eval_path(prefix)
    paths = list()
    for d in os.listdir(pfx):
        dir = os.path.join(pfx,d)
        if os.path.isdir(dir):
            filepath = eval_path(dir, filename)
            if os.path.exists(filepath):
                if 'return_dirs' in kwargs.keys():
                    if kwargs['return_dirs'] == True:
                        paths.append(dir)
                else:
                    paths.append(filepath)
    return paths


def load_traj(traj_file, topo_file):
    tj = os.path.expandvars(traj_file)
    tp = os.path.expandvars(topo_file)
    t = mdtraj.load(tj, top=tp)
    return t


################################################
#
# TODO goal for this one:
#      - use update_entry_state to 'created'
#        and reset all other task entry fields
#        to reflect a newly created task
#
################################################
#def reset_task(taskstore, taskid):
#    '''
#    This is not functional, to reset task to
#    created from running state must:
#     - change worker field to None
#     - change state field to 'created'
#    Use pymongo.collection.find_one_and_update(...)
#    '''
#
#    uuid = None
#    if isinstance(taskid, long):
#        uuid = convert_to_uuid(taskid)
#    elif isinstance(taskid, str):
#        uuid = taskid
#
#    if uuid:
#        task = taskstore.find()
#    else:
#        print("Could not process the given task id")
#        raise Exception
