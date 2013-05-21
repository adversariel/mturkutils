"""
Module of functions that streamline HIT publishing and data collection from MTurk.
"""
import pymongo
import urllib
import os.path
from hyperopt.base import SONify
import json
import datetime
import numpy as np
import cPickle as pk
import boto.mturk
from boto.mturk.connection import MTurkConnection
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto

class experiment(object):

    def __init__(self, sandbox = False, access_key_id = 'AKIAIVPHBWLGLGI5SYTQ', secretkey = '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', \
    keywords = [''], lifetime=1209600, max_assignments=1, title = '', reward=0.01, duration=1500, approval_delay=172800, \
    description='', frame_height_pix=1000, comment = '', collection_name = '', meta = None, LOG_PREFIX = './'):

        self.sandbox = sandbox
        self.access_key_id = access_key_id
        self.secretkey = secretkey
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
        self.setQual(90)

        self.setMongoVars(collection_name, comment, meta)
        self.conn = self.connect()

    def getBalance(self):
        return self.conn.get_account_balance()[0].amount   

    def setMongoVars(self, collection_name, comment, meta):
        """
        Establishes connection to database on dicarlo2. You must specify a valid collection name. If it does not alreay exist, \
        a new collection with that name will be created in the mturk database. You can optionally provide a metadata object.
        """

        self.collection_name = collection_name
        self.comment = comment

        if meta == None:
            self.meta = meta
        elif type(meta) != dict:
            print('Converting tabarray to dictionary for speed. This may take a minute...')
            self.meta = convertTabArrayToDict(meta)
        else:
            self.meta = meta

        if len(self.comment) == 0 or self.comment == None:
            raise AttributeError('Must provide comment!')
        
        if (type(self.collection_name) != str and type(self.collection_name) != None) or \
        (len(self.collection_name) == 0 and type(self.collection_name) == str):
            raise NameError('Please provide a valid MTurk database collection name.')
        else:
            print('Results will not be stored in a database until you set a proper collection name.')
            self.collection = None
            return

        #Connect to pymongo database for MTurk results.
        self.mongo_conn = pymongo.Connection(port = 22334, host = 'localhost')
        self.db = self.mongo_conn.mturk
        self.collection = self.db[collection_name]

    def connect(self):
        """
        Establishes connection to MTurk for publishing HITs and getting data. Pass sandbox=True if you want to use sandbox mode.
        Default access and secret keys will connect to Ethan's MTurk account.
        """
        if self.sandbox == False:
            conn = MTurkConnection(aws_access_key_id = self.access_key_id,
                   aws_secret_access_key = self.secretkey, )
        else: 
            conn = MTurkConnection(aws_access_key_id = self.access_key_id,
                   aws_secret_access_key = self.secretkey,
                   host='mechanicalturk.sandbox.amazonaws.com' )
        return conn

    def setQual(self, performance_thresh = 90):
        self.qual = self.createQual(performance_thresh)

    def createQual(self, performance_thresh = 90):
        """
        Returns an MTurk Qualification object which can then be passed to a HIT object. For now, I've only implemented \
        a prior HIT approval qualification, but more might be on the way.
        """
        from boto.mturk.qualification import PercentAssignmentsApprovedRequirement
        from boto.mturk.qualification import Qualifications
        
        if type(performance_thresh) != int:
            raise ValueError('Performance threshold must be an integer')
        req = PercentAssignmentsApprovedRequirement(comparator = 'GreaterThan', integer_value = performance_thresh)
        qual = Qualifications()
        qual.add(req)
        return qual

    def createHIT(self, URLlist, verbose=True):
        """
        - Pass a list of URLs (check that they work first!) for each one to be published as a HIT. 
        - This function returns a list of HIT IDs which can be used to collect data later. Those IDs are stored in 'self.hitids'.
        """
        if self.sandbox:
            print('**WORKING IN SANDBOX MODE**')
        
        conn = self.conn

        #Check if sufficient funds are available
        totalCost = (self.max_assignments*len(URLlist)*self.reward)*1.10
        available_funds = self.getBalance()

        if totalCost > available_funds:
            print('Insufficient funds available. You have $'+str(available_funds)+' in the bank, but this experiment' 
                'will cost $'+str(totalCost)+'. Aborting HIT creation.')
            return
        
        from boto.mturk.question import ExternalQuestion
        self.hitids = []
        for urlnum, url in enumerate(URLlist):
            q = ExternalQuestion(external_url=url, frame_height=self.frame_height_pix)
            create_hit_rs = conn.create_hit(question=q, lifetime=self.lifetime, max_assignments=self.max_assignments, \
                 title=self.title, keywords=self.keywords, reward=self.reward, duration=self.duration, \
                 approval_delay=self.approval_delay, annotation=url,  qualifications = self.qual, \
                 description = self.description, response_groups=['Minimal','HITDetail','HITQuestion','HITAssignmentSummary'])
            
            for hit in create_hit_rs:
                self.hitids.append(hit.HITId)
            assert create_hit_rs.status == True
            self.htypid = hit.HITTypeId

            if verbose == True:
                print(str(urlnum)+': '+url+', '+self.hitids[-1])
        file_string = self.LOG_PREFIX+str(self.htypid)+'_'+str(datetime.datetime.now())+'.pkl'
        file_string = file_string.replace(' ', '_')
        pk.dump(self.hitids, file(file_string, 'wb'))   
        return self.hitids


    def updateDBwithHITs(self, verbose=False):
        """
        - Takes a list of HIT IDs, gets data from MTurk, attaches metadata (if necessary) and puts results in dicarlo2 database.
        - Also stores data in object variable 'all_data' for immediate use.
        - Even if you've already gotten some HITs, this will get them again anyway. Maybe later I'll fix this.
        """
        self.all_data = []
        if self.sandbox:
            print('**WORKING IN SANDBOX MODE**')
        
        conn = self.conn
        col = self.collection
        meta = self.meta
        
        for hitid in self.hitids:
            #print('Getting HIT results...')
            sdata = self.getHITdata(hitid)
            self.all_data.extend(sdata)
            if col == None:
                continue
            else:
                pass
            
            #print('Connecting to database...')
            col.ensure_index([('WorkerID', pymongo.ASCENDING), ('Timestamp', pymongo.ASCENDING)], unique=True)
        
            #print('Updating database...')
            for subj in sdata:
                try:
                    subj_id = col.insert(subj, safe = True)
                    if meta != None:
                        if type(meta) == dict:
                            #Assuming meta is a dict -- this should be much faster!
                            m = [self.get_meta_fromdict(e, meta) for e in subj['StimShown']]
                            col.update({'_id': subj_id}, {'$set':{'ImgData': m}}, w=0)
                            if verbose:
                                print(subj_id)
                                print('------------')
                        else:
                            #Assuming meta is a tabarray
                            m = [self.get_meta(e, meta) for e in subj['StimShown']]
                            col.update({'_id': subj_id}, {'$set':{'ImgData': m}}, w=0)
                            if verbose:
                                print(subj_id)
                                print('------------')
                except pymongo.errors.DuplicateKeyError:
                    #print('Entry already exists, moving to next...')
                    continue    
            

    def getHITdata(self, hitid):
        assignment = self.conn.get_assignments(hit_id = hitid)
        subj_data = []
        for a in assignment:
            print a.WorkerId
            for qfa in a.answers[0]:
                ansdat = json.loads(qfa.fields[0][1:-1])
            HITdat = self.conn.get_hit(hit_id = hitid)
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
                try:
                    qual = {} #Should see how this code works for multiple qual types.
                    qual['QualificationTypeId'] = h.QualificationTypeId
                    qual['IntegerValue'] = h.IntegerValue
                    qual['Comparator'] = h.Comparator
                    ansdat['Qualification'] = qual
                except AttributeError:
                    pass
            subj_data.append(ansdat)
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
                
    def get_meta(self, url, meta, lookup_field = 'id'):
        if type(url) == list:
            dat = []
            for u in url:
                _id = getidfromURL(u)
                try:
                    dat.append(SONify(dict(zip(meta.dtype.names, meta[meta[lookup_field] == _id][0]))))
                except IndexError:
                    #print('This object not found in metadata. Skipping to next...')
                    #I'm assuming for now this error occurs because the ImgOrder format contains URLs for response images,
                    #which have no metadata. However, this error might also occur if something is wrong with a URL or
                    #the metadata file, in which case the error will be silent and that's not good.
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

    def uploadHTML(self, filelist, bucketname, verbose=True):
        """
        Pass a list of paths to the files you want to upload (or the filenames themselves in you're already
        in the directory) and the name of a bucket as a string. If the bucket does not exist, a new one will be created.
        This function uploads the files and sets their ACL to public-read, then returns a list of URLs. This will also \
        set self.URLs to that list of urls.
        
        Sub-directories within the bucket are not yet supported.
        """
        try:
            conn = S3Connection(self.access_key_id, self.secretkey)
        except boto.exception.S3ResponseError:
            print('Could not establish an S3 conection. Is your account properly configured?')
            return
        try:
            bucket = conn.get_bucket(bucketname)
        except boto.exception.S3ResponseError:
            print('Bucket does not exist, creating a new bucket...')
            bucket = conn.create_bucket(bucketname)
        
        urls = []
        for idx, f in enumerate(filelist):
            k = Key(bucket)
            k.key = f.split('/')[-1]
            k.set_contents_from_filename(f)
            bucket.set_acl('public-read', k.key)
            urls.append('http://s3.amazonaws.com/'+bucketname+'/'+k.key)
            if verbose:
                print str(idx)+': '+f
        
        self.URLs = urls        
        return urls    
        

