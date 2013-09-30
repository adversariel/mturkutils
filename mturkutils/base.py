"""
Module of functions that streamline HIT publishing and data collection from MTurk. Contact Ethan Solomon
(esolomon@mit.edu) or Diego Ardila (ardila@mit.edu) for help!
"""
import pymongo
import urllib
import os.path
import json
import datetime
import numpy as np
import cPickle as pk
import boto.mturk
from bson.objectid import ObjectId
from boto.mturk.connection import MTurkConnection
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto
import csv
from boto.pyami.config import Config

MTURK_CRED_SECTION = 'MTurkCredentials'
BOTO_CRED_FILE = os.path.expanduser('~/.boto')


def parse_credentials_file(path=None, section_name='Credentials'):
    if path is None:
        path = BOTO_CRED_FILE
    config = Config(path)
    assert config.has_section(section_name), \
        'Field ' + section_name + ' not found in credentials file located at ' + path
    return config.get(section_name, 'aws_access_key_id'), config.get(section_name, 'aws_secret_access_key')


class Experiment(object):
    """
    An Experiment object contains all the functions and data necessary for publishing a hit on MTurk.

    MTurk Parameters
    Required:
    - sandbox (default True): Publish to the MTurk Worker Sandbox if True (workersandbox.mturk.com). I recommend
        publishing to the sandbox first and checking that  your HIT works properly.
    - lifetime: Time, in seconds, for how long the HITs will stay active on Mechanical Turk. The default value is
        2 weeks, which is fine for most purposes.
    - max_assignments: How many Workers are allowed to complete each HIT. Remember that a given Worker cannot complete
        the same HIT twice
        (but they can complete as many HITs within the same HIT Type as they want).
    - title: What shows up as the HIT Type header on the MTurk website.
    - reward: In dollars, how much a Worker gets paid for completing 1 HIT.
    - duration: Time, in seconds, that a worker has to complete a HIT aftering clicking "accept." I try to give them a
        comfortable margin beyond how long I actually expect the task to take. But don't make it too long or workers
        will be dissuaded from even trying it.
    - approval_delay: Time, in seconds, until MTurk automatically approves HITs and pays workers. The default is 2 days.
    - description: The text workers see on the MTurk website before previewing a HIT. Should be a short-and-sweet
        explanation of what the task is
        and how long it should take. Also include the experimental disclaimer.
    - frame_height_pix: Size of the embedded frame that pulls in your external URL. 1000 should be fine for most
        purposes.

    Non-MTurk Parameters
    - comment: Explanation of the task and data format to be included in the database for this experiment. The
        description should be adequate for future investigators to understand what you did and what the data means.
    - collection_name: String, name of collection within the 'mturk' dicarlo2 database.  If `None`, no DB connection
        will be made.
    - meta (optional): Tabarray or dictionary to link stimulus names with their metadata. There's some work to be done
        with this feature. Right now, mturkutils extracts image filenames from 'StimShown' and looks up metadata in meta
        by that filename. For speed, it re-sorts any tabarray into a dictionary indexed by the original 'id' field.
        Feel free to pass None and attach metadata yourself later, especially if your experiment isn't the usual
        recognition-style task.
    - LOG_PREFIX: Where to save a pickle file with a list of published HIT IDs. You can retrieve data from any hit
        published in the past using these IDs (within the Experiment object, the IDs are also saved in 'hitids').
    """

    def __init__(self, sandbox=True, keywords=None, lifetime=1209600,
                 max_assignments=1, title='TEST', reward=0.01, duration=1500, approval_delay=172800,
                 description='TEST', frame_height_pix=1000, comment='TEST', collection_name='TEST', meta=None,
                 LOG_PREFIX='./', section_name=MTURK_CRED_SECTION):
        if keywords is None:
            keywords = ['']
        self.sandbox = sandbox
        self.access_key_id, self.secretkey = parse_credentials_file(section_name=section_name)
        self.keywords = keywords
        self.lifetime = lifetime
        self.max_assignments = max_assignments
        self.title = title
        self.reward = reward
        self.duration = duration
        self.approval_delay = approval_delay
        self.description = description
        self.frame_height_pix = frame_height_pix
        self.LOG_PREFIX = LOG_PREFIX
        self.section_name = section_name
        self.setQual(90)

        self.setMongoVars(collection_name, comment, meta)
        self.conn = self.connect()

    def getBalance(self):
        """
        Returns the amount of available funds. If you're in Sandbox mode, this will always return $10,000.
        """
        return self.conn.get_account_balance()[0].amount

    def setMongoVars(self, collection_name, comment, meta):
        """
        Establishes connection to database on dicarlo2.

        :param collection_name: You must specify a valid collection name. If it does not already exist, a new collection
            with that name will be created in the mturk database.  If `None` is given, the actual db coonection will
            be bypassed, and all db-related functions will not work.
        :param comment: Explanation of the task and data format to be included in the database for this experiment. The
            description should be adequate for future investigators to understand what you did and what the data means.
        :param meta: You can optionally provide a metadata object, which will be converted into a dictionary indexed by
            the 'id' field (unless otherwise specified).
        """

        self.collection_name = collection_name
        self.comment = comment

        if 'tabarray' in type(meta).__name__:
            print('Converting tabarray to dictionary for speed. This may take a minute...')
            self.meta = convertTabArrayToDict(meta)
        else:
            self.meta = meta

        if len(self.comment) == 0 or self.comment is None:
            raise AttributeError('Must provide comment!')

        # if no db connection is requested, bypass the rest
        if collection_name is None:
            self.mongo_conn = None
            self.db = None
            self.collection = None
            return

        # make db connection and create collection
        if (type(self.collection_name) != str and type(self.collection_name) is not None) or \
                (len(self.collection_name) == 0 and type(self.collection_name) == str):
            raise NameError('Please provide a valid MTurk database collection name.')

        #Connect to pymongo database for MTurk results.
        self.mongo_conn = pymongo.Connection(port=22334, host='localhost')
        self.db = self.mongo_conn['mturk']
        self.collection = self.db[collection_name]

    def connect(self):
        """
        Establishes connection to MTurk for publishing HITs and getting data. Pass sandbox=True if you want to use
        sandbox mode.
        """
        if not self.sandbox:
            conn = MTurkConnection(aws_access_key_id=self.access_key_id,
                                   aws_secret_access_key=self.secretkey, )
        else:
            conn = MTurkConnection(aws_access_key_id=self.access_key_id,
                                   aws_secret_access_key=self.secretkey,
                                   host='mechanicalturk.sandbox.amazonaws.com')
        return conn

    def setQual(self, performance_thresh=90):
        self.qual = self.createQual(performance_thresh)

    def createQual(self, performance_thresh=90):
        """
        Returns an MTurk Qualification object which can then be passed to a HIT object. For now, I've only implemented a
        prior HIT approval qualification, but boto supports many more.
        """
        from boto.mturk.qualification import PercentAssignmentsApprovedRequirement
        from boto.mturk.qualification import Qualifications

        if type(performance_thresh) != int:
            raise ValueError('Performance threshold must be an integer')
        req = PercentAssignmentsApprovedRequirement(comparator='GreaterThan', integer_value=performance_thresh)
        qual = Qualifications()
        qual.add(req)
        return qual

    def createHIT(self, URLlist=None, verbose=True, hitidslog=None):
        """
        - Pass a list of URLs (check that they work first!) for each one to be published as a HIT. If you've used
            mturkutils to upload HTML, those (self.URLs) will be used by default.
        - This function returns a list of HIT IDs which can be used to collect data later. Those IDs are stored in
            'self.hitids'.
        - The HITids are also stored in a pickle file saved to LOG_PREFIXi or, if given, `hitidslog`.
        """
        if URLlist is None:
            URLlist = self.URLs
        if self.sandbox:
            print('**WORKING IN SANDBOX MODE**')

        conn = self.conn

        #Check if sufficient funds are available
        totalCost = (self.max_assignments * len(URLlist) * self.reward) * 1.10
        available_funds = self.getBalance()

        if totalCost > available_funds:
            print(
                'Insufficient funds available. You have $' + str(available_funds) +
                ' in the bank, but this experiment will cost $' + str(totalCost) + '. Aborting HIT creation.')
            return

        from boto.mturk.question import ExternalQuestion

        self.hitids = []
        for urlnum, url in enumerate(URLlist):
            q = ExternalQuestion(external_url=url, frame_height=self.frame_height_pix)
            create_hit_rs = conn.create_hit(question=q, lifetime=self.lifetime, max_assignments=self.max_assignments,
                                            title=self.title, keywords=self.keywords, reward=self.reward,
                                            duration=self.duration,
                                            approval_delay=self.approval_delay, annotation=url,
                                            qualifications=self.qual,
                                            description=self.description,
                                            response_groups=['Minimal', 'HITDetail', 'HITQuestion',
                                                             'HITAssignmentSummary'])

            for hit in create_hit_rs:
                self.hitids.append(hit.HITId)
                self.htypid = hit.HITTypeId
            assert create_hit_rs.status

            if verbose:
                print(str(urlnum) + ': ' + url + ', ' + self.hitids[-1])
        if hitidslog is None:
            file_string = self.LOG_PREFIX + str(self.htypid) + '_' + str(datetime.datetime.now()) + '.pkl'
            file_string = file_string.replace(' ', '_')
        else:
            file_string = hitidslog
        pk.dump(self.hitids, file(file_string, 'wb'))
        return self.hitids

    def disableHIT(self, hitids=None):
        """Disable published HITs"""
        if hitids is None:
            hitids = self.hitids
        for hitid in hitids:
            self.conn.disable_hit(hitid)

    def updateDBcore(self, datafile=None, verbose=False):
        """See the documentation of updateDBwithHITs() and updateDBwithHITslocal()"""
        # XXX: hahong: is the support for datafile implemented correctly??
        if self.mongo_conn is None:
            print('**NO DB CONNECTION**')
            return 

        self.all_data = []
        if self.sandbox:
            print('**WORKING IN SANDBOX MODE**')

        col = self.collection
        meta = self.meta

        for hitid in self.hitids:
            #print('Getting HIT results...')
            if datafile is None:
                sdata = self.getHITdata(hitid)
            else:
                sdata = parse_human_data(datafile)   # XXX: hahong: seems that this part is broken (Issue #1)
            self.all_data.extend(sdata)
            if col is None:
                continue
            else:
                pass

            #print('Connecting to database...')
            col.ensure_index([('WorkerID', pymongo.ASCENDING), ('Timestamp', pymongo.ASCENDING)], unique=True)  # bug (hahong: marked as bug, but for what??)

            #print('Updating database...')
            for subj in sdata:
                try:
                    subj_id = col.insert(subj, safe=True)
                    if meta is not None:
                        if type(meta) == dict:
                            #Assuming meta is a dict -- this should be much faster!
                            m = [self.get_meta_fromdict(e, meta) for e in subj['StimShown']]
                            col.update({'_id': subj_id}, {'$set': {'ImgData': m}}, w=0)
                            if verbose:
                                print(subj_id)
                                print('------------')
                        else:
                            #Assuming meta is a tabarray
                            m = [self.get_meta(e, meta) for e in subj['StimShown']]
                            col.update({'_id': subj_id}, {'$set': {'ImgData': m}}, w=0)
                            if verbose:
                                print(subj_id)
                                print('------------')
                except pymongo.errors.DuplicateKeyError:
                    #print('Entry already exists, moving to next...')
                    continue

    def updateDBwithHITs(self, verbose=False):
        """
        - Takes a list of HIT IDs, gets data from MTurk, attaches metadata (if necessary) and puts results in dicarlo2
            database.
        - Also stores data in object variable 'all_data' for immediate use. This might be dangerous for MH17's memory.
        - Even if you've already gotten some HITs, this will try to get them again anyway. Maybe later I'll fix this.
        """
        self.updateDBcore(self, verbose=verbose)

    def updateDBwithHITslocal(self, datafile, verbose=False):
        """
        - Takes data directly downloaded from MTurk in the form of csv file, attaches metadata (if necessary) and puts
            results in dicarlo2 database.
        - Also stores data in object variable 'all_data' for immediate use.
        - Even if you've already gotten some HITs, this will get them again anyway. Maybe later I'll fix this.
        """
        # XXX: hahong: is this implemented correctly???
        self.updateDBcore(self, datafile=datafile, verbose=verbose)

    def getHITdata(self, hitid):
        assignment = self.conn.get_assignments(hit_id=hitid, page_size=self.max_assignments)
        subj_data = []
        for a in assignment:
            try:
                print a.WorkerId
                for qfa in a.answers[0]:
                    ansdat = json.loads(qfa.fields[0][1:-1])
                HITdat = self.conn.get_hit(hit_id=hitid)
                for h in HITdat:
                    ansdat['HITid'] = h.HITId
                    ansdat['Title'] = h.Title
                    ansdat['Reward'] = h.FormattedPrice
                    ansdat['URL'] = h.RequesterAnnotation
                    ansdat['Duration'] = h.AssignmentDurationInSeconds
                    ansdat['AssignmentID'] = a.AssignmentId
                    ansdat['WorkerID'] = a.WorkerId
                    ansdat['HITTypeID'] = h.HITTypeId
                    ansdat['Timestamp'] = a.SubmitTime
                    ansdat['Keywords'] = h.Keywords
                    ansdat['CreationTime'] = h.CreationTime
                    ansdat['AcceptTime'] = a.AcceptTime
                    ansdat['Comment'] = self.comment
                    ansdat['Description'] = self.description
                    try:
                        qual = {'QualificationTypeId': h.QualificationTypeId, 'IntegerValue': h.IntegerValue,
                                'Comparator': h.Comparator}  # Should see how this code works for multiple qual types.
                        ansdat['Qualification'] = qual
                    except AttributeError:
                        pass
                subj_data.append(ansdat)
            except ValueError:
                print('Error in decoding JSON data. Skipping for now...')
                continue
        return subj_data

    def get_meta_fromdict(self, url, meta):
        if type(url) == list:
            dat = []
            for u in url:
                _id = getidfromURL(u)
                try:
                    dat.append(meta[_id])
                except KeyError:
                    #Object not found in metadata. Skip to next
                    continue
            return dat
        elif type(url) == str or type(url) == unicode:
            _id = getidfromURL(url)
            try:
                return meta[_id]
            except KeyError:
                #Object not found in metadata. Return empty dict.
                return {}
        else:
            print(url)
            raise ValueError('Stimulus name not recognized. Is it a URL or metadata id?')

    def get_meta(self, url, meta, lookup_field='id'):
        if type(url) == list:
            dat = []
            for u in url:
                _id = getidfromURL(u)
                try:
                    dat.append(SONify(dict(zip(meta.dtype.names, meta[meta[lookup_field] == _id][0]))))
                except IndexError:
                    #print('This object not found in metadata. Skipping to next...')
                    #I'm assuming for now this error occurs because the ImgOrder format contains URLs for response
                    #images, which have no metadata. However, this error might also occur if something is wrong with a
                    #URL or the metadata file, in which case the error will be silent and that's not good.
                    continue
            return dat
        elif type(url) == str or type(url) == unicode:
            _id = getidfromURL(url)
            try:
                return SONify(dict(zip(meta.dtype.names, meta[meta[lookup_field] == _id][0])))
            except IndexError:
                print('This object not found in metadata. Returning empty dict.')
                return {}
        else:
            print(url)
            raise ValueError('Stimulus name not recognized. Is it a URL?')

    def uploadHTML(self, filelist, bucketname, dstprefix='', verbose=10, section_name=None, test=True):
        """
        Pass a list of paths to the files you want to upload (or the filenames themselves in you're already
        in the directory) and the name of a bucket as a string. If the bucket does not exist, a new one will be created.
        This function uploads the files and sets their ACL to public-read, then returns a list of URLs. This will also \
        set self.URLs to that list of urls.

        Sub-directories within the bucket are not yet supported.
        """
        if section_name is None:
            # section_name is provided to give flexibility of
            # using different accounts
            section_name = self.section_name

        keys = uploader(filelist, bucketname, dstprefix=dstprefix,
                section_name=section_name, test=test, verbose=verbose)

        urls = []
        for idx, (k, f) in enumerate(zip(keys, filelist)):
            urls.append('http://s3.amazonaws.com/' + bucketname + '/' + k)
            if verbose > 0:
                print str(idx) + ': ' + f
        self.URLs = urls
        return urls

