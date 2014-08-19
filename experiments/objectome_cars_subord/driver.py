#!/usr/bin/env python
import numpy as np
import cPickle as pk
import tabular as tb
import itertools
import copy
import sys
from mturkutils.base import MatchToSampleFromDLDataExperiment

# 30 closets objects to the "car" basic-level object
SELECTED_BASIC_OBJS = set(['MB29874', 'MB31405', 'MB30758', 'MB27585',
       'lo_poly_animal_TRTL_B', 'antique_furniture_item_18',
       'household_aid_29', 'laptop01',
       'MB27346', 'MB30798', '04_piano', 'build51', 'jewelry_29',
       'MB29346', 'fast_food_23_1', 'interior_details_033_2',
       'lo_poly_animal_RHINO_2', 'MB29822', 'MB30071', '31_african_drums',
       'calc01', 'lo_poly_animal_ANT_RED', 'pear_obj_2',
       'lo_poly_animal_DUCK', 'foreign_cat', 'Colored_shirt_03M',
       'womens_stockings_01M', 'lo_poly_animal_TRANTULA',
       'lo_poly_animal_ELE_AS1', 'zebra'])
REPEATS_PER_QE_IMG = 4
ACTUAL_TRIALS_PER_HIT = 150


def get_meta(selected_basic_objs=SELECTED_BASIC_OBJS):
    """Mix the objectome 64 basic-level set and the car subordinate
    level set"""
    assert len(np.unique(selected_basic_objs)) == 30
    meta_cars = pk.load(open('meta_objt_cars_subord.pkl'))
    meta_basic = pk.load(open('meta_objt_full_64objs.pkl'))

    si = [i for i, e in enumerate(meta_basic)
            if e['obj'] in selected_basic_objs]
    assert len(si) == 30 * 1000

    cnames = list(meta_cars.dtype.names)
    assert list(meta_basic.dtype.names) == cnames
    cnames.remove('internal_canonical')
    cnames.remove('texture')        # contains None
    cnames.remove('texture_mode')   # contains None

    meta = tb.tabarray(
            columns=[np.concatenate([meta_basic[e][si], meta_cars[e]])
                for e in cnames],
            names=cnames)
    assert len(meta) == 30 * 1000 * 2
    assert len(np.unique(meta['obj'])) == 60   # 30 non-cars + 30 cars
    return meta, meta_basic, meta_cars


def get_urlbase(obj, selected_basic_objs=SELECTED_BASIC_OBJS):
    if obj in selected_basic_objs:
        return 'https://s3.amazonaws.com/objectome32_final/'
    else:
        return 'https://s3.amazonaws.com/dicarlocox-rendered-imagesets/' \
                'objectome_cars_subord/'


def get_url(obj, idstr, resized=True):
    if resized:
        return get_urlbase(obj) + '360x360/' + idstr + '.png'
    return get_urlbase(obj) + idstr + '.png'


def get_url_labeled_resp_img(obj):
    return get_urlbase(obj) + 'label_imgs/' + obj + '_label.png'


