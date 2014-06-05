import dldata.stimulus_sets.toy_containment as t
from mturkutils.base import MatchToSampleFromDLDataExperimentWithReward

two_way = [True, False]

def inside(meta_dict, dataset):
    if meta_dict['contained']:
        return 'Dot Inside'
    else:
        return 'Dot Outside'

html_data = {'response_images': [{'urls': ['https://s3.amazonaws.com/toy_containment/6038.jpg',
                                'https://s3.amazonaws.com/toy_containment/82722.jpg'],
                       'meta': [{'contained': c} for c in two_way],
                       'labels': ['Dot Inside', 'Dot Outside']}],
                       
             'combs': [two_way],
             'dataset':  t.toy_containment(),
             'preproc': None,
             'num_trials': 50,          
             'meta_field': 'contained',
             'dummy_upload': True,
             'meta_query': None,
             'labelfunc': inside,
             'seed': 0,
             'presentation_time': 100,
             'image_bucket_name': 'images_codetest_toy_containment',
             'reward_scale': 0.5
            }

exp = MatchToSampleFromDLDataExperimentWithReward(htmlsrc = 'two_way_containment_with_reward.html',
                              htmldst = 'two_way_containment_with_reward_n%04d.html',
                              sandbox = True,
                              title = 'Toy Containment Task',
                              reward = 0.5,
                              duration=1500,
                              description = 'Classify toy containment images for up to 50 cent bonus',
                              comment = "Code test forMeasuring toy containment example",
                              collection_name = 'codetest_toy_cntainment',
                              max_assignments=1, 
                              bucket_name='codetest_toy_containment',
                              trials_per_hit=50,
                              html_data = html_data)

exp.createTrials()
exp.prepHTMLs()
exp.testHTMLs()
exp.uploadHTMLs()
exp.createHIT()

#hitids = ['3YLTXLH3DFGSTOVAX3N7WV2YQWNHP0',
#          '34ZTTGSNJXYDT0WPXG2WW0S8VS9HQR',
#          '3ATYLI1PRTC6ZUEZ63DDJ8DNTJVJOQ',
#          '32ZCLEW0BZUOKUQ0L3QS88ID3ORJP7']
#exp.disableHIT(hitids=hitids)
