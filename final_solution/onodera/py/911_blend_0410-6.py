#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 07:27:43 2019

@author: Kazuki
"""

import numpy as np
import pandas as pd
from glob import glob
import utils

# =============================================================================
# 
# =============================================================================
SUBMIT_FILE_PATH = '../output/0410-6.csv.gz'

COMMENT = 'lgb(onodera harada akiyama) + nn(akiyama) 1:3'

EXE_SUBMIT = True


fake_index = np.load('../data/fake_index.npy')

sample = pd.read_csv('../input/sample_submission.csv.zip')

sample_real = sample.drop(fake_index)
sample_fake = sample.iloc[fake_index]

# =============================================================================
# onodera(real)
# =============================================================================

sub_o = sample.drop(fake_index)

fi_o = sorted(glob('../output/0410-1*.csv.gz'))

for x in fi_o:
    sub_o.target += pd.read_csv(x).drop(fake_index).target.rank()

sub_o = sub_o.target.rank(pct=1)

# =============================================================================
# harada(real)
# =============================================================================

sub_h = sample.drop(fake_index)

fi_h = sorted(glob('../output/0410-2*.csv.gz'))

for x in fi_h:
    sub_h.target += pd.read_csv(x).drop(fake_index).target.rank()

sub_h = sub_h.target.rank(pct=1)

# =============================================================================
# akiyama(real)
# =============================================================================
sub_a_nn = pd.read_csv('../external/929_nn2.csv.gz').drop(fake_index).target
sub_a_nn.name = 'akiyama_nn10ave'

sub_a_lgb = pd.read_csv('../external/930_lgb2.csv.gz').drop(fake_index).target
sub_a_lgb.name = 'akiyama_lgb10ave'


# =============================================================================
# akiyama(fake)
# =============================================================================
fake_nn  = pd.read_csv('../external/929_nn2.csv.gz').iloc[fake_index].target
fake_lgb = pd.read_csv('../external/930_lgb2.csv.gz').iloc[fake_index].target


# =============================================================================
# blending
# =============================================================================

# lgb
sub_lgb = sub_o.rank() + sub_h.rank() + sub_a_lgb.rank()

# nn
sub_nn = sub_a_nn

sub_real = (sub_lgb.rank()*1) + (sub_nn.rank()*3)

# fake
sub_fake = fake_nn.rank() + fake_lgb.rank()

sample_real['target'] = sub_real.values
sample_fake['target'] = sub_fake.values

sub = pd.concat([sample_real, sample_fake])

sub = pd.merge(sample[['ID_code']], sub, on='ID_code', how='left')

sub.target /= sub.target.max()

# =============================================================================
# corr with best
# =============================================================================
sub_best = pd.merge(sample[['ID_code']],
                    pd.read_csv('../output/0410-3.csv.gz'),
                    on='ID_code', how='left')

sub_best = pd.merge(sub_best, sub, on='ID_code', how='left')

sub_best_real = sub_best.drop(fake_index)
print('corr wo fake:', sub_best_real.target_x.rank().corr(sub_best_real.target_y.rank()))


# save
sub.to_csv(SUBMIT_FILE_PATH, index=False, compression='gzip')

# =============================================================================
# submission
# =============================================================================
if EXE_SUBMIT:
    print('submit')
    utils.submit(SUBMIT_FILE_PATH, COMMENT)



