#!/usr/bin/env python3

import sys
import collections
import os

# Replacement of the standard print() function to flush the output
def progress(string):
    print(string, file=sys.stdout)
    sys.stdout.flush()

def flatten(d, parent_key='', sep=':'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def get_key_from_value(dictionary, value):
    idx = list(dictionary.values()).index(value)
    return list(dictionary.keys())[idx]

def generate_dirname(parent=None, root="", conj="_"):
    if parent is None:
        subdirs = os.listdir()
    else:
        subdirs = os.listdir(parent)
    
    pref = root + conj    
    if len(subdirs) == 0:
        return pref + "1"

    if root != "":
        subdirs_ = [x[len(pref):] for x in subdirs if x[:len(pref)] == pref and x[len(pref):].isnumeric()]
    else:
        pref = ""
        subdirs_ = subdirs
        
    subdirs_.sort()    
    try:
        idx = subdirs_[-1]
        new = int(idx)+1
    except:
        new = 1
    return pref + str(new)