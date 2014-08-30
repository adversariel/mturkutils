import math
import numpy as np

import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment


LEARNING_PERIOD = 10
REPEATS = 20
BSIZE = 100

class HvMPositionExperiment(Experiment):

    def createTrials(self):

        dataset = hvm.HvMWithDiscfade()
        preproc = None

        dummy_upload = True
        image_bucket_name = 'hvm_timing'
        seed = 0

        meta = dataset.meta
        emeta = dataset.extended_meta
        query_inds = ((emeta['centroid_x'] > 0) & (emeta['centroid_y'] > 0)).nonzero()[0]

        urls = dataset.publish_images(query_inds, preproc,
                                      image_bucket_name, dummy_upload=dummy_upload)

        rng = np.random.RandomState(seed=seed)
        perm = rng.permutation(len(query_inds))

        nblocks = int(math.ceil(float(len(perm))/BSIZE))
        print('%d blocks' % nblocks)
        imgs = []
        imgData = []
        for bn in range(nblocks)[:1]:
            pinds = perm[BSIZE * bn: BSIZE * (bn + 1)]
            pinds = np.concatenate([pinds, pinds[: REPEATS]])
            rng.shuffle(pinds)
            if bn == 0:
                learning = perm[-LEARNING_PERIOD: ]
            else:
                learning = perm[BSIZE * bn - LEARNING_PERIOD: BSIZE*bn]
            pinds = np.concatenate([learning, pinds])
            assert (bn + 1 == nblocks) or (len(pinds) == BSIZE + REPEATS + LEARNING_PERIOD), len(pinds)
            bmeta = emeta[query_inds[pinds]]
            burls = [urls[_i] for _i in pinds]
            bmeta = [{df: bm[df] for df in meta.dtype.names + ('centroid_x', 'centroid_y')} for bm in bmeta]
            imgs.extend(burls)
            imgData.extend(bmeta)
        self._trials = {'imgFiles': imgs, 'imgData': imgData}

additionalrules = [{'old': 'LEARNINGPERIODNUMBER',
                    'new':  str(LEARNING_PERIOD)}]
exp = HvMPositionExperiment(htmlsrc = 'hvm_position_newtiming.html',
                              htmldst = 'hvm_position_newtiming_n%04d.html',
                              othersrc = ['raphael.min.js', 'dltk.js'],
                              sandbox = True,
                              title = 'Position Judgement',
                              reward = 0.5,
                              duration = 1500,
                              description = 'Make position judgements for up to 50 cent bonus',
                              comment = "Position judgement in HvM dataset",
                              collection_name = 'hvm_position_newtiming_test',
                              max_assignments=1,
                              bucket_name='hvm_position',
                              trials_per_hit=BSIZE + REPEATS + LEARNING_PERIOD,
                              additionalrules=additionalrules,
                              frame_height_pix=1200)

if __name__ == '__main__':

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    exp.uploadHTMLs()
    #exp.createHIT()
    #exp.updateDBwithHITs()
    #exp.payBonuses()


#hitids = ['3YLTXLH3DFGSTOVAX3N7WV2YQWNHP0',
#          '34ZTTGSNJXYDT0WPXG2WW0S8VS9HQR',
#          '3ATYLI1PRTC6ZUEZ63DDJ8DNTJVJOQ',
#          '32ZCLEW0BZUOKUQ0L3QS88ID3ORJP7']
#import cPickle
#hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
#exp.disableHIT(hitids=hitids)
