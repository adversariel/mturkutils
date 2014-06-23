import math
import numpy as np

import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment

hvm_equivalents = {'Apple_Fruit_obj': 'single_apple', 'Apricot': 'Apricot_obj', 'BAHRAIN': 'MB27239',
 'Beetle': 'MB31409', 'CGTG_L': 'MB27840', 'DTUG_L': 'MB28041', 'ELEPHANT_M': 'lo_poly_animal_ELE_AF1',
 'GORILLA': 'MB28626', 'LIONESS': 'MB29302', 'MQUEEN_L': 'MB29654', 'Peach_obj': 'Peach_obj',
 'Pear_obj': 'single_pear', 'SISTER_L': 'icebreaker', 'Strawberry_obj': 'Strawberry_obj', 'TURTLE_L': 'terapin',
 '_001': 'MB29830', '_004': 'MB28045', '_008': 'MB29834', '_010': 'MB29834', '_011': 'MB27680', '_014': 'MB29822',
 '_01_Airliner_2jetEngines': 'MB27463', '_031': 'MB29822', '_033': 'MB27667', '_05_future': 'MB28029',
 '_08': 'antique_furniture_item_08', '_10': 'antique_furniture_item_10', '_11': 'antique_furniture_item_11', '_12': 'antique_furniture_item_12', '_18': 'antique_furniture_item_37', '_19_flyingBoat': 'MB28113',
 '_37': 'antique_furniture_item_37', '_38': 'antique_furniture_item_38', '_44': 'antique_furniture_item_44', 'alfa155': 'MB27827',
 'astra': 'MB28343', 'bear': 'lo_poly_animal_BEAR_BLK', 'blCow': 'MB27925', 'bmw325': 'MB27451', 'bora_a': 'MB31518',
 'breed_pug': 'lo_poly_animal_DOBERMAN', 'celica': 'MB28855',
 'clio': 'MB31518',
 'cruiser': 'icebreaker',
 'f16': 'MB28243',
 'face0001': 'face0001',
 'face0002': 'face0001',
 'face0003': 'face0001',
 'face0004': 'face0001',
 'face0005': 'face0001' , 'face0006': 'face0001',
 'face0007': 'face0001' , 'face0008': 'face0001',
 'hedgehog': 'hedgehog',
 'junkers88': 'MB29050',
 'mig29': 'MB29629' ,
 'motoryacht': 'motoryacht', 'raspberry_obj': 'Raspberry_obj',
 'rdbarren': 'MB27309',
 'sopwith': 'MB29050',
 'support': 'support_ship',
 'walnut_obj': 'walnut_obj',
 'watermelon_obj': 'single_watermelon',
 'z3': 'MB31079'}

class HvMPoseExperiment(Experiment):

    def createTrials(self):

        dataset = hvm.HvMWithDiscfade()
        preproc = None

        dummy_upload = False
        image_bucket_name = 'hvm_images_for_pose'
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
        for bn in range(nblocks):
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


goodexts = ['.JPG', '.bmp', '.jpg', '.js', '.png', '.tif']
L = filter(lambda x : x.endswith(tuple(goodexts)), os.listdir('hvm_js'))


othersrc = ['three.min.js', 'MTLLoader.js', 'OBJMTLLoader.js', 'OrbitControls.js',
            'Detector.js', 'stats.min.js'] + L

exp = HvMPoseExperiment(htmlsrc = 'hvm_pose.html',
                        htmldst = 'hvm_pose_n%04d.html',
                        othersrc = othersrc,
                        sandbox = True,
                        title = 'Pose Judgement',
                        reward = 0.5,
                        duration=1500,
                        description = 'Make object 3-d pose judgements for up to 50 cent bonus',
                        comment = "Pose judgement in HvM dataset (var6)",
                        collection_name = None,
                        max_assignments=1,
                        bucket_name='hvm_pose',
                        trials_per_hit=100)

if __name__ == '__main__':

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    #exp.uploadHTMLs()
    #exp.createHIT()

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
