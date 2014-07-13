import math
import numpy as np

import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment

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

        bsize = 100
        nblocks = int(math.ceil(float(len(perm))/bsize))
        print('%d blocks' % nblocks)
        imgs = []
        imgData = []
        additional = ('centroid_x', 'centroid_y')
        for bn in range(nblocks):
            pinds = perm[bsize * bn: bsize * (bn + 1)]
            pinds = np.concatenate([pinds, pinds[:20]])
            assert (bn + 1 == nblocks) or (len(pinds) == 120), len(pinds)
            rng.shuffle(pinds)
            bmeta = emeta[query_inds[pinds]]
            burls = [urls[_i] for _i in pinds]
            bmeta = [{df: bm[df] for df in meta.dtype.names + additional} for bm in bmeta]
            imgs.extend(burls)
            imgData.extend(bmeta)
        self._trials = {'imgFiles': imgs, 'imgData': imgData}


exp = HvMPositionExperiment(htmlsrc = 'hvm_position.html',
                              htmldst = 'hvm_position_n%04d.html',
                              sandbox = True,
                              title = 'Position Judgement',
                              reward = 0.5,
                              duration = 1500,
                              description = 'Make position judgements for up to 50 cent bonus',
                              comment = "Position judgement in HvM dataset",
                              collection_name = None, #'hvm_position',
                              max_assignments=1,
                              bucket_name='hvm_position',
                              trials_per_hit=120)

if __name__ == '__main__':

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    exp.uploadHTMLs()
    #exp.createHIT()

#hitids = ['3YLTXLH3DFGSTOVAX3N7WV2YQWNHP0',
#          '34ZTTGSNJXYDT0WPXG2WW0S8VS9HQR',
#          '3ATYLI1PRTC6ZUEZ63DDJ8DNTJVJOQ',
#          '32ZCLEW0BZUOKUQ0L3QS88ID3ORJP7']
#import cPickle
#hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
#exp.disableHIT(hitids=hitids)
