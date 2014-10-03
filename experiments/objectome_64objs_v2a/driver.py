#!/usr/bin/env python
import numpy as np
import cPickle as pk
import copy
import sys
from mturkutils.base import MatchToSampleFromDLDataExperiment

REPEATS_PER_QE_IMG = 4
ACTUAL_TRIALS_PER_HIT = 100
URLBASE = 'https://s3.amazonaws.com/objectome32_final/'
OBJS = [    # equals to roschlib.ps64_models
    'weimaraner', 'lo_poly_animal_TRTL_B', 'lo_poly_animal_ELE_AS1',
    'lo_poly_animal_TRANTULA', 'foreign_cat', 'lo_poly_animal_CHICKDEE',
    'lo_poly_animal_HRS_ARBN', 'MB29346', 'MB31620', 'MB29874',
    'interior_details_033_2', 'MB29822', 'face7', 'single_pineapple',
    'pumpkin_3', 'Hanger_02', 'MB31188', 'antique_furniture_item_18',
    'MB27346', 'interior_details_047_1', 'laptop01', 'womens_stockings_01M',
    'pear_obj_2', 'household_aid_29', '22_acoustic_guitar', 'MB30850',
    'MB30798', 'MB31015', 'Nurse_pose01', 'fast_food_23_1',
    'kitchen_equipment_knife2', 'flarenut_spanner', 'womens_halterneck_06',
    'dromedary', 'MB30758', 'MB30071', 'leaves16', 'lo_poly_animal_DUCK',
    '31_african_drums', 'lo_poly_animal_RHINO_2', 'lo_poly_animal_ANT_RED',
    'interior_details_103_2', 'interior_details_103_4', 'MB27780', 'MB27585',
    'build51', 'Colored_shirt_03M', 'calc01', 'Doctor_pose02', 'bullfrog',
    'MB28699', 'jewelry_29', 'trousers_03', '04_piano', 'womens_shorts_01M',
    'womens_Skirt_02M', 'lo_poly_animal_TIGER_B', 'MB31405', 'MB30203',
    'zebra', 'lo_poly_animal_BEAR_BLK', 'lo_poly_animal_RB_TROUT',
    'interior_details_130_2', 'Tie_06']


def get_url(idstr, resized=True):
    if resized:
        return URLBASE + '360x360/' + idstr + '.png'
    return URLBASE + idstr + '.png'


def get_url_labeled_resp_img(obj):
    return URLBASE + 'label_imgs/' + obj + '_label.png'


def createTrials(flip=True, rseed=0):
    meta = pk.load(open('meta_objt_full_64objs.pkl'))
    assert len(meta) == 64 * 1000
    assert set(OBJS) == set(meta['obj'])

    alldat = np.load('objt_data_all_ethan_collected.npy')
    assert alldat.shape == (5040, 100, 5)
    alldat = alldat.reshape((-1, 5))

    trials = {'imgFiles': [], 'labels': []}
    urls = [get_url(e['id']) for e in meta]
    rng = np.random.RandomState(0)

    for trial in alldat:
        # trial: [presented img idx for meta,
        #         choice 1 obj idx for OBJ, choice 2 obj idx for OBJ,
        #         presented obj idx, picked obj idx]
        samp_idx, test1_idx, test2_idx, _, _ = trial
        test1_obj, test2_obj = OBJS[test1_idx], OBJS[test2_idx]

        sample = urls[samp_idx]
        test1 = get_url_labeled_resp_img(test1_obj)
        test2 = get_url_labeled_resp_img(test2_obj)
        test = [test1, test2]
        if flip:
            rng.shuffle(test)
        trials['imgFiles'].append([sample, test])
        trials['labels'].append(test)   # not actually meant to be displayed

    return trials, alldat, meta


def get_exp(sandbox=True, debug=False):
    exp = MatchToSampleFromDLDataExperiment(
            htmlsrc='web/objectome_64objs_v2a.html',
            htmldst='objectome_64objs_v2a_n%05d.html',
            sandbox=sandbox,
            title='Object recognition --- report what you see',
            reward=0.15,
            duration=1600,
            keywords=['neuroscience', 'psychology', 'experiment', 'object recognition'],  # noqa
            description="***You may complete as many HITs in this group as you want*** Complete a visual object recognition task where you report the identity of objects you see. We expect this HIT to take about 5 minutes or less, though you must finish in under 25 minutes.  By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment.",  # noqa
            comment='objectome_64objs_v2a',
            collection_name='objectome_64objs_v2a',
            max_assignments=1,
            bucket_name='objectome_64objs_v2a',
            trials_per_hit=ACTUAL_TRIALS_PER_HIT + 16,  # 150 + 4x4 repeats
            tmpdir='tmp',
            frame_height_pix=1200,
            othersrc=['../../lib/dltk.js', '../../lib/dltkexpr.js', '../../lib/dltkrsvp.js'],   # noqa
            set_destination=True,
            )

    # -- create trials
    # exp.createTrials(sampling='with-replacement', verbose=1)   Don't use this
    exp._trials, alldat, _ = createTrials()
    n_total_trials = len(exp._trials['imgFiles'])
    assert n_total_trials == (64 * 63 / 2) * 250
    if debug:
        return exp

    # -- in each HIT, the followings will be repeated 4 times to
    # estimate "quality" of data
    # 138334: dog v camel  (difficult!)
    # 139363: rhino v elephant  (difficult!)
    ind_repeats = [138334, 139363, 47, 9] * REPEATS_PER_QE_IMG
    assert all(alldat[138334] == [701, 0, 33, 0, 33])
    assert all(alldat[139363] == [44070, 2, 39, 39, 39])

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

    for i, flip in enumerate(flips):
        if not flip:
            continue
        trials_qe['imgFiles'][i][1].reverse()
        trials_qe['labels'][i].reverse()

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
    assert 5040 == n_applied_hits, n_applied_hits
    assert len(exp._trials['imgFiles']) == 5040 * (100 + 16)
    s_ref_labels = [tuple(e) for e in trials_qe['labels']]
    print '**', s_ref_labels
    offsets2 = np.arange(16)[::-1] + offsets
    ibie = zip(range(0, 5040 * 116, 116), range(116, 5041 * 116, 116))
    assert all(
        [[(e1, e2) for e1, e2 in
         np.array(exp._trials['labels'][ib:ie])[offsets2]] == s_ref_labels
         for ib, ie in ibie])

    # -- drop unneeded, potentially abusable stuffs
    # del exp._trials['imgData']
    print '** Finished creating trials.'

    return exp


def main(argv=[], partial=False, debug=False):
    sandbox = True
    if len(argv) > 1 and argv[1] == 'production':
        sandbox = False
        print '** Creating production HITs'
    else:
        print '** Sandbox mode'
        print '** Enter "driver.py production" to publish production HITs.'

    exp = get_exp(sandbox=sandbox, debug=debug)
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
