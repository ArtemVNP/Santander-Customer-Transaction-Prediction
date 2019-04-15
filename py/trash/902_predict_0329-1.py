#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 14:24:34 2019

@author: kazuki.onodera
"""

import numpy as np
import pandas as pd
import os, gc
from glob import glob
from tqdm import tqdm

import sys
sys.path.append(f'/home/{os.environ.get("USER")}/PythonLibrary')
import lgbextension as ex
import lightgbm as lgb
from multiprocessing import cpu_count
from collections import OrderedDict
from sklearn.metrics import roc_auc_score

import utils
utils.start(__file__)
#==============================================================================

SUBMIT_FILE_PATH = '../output/0329-1.csv.gz'

COMMENT = 'f001 f003'

EXE_SUBMIT = True


SEED = np.random.randint(9999)
print('SEED:', SEED)


NFOLD = 5

LOOP = 2

param = {
         'objective': 'binary',
         'metric': 'None',
         
         'learning_rate': 0.01,
         'max_depth': -1,
         'num_leaves': 2**6 -1,
         'max_bin': 255,
         
         'min_child_weight': 10,
         'min_data_in_leaf': 150,
         'reg_lambda': 0.5,  # L2 regularization term on weights.
         'reg_alpha': 0.5,  # L1 regularization term on weights.
         
         'colsample_bytree': 0.5,
         'subsample': 0.7,
#         'nthread': 32,
         'nthread': cpu_count(),
         'bagging_freq': 1,
         'verbose':-1,
         }


NROUND = 9999
ESR = 100
VERBOSE_EVAL = 50

USE_PREF = [
        'f001',
        'f003',
        ]

DROP = [
        
        ]

#DESCRIPTION = OrderedDict()
DESCRIPTION = {}


# =============================================================================
# load train
# =============================================================================


files_tr = sorted(glob('../data/train_f*.pkl'))

# USE_PREF
li = []
for i in files_tr:
    for j in USE_PREF:
        if j in i:
            li.append(i)
            break
files_tr = li

[print(i,f) for i,f in enumerate(files_tr)]

X_train = pd.concat([
                pd.read_pickle(f) for f in tqdm(files_tr, mininterval=30)
               ], axis=1)

y_train = utils.load_target()['target']


# drop
if len(DROP) > 0:
    X_train.drop(DROP, axis=1, inplace=True)


if X_train.columns.duplicated().sum()>0:
    raise Exception(f'duplicated!: { X_train.columns[X_train.columns.duplicated()] }')
print('no dup :) ')
print(f'X_train.shape {X_train.shape}')

gc.collect()

COL = X_train.columns.tolist()

DESCRIPTION['used files'] = ' '.join(USE_PREF)
DESCRIPTION['feature size'] = len(COL)

# =============================================================================
# cv
# =============================================================================

dtrain = lgb.Dataset(X_train, y_train.values, 
                     free_raw_data=False)
gc.collect()

model_all = []
nround_mean = 0
loss_list = []
y_preds = []
for i in range(LOOP):
    gc.collect()
    
    param['seed'] = np.random.randint(9999)
    
    ret, models = lgb.cv(param, dtrain, NROUND,
                         nfold=NFOLD,
                         stratified=True, shuffle=True,
                         feval=ex.eval_auc,
                         early_stopping_rounds=ESR, 
                         verbose_eval=VERBOSE_EVAL,
                         seed=SEED+i)
    
    y_pred = ex.eval_oob(X_train, y_train.values, models, SEED+i, 
                         stratified=True, shuffle=True)
    y_preds.append(y_pred)
    
    model_all += models
    nround_mean += len(ret['auc-mean'])
    loss_list.append( ret['auc-mean'][-1] )

nround_mean = int((nround_mean/LOOP) * 1.3)


imp = ex.getImp(model_all)
imp['split'] /= imp['split'].max()
imp['gain'] /= imp['gain'].max()
imp['total'] = imp['split'] + imp['gain']
imp.sort_values('total', ascending=False, inplace=True)
imp.reset_index(drop=True, inplace=True)


for i,y_pred in enumerate(y_preds):
    if i==0:
        oof = y_pred
    else:
        oof += y_pred
oof /= len(y_preds)


imp.to_csv(f'LOG/imp_{__file__}.csv', index=False)
pd.DataFrame(oof, columns=['oof']).to_csv(f'../data/oof_{__file__}.csv', index=False)

utils.savefig_imp(imp, f'LOG/imp_{__file__}.png', x='total')


DESCRIPTION['oof AUC'] = round(roc_auc_score(y_train, oof), 5)

del X_train, y_train; gc.collect()

# =============================================================================
# load test
# =============================================================================


files_te = sorted(glob('../data/test_f*.pkl'))

# USE_PREF
li = []
for i in files_te:
    for j in USE_PREF:
        if j in i:
            li.append(i)
            break
files_te = li

[print(i,f) for i,f in enumerate(files_te)]

X_test = pd.concat([
                pd.read_pickle(f) for f in tqdm(files_te, mininterval=30)
               ], axis=1)[COL]


print(f'X_test.shape {X_test.shape}')

gc.collect()

# =============================================================================
# predict
# =============================================================================

sub = pd.read_csv('../input/sample_submission.csv.zip')

for model in tqdm(model_all):
    sub['target'] += pd.Series(model.predict(X_test)).rank()
sub['target'] /= sub['target'].max()



# save
sub.to_csv(SUBMIT_FILE_PATH, index=False, compression='gzip')

DESCRIPTION[f'corr with best({utils.SUB_BEST.split("/")[-1]})'] = sub.target.corr(pd.read_csv(utils.SUB_BEST).target, method='spearman').round(5)

print("""
# =============================================================================
# write down these info to benchmark.xlsx
# =============================================================================
""")
for k,v in DESCRIPTION.items():
    print(f'{k:<30}: {v}')


print("""
# =============================================================================
""")


# =============================================================================
# submission
# =============================================================================
if EXE_SUBMIT:
    print('submit')
    utils.submit(SUBMIT_FILE_PATH, COMMENT)






#==============================================================================
utils.end(__file__)
#utils.stop_instance()

