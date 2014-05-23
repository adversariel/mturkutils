import itertools
import random
import json
import os
import gzip
import copy
from collections import (Counter,
                         defaultdict)

from boto.s3.key import Key
import boto
import cPickle
import numpy as np
import yamutils.basic
import scipy.stats as s


def log_experiment_id(bucket_name):
    """
    :param bucket_name: for a given bucket name, check what experiments exist, create and log a new experiment id
    :return: the experiment id
    """
    upload_dir = os.path.join(os.getcwd(), 'upload_tmp')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    conn = boto.connect_s3()
    bucket = conn.create_bucket(bucket_name)  # Creates if it doesn't exist, gets existing if it does
    experiment_list_key = bucket.get_key('experiment_list.p')
    exp_list_filename = os.path.join(upload_dir, 'experiment_list.p')
    if experiment_list_key is not None:
        experiment_list_key.get_contents_to_filename(exp_list_filename)
        experiment_list = cPickle.load(open(exp_list_filename, 'rb'))
        experiment_id = bucket_name + str(1 + max([int(exp_id.lstrip(bucket_name)) for exp_id in experiment_list]))
        experiment_list.append(experiment_id)
    else:
        experiment_list_key = Key(bucket)
        experiment_list_key.key = 'experiment_list.p'
        experiment_id = bucket_name + str(0)
        experiment_list = [experiment_id]

    cPickle.dump(experiment_list, open(exp_list_filename, 'wb'))
    experiment_list_key.set_contents_from_filename(exp_list_filename)
    return experiment_id


def write_html(js_filename, out_filename, task_type='two_way'):
    """
    Modifies base html by replacing IMAGE_FILES_JS_FILENAME with a reference to the correct javascript that loads in
    experiment information

    :rtype : string, filename that was written to
    :param js_filename: javascript containing image files, labels, and other json objects needed by task
    :param out_filename: what filename to write html to
    :param task_type: what type of task (eight or two-way)

    """


    base_html_filename = task_type + '.html'
    import mturkutils

    path = os.path.join(mturkutils.__path__[0], 'templates')
    base_html_filename = os.path.join(path, base_html_filename)
    website_string = str(open(base_html_filename, 'rb').read())
    website_string = website_string.replace('IMAGE_FILES_JS_FILENAME', js_filename)
    # website_string.replace("BUCKET_NAME", bucket)
    with open(out_filename, 'wb') as of:
        of.write(website_string)
    return out_filename


