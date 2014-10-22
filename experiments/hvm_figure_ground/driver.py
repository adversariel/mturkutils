#!/usr/bin/env python
import numpy as np
import cPickle as pk
import tabular as tb
import itertools
import copy
from os import path
import sys
from mturkutils.base import MatchToSampleFromDLDataExperiment
import dldata.stimulus_sets.semi_synthetic.hvm as hvm

REPEATS_PER_QE_IMG = 4
ACTUAL_TRIALS_PER_HIT = 150
LEARNING_PERIOD = 10

def get_exp(sandbox=True, dummy_upload=True):

    dataset = hvm.HvMWithDot()
    base_url = 'https://canonical_images.s3.amazonaws.com/'
    fields = dataset.meta.dtype.names
    meta = dataset.meta
    names = ['RedPixelOnCanonical', 'RedPixelOffCanonical']
    response_images = [{'urls': [base_url + name + '.png' for name in names],
                       'meta': [{field: meta[i][field] for field in fields} for i in [4020, 5060]],
                       'labels': ['The red pixel was on the object',
                                 'The red pixel was not on the object']}]
    preproc = {'crop': None,
               'crop_rand': None,
               'dtype': 'float32',
               'mask': None,
               'mode': 'RGB',
               'normalize': False,
               'resize_to': (256, 256),
               'seed': 0}
    cat_dict = "{true: 'Dot is on the object', false:'Dot is not on the object'}"

    with open(path.join(path.dirname(__file__), 'tutorial_html'), 'r') as tutorial_html_file:
        tutorial_html = tutorial_html_file.read()

    additionalrules = [{'old': 'LEARNINGPERIODNUMBER',
                        'new':  str(10)},
                       {'old': 'OBJTYPE',
                        'new': 'Figure/ground task'},
                       {'old': 'TUTORIAL_HTML',
                        'new': tutorial_html},
                       {'old': 'CATDICT',
                        'new': cat_dict},
                       {'old': 'METAFIELD',
                        'new': "'dot_on'"}]

    variation_level = 'V6'
    disallowed_images = [meta[i]['filename'] for i in [4020, 5060]]
    query = lambda x: x['var'] == variation_level and (x['filename'] not in disallowed_images)
    html_data = {
            'response_images': response_images,
            'combs': [[True, False]],
            'num_trials': 1190,
            'meta_field': 'dot_on',
            'meta': meta,
            'urls': dataset.publish_images(range(meta.shape[0]), preproc, 'hvm_figure_ground', dummy_upload),
            'meta_query': query
    }
    exp = MatchToSampleFromDLDataExperiment(
            htmlsrc='general_two_way.html',
            htmldst='hvm_figure_ground%05d.html',
            sandbox=sandbox,
            title='Report whether the dot is on the object',
            reward=0.35,
            duration=1500,
            keywords=['neuroscience', 'psychology', 'experiment', 'object recognition'],  # noqa
            description="***You may complete as many HITs in this group as you want*** Complete a visual object recognition task where you report dots are on an object or not. We expect this HIT to take about 10 minutes or less, though you must finish in under 25 minutes.  By completing this HIT, you understand that you are participating in an experiment for the Massachusetts Institute of Technology (MIT) Department of Brain and Cognitive Sciences. You may quit at any time, and you will remain anonymous. Contact the requester with questions or concerns about this experiment.",  # noqa
            comment="hvm_figure_ground",  # noqa
            collection_name= 'hvm_figure_ground_2',
            max_assignments=1,
            bucket_name='hvm_figure_ground_2',
            trials_per_hit=170,  # 150 + 8x4 repeats
            html_data=html_data,
            frame_height_pix=1200,
            othersrc = ['../../lib/dltk.js', '../../lib/dltkexpr.js', '../../lib/dltkrsvp.js'],
            additionalrules=additionalrules
            )

    # -- create trials
    exp.createTrials(sampling='with-replacement', verbose=1)

    return exp, html_data


if __name__ == '__main__':
    exp, _ = get_exp(sandbox=True, dummy_upload=False)
    exp.prepHTMLs()
    exp.testHTMLs()
    exp.uploadHTMLs()
    exp.createHIT(secure=True)

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