experiment = Experiment   # for backward compatibility


# -- Some helper functions that are not a part of an Experiment object.
def parse_human_data(datafile):
    csv.field_size_limit(10000000000)
    count = 0
    with open(datafile, 'rb+') as csvfile:

        datareader = csv.reader(csvfile, delimiter='\t')
        subj_data = []
        for row in datareader:
            if count == 0 and len(row) > 0 and row[0] == 'hitid':
                count += 1
                # column_labels = row

            else:
                try:
                    subj_data.append(json.loads(row[-1][1:-1]))
                except ValueError:
                #   print(row[-1])
                    continue
                subj_data[-1]['HITid'] = row[0]
                subj_data[-1]['Title'] = row[2]
                subj_data[-1]['Reward'] = row[5]
                subj_data[-1]['URL'] = row[13]
                subj_data[-1]['Duration'] = row[14]
                subj_data[-1]['ViewHIT'] = row[17]
                subj_data[-1]['AssignmentID'] = row[18]
                subj_data[-1]['WorkerID'] = row[19]
                subj_data[-1]['Timestamp'] = row[23]

        csvfile.close()
    return subj_data


def getidfromURL(url):
    u = urllib.url2pathname(url).split('/')[-1]
    u = os.path.splitext(u)[0]
    return u


def convertTabArrayToDict(meta_tabarray, lookup_field='id'):
    meta_dict = {}
    for m in meta_tabarray:
        meta_dict[m[lookup_field]] = SONify(dict(zip(meta_tabarray.dtype.names, m)))
    return meta_dict