class MatchToSampleExperiment(object):
    def __init__(self, combs, preproc,
                 dataset,
                 meta_field,
                 labelfunc,
                 bucket_name,
                 k=2,
                 seed=0,
                 dummy_upload=False,
                 meta_query=None,
                 task_type='two_way',
                 response_images=None):
        """
        Stores 3 lists containing info for running a forced choice task as instance variables
        imgs, imgData, labels
        :param meta_field: which field in the meta of the dataset to use
        :param task_type: 'two_way', 'eight_way' among others (see write_url)
        The base match to sample experiment object has three main lists describing the experiment:
        imgs, imgData and labels

        imgs is a list of of trial by trial stimuli urls. This means a list of entries like this for each trial:
        [[sample_image_urls] [test_image_1_url test_image_2_url]]

        imgData is a list of dictionaries containing information about the images in dictionary format
        This information is drawn from dataset.meta. This means a list of entries like this, one per trial.
        {
        "Sample":
            {"Category": 'Fruit', "Object": 'apple_obj_1'},
         "Test":
            [{"Category": 'Fruit', "Object": 'apple_obj_1'}, {"Category": 'Animal', "Object": 'dog_obj_1'}]
        }

        labels is a list of lists of labels to display alongside test images. This is a list for one trial:
        ['Apple', 'Dog']

        :param dummy_upload: If true, image files are assumed to have been uploaded previouls
        :param preproc: what preproc to use on images
            (see dldata.stimulus_sets.dataset_templates.ImageLoaderPreprocesser)
        :param bucket_name: what bucket to upload files to
        :param seed: random seed to use for shuffling
        :param dataset: which dataset to get images from
        :param combs: List of tuples of synsets to measure confusions for
        :param k: Number of times to measure each confusion.
        :param meta_query: subset the dataset according to this query, evaluated once at every meta entry
        sampled equally
        :param: labelfunc: callable that takes a dictionary meta entry and the dataset, and returns the label to be
            printed
        :param: response_images: list of
            tuple of image_urls, imgData, and labels to use for response images. There must be one set
             of responses per confusion to be measured. If this is not
                set, random images from the same category are used by default.
        """
        self.bucket_name = bucket_name
        self.task_type = task_type
        random.seed(seed)
        meta = dataset.meta
        if meta_query is not None:
            query_inds = set(np.ravel(np.argwhere(map(meta_query, meta))))
        else:
            query_inds = set(range(len(meta)))
        category_occurences = Counter(itertools.chain.from_iterable(combs))
        synset_urls = defaultdict(list)
        img_inds = []
        imgData = []
        n = len(list(combs[0]))
        category_meta_dicts = defaultdict(list)
        if response_images is None:
            num_per_category = int(np.ceil(float(k) / n) * (n + 1))
            response_images = [None]*len(combs)
        else:
            num_per_category = int(np.ceil(float(k) / n))
        for category in category_occurences.keys():
            cat_inds = set(np.ravel(np.argwhere(meta[meta_field] == category)))
            inds = list(query_inds & cat_inds)
            num_sample = category_occurences[category] * num_per_category
            assert len(inds) >= num_per_category, "Category %s has %s images, %s are required for this experiment" % \
                                                  (category, len(inds), num_sample)
            img_inds.extend(random.sample(inds, num_sample))

        urls = dataset.publish_images(img_inds, preproc, bucket_name, dummy_upload=dummy_upload)
        for url, img_ind in zip(urls, img_inds):
            meta_entry = meta[img_ind]
            category = meta_entry[meta_field]
            synset_urls[category].append(url)
            meta_dict = {name: value for name, value in
                         zip(meta_entry.dtype.names, meta_entry.tolist())}
            category_meta_dicts[category].append(meta_dict)
        imgs = []
        labels = []
        for c, ri in zip(combs, response_images):
            #We cycle through the possible sample categories one by one.
            for _ in np.arange(np.ceil(float(k) / n)):
                for sample_synset in c:
                    sample = synset_urls[sample_synset].pop()
                    sample_meta = category_meta_dicts[sample_synset].pop()
                    if ri is None:
                        test = [synset_urls[s].pop() for s in c]
                        test_meta = [category_meta_dicts[s].pop() for s in c]
                    else:
                        test = ri['urls']
                        test_meta = ri['meta']
                    imgs.append([sample, test])
                    imgData.append({"Sample": sample_meta, "Test": test_meta})
                    if ri is None:
                        if labels is None:
                            labels.append([''] * len(test_meta))
                        labels.append([labelfunc(meta_dict, dataset) for meta_dict in test_meta])
                    else:
                        labels.append(ri['labels'])

        for list_data in [imgs, imgData, labels]:
            random.seed(seed)
            random.shuffle(list_data)
        self.imgs = imgs
        self.imgData = imgData
        self.labels = labels
        self.experimentData = {'imgFiles': imgs, 'imgData': imgData, 'labels': labels,
                               'meta_field': [meta_field] * len(labels)}

    def hit_urls(self, trials_per_hit):
        """
        Using chunks of experiment data, writes and uploads tasks to s3
        :param trials_per_hit: How many trials to do per hit
        """
        bucket_name = self.bucket_name
        task_type = self.task_type
        experimentData = self.experimentData
        upload_dir = os.path.join(os.getcwd(), 'upload_tmp')
        experiment_id = log_experiment_id(bucket_name)
        bucket = boto.connect_s3().create_bucket(bucket_name)
        URLs = []
        files_to_upload = []

        for chunk_idx, chunk in enumerate(range(0, len(experimentData['imgFiles']), trials_per_hit)):
            js_file = os.path.join(upload_dir,
                                   'experiment_data_' + str(experiment_id) + '_' + str(chunk_idx) + '.js')
            f = file(js_file, 'wb')
            eData = {key: experimentData[key][chunk:chunk + trials_per_hit] for key in experimentData.keys()}
            eData['totalTrials'] = len(eData['imgFiles'])
            f.write('var ExperimentData = ' + json.dumps(eData))
            f.close()
            files_to_upload.append(js_file)
            html_file = os.path.join(upload_dir,
                                     '_'.join(['experiment', experiment_id, str(chunk_idx)]) + '.html')
            write_html(js_file.split('/')[-1], out_filename=html_file, task_type=task_type)
            files_to_upload.append(html_file)
            URLs.append('https://s3.amazonaws.com/' + bucket_name + '/' + html_file.split('/')[-1], )
        print 'Uploading html/jss files'
        for idx, f in enumerate(files_to_upload):
            if idx % 20 == 0:
                print '%s of %s' % (idx, len(files_to_upload))
            k = Key(bucket)
            k.key = f.split('/')[-1]
            k.set_contents_from_filename(f)
            bucket.set_acl('public-read', k.key)
        return URLs


