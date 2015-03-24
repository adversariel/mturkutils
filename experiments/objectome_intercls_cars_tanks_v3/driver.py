#!/usr/bin/env python
import numpy as np
import cPickle as pk
import tabular as tb
import copy
import sys
from mturkutils.base import MatchToSampleFromDLDataExperiment

# -- objects near to cars and tanks
# 30 closets objects to the "car" basic-level object
SELECTED_BASIC_OBJS_NEAR_CARS = set(
    ['MB29874', 'MB30758', 'MB27585', 'MB31405',
     'antique_furniture_item_18', 'MB29346', 'household_aid_29', 'MB27346',
     'interior_details_033_2', 'lo_poly_animal_TRTL_B', 'MB30798', '04_piano',
     'laptop01', 'jewelry_29', '31_african_drums', 'calc01',
     'lo_poly_animal_DUCK', 'build51', 'foreign_cat', 'MB31188', 'MB30071',
     'womens_Skirt_02M', 'lo_poly_animal_CHICKDEE', '22_acoustic_guitar',
     'kitchen_equipment_knife2', 'interior_details_130_2', 'Colored_shirt_03M',
     'MB30850', 'fast_food_23_1', 'lo_poly_animal_TRANTULA'])

# 30 closets objects to the "tank" basic-level object
SELECTED_BASIC_OBJS_NEAR_TANKS = set(
    ['MB31405', 'MB29874', 'MB27346', '04_piano', '31_african_drums',
     'MB31620', 'MB31188', 'MB30850', 'lo_poly_animal_DUCK',
     'lo_poly_animal_CHICKDEE', 'fast_food_23_1', 'MB29346',
     '22_acoustic_guitar', 'foreign_cat', 'laptop01', 'bullfrog',
     'interior_details_033_2', 'lo_poly_animal_TRTL_B', 'MB30798',
     'MB27585', 'MB28699', 'womens_halterneck_06', 'MB30203',
     'interior_details_130_2', 'MB30071', 'build51', 'single_pineapple',
     'antique_furniture_item_18', 'lo_poly_animal_TIGER_B',
     'lo_poly_animal_RHINO_2'])

SELECTED_BASIC_OBJS = (SELECTED_BASIC_OBJS_NEAR_CARS &
                       SELECTED_BASIC_OBJS_NEAR_TANKS)
assert len(SELECTED_BASIC_OBJS) == 22

# -- various meta data
META_BASIC = pk.load(open('meta_objt_full_64objs.pkl'))
META_CARS = pk.load(open('meta_objt_cars_subord_v3.pkl'))
META_TANKS = pk.load(open('meta_objt_tanks_subord_v3.pkl'))
UOBJS_TANKS = set(META_TANKS['obj'])

# -- other constants
DATA_INTERCLS = pk.load(open('objt_raw_pred_cars_tanks.pkl'))
REPEATS_PER_QE_IMG = 4
ACTUAL_TRIALS_PER_HIT = 100


def get_meta(selected_basic_objs=SELECTED_BASIC_OBJS,
             meta_cars=META_CARS, meta_tanks=META_TANKS,
             meta_basic=META_BASIC):
    """Mix the objectome 64 basic-level set and the car/tank subordinate
    level set"""
    assert len(np.unique(selected_basic_objs)) == 22
    si = [i for i, e in enumerate(meta_basic)
          if e['obj'] in selected_basic_objs]
    assert len(si) == 22 * 1000

    meta = meta_basic[si]
    for meta_subord in [meta_cars, meta_tanks]:
        cnames = list(meta_subord.dtype.names)
        assert list(meta_basic.dtype.names) == cnames
        cnames.remove('internal_canonical')
        cnames.remove('texture')        # contains None
        cnames.remove('texture_mode')   # contains None

        meta = tb.tabarray(
            columns=[np.concatenate([meta[e], meta_subord[e]])
                     for e in cnames],
            names=cnames)

    assert len(meta) == (22 + 30 + 30) * 1000
    # 22 basic + 30 cars + 30 tanks
    assert len(np.unique(meta['obj'])) == 22 + 30 + 30
    return meta, meta_basic, meta_cars, meta_tanks


def get_urlbase(obj, selected_basic_objs=SELECTED_BASIC_OBJS,
                uobjs_tanks=UOBJS_TANKS):
    if obj in selected_basic_objs:
        return 'https://s3.amazonaws.com/objectome32_final/'
    elif obj in uobjs_tanks:
        return 'https://s3.amazonaws.com/dicarlocox-rendered-imagesets/' \
            'objectome_tanks_subord_v3/'
    else:
        return 'https://s3.amazonaws.com/dicarlocox-rendered-imagesets/' \
            'objectome_cars_subord_v3/'


def get_url(obj, idstr, resized=True):
    if resized:
        return get_urlbase(obj) + '360x360/' + idstr + '.png'
    return get_urlbase(obj) + idstr + '.png'


