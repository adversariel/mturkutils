#!/usr/bin/env python
import numpy as np
import cPickle as pk
import tabular as tb
import itertools
import copy
import sys
import dldata.stimulus_set.hvm as hvm
from mturkutils.base import MatchToSampleFromDLDataExperiment

REPEATS_PER_QE_IMG = 4
ACTUAL_TRIALS_PER_HIT = 140


# def get_meta():
#     meta_basic = pk.load(open('meta_objt_full_64objs.pkl'))
#     assert len(meta_basic) == 64 * 1000
#
#     cnames = list(meta_basic.dtype.names)
#     cnames.remove('internal_canonical')
#     cnames.remove('texture')        # contains None
#     cnames.remove('texture_mode')   # contains None
#
#     meta = tb.tabarray(columns=[meta_basic[e] for e in cnames],
#                        names=cnames)
#     assert len(meta) == 64 * 1000
#     assert len(np.unique(meta['obj'])) == 64
#     return meta


# def get_urlbase():
#     return
    # return 'https://s3.amazonaws.com/dicarlocox-rendered-imagesets/' \
    #        'objectome_cars_subord/'

#
# def get_url(obj, idstr, resized=True):
#     if resized:
#         return get_urlbase(obj) + idstr + '.png'
#     return get_urlbase(obj) + idstr + '.png'


def get_url_labeled_resp_img(obj, meta):
    id = meta[meta['obj'] == obj]['id'][0]
    url_base = 'https://s3.amazonaws.com/hvm_timing/'
    return url_base + id + '.png'


def get_subordinate_exp(sandbox=True, debug=False, dummy_upload=True):
    meta = hvm.meta
    combs = []
    for category in np.unique(meta['category']):
        objs = np.unique(meta[meta['category']==category]['obj'])
        obj_combs= [e for e in itertools.combinations(objs, 2)]
        response_images.extend([{
        'urls': [get_url_labeled_resp_img(o1, meta), get_url_labeled_resp_img(o2, meta)],
        'meta': [{'obj': o, 'category': category} for o in [o1, o2]],
        'labels': [o1, o2]
        } for o1, o2 in obj_combs])
        combs.extend(obj_combs)
    #urls = [get_url(e['obj'], e['id']) for e in meta]

    urls = dataset.publish_images(range(len(dataset.meta)), None, 'hvm_timing',
                                      dummy_upload=dummy_upload)

    with open(path.join(path.dirname(__file__), 'tutorial_html'), 'r') as tutorial_html_file:
        tutorial_html = tutorial_html_file.read()

    html_data = {
        'combs': combs,
        'response_images': response_images,
        'num_trials': 125 * 2,
        'meta_field': 'obj',
        'meta': meta,
        'urls': urls,
        'shuffle_test': True,
        'query' : lambda x: x['var'] == 'V6'
    }

    additionalrules = [{'old': 'LEARNINGPERIODNUMBER',
                        'new':  str(10)},
                       {'old': 'OBJTYPE',
                        'new': 'Object Recognition'},
                       {'old': 'TUTORIAL_HTML',
                        'new': tutorial_html},
                       {'old': 'CATDICT',
                        'new': hvm.OBJECT_NAMES},
                       {'old': 'METAFIELD',
                        'new': "'obj'"}]

    exp = MatchToSampleFromDLDataExperiment(
            htmlsrc='web/general_two_way.html',
            htmldst='hvm_subordinate_2wat_n%05d.html',
            sandbox=sandbox,
            title='Object recognition --- report what you see',
            reward=0.25,
            duration=1600,
            keywords=['neuroscience', 'psychology', 'experiment', 'object recognition'],  # noqa
            description="***You may complete as many HITs in this group as you want*** Complete a visual object recognition task where you report the identity of objects you see. We expect this HIT to take about 10 minutes or less, though you must finish in under 25 minutes.  By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment.",  # noqa
            comment='hvm_subordinate_2ways',
            collection_name='hvm_subordinate_2ways',
            max_assignments=1,
            bucket_name='hvm_2ways',
            trials_per_hit=ACTUAL_TRIALS_PER_HIT + 24,  # 140 + 6x4 repeats
            html_data=html_data,
            tmpdir='tmp',
            frame_height_pix=1200,
            othersrc=['../../lib/dltk.js', '../../lib/dltkexpr.js', '../../lib/dltkrsvp.js'],
            additionalrules=additionalrules
            )

    # -- create trials
    exp.createTrials(sampling='with-replacement', verbose=1)
    n_total_trials = len(exp._trials['imgFiles'])
    assert n_total_trials == (8 * 7 / 2) * 250 * 8
    if debug:
        return exp, html_data

    # -- in each HIT, the followings will be repeated 4 times to
    # estimate "quality" of data
    ind_repeats = [0, 4, 47, 9, 17, 18] * REPEATS_PER_QE_IMG
    rng = np.random.RandomState(0)
    rng.shuffle(ind_repeats)
    trials_qe = {e: [copy.deepcopy(exp._trials[e][r]) for r in ind_repeats]
                 for e in exp._trials}

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
                # exp._trials[k].insert(i_trial_begin + offset, 'test')
        n_applied_hits += 1

    print '** n_applied_hits =', n_applied_hits
    print '** len for each in _trials =', \
        {e: len(exp._trials[e]) for e in exp._trials}

    # -- sanity check
    assert 50 == n_applied_hits, n_applied_hits
    assert len(exp._trials['imgFiles']) == 50 * 164 * 8
    s_ref_labels = [tuple(e) for e in trials_qe['labels']]
    offsets2 = np.arange(24)[::-1] + offsets
    ibie = zip(range(0, 50 *8* 164, 164), range(164, 50 * 8* 164, 164))
    assert all(
        [[(e1, e2) for e1, e2 in
         np.array(exp._trials['labels'][ib:ie])[offsets2]] == s_ref_labels
         for ib, ie in ibie])

    # -- drop unneeded, potentially abusable stuffs
    del exp._trials['imgData']
    print '** Finished creating trials.'

    return exp, html_data


def main(argv=[], partial=False, debug=False):
    sandbox = True
    if len(argv) > 1 and argv[1] == 'production':
        sandbox = False
        print '** Creating production HITs'
    else:
        print '** Sandbox mode'
        print '** Enter "driver.py production" to publish production HITs.'

    exp = get_exp(sandbox=sandbox, debug=debug)[0]
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
