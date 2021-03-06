#!/usr/bin/env python

"""
Runs estimators for the given parameters

Example:

[SMC]

python ct_estimator.py -d 4 \
    -s examples/linguistic_case_study/folha.txt \
    -t ../test/tmp \
    -r ../test/results \
    -j 1 \
    --num_cores 4 \
    smc -p 4

[BIC]

python ct_estimator.py -d 4 \
    -s examples/linguistic_case_study/folha.txt \
    -j 1 \
    bic -c 0.5

"""


import argparse
import os
from pathlib import Path
from g4l.estimators.smc import SMC
from g4l.estimators.bic import BIC
from g4l.data import Sample
import logging


def dir_path_force(temp_folder):
    return dir_path(temp_folder, force=True)


def dir_path(temp_folder, force=False):
    if force:
        Path(temp_folder).mkdir(parents=True, exist_ok=True)
    if os.path.isdir(temp_folder):
        return temp_folder
    else:
        raise NotADirectoryError(temp_folder)


def log_levels():
    return {
        'quiet': None,
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR
    }


def set_log(log_file=None, lvl='info'):
    if lvl == 'quiet':
        return
    log_handlers = []
    if log_file:
        log_handlers.append(logging.FileHandler(log_file))
    else:
        log_handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=log_levels()[lvl],
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=log_handlers
    )


def run_smc(X):
    logging.info("Estimating champion trees:")
    smc = SMC(args.max_depth,
              penalty_interval=tuple(args.penalty_interval),
              epsilon=args.epsilon,
              cache_dir=args.temp_folder,
              scan_offset=args.scan_offset,
              df_method=args.df,
              perl_compatible=args.perl_compatible)
    smc.fit(X)
    logging.info("Champions tree found:")
    for i, tree in enumerate(smc.context_trees):
        used_c = smc.tresholds[i]
        logging.info("c:%s\t%s" % (used_c, tree.to_str()))

    logging.info("Finding optimal tree:")
    opt_idx = smc.optimal_tree('%s/resamples' % args.results_folder,
                               args.resamples,
                               args.n_sizes,
                               args.alpha,
                               args.renewal_point,
                               num_cores=args.num_cores)
    logging.info("Tree found:")
    tree_found = smc.context_trees[opt_idx]
    logging.info(tree_found.to_str(reverse=True))


def run_bic(X):
    logging.info("Estimating BIC tree:")
    bic = BIC(args.penalty, args.max_depth,
              scan_offset=args.scan_offset,
              df_method=args.df,
              perl_compatible=args.perl_compatible)
    bic.fit(X)
    tree = bic.context_tree
    logging.info("Tree found:")
    logging.info(tree.to_str(reverse=True))
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description='Estimates context tree')
    subparsers = parser.add_subparsers(dest='method', help='Estimation method')
    subparsers.required = True
    parser_bic = subparsers.add_parser('bic', help='Bayesian information criteria parameters')
    parser_bic.add_argument('-c', '--penalty', type=float, help='Penalty constant')

    parser_smc = subparsers.add_parser('smc', help='Smallest Maximizer Criterion parameters')
    parser_smc.add_argument('-S', '--n_sizes',
                            nargs=2,
                            type=float,
                            metavar=('j1', 'j2'),
                            default=(0.3, 0.9),
                            help='Bootstrap sample sizes factor for j = 1, 2',
                            )

    parser_smc.add_argument('-c', '--penalty_interval',
                            nargs=2,
                            type=float,
                            metavar=('pen_min', 'pen_max'),
                            default=(0, 100),
                            help='Penalization constant intervals for BIC',
                            )
    parser_smc.add_argument('-b', '--resamples',
                            type=int,
                            default='200',
                            help='Number of bootstrap samples used')
    parser_smc.add_argument('-a', '--alpha',
                            type=float,
                            default='0.01',
                            help='Alpha value for t-test')
    parser_smc.add_argument('-e', '--epsilon',
                            type=float,
                            default='0.01',
                            help='SMC stop condition value')
    parser_smc.add_argument('-p', '--renewal_point',
                            type=str,
                            default=None,
                            help='Renewal point')
    parser.add_argument('-d', '--max_depth',
                        type=int,
                        default=4,
                        help='Max tree depth')

    parser.add_argument('-s', '--sample_path',
                        type=argparse.FileType('r'),
                        help='Sample path')
    parser.add_argument('-t', '--temp_folder',
                        type=dir_path_force,
                        default='./tmp',
                        help='Path for temporary files')
    parser.add_argument('-r', '--results_folder',
                        type=dir_path_force,
                        default='./results',
                        help='Path for results')
    parser.add_argument('-o', '--scan_offset',
                        type=int,
                        default='0',
                        help='Start reading sample from this index on')
    parser.add_argument('-j', '--perl_compatible',
                        type=bool,
                        default=False,
                        help='Keeps compatibility with original version in perl (def. False)')
    parser.add_argument('--df',
                        choices=['csizar_and_talata', 'perl', 'g4l'],
                        default='perl',
                        help='Penalization strategy')
    parser.add_argument('--num_cores',
                        type=int,
                        default=0,
                        help='Number of processors for parallel processing')
    parser.add_argument('-l', '--log_file',
                        type=argparse.FileType('w'),
                        default=None,
                        help='Log file path')
    parser.add_argument('-i', '--log_level',
                        type=str,
                        choices=list(log_levels().keys()),
                        default='info',
                        help='Log level')

    args = parser.parse_args()
    set_log(args.log_file, args.log_level)
    {
        'smc': run_smc,
        'bic': run_bic
    }[args.method](Sample(args.sample_path.name, None))



