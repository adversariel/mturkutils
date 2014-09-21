#!/usr/bin/env python
import numpy as np
import cPickle as pk
import tabular as tb
import itertools
import copy
import sys
from mturkutils.base import MatchToSampleFromDLDataExperiment

# 16 "last" object Rishi used in his experiment.
models_testing8_b1 = ['build51', 'Hanger_02', 'interior_details_130_2',
    'MB28699', 'zebra', 'interior_details_103_4', '22_acoustic_guitar',
    'lo_poly_animal_BEAR_BLK']

models_testing8_b2 = ['MB30203', 'weimaraner', 'lo_poly_animal_TRANTULA',
    'MB29874', 'antique_furniture_item_18', 'calc01', 'MB27346',
    'kitchen_equipment_knife2']

SELECTED_BASIC_OBJS = set(models_testing8_b1 + models_testing8_b2)
REPEATS_PER_QE_IMG = 4
ACTUAL_TRIALS_PER_HIT = 150
STIMDURS = [100, 1000 / 30., 1000 / 30., 50,
        1000 / 60. * 4, 100, 150, 200, 500]
MODES = ['mask',                 # postmask
         'winchromeonlymask',    # 33ms + postmask
         'winchromeonly',        # 33ms
         'winonly',              # 50ms
         'winonly',              # 66ms
         'default',              # 100ms
         'default',              # 150ms
         'default',              # 200ms
         'default']              # 500ms
assert len(STIMDURS) == len(MODES)


def get_meta(selected_basic_objs=SELECTED_BASIC_OBJS):
    """Extract the selected objects from the original
    objectome 64 basic-level set"""
    assert len(np.unique(selected_basic_objs)) == 16
    meta_basic = pk.load(open('meta_objt_full_64objs.pkl'))

    si = [i for i, e in enumerate(meta_basic)
            if e['obj'] in selected_basic_objs]
    assert len(si) == 16 * 1000

    cnames = list(meta_basic.dtype.names)
    cnames.remove('internal_canonical')
    cnames.remove('texture')        # contains None
    cnames.remove('texture_mode')   # contains None

    meta = tb.tabarray(
            columns=[meta_basic[e][si] for e in cnames],
            names=cnames)
    assert len(meta) == 16 * 1000
    assert np.unique(meta['obj']).tolist() == \
            np.unique(selected_basic_objs).tolist()
    return meta


def get_urlbase(obj, selected_basic_objs=SELECTED_BASIC_OBJS):
    if obj in selected_basic_objs:
        return 'https://s3.amazonaws.com/objectome32_final/'
    else:
        assert False    # shouldn't happen
        # return 'https://s3.amazonaws.com/dicarlocox-rendered-imagesets/' \
        #        'objectome_cars_subord/'


def get_url(obj, idstr, resized=True):
    if resized:
        return get_urlbase(obj) + '360x360/' + idstr + '.png'
    return get_urlbase(obj) + idstr + '.png'


def get_url_labeled_resp_img(obj):
    return get_urlbase(obj) + 'label_imgs/' + obj + '_label.png'