def get_exp(sandbox=True, selected_basic_objs=SELECTED_BASIC_OBJS):
    meta, _, meta_cars = get_meta()
    cars = np.unique(meta_cars['obj'])
    combs = [(o1, o2) for o1 in selected_basic_objs for o2 in cars] + \
            [e for e in itertools.combinations(cars, 2)]
    urls = [get_url(e['obj'], e['id']) for e in meta]
    response_images = [{
        'urls': [get_url_labeled_resp_img(o1), get_url_labeled_resp_img(o2)],
        'meta': [{'obj': o} for o in [o1, o2]],
        'labels': [o1, o2]
        } for o1, o2 in combs]

    html_data = {
            'response_images': response_images,
            'combs': combs,
            'num_trials': 125 * 2,
            'meta_field': 'obj',
            'meta': meta,
            'urls': urls,
    }

    exp = MatchToSampleFromDLDataExperiment(
            htmlsrc='web/cars_subord.html',
            htmldst='cars_subord_n%05d.html',
            sandbox=sandbox,
            title='Object recognition --- report what you see',
            reward=0.35,
            duration=1600,
            keywords=['neuroscience', 'psychology', 'experiment', 'object recognition'],  # noqa
            description="***You may complete as many HITs in this group as you want*** Complete a visual object recognition task where you report the identity of objects you see. We expect this HIT to take about 10 minutes or less, though you must finish in under 25 minutes.  By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment.",  # noqa
            comment="objectome_cars_subord.  30 cars and 30 non-cars",  # noqa
            collection_name='objectome_cars_subord',
            max_assignments=1,
            bucket_name='objectome_cars_subord',
            trials_per_hit=ACTUAL_TRIALS_PER_HIT + 24,  # 150 + 6x4 repeats
            html_data=html_data)

    # -- create trials
    exp.createTrials(sampling='with-replacement', verbose=1)
    n_total_trials = len(exp._trials['imgFiles'])
    assert n_total_trials == (30 * 29 / 2 + 30 * 30) * 250

    # -- in each HIT, the followings will be repeated 4 times to
    # estimate "quality" of data
    #
    # car:      0 - laptop01     v car MB27542*
    # car:      4 - car MB27534* v car MB27803
    # car:     12 - tank MB30758 v car MB27577*
    # non-car:  9 - train MB31405* v car MB29535
    # non-car: 10 - pear* v car MB28307
    # non-car: 18 - turtle* v car MB27819
    ind_repeats = [0, 4, 12, 9, 10, 18] * REPEATS_PER_QE_IMG
    rng = np.random.RandomState(0)
    rng.shuffle(ind_repeats)
    trials_qe = {e: [copy.deepcopy(exp._trials[e][r]) for r in ind_repeats]
            for e in exp._trials}
    offsets = np.arange(
                ACTUAL_TRIALS_PER_HIT - 3, -1,
                -ACTUAL_TRIALS_PER_HIT / float(len(ind_repeats))
            ).round().astype('int')
    assert len(offsets) == len(offsets)

    n_hits_floor = n_total_trials / ACTUAL_TRIALS_PER_HIT
    n_applied_hits = 0
    for i_trial_begin in xrange((n_hits_floor - 1) * ACTUAL_TRIALS_PER_HIT,
            -1, -ACTUAL_TRIALS_PER_HIT):
        for k in trials_qe:
            for i, offset in enumerate(offsets):
                exp._trials[k].insert(i_trial_begin + offset, trials_qe[k][i])
                #exp._trials[k].insert(i_trial_begin + offset, 'test')
        n_applied_hits += 1

    print '** n_applied_hits =', n_applied_hits
    print '** len for each in _trials =', \
            {e: len(exp._trials[e]) for e in exp._trials}

    # -- sanity check
    assert 2225 == n_applied_hits
    assert len(exp._trials['imgFiles']) == 387150
    s_ref_labels = set([tuple(e) for e in trials_qe['labels']])
    offsets2 = np.arange(24)[::-1] + offsets
    ibie = zip(range(0, 387150, 174), range(174, 387150 + 174, 174))
    assert all([set([(e1, e2) for e1, e2 in
        np.array(exp._trials['labels'][ib:ie])[offsets2]]) == s_ref_labels
        for ib, ie in ibie])
    print '** Finished creating trials.'

    return exp, html_data


def main(argv=[], partial=False):
    sandbox = True
    if len(argv) > 1 and argv[1] == 'production':
        sandbox = False
        print '** Creating production HITs'
    else:
        print '** Sandbox mode'
        print '** Enter "driver.py production" to publish production HITs.'

    exp, _ = get_exp(sandbox=sandbox)
    exp.prepHTMLs()
    print '** Done prepping htmls.'
    if partial:
        return exp
    exp.testHTMLs()
    print '** Done testing htmls.'
    exp.uploadHTMLs()
    exp.createHIT(secure=True)
    return exp


if __name__ == '__main__':
    main(sys.argv)