def updateGeoData(collect):
    conn = pymongo.Connection(port=22334, host='localhost')
    db = conn.mturk
    col = db[collect]

    workers_seen = {}
    for c in col.find():
        if c.get('countryName') is not None:
            continue
        else:
            if workers_seen.get(c['WorkerID']) is not None:
                col.update({'_id': c['_id']}, {'$set': workers_seen[c['WorkerID']]}, w=0)
                #print('Worker already seen, updating entry...')
            else:
                #worker not already seen, get data from API
                response = json.loads(urllib.urlopen(
                    'http://api.ipinfodb.com/v3/ip-city/?' +
                    'key=8ee1f67f03db64c9d69c0ff899ee36348c3122d1a3e38f5cfaf1ec80ff269ee5&ip=' +
                    str(c['IPaddress']) + '&format=json').read())
                workers_seen[c['WorkerID']] = response
                col.update({'_id': c['_id']}, {'$set': workers_seen[c['WorkerID']]}, w=0)
                print(str(c['WorkerID']) + ': ' + str(response['countryName']))


def SONify(arg, memo=None):
    if memo is None:
        memo = {}
    if id(arg) in memo:
        rval = memo[id(arg)]
    if isinstance(arg, ObjectId):
        rval = arg
    elif isinstance(arg, datetime.datetime):
        rval = arg
    elif isinstance(arg, np.floating):
        rval = float(arg)
    elif isinstance(arg, np.integer):
        rval = int(arg)
    elif isinstance(arg, (list, tuple)):
        rval = type(arg)([SONify(ai, memo) for ai in arg])
    elif isinstance(arg, dict):
        rval = dict([(SONify(k, memo), SONify(v, memo))
                     for k, v in arg.items()])
    elif isinstance(arg, (basestring, float, int, type(None))):
        rval = arg
    elif isinstance(arg, np.ndarray):
        if arg.ndim == 0:
            rval = SONify(arg.sum())
        else:
            rval = map(SONify, arg)  # N.B. memo None
    # -- put this after ndarray because ndarray not hashable
    elif arg in (True, False):
        rval = int(arg)
    else:
        raise TypeError('SONify', arg)
    memo[id(rval)] = rval
    return rval