def get_exp(sandbox=True, stimdur=100,
        selected_basic_objs=SELECTED_BASIC_OBJS, debug=False, mode='default'):
    meta = get_meta()
    combs = [e for e in itertools.combinations(selected_basic_objs, 2)]
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

    # few different options
    htmlsrcdct = {}
    descdct = {}
    htmldstdct = {}
    tmpdirdct = {}
    addirules = {}

    htmlsrcdct['default'] = 'web/objt_tcurve_o16s0.html'
    descdct['default'] = "***You may complete as many HITs in this group as you want*** Complete a visual object recognition task where you report the identity of objects you see. We expect this HIT to take about 10 minutes or less, though you must finish in under 25 minutes.  By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment."  # noqa
    htmldstdct['default'] = 'objt_tcurve_o16s0_%04d_n%%05d.html' % int(stimdur)   # noqa
    tmpdirdct['default'] = 'tmp/t%04d' % int(stimdur)
    addirules['default'] = []

    htmlsrcdct['softnotice'] = 'web/objt_tcurve_o16s0_softnotice.html'
    descdct['softnotice'] = descdct['default']
    htmldstdct['softnotice'] = 'objt_tcurve_o16s0_soft_%04d_n%%05d.html' % int(stimdur)  # noqa
    tmpdirdct['softnotice'] = 'tmp/t%04d_soft' % int(stimdur)
    addirules['softnotice'] = []

    htmlsrcdct['winonly'] = htmlsrcdct['default']
    descdct['winonly'] = "***Chrome or Firefox on Windows only*** Complete a visual object recognition task where you report the identity of objects you see. We expect this HIT to take about 10 minutes or less, though you must finish in under 25 minutes.  By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment."  # noqa
    htmldstdct['winonly'] = htmldstdct['default']
    tmpdirdct['winonly'] = tmpdirdct['default']
    addirules['winonly'] = [{
        'old': "supportedOS: ['Windows', 'Mac', 'Linux']",
        'new': "supportedOS: ['Windows']",
        'n': 1,
        }]

    htmlsrcdct['winchromeonly'] = htmlsrcdct['default']
    descdct['winchromeonly'] = "***Latest Chrome on Windows only*** Complete a visual object recognition task where you report the identity of objects you see. We expect this HIT to take about 10 minutes or less, though you must finish in under 25 minutes.  By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment."  # noqa
    htmldstdct['winchromeonly'] = htmldstdct['default']
    tmpdirdct['winchromeonly'] = tmpdirdct['default']
    addirules['winchromeonly'] = [{
        'old': "supportedBrowser: ['Chrome', 'Firefox']",
        'new': "supportedBrowser: ['Chrome']",
        'n': 1,
        }] + addirules['winonly']

    htmlsrcdct['winchromeonlymask'] = 'web/objt_tcurve_o16s0_postmask.html'
    descdct['winchromeonlymask'] = descdct['winchromeonly']
    htmldstdct['winchromeonlymask'] = 'objt_tcurve_o16s0_mask_%04d_n%%05d.html' % int(stimdur)  # noqa
    tmpdirdct['winchromeonlymask'] = 'tmp/t%04d_mask' % int(stimdur)
    addirules['winchromeonlymask'] = [{
        'old': "supportedBrowser: ['Chrome', 'Firefox']",
        'new': "supportedBrowser: ['Chrome']",
        'n': 1,
        }] + addirules['winonly']

    htmlsrcdct['mask'] = 'web/objt_tcurve_o16s0_postmask.html'
    descdct['mask'] = descdct['default']
    htmldstdct['mask'] = 'objt_tcurve_o16s0_mask_%04d_n%%05d.html' % int(stimdur)  # noqa
    tmpdirdct['mask'] = 'tmp/t%04d_mask' % int(stimdur)
    addirules['mask'] = addirules['default']

    exp = MatchToSampleFromDLDataExperiment(
            htmlsrc=htmlsrcdct[mode],
            htmldst=htmldstdct[mode],
            sandbox=sandbox,
            title='Object recognition --- report what you see',
            reward=0.25,
            duration=1600,
            keywords=['neuroscience', 'psychology', 'experiment', 'object recognition'],  # noqa
            description=descdct[mode],
            comment="objectome_time_curve_%dms.  0-th set of 16 objects" % int(stimdur),  # noqa
            collection_name='objectome_tcurve_16objsset0',
            max_assignments=1,
            bucket_name='objectome_tcurve_16objsset0',
            trials_per_hit=ACTUAL_TRIALS_PER_HIT + 24,  # 150 + 6x4 repeats
            html_data=html_data,
            tmpdir=tmpdirdct[mode],
            frame_height_pix=1200,
            additionalrules=[{
                'old': 'stimduration = 100;',
                'new': 'stimduration = %f;' % stimdur,
                'n': 1,
                }] + addirules[mode],
            )

    # -- create trials
    exp.createTrials(sampling='with-replacement', verbose=1)
    n_total_trials = len(exp._trials['imgFiles'])
    assert n_total_trials == (16 * 15 / 2) * 250
    if debug:
        return exp, html_data

    # -- in each HIT, the followings will be repeated 4 times to
    # estimate "quality" of data
    ind_repeats = [0, 4, 47, 9, 17, 18] * REPEATS_PER_QE_IMG
    rng = np.random.RandomState(0)
    rng.shuffle(ind_repeats)
    trials_qe = {e: [copy.deepcopy(exp._trials[e][r]) for r in ind_repeats]
            for e in exp._trials}
    #print np.unique([e[0] for e in trials_qe['imgFiles']])
    #print np.unique([tuple(e) for e in trials_qe['labels']])

    # -- flip answer choices of some repeated images
    n_qe = len(trials_qe['labels'])
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
                #exp._trials[k].insert(i_trial_begin + offset, 'test')
        n_applied_hits += 1

    print '** n_applied_hits =', n_applied_hits
    print '** len for each in _trials =', \
            {e: len(exp._trials[e]) for e in exp._trials}

    # -- sanity check
    assert 200 == n_applied_hits, n_applied_hits
    assert len(exp._trials['imgFiles']) == 200 * 174
    s_ref_labels = [tuple(e) for e in trials_qe['labels']]
    offsets2 = np.arange(24)[::-1] + offsets
    ibie = zip(range(0, 200 * 174, 174), range(174, 201 * 174, 174))
    assert all([[(e1, e2) for e1, e2 in
        np.array(exp._trials['labels'][ib:ie])[offsets2]] == s_ref_labels
        for ib, ie in ibie])
    #print set(s_ref_labels), len(set(s_ref_labels))

    # -- drop unneeded, potentially abusable stuffs
    del exp._trials['imgData']
    print '** Finished creating trials.'

    return exp, html_data


def main(argv=[], partial=False, debug=False, stimdurs=STIMDURS, modes=MODES):
    sandbox = True
    if len(argv) > 1 and argv[1] == 'production':
        sandbox = False
        print '** Creating production HITs'
    else:
        print '** Sandbox mode'
        print '** Enter "driver.py production" to publish production HITs.'

    exps = [get_exp(sandbox=sandbox, debug=debug, stimdur=t, mode=m)[0]
            for t, m in zip(stimdurs, modes)]
    for exp in exps:
        exp.prepHTMLs()
    print '** Done prepping htmls.'
    if partial:
        return exps

    for exp in exps:
        exp.testHTMLs()
    print '** Done testing htmls.'
    for exp in exps:
        exp.uploadHTMLs()
        exp.createHIT(secure=True)
    return exps


if __name__ == '__main__':
    main(sys.argv)
