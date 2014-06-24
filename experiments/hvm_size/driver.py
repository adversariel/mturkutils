import math
import numpy as np

import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment

class HvMSizeExperiment(Experiment):

    def createTrials(self):

        dataset = hvm.HvMWithDiscfade()
        preproc = None

        dummy_upload = True
        image_bucket_name = 'hvm_timing'
        seed = 0

        meta = dataset.meta
        query_inds = np.arange(len(meta))

        urls = dataset.publish_images(query_inds, preproc,
                                      image_bucket_name, dummy_upload=dummy_upload)

        rng = np.random.RandomState(seed=seed)
        perm = rng.permutation(len(query_inds))

        bsize = 50
        nblocks = int(math.ceil(float(len(perm))/bsize))
        print('%d blocks' % nblocks)
        imgs = []
        imgData = []
        for bn in range(nblocks)[:2]:
            pinds = perm[bsize * bn: bsize * (bn + 1)]
            pinds2 = np.concatenate([pinds, pinds.copy()])
            perm0 = rng.permutation(len(pinds2))
            pinds2 = pinds2[perm0]
            bmeta = meta[query_inds[pinds2]]
            burls = [urls[_i] for _i in pinds2]
            bmeta = [{df: bm[df] for df in meta.dtype.names} for bm in bmeta]
            imgs.extend(burls)
            imgData.extend(bmeta)
        self._trials = {'imgFiles': imgs, 'imgData': imgData}

othersrc = ['three.min.js', 'posdict.js', 'Detector.js', 'TrackballControls.js']

exp = HvMSizeExperiment(htmlsrc = 'hvm_size.html',
                        htmldst = 'hvm_size_n%04d.html',
                        othersrc = othersrc,
                        sandbox = True,
                        title = 'Size Judgement',
                        reward = 0.5,
                        duration=1500,
                        description = 'Make object size judgements for up to 50 cent bonus',
                        comment = "Size judgement in HvM dataset (var6)",
                        collection_name = None,
                        max_assignments=1,
                        bucket_name='hvm_size',
                        trials_per_hit=100)

if __name__ == '__main__':

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    exp.uploadHTMLs()
    #exp.createHIT()

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
