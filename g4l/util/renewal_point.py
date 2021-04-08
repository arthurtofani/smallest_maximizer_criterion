def max_depth_and_freq(X, args):
    from ..bic import BIC
    c = 0
    # get the complete tree (c=0)
    t = BIC(c, df_method=args.df,
            perl_compatible=args.perl_compatible).fit(X)
    # return the largest node with higher frequency
    df = t.context_tree.df.sort_values(['depth', 'freq'], ascending=False)
    return df.node.values[0]
