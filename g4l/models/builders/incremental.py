import numpy as np
import pandas as pd
from collections import Counter


def run(sample, max_depth):
  """
  Creates contexts and transition probabilites given the sample and a maximum depth value:
  """

  df = pd.DataFrame()
  # count frequencies of each unique subsequence of size 1..max_depth
  df = count_subsequence_frequencies(df, sample, max_depth)
  # create depth-related info columns
  df = create_indexes(df)
  # calculate transition probabilities
  transition_probs = calculate_transition_probs(df)
  df = remove_last_level(df, max_depth)
  # create parent relationship between nodes
  df = bind_parent_nodes(df)
  # remove invalid nodes
  find_admissible_tree(df)
  # calculate nodes likelihoods
  df = calculate_likelihood(df, transition_probs)
  # remove unuseful data
  df = cleanup(df, max_depth)
  return df, transition_probs

def find_admissible_tree(df):
  while True:
    df = calculate_num_child_nodes(df)
    leaves = df.loc[~df.index.isin(df.parent_idx)]
    single_leaves_parents = df.loc[leaves.parent_idx]
    single_leaves_parents = single_leaves_parents[single_leaves_parents.num_child_nodes==1]
    nodes_to_remove = df[df.parent_idx.isin(single_leaves_parents.index)]
    if len(nodes_to_remove)==0:
      break
    df.drop(index=nodes_to_remove.index, inplace=True)

def remove_last_level(df, max_depth):
  return df[df.depth <= max_depth]

def sum_log_likelihoods(df_children):
  return (df_children.freq * np.log(df_children.node_prob)).sum()

def transition_sum_log_probs(df_children):
  return np.sum(np.log(df_children[df_children.node_prob > 0].node_prob))

def count_subsequence_frequencies(df, sample, max_depth):
  sample_data = sample.data
  # for each position in a sliding window of size max_depth over sample_data,
  #for d in range(1, context_tree.max_depth + 1):
  for d in range(1, max_depth + 2):
    # create a dataframe with all subsequences and their frequencies
    substr_freqs = Counter([sample_data[i:i + d] for i in range(len(sample_data)-d+1)])
    df_tmp = pd.DataFrame.from_dict(substr_freqs, orient='index').reset_index()
    df_tmp = df_tmp.rename(columns={'index':'node', 0:'freq'})
    df_tmp.node = substr_freqs.keys()
    df = df.append(df_tmp)
  df['active'] = 0
  return df

def create_indexes(df):
  df['depth'] = df.node.str.len()
  # depth_idx is an index for all nodes with same depth
  df.index.name = 'depth_idx'
  # create a unique index per node
  df.reset_index(inplace=True)
  df.index.name = 'node_idx'
  return df

def calculate_transition_probs(df):
  nodes = df[['node', 'freq', 'depth']].copy()
  nodes['prev'] = nodes.node.str.slice(stop=-1)
  nodes['next_symbol'] = nodes.node.str.slice(start=-1)
  nodes.reset_index(drop=False, inplace=True)
  nodes.set_index(['prev'], inplace=True)
  nodes['idx'] = nodes.set_index(['node']).node_idx.astype(int)
  nodes = nodes[nodes.depth > 1]
  nodes['idx'] = nodes['idx'].astype(int)
  transition_probs = nodes[['idx', 'next_symbol', 'freq']].reset_index(drop=True)
  all_transition_freqs = transition_probs.groupby(['idx']).apply(lambda  x: x.freq.sum())
  transition_probs.set_index(['idx'], inplace=True)
  transition_probs['prob'] = transition_probs.freq / all_transition_freqs.loc[transition_probs.index]
  return transition_probs

def bind_parent_nodes(df):
  df['parent_node'] = df.node.str.slice(start=1)
  df.reset_index(inplace=True)
  df.set_index('node', inplace=True)
  parent_nodes = df[df.depth > 1].parent_node
  parent_nodes_idx = df.loc[parent_nodes].node_idx
  df.reset_index(inplace=True)
  parent_nodes_idx = parent_nodes_idx.reset_index().node_idx.values
  depth_1_values = np.repeat(None, len(df.loc[df.depth == 1]))
  df['parent_idx'] = np.concatenate((depth_1_values, parent_nodes_idx))
  df.drop('parent_node', axis='columns', inplace=True)
  df.set_index('node_idx', inplace=True)
  return df

def calculate_num_child_nodes(df):
  num_child_nodes = df[df.depth>1].reset_index(drop=False).groupby(['parent_idx']).apply(lambda x: x.count().node_idx)
  try:
    df['num_child_nodes'] = num_child_nodes
  except ValueError:
    df['num_child_nodes'] = 0
  return df


def calculate_likelihood(df, transition_probs):
  #df.set_index(['node_idx'], inplace=True)
  x = transition_probs
  try:
    transition_probs['likelihood'] = x.freq[x.freq > 0] * np.log(x.prob[x.freq > 0])
    df['likelihood'] = transition_probs.groupby(['idx']).apply(lambda s: s.likelihood.sum())
  except:
    import code; code.interact(local=dict(globals(), **locals()))

  return df

def cleanup(df, max_depth):
  df.reset_index(inplace=True)
  df = df[df.depth <= max_depth]
  return df