def get_url_labeled_resp_img(obj):
    return get_urlbase(obj).replace('_subord_v3/', '_subord/') \
        + 'label_imgs/' + obj + '_label.png'


def get_exp(sandbox=True, selected_basic_objs=SELECTED_BASIC_OBJS,
            data_intercls=DATA_INTERCLS,
            debug=False):
    selected_intercls_pairs = np.array(data_intercls['CMinds_cars_tanks'])
    selected_intercls_pairs = selected_intercls_pairs[data_intercls['si']]
    selected_intercls_pairs[:, 0] -= 64         # subtract car base index
    selected_intercls_pairs[:, 1] -= 64 + 90    # same for tanks

    meta, _, meta_cars, meta_tanks = get_meta()
    cars = np.unique(meta_cars['obj'])
    tanks = np.unique(meta_tanks['obj'])
    combs = [(cars[e1], tanks[e2]) for e1, e2 in selected_intercls_pairs]
    combs_dummy1 = [(o1, o2) for o1 in selected_basic_objs for o2 in cars]
    combs_dummy2 = [(o1, o2) for o1 in selected_basic_objs for o2 in tanks]
    rng = np.random.RandomState(0)
    rng.shuffle(combs_dummy1)
    rng.shuffle(combs_dummy2)
    combs = combs + combs_dummy1[:50] + combs_dummy2[:50]
    assert len(combs) == 200

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
        'shuffle_test': True,
    }

    exp = MatchToSampleFromDLDataExperiment(
            htmlsrc='web/intercls_cars_tanks.html',
            htmldst='intercls_cars_tanks_n%05d.html',
            sandbox=sandbox,
            title='Object recognition --- report what you see',
            reward=0.15,
            duration=1600,
            keywords=['neuroscience', 'psychology', 'experiment', 'object recognition'],  # noqa
            description="***You may complete as many HITs in this group as you want*** Complete a visual object recognition task where you report the identity of objects you see. We expect this HIT to take about 5 minutes or less, though you must finish in under 25 minutes.  By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment.",  # noqa
            comment="objectome_intercls_cars_tanks_v3.  100+100 selected pairs across 22 basic, 30 cars, and 30 tanks",  # noqa
            collection_name='objectome_intercls_cars_tanks_v3',
            max_assignments=1,
            bucket_name='objectome_intercls_cars_tanks_v3',
            trials_per_hit=ACTUAL_TRIALS_PER_HIT + 16,  # 100 + 4x4 repeats
            tmpdir='tmp',
            html_data=html_data,
            frame_height_pix=1200,
            othersrc=['../../lib/dltk.js', '../../lib/dltkexpr.js', '../../lib/dltkrsvp.js'],   # noqa
            set_destination=True,
            )

    # -- create trials
    exp.createTrials(sampling='with-replacement', verbose=1)
    if debug:
        return exp

    n_total_trials = len(exp._trials['imgFiles'])
    assert n_total_trials == 200 * 250

    # -- in each HIT, the followings will be repeated 4 times to
    # estimate "quality" of data
    # the choice of v--- this array below is arbitrary
    ind_repeats = [1, 9, 60, 27] * REPEATS_PER_QE_IMG
    rng = np.random.RandomState(0)
    rng.shuffle(ind_repeats)
    trials_qe = {e: [copy.deepcopy(exp._trials[e][r]) for r in ind_repeats]
                 for e in exp._trials}

    # -- flip answer choices of some repeated images
    n_qe = len(trials_qe['imgFiles'])
    print '** n_qe =', n_qe
    # if True, flip
    flips = [True] * (n_qe / 2) + [False] * (n_qe - n_qe / 2)
    assert len(flips) == n_qe
    rng.shuffle(flips)
    assert len(trials_qe.keys()) == 4

    for i, flip in enumerate(flips):
        if not flip:
            continue
        trials_qe['imgFiles'][i][1].reverse()
        trials_qe['labels'][i].reverse()
        trials_qe['imgData'][i]['Test'].reverse()

    # -- actual application
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
                # exp._trials[k].insert(i_trial_begin + offset, 'test')
        n_applied_hits += 1

    print '** n_applied_hits =', n_applied_hits
    print '** len for each in _trials =', \
        {e: len(exp._trials[e]) for e in exp._trials}

    # -- sanity check
    assert 500 == n_applied_hits
    assert len(exp._trials['imgFiles']) == 500 * (100 + 16)
    s_ref_labels = [tuple(e) for e in trials_qe['labels']]
    print '**', s_ref_labels
    offsets2 = np.arange(16)[::-1] + offsets
    ibie = zip(range(0, 500 * 116, 116), range(501 * 116, 116))
    assert all(
        [[(e1, e2) for e1, e2 in
         np.array(exp._trials['labels'][ib:ie])[offsets2]] == s_ref_labels
         for ib, ie in ibie])

    # -- drop unneeded, potentially abusable stuffs
    del exp._trials['imgData']
    del exp._trials['meta_field']
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
