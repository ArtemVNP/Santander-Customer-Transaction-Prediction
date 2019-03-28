#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 23:55:50 2019

@author: Kazuki
"""

import numpy as np
import pandas as pd
from tqdm import tqdm
import utils

PREF = 'f003'


def fe(df):
    
    feature = pd.DataFrame(index=df.index)
    for c in tqdm(df.columns):
        di = df[c].value_counts().to_dict()
        feature[c] = df[c].map(di)
    
    feature = feature.add_prefix(PREF+'_')
    feature.iloc[:200000].to_pickle(f'../data/train_{PREF}.pkl')
    feature.iloc[200000:].to_pickle(f'../data/test_{PREF}.pkl')
    
    return


# =============================================================================
# main
# =============================================================================
if __name__ == "__main__":
    utils.start(__file__)
    
    tr = utils.load_train().drop(['ID_code', 'target'], axis=1)
    te = utils.load_test().drop(['ID_code'], axis=1)
    
    trte = pd.concat([tr, te], ignore_index=True)[tr.columns]
    
    fe(trte)
    
    
    utils.end(__file__)


