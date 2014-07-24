import math
import numpy as np

import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment

othersrc = ['three.min.js', 'posdict.js', 'Detector.js', 'TrackballControls.js', 'jstat.min.js']

LEARNING_PERIOD = 20
REPEATS = 20
BSIZE = 100

class HvMPoseExperiment(Experiment):

    def createTrials(self):

        dataset = hvm.HvMWithDiscfade()
        preproc = None

        dummy_upload = True
        image_bucket_name = 'hvm_timing'
        seed = 0

        meta = dataset.meta
        query_inds = np.arange(len(meta))
        #query_inds = ((np.sqrt(meta['rxy']**2) > 30) &  (np.sqrt(meta['rxz']**2) > 30) & (np.sqrt(meta['ryz']**2) > 30)).nonzero()[0]
        #query_inds = ((meta['var'] == 'V6') &  (meta['category'] == 'Faces')).nonzero()[0]
        #query_inds = ((meta['var'] == 'V6')  & (meta['category'] == 'Faces')).nonzero()[0]
        #query_inds = ((np.sqrt(meta['ryz']**2) > 0) & (np.sqrt((meta['rxy']**2 + meta['rxz']**2)) <  10) &  (meta['category'] == 'Tables')).nonzero()[0]
        #query_inds = ((np.sqrt(meta['ryz']**2) > 0) & (np.sqrt((meta['rxy']**2 + meta['rxz']**2)) <  50) &  (meta['category'] == 'Chairs')).nonzero()[0]
        #query_inds = ((meta['var'] == 'V6') & (meta['obj'] == '_01_Airliner_2jetEngines')).nonzero()[0]
        #query_inds = ((meta['var'] == 'V6') & (meta['obj'] == 'face0001')).nonzero()[0]
        #aquery_inds = ((meta['var'] == 'V6') &  (meta['obj'] == 'bear')).nonzero()[0]

        urls = dataset.publish_images(query_inds, preproc,
                                      image_bucket_name, dummy_upload=dummy_upload)

        rng = np.random.RandomState(seed=seed)
        perm = rng.permutation(len(query_inds))

        nblocks = int(math.ceil(float(len(perm))/BSIZE))
        print('%d blocks' % nblocks)
        imgs = []
        imgData = []
        for bn in range(nblocks)[:2]:
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

additionalrules = [{'old': 'LEARNINGPERIODNUMBER',
                    'new':  str(LEARNING_PERIOD)}]
exp = HvMPoseExperiment(htmlsrc = 'hvm_pose_test4.html',
                        htmldst = 'hvm_pose_test_n%04d.html',
                        othersrc = othersrc,
                        sandbox = True,
                        title = 'Pose Judgement',
                        reward = 0.5,
                        duration=1500,
                        description = 'Make object 3-d pose judgements for up to 50 cent bonus',
                        comment = "Pose judgement in HvM dataset",
                        collection_name = None,
                        max_assignments=1,
                        bucket_name='hvm_pose',
                        trials_per_hit=BSIZE + REPEATS + LEARNING_PERIOD,
                        additionalrules=additionalrules)

if __name__ == '__main__':

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    #exp.uploadHTMLs()
    #exp.createHIT()

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
