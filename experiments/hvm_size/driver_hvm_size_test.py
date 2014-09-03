import math
import numpy as np

import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment

"""
TODOs (From Judy's suggestions):
   reduce lags between stim presentation!!! fix this
   longer ISI?
   surface texture doesn't come immediately
   better instructions about angle and real size and depth
   move submit button to near the bar?
"""

LEARNING_PERIOD = 5
REPEATS = 5
BSIZE = 65

class HvMSizeExperiment(Experiment):

    def createTrials(self):

        dataset = hvm.HvMWithDiscfade()
        preproc = None

        dummy_upload = True
        image_bucket_name = 'hvm_timing'
        seed = 0

        meta = dataset.meta
        query_inds = np.arange(len(meta))
        #query_inds = ((meta['obj'] == '_11') & (meta['var'] == 'V3')).nonzero()[0]

        urls = dataset.publish_images(query_inds, preproc,
                                      image_bucket_name, dummy_upload=dummy_upload)

        rng = np.random.RandomState(seed=seed)
        perm = rng.permutation(len(query_inds))

        nblocks = int(math.ceil(float(len(perm))/BSIZE))
        print('%d blocks' % nblocks)
        imgs = []
        imgData = []
        for bn in range(nblocks)[1:3]:
            pinds = perm[BSIZE * bn: BSIZE * (bn + 1)]
            pinds = np.concatenate([pinds, pinds[: REPEATS]])
            rng.shuffle(pinds)
            if bn == 0:
                learning = perm[-LEARNING_PERIOD: ]
            else:
                learning = perm[BSIZE * bn - LEARNING_PERIOD: BSIZE*bn]
            pinds = np.concatenate([learning, pinds])
            assert (bn + 1 == nblocks) or (len(pinds) == BSIZE + REPEATS + LEARNING_PERIOD), len(pinds)
            bmeta = meta[query_inds[pinds]]
            burls = [urls[_i] for _i in pinds]
            bmeta = [{df: bm[df] for df in meta.dtype.names} for bm in bmeta]
            imgs.extend(burls)
            imgData.extend(bmeta)
        self._trials = {'imgFiles': imgs, 'imgData': imgData}

othersrc = ['three.min.js', 'posdict.js', 'Detector.js', 'jstat.min.js']

additionalrules = [{'old': 'LEARNINGPERIODNUMBER',
                    'new':  str(LEARNING_PERIOD)}]
                    
from boto.mturk.connection import MTurkConnection
from boto.mturk.qualification import Requirement

conn = MTurkConnection(aws_access_key_id="AKIAI7LNZISMTBL77M3Q", aws_secret_access_key="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")

userid = 'AOAZMLP27GD81'

name = "DiCarlo Lab Special Size Task Qualification for %s, " % userid
description = name

#qual_type = conn.create_qualification_type(name, description, 'Active')
#qtypeid = qual_type[0].QualificationTypeId
qtypeid = '306WV99NLIKZV7AA8XLX13YSYVN1N6'
print(qtypeid)
req = Requirement(qtypeid, 'Exists')
#conn.assign_qualification(qtypeid, userid, value=1, send_notification=True)
                     
exp = HvMSizeExperiment(htmlsrc = 'hvm_size.html',
                        htmldst = 'hvm_size_n%04d.html',
                        othersrc = othersrc,
                        sandbox = False,
                        title = 'Size Judgement, Just For %s' % userid,
                        reward = 1.50,
                        duration = 3500,
                        description = 'Make object size judgements for up to 50 cent bonus',
                        comment = "Size judgement in HvM dataset",
                        collection_name = None,
                        max_assignments=1,
                        bucket_name='hvm_size_judgements',    
                        trials_per_hit=BSIZE + REPEATS + LEARNING_PERIOD, 
                        additionalrules=additionalrules,
                        other_quals=[req])

if __name__ == '__main__':

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    exp.uploadHTMLs()
    exp.createHIT(hits_per_url=1)

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
