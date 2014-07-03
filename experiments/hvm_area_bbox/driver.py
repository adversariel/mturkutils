import math
import numpy as np

import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment

class HvMAreaBBoxExperiment(Experiment):

    def createTrials(self):

        dataset = hvm.HvMWithDiscfade()
        preproc = None

        dummy_upload = True
        image_bucket_name = 'hvm_timing'
        seed = 0

        meta = dataset.meta
        extended_meta = dataset.extended_meta
        query_inds = ((meta['var'] == 'V6') & (extended_meta['axis_bb_top'] > 0)).nonzero()[0]

        urls = dataset.publish_images(query_inds, preproc,
                                      image_bucket_name, dummy_upload=dummy_upload)

        rng = np.random.RandomState(seed=seed)
        perm = rng.permutation(len(query_inds))

        bsize = 50
        nblocks = int(math.ceil(float(len(perm))/bsize))
        print('%d blocks' % nblocks)
        additional = ('area_bb_0_x',
                     'area_bb_0_y',
                     'area_bb_1_x',
                     'area_bb_1_y',
                     'area_bb_2_x',
                     'area_bb_2_y',
                     'area_bb_3_x',
                     'area_bb_3_y')
        imgs = []
        imgData = []
        for bn in range(nblocks):
            pinds = perm[bsize * bn: bsize * (bn + 1)]
            pinds2 = np.concatenate([pinds, pinds.copy()])
            perm0 = rng.permutation(len(pinds2))
            pinds2 = pinds2[perm0]
            bmeta = extended_meta[query_inds[pinds2]]
            burls = [urls[_i] for _i in pinds2]
            bmeta = [{df: bm[df] for df in meta.dtype.names + additional} for bm in bmeta]
            imgs.extend(burls)
            imgData.extend(bmeta)
        self._trials = {'imgFiles': imgs, 'imgData': imgData}


exp = HvMAreaBBoxExperiment(htmlsrc = 'hvm_area_bbox.html',
                              htmldst = 'hvm_area_bbox_var6_n%04d.html',
                              sandbox = True,
                              title = 'Minimum-area Bounding Box Judgement',
                              reward = 0.5,
                              duration=1500,
                              description = 'Make bounding box judgements for up to 50 cent bonus',
                              comment = "Minimum Area bounding box judgement in HvM dataset (var6)",
                              collection_name = None,
                              max_assignments=1,
                              bucket_name='hvm_area_bbox',
                              trials_per_hit=100,
                              othersrc = ['raphael.min.js', 'intersect.js'])

if __name__ == '__main__':

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    #exp.uploadHTMLs()
    #exp.createHIT()

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
