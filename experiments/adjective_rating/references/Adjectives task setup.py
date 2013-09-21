# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

cd ~/objectome_32/

# <codecell>

import cPickle as pk
meta = pk.load(file('meta64_rotonly_graybg.pkl', 'rb'))

# <codecell>

import roschlib as rl
models64 = rl.ps64_models

# <codecell>

#For the slider task

adjs = ['light', 'bulbous', 'boxy', 'curly', 'globular', 'disc-like', 'pointy', 'bumpy', 'rectangular', 'striped', 'spotted', 'juicy', 'cuddly']

import random
numReps = 50
trials = []
for o in range(0, 64):
    for a in adjs:
        for i in range(0, numReps):
            trial = []
            trial.append('http://s3.amazonaws.com/subjsimilarity/'+random.sample(list(meta[meta['obj'] == models64[o]]), 1)[0][14]+'.png')
            trial.append(a)
            trials.append(trial)
            
shuffle(trials)

# <codecell>

trials[0]

# <codecell>

import json
f = file('/mindhive/dicarlolab/u/esolomon/objectome_32/adjectives/pilot_slider_list.js', 'wb')
f.write('var imgFiles = '+json.dumps(trials))
f.close()

# <codecell>


