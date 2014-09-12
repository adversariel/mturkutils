import math
import numpy as np

import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment


LEARNING_PERIOD = 10
REPEATS = 20
BSIZE = 100

class HvMAreaBBoxExperiment(Experiment):

    def createTrials(self):

        dataset = hvm.HvMWithDiscfade()
        preproc = None

        dummy_upload = True
        image_bucket_name = 'hvm_timing'
        seed = 0

        meta = dataset.meta
        extended_meta = dataset.extended_meta
        query_inds = (extended_meta['axis_bb_top'] > 0).nonzero()[0]

        urls = dataset.publish_images(query_inds, preproc,
                                      image_bucket_name, dummy_upload=dummy_upload)

        rng = np.random.RandomState(seed=seed)
        perm = rng.permutation(len(query_inds))

        additional = ('area_bb_0_x',
                      'area_bb_0_y',
                      'area_bb_1_x',
                      'area_bb_1_y',
                      'area_bb_2_x',
                      'area_bb_2_y',
                      'area_bb_3_x',
                      'area_bb_3_y')

        nblocks = int(math.ceil(float(len(perm))/BSIZE))
        print('%d blocks' % nblocks)
        imgs = []
        imgData = []
        for bn in range(nblocks)[:]:
            pinds = perm[BSIZE * bn: BSIZE * (bn + 1)]
            pinds = np.concatenate([pinds, pinds[: REPEATS]])
            rng.shuffle(pinds)
            if bn == 0:
                learning = perm[-LEARNING_PERIOD: ]
            else:
                learning = perm[BSIZE * bn - LEARNING_PERIOD: BSIZE*bn]
            pinds = np.concatenate([learning, pinds])
            assert (bn + 1 == nblocks) or (len(pinds) == BSIZE + REPEATS + LEARNING_PERIOD), len(pinds)
            bmeta = extended_meta[query_inds[pinds]]
            burls = [urls[_i] for _i in pinds]
            names = meta.dtype.names + additional
            names = [ n for n in names if not 'semantic' in n ]
            bmeta = [{df: bm[df] for df in names} for bm in bmeta]
            imgs.extend(burls)
            imgData.extend(bmeta)
        self._trials = {'imgFiles': imgs, 'imgData': imgData}


additionalrules = [{'old': 'LEARNINGPERIODNUMBER',
                    'new':  str(LEARNING_PERIOD)}]
exp = HvMAreaBBoxExperiment(htmlsrc = 'hvm_area_bbox_newtiming.html',
                              htmldst = 'hvm_area_bbox_newtiming_n%04d.html',
                              othersrc = ['raphael.min.js', 'intersect.js', '../../lib/dltk.js'],
                              sandbox = False,
                              title = 'Minimum-area Bounding Box Judgement',
                              reward = 0.35,
                              duration=1500,
                              description = 'Make bounding box judgements for up to 50 cent bonus',
                              comment = "Minimum Area bounding box judgement in HvM dataset",
                              collection_name = 'hvm_area_bbox',
                              max_assignments=1,
                              bucket_name='hvm_area_bbox',
                              trials_per_hit=BSIZE + REPEATS + LEARNING_PERIOD,
                              additionalrules=additionalrules)



if __name__ == '__main__':

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    exp.uploadHTMLs()
    #exp.createHIT(secure=True)

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
