#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 17:35:13 2019

@author: kazuki.onodera
"""

import numpy as np
import pandas as pd
from tqdm import tqdm
import utils


# =============================================================================
# main
# =============================================================================
if __name__ == "__main__":
    utils.start(__file__)
    
    tr = pd.read_csv('../input/train.csv.zip')
    te = pd.read_csv('../input/test.csv.zip')
    
    tr.to_pickle('../data/train.pkl')
    tr[['target']].to_pickle('../data/target.pkl')
    te.to_pickle('../data/test.pkl')
    
    
    # ===== fake samples =====
    te_ = te.drop(['ID_code'], axis=1).values
    
    unique_samples = []
    unique_count = np.zeros_like(te_)
    for feature in tqdm(range(te_.shape[1])):
        _, index_, count_ = np.unique(te_[:, feature], return_counts=True, return_index=True)
        unique_count[index_[count_ == 1], feature] += 1
    
    # Samples which have unique values are real the others are fake
    real_samples_indexes = np.argwhere(np.sum(unique_count, axis=1) > 0)[:, 0]
    synthetic_samples_indexes = np.argwhere(np.sum(unique_count, axis=1) == 0)[:, 0]
    
    np.save('../data/fake_index', synthetic_samples_indexes)
    
    
    
    utils.end(__file__)


