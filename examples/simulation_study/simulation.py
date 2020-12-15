import math
import os
import pandas as pd
from g4l.estimators import BIC
from g4l.estimators import SMC
from g4l.estimators import Prune
from g4l.data import persistence
from g4l.bootstrap import Bootstrap
from g4l.bootstrap.resampling import BlockResampling
import logging


A = ['0', '1']
SAMPLE_SIZES = [5000, 10000, 20000]
NUM_RESAMPLES = 200
NUM_CORES = 6
RENEWAL_POINT = 1
N1_FACTOR = 0.3
N2_FACTOR = 0.9
C = 2
MAX_SAMPLES = math.inf
max_depth = 6


def get_results_file(estimator, model_name, sample_size, results_folder):
    results_file = "%s/%s/%s_%s.csv" % (results_folder, estimator,
                                        model_name, sample_size)
    if os.path.exists(results_file):
        os.remove(results_file)
    return results_file


def run_simulation(model_name, temp_folder, results_folder, samples_path):
    estimators = {'prune': prune, 'smc': smc, 'bic': bic}
    logging.info("Running simulation with %s" % model_name)
    for sample_size in SAMPLE_SIZES:
        folder = "%s/%s/%s" % (temp_folder, model_name, sample_size)
        n_sizes = (sample_size * N1_FACTOR, sample_size * N2_FACTOR)
        print("Generating resamples")
        generate_bootstrap_resamples(model_name,
                                     sample_size,
                                     folder,
                                     n_sizes,
                                     samples_path)
        for estimator in ['smc', 'prune']:
            results_file = get_results_file(estimator, model_name, sample_size, results_folder)
            for sample_idx, sample in fetch_samples(model_name, sample_size, samples_path):
                print('sample:', sample_size, sample_idx)
                print("estimating champion trees")
                champion_trees = estimators[estimator](sample, temp_folder)
                resamples_file = resample_file(folder, sample_idx)
                bootstrap = Bootstrap(champion_trees, resamples_file, n_sizes)
                resamples_folder = '%s/likelihoods' % folder
                L = bootstrap.calculate_likelihoods(resamples_folder,
                                                    num_cores=NUM_CORES)

                diffs = bootstrap.calculate_diffs(L)
                opt_idx = bootstrap.find_optimal_tree(diffs, alpha=0.01)
                for tree_idx, champion_tree in enumerate(champion_trees):
                    opt = int(tree_idx == opt_idx)
                    obj = {'model_name': model_name,
                           'sample_idx': sample_idx,
                           'method': estimator,
                           'tree_idx': tree_idx,
                           'tree': champion_tree.to_str(),
                           'num_contexts': champion_tree.num_contexts(),
                           'likelihood': champion_tree.log_likelihood(),
                           'opt': opt,
                           'opt_idx': opt_idx}
                    use_header = (not os.path.exists(results_file))
                    df = pd.DataFrame.from_dict([obj])
                    df.to_csv(results_file, mode='a',
                              index=False,
                              header=use_header)


def resample_file(folder, sample_idx):
    return "%s/resamples/%s.txt" % (folder, sample_idx)


def generate_bootstrap_resamples(model_name, sample_size, folder, larger_size, samples_path):
    args = (model_name, sample_size, samples_path, MAX_SAMPLES)
    for sample_idx, sample in fetch_samples(*args):
        file = resample_file(folder, sample_idx)
        resample_fctry = BlockResampling(sample, file, larger_size,
                                         RENEWAL_POINT)
        resample_fctry.generate(NUM_RESAMPLES, num_cores=NUM_CORES)


def resample_sizes(sample_size):
    return tuple(math.floor(f * sample_size) for f in [N1_FACTOR, N2_FACTOR])


def bic(sample, c, temp_folder):
    return [BIC(c, max_depth).fit(sample).context_tree]


def smc(sample, temp_folder):
    if temp_folder is None:
        cache_dir = None
    else:
        cache_dir = '%s/trees' % temp_folder

    smc = SMC(max_depth, penalty_interval=(0, 500),
              epsilon=0.00001,
              cache_dir=cache_dir)
    trees = smc.fit(sample).context_trees
    return sort_trees(trees)


def prune(sample, temp_folder):
    return sort_trees(Prune(max_depth).fit(sample).context_trees)


def sort_trees(context_trees):
    return sorted(context_trees, key=lambda x: -x.num_contexts())


def fetch_samples(model_name, sample_size, path, max_samples=math.inf):
    i = -1
    key = '%s_%s' % (model_name, sample_size)
    filename = '%s/%s.mat' % (path, key)
    for s in persistence.iterate_from_mat(filename, key, A):
        if i > max_samples:
            break
        i += 1
        yield i, s