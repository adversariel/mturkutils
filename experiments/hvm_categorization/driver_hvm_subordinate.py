#!/usr/bin/env python
import numpy as np
import cPickle as pk
import tabular as tb
import itertools
import copy
import sys
import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import MatchToSampleFromDLDataExperiment

REPEATS_PER_QE_IMG = 4
ACTUAL_TRIALS_PER_HIT = 150
LEARNING_PERIOD = 16

repeat_inds = {'Animals': [400, 440, 486, 523, 563, 600, 642, 680],
               'Boats': [401, 440, 482, 520, 562, 603, 642, 681],
               'Cars': [401, 441, 481, 521, 560, 600, 640, 680],
               'Chairs': [402, 440, 480, 521, 560, 600, 641, 680],
               'Faces': [401, 441, 480, 521, 562, 604, 642, 681],
               'Fruits': [402, 440, 483, 521, 562, 600, 640, 680],
               'Planes': [401, 441, 481, 520, 561, 601, 640, 680],
               'Tables': [400, 442, 486, 521, 562, 600, 640, 680]}

practice_inds = {'Animals': [0, 10, 20, 30, 40, 50, 60, 70, 80, 120, 160, 200, 240, 280, 320, 360],
                'Boats': [0, 10, 20, 30, 40, 50, 60, 70, 80, 120, 160, 200, 240, 280, 320, 360],
                'Cars': [0, 10, 20, 30, 40, 50, 60, 70, 80, 120, 160, 200, 240, 280, 320, 360],
                'Chairs': [0, 10, 20, 30, 40, 50, 60, 70, 80, 120, 160, 200, 240, 280, 320, 360],
                'Faces': [0, 10, 20, 30, 40, 50, 60, 70, 80, 120, 160, 200, 240, 280, 320, 360],
                'Fruits': [0, 10, 20, 30, 40, 50, 60, 70, 80, 120, 160, 200, 240, 280, 320, 360],
                'Planes': [0, 10, 20, 30, 40, 50, 60, 70, 80, 120, 160, 200, 240, 280, 320, 360],
                'Tables': [0, 10, 20, 30, 40, 50, 60, 70, 80, 120, 160, 200, 240, 280, 320, 360]}

def get_exp(category, sandbox=True, dummy_upload=True):

    dataset = hvm.HvMWithDiscfade()
    meta = dataset.meta
    inds = (meta['category'] == category).nonzero()[0]
    meta = meta[inds]
    objs = np.unique(meta['obj'])
    combs = [objs]
    preproc = None
    image_bucket_name = 'hvm_timing'
    urls = dataset.publish_images(inds, preproc,
                                  image_bucket_name,
                                  dummy_upload=dummy_upload)


    base_url = 'https://s3.amazonaws.com/hvm_timing/'
    obj_resp_ids = [meta[meta['obj'] == o]['id'][0] for o in objs]
    response_images = [{
        'urls': [base_url + obj_id + '.png' for obj_id in obj_resp_ids],
        'meta': [{'obj': obj, 'category': category} for obj in objs],
        'labels': objs}]

    html_data = {
            'response_images': response_images,
            'combs': combs,
            'num_trials': 90 * 8,
            'meta_field': 'obj',
            'meta': meta,
            'urls': urls,
            'shuffle_test': True,
    }

    objdict = {o: category + " " + str(i) for (i, o) in enumerate(objs)}

    additionalrules = [{'old': 'LEARNINGPERIODNUMBER',
                        'new':  str(LEARNING_PERIOD)},
                       {'old': 'OBJTYPE',
                        'new': category}]

    trials_per_hit = ACTUAL_TRIALS_PER_HIT + 32 + 16
    exp = MatchToSampleFromDLDataExperiment(
            htmlsrc='hvm_subordinate.html',
            htmldst='hvm_subordinate_' + category + '_n%05d.html',
            tmpdir='tmp_%s' % category,
            sandbox=sandbox,
            title='Object recognition --- report what you see',
            reward=0.35,
            duration=1500,
            keywords=['neuroscience', 'psychology', 'experiment', 'object recognition'],  # noqa
            description="***You may complete as many HITs in this group as you want*** Complete a visual object recognition task where you report the identity of objects you see. We expect this HIT to take about 10 minutes or less, though you must finish in under 25 minutes.  By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment.",  # noqa
            comment="hvm subordinate identification",  # noqa
            collection_name= None, #'hvm_basic_categorization',
            max_assignments=1,
            bucket_name='hvm_subordinate_identification_test',
            trials_per_hit=trials_per_hit,  # 150 + 8x4 repeats
            html_data=html_data,
            frame_height_pix=1200,
            othersrc = ['objnames.js', '../../lib/dltk.js', '../../lib/dltkexpr.js', '../../lib/dltkrsvp.js'],
            additionalrules=additionalrules
            )

    # -- create trials
    exp.createTrials(sampling='without-replacement', verbose=1)
    n_total_trials = len(exp._trials['imgFiles'])
    assert n_total_trials == 90 * 8, n_total_trials

    # -- in each HIT, the followings will be repeated 4 times to
    # estimate "quality" of data

    ind_repeats = repeat_inds[category] * REPEATS_PER_QE_IMG
    rng = np.random.RandomState(0)
    rng.shuffle(ind_repeats)
    trials_qe = {e: [copy.deepcopy(exp._trials[e][r]) for r in ind_repeats]
            for e in exp._trials}

    ind_learn = practice_inds[category]
    goodids = [meta[i]['id'] for i in ind_learn]

    trials_lrn = {}
    for e in exp._trials:
        trials_lrn[e] = []
        got = []
        for _ind, r in enumerate(exp._trials[e]):
            if exp._trials['imgData'][_ind]['Sample']['id'] in goodids and exp._trials['imgData'][_ind]['Sample']['id'] not in got :
                trials_lrn[e].append(copy.deepcopy(r))
                got.append(exp._trials['imgData'][_ind]['Sample']['id'])
    assert len(trials_lrn['imgData']) == len(goodids), len(trials_lrn['imgData'])

    offsets = np.arange(ACTUAL_TRIALS_PER_HIT - 3, -1, -ACTUAL_TRIALS_PER_HIT / float(len(ind_repeats))
            ).round().astype('int')

    n_hits_floor = n_total_trials / ACTUAL_TRIALS_PER_HIT
    n_applied_hits = 0
    for i_trial_begin in xrange((n_hits_floor - 1) * ACTUAL_TRIALS_PER_HIT,
            -1, -ACTUAL_TRIALS_PER_HIT):
        for k in trials_qe:
            for i, offset in enumerate(offsets):
                exp._trials[k].insert(i_trial_begin + offset, trials_qe[k][i])
        n_applied_hits += 1

    for j in range(4):
        for k in trials_lrn:
            for i in range(len(ind_learn)):
                exp._trials[k].insert((182 + 16) * j, trials_lrn[k][i])
                if k == 'imgData':
                    print((182 + 16) * j, trials_lrn[k][i]['Sample']['var'])

    print([(x['Sample']['var'], x['Sample']['obj']) for x in exp._trials['imgData'][:16]])

    print '** n_applied_hits =', n_applied_hits
    print '** len for each in _trials =', \
            {e: len(exp._trials[e]) for e in exp._trials}

    # -- sanity check
    assert 4 == n_applied_hits, n_applied_hits
    assert len(exp._trials['imgFiles']) == 720 + 4 * (32 + 16),  len(exp._trials['imgFiles'])
    """
    s_ref_labels = set([tuple(e) for e in trials_qe['labels']])
    print(s_ref_labels)
    offsets2 = np.arange(8 * 4)[::-1] + offsets

    ibie = zip(range(0, 720 + 4 * 32, trials_per_hit), range(trials_per_hit, 720 + 4 * 32 + trials_per_hit, trials_per_hit))
    assert all([set([tuple(e) for e in
        np.array(exp._trials['labels'][ib:ie])[offsets2]]) == s_ref_labels
        for ib, ie in ibie[:-1]])
    print '** Finished creating trials.'
    """

    return exp, html_data


if __name__ == '__main__':
    exp, _ = get_exp('Chairs', sandbox=False, dummy_upload=True)
    exp.prepHTMLs()
    exp.testHTMLs()
    exp.uploadHTMLs()
    #exp.createHIT(secure=True)

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