class MatchToSampleExperimentWithTiming(MatchToSampleExperiment):
    def __init__(self, combs, preproc,
                 dataset,
                 meta_field,
                 labelfunc,
                 bucket_name,
                 k=2,
                 seed=0,
                 dummy_upload=False,
                 meta_query=None,
                 task_type='two_way',
                 response_images=None,
                 presentation_time=100):
        """
        See documentation for MatchToSampleExperiment
        :param presentation_time: Presentation time in ms
        """
        super(MatchToSampleExperimentWithTiming, self).__init__(combs=combs,
                                                                preproc=preproc,
                                                                k=k,
                                                                dataset=dataset,
                                                                bucket_name=bucket_name,
                                                                seed=seed,
                                                                dummy_upload=dummy_upload,
                                                                meta_query=meta_query,
                                                                meta_field=meta_field,
                                                                labelfunc=labelfunc,
                                                                task_type=task_type,
                                                                response_images=response_images)
        self.experimentData['stimduration'] = [presentation_time] * len(self.experimentData['imgFiles'])


class MatchToSampleExperimentWithReward(MatchToSampleExperiment):
    def __init__(self, reward_scale, combs, preproc,
                 dataset,
                 meta_field,
                 labelfunc,
                 bucket_name,
                 k=2,
                 seed=0,
                 dummy_upload=False,
                 meta_query=None,
                 task_type='two_way',
                 response_images=None,
                 presentation_time=100 ):
        """
        See documentation for MatchToSampleExperiment
        :param presentation_time: Presentation time in ms
        """
        super(MatchToSampleExperimentWithReward, self).__init__(combs=combs,
                                                                preproc=preproc,
                                                                k=k,
                                                                dataset=dataset,
                                                                bucket_name=bucket_name,
                                                                seed=seed,
                                                                dummy_upload=dummy_upload,
                                                                meta_query=meta_query,
                                                                meta_field=meta_field,
                                                                labelfunc=labelfunc,
                                                                task_type=task_type,
                                                                response_images=response_images)
        acc = np.linspace(0, 1, 100)
        n = float(len(combs[0]))
        print n
        fudged_hr = (acc/n)/(1/n)
        fudged_fa = ((1/n)-acc/n)/(1-1/n)
        fudged_hr[0] = 1. / (2 * 100)
        fudged_fa[0] = 1 - 1. / (2 * 100)
        fudged_fa[-1] = 1. / (2 * 100)
        fudged_hr[-1] = 1 - 1. / (2 * 100)
        dprime = s.norm.ppf(fudged_hr) - s.norm.ppf(fudged_fa)
        reward = dprime
        reward[reward < 0] = 0
        reward = list(reward/max(reward)*reward_scale)
        self.experimentData['reward_scale'] = [reward] * len(self.experimentData['imgFiles'])


