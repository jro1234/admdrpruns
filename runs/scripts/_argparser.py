#!/usr/bin/env/ python


from argparse import ArgumentParser

stripper = lambda arg: arg.strip()

def argparser():

    parser = ArgumentParser(description="Create admd jobs")

    parser.add_argument("project_name",
        help="Name of project", type=stripper)

    parser.add_argument("--reinit", dest="reinitialize",
        help="Delete project if exists to reinitialize",
        action='store_true')

    parser.add_argument("system_name",
        help="Name of system", type=stripper)

    parser.add_argument("--init_only",
        help="Only initialize project",
        action="store_true")

    parser.add_argument("-N","--n-trajectory", dest="n_traj",
        help="Number of trajectories to create",
        type=int, default=16)

    parser.add_argument("-M","--modeller",
        help="Create a model each iteration", type=stripper)

    parser.add_argument("-x","--n-extension", dest="n_ext",
        help="Number of extensions to trajectories",
        type=int, default=1)

    parser.add_argument("--longts", dest="longts",
        help="Flag for 5fs timesteps",
        action='store_true')

    parser.add_argument("-l","--length",
        help="Length of trajectory segments in frames",
        type=int, default=100)

    parser.add_argument("-b","--n_rounds",
        help="Number of task rounds inside a single PBS job",
        type=int, default=0)

    parser.add_argument("-t","--threads",
        help="Number of threads per task",
        type=int, default=1)

    parser.add_argument("-e","--environment",
        help="Conda Environment for running tasks", type=stripper)

    parser.add_argument("-w","--virtualenv",
        help="Virtualenv environment for running tasks", type=stripper)

    parser.add_argument("-A","--activate_prefix",
        help="Prefix for activate script", type=stripper)

    parser.add_argument("-k","--minlength",
        help="Minimum trajectory total length in frames",
        type=int, default=100)

    # TODO the default behavior doesn't carry through, and should
    #      be set to fixed and changed to false. investigate this...
    parser.add_argument("-f","--fixedlength",
        help="Default randomizes traj length, flag to fix to n_steps",
        action='store_true')

    parser.add_argument("-p","--protein-stride", dest="prot",
        help="Stride between saved protein structure frames",
        type=int, default=2)

    parser.add_argument("-m","--master-stride", dest="all",
        help="Stride between saved frames with all atoms",
        type=int, default=10)

    parser.add_argument("-P","--platform",
        help="Simulation Platform: Reference, CPU, CUDA, or OpenCL",
        default="CPU", type=stripper)

  #  parser.add_argument("-d","--dblocation",
  #      help="IP address of MongoDB host",
  #      default="localhost", type=stripper)

  #  parser.add_argument("--dburl",
  #      help="Full URL of the MongoDB",
  #      default="mongodb://localhost:27017/", type=stripper)

    parser.add_argument("-r","--strategy",
        help="Filename of strategy script to run for generating tasks",
        default="run_admd.py", type=stripper)

    parser.add_argument("-S","--sampling_function",
        help="Name of sampling function saved in sampling_functions.py",
        default="random_restart", type=stripper)

    parser.add_argument("-i","--template", dest="template",
        help="Input job template file, ie admd_workers.pbs",
        default="run_admdrp.sh", type=stripper)

    parser.add_argument("--launch",
        help="Use PBS-launched client application",
        action='store_true')

    parser.add_argument("--tica_lag",
        help="TICA lag in frames",
        type=int, default=20)

    parser.add_argument("--tica_dim",
        help="Number of TICA dimensions for clustering",
        type=int, default=3)

    parser.add_argument("--tica_stride",
        help="TICA stride in frames",
        type=int, default=1)

    parser.add_argument("--clust_stride",
        help="Clustering stride in frames",
        type=int, default=1)

    parser.add_argument("--msm_lag",
        help="MSM lag in frames",
        type=int, default=20)

    parser.add_argument("--msm_states",
        help="MISLEADING name, number of microstates for clustering",
        type=int, default=25)

    return parser