#Some helper functions that are not a part of an experiment object.

def getidfromURL(url):
    u = urllib.url2pathname(url).split('/')[-1]
    u = os.path.splitext(u)[0]
    return u

def convertTabArrayToDict(meta_tabarray, lookup_field = 'id'):
    meta_dict = {}
    for m in meta_tabarray:
        meta_dict[m[lookup_field]] = SONify(dict(zip(meta_tabarray.dtype.names, m)))
    return meta_dict        

def updateGeoData(collect):
    conn = pymongo.Connection(port = 22334, host = 'localhost')
    db = conn.mturk
    col = db[collect]
    
    workers_seen = {}
    for c in col.find():
        if c.get('countryName') != None:
            continue
        else:
            if workers_seen.get(c['WorkerID']) != None:
                col.update({'_id': c['_id']}, {'$set': workers_seen[c['WorkerID']]}, w=0)
                #print('Worker already seen, updating entry...')
            else:
                #worker not already seen, get data from API
                response = json.loads(urllib.urlopen('http://api.ipinfodb.com/v3/ip-city/?key=8ee1f67f03db64c9d69c0ff899ee36348c3122d1a3e38f5cfaf1ec80ff269ee5&ip='+str(c['IPaddress'])+'&format=json').read())
                workers_seen[c['WorkerID']] = response
                col.update({'_id': c['_id']}, {'$set': workers_seen[c['WorkerID']]}, w=0)
                print(str(c['WorkerID'])+': '+str(response['countryName']))