class ReactionTimeTunedExperiment(MatchToSampleExperiment):
    def __init__(self,
                 combs, preproc,
                 dataset,
                 meta_field,
                 labelfunc,
                 bucket_name,
                 response_images,
                 meta_query=None,
                 task_type='two_way',
                 k_train=10, k_test=2,
                 dummy_upload=False,
                 stim_duration=100, response_duration=10000):
        """
        See documentation for MatchToSampleExperiment
        :param combs: List of lists: each list is represents the task with the names of the categories of choices
        :param preproc: How to preprocess images for display
                    (see dldata.stimulus_sets.dataset_templates.ImageLoaderPreprocessor)
        :param response_images: Canonical image response choices
        :param k_train: How many training trials to include at the beginning of each HIT
        :param k_test: How many trials to test (Canonical image responses)
        :param dataset: What dataset to use for meta/images
        :param bucket_name: Where to upload images, html, javascript on S3
        :param seed: Random seed used to shuffle trials
        :param dummy_upload: Set to true to assume images have already been appropriately uploaded (careful...)
        :param meta_query: Lambda function to subselect images for display
        :param meta_field: Which field in the meta to use for judging correct trials
        :param labelfunc: Lambda which takes a meta entry and generates text to display
        :param task_type: Base HTML file to use
        :param response_duration: How long subjects have to respond
        :param stim_duration: Presentation time in ms
        """
        self.train_trials = MatchToSampleExperiment(combs=combs,
                                                    preproc=preproc,
                                                    k=k_train,
                                                    dataset=dataset,
                                                    bucket_name=bucket_name,
                                                    seed=seed,
                                                    dummy_upload=dummy_upload,
                                                    meta_query=meta_query,
                                                    meta_field=meta_field,
                                                    labelfunc=labelfunc,
                                                    task_type=task_type,
                                                    response_images=None).experimentData
        imgs_shown = []

        for d in self.train_trials['imgData']:
            imgs_shown.append(d['Sample'])
            imgs_shown.extend(d['Test'])
        imgs_shown = set(imgs_shown)
        meta_query_new = lambda x: meta_query(x) and x['filename'] not in imgs_shown
        MatchToSampleExperiment.__init__(self,
                                         combs=combs,
                                         preproc=preproc,
                                         k=k_test,
                                         dataset=dataset,
                                         bucket_name=bucket_name,
                                         seed=seed,
                                         dummy_upload=dummy_upload,
                                         meta_query=meta_query_new,
                                         meta_field=meta_field,
                                         labelfunc=labelfunc,
                                         taskt_type=task_type,
                                         response_images=response_images)
        self.test_trials = self.experimentData
        self.bucket_name = bucket_name
        self.task_type = task_type
        self.experimentData = {}

        self.train_trials['responseduration'] = response_duration*2 * k_train
        self.train_trials['stimduration'] = stim_duration*1.5 * k_train
        self.test_trials['responseduration'] = response_duration * k_test
        self.test_trials['stimduration'] = stim_duration * k_test

    def hit_urls(self, trials_per_hit):
        test_trials_per_hit = trials_per_hit-len(self.train_trials['imgData'])
        for testk in self.test_trials.keys():
            trials = []
            test = self.test_trials[testk]
            train = self.train_trials[testk]
            for chunk in range(0, len(test), test_trials_per_hit):
                trials.extend(train)
                trials.extend(test[chunk:chunk+test_trials_per_hit])
            self.experimentData[testk] = trials
        return MatchToSampleExperiment.hit_urls(self, trials_per_hit)