def uploader(srcfiles, bucketname, dstprefix='', section_name=MTURK_CRED_SECTION,
        test=True, verbose=False, accesskey=None, secretkey=None,
        dstfiles=None, acl='public-read'):
    """Upload multiple files into a S3 bucket"""
    if accesskey is None or secretkey is None:
        accesskey, secretkey = parse_credentials_file(section_name=section_name)

    # -- establish connections
    try:
        conn = S3Connection(accesskey, secretkey)
    except boto.exception.S3ResponseError:
        raise ValueError('Could not establish an S3 conection. Is your account properly configured?')
    try:
        bucket = conn.get_bucket(bucketname)
    except boto.exception.S3ResponseError:
        print('Bucket does not exist, creating a new bucket...')
        bucket = conn.create_bucket(bucketname)

    if dstfiles is None:
        dstfiles = [None] * len(srcfiles)

    # -- upload files
    keys = []
    for i_fn, (fn, dfn) in enumerate(zip(srcfiles, dstfiles)):
        if dfn is None:
            dfn = fn
        # upload
        key_dst = dstprefix + os.path.basename(dfn)
        k = Key(bucket)
        k.key = key_dst
        k.set_contents_from_filename(fn)
        k.close()
        if acl is not None:
            bucket.set_acl(acl, key_dst)

        # download and check... although this is a bit redundant
        if test:
            k = Key(bucket)
            k.key = key_dst
            s = k.get_contents_as_string()
            k.close()
            assert s == open(fn).read()
        keys.append(key_dst)

        if verbose and i_fn % verbose == 0:
            print 'At:', i_fn, 'out of', len(srcfiles)

    return keys
