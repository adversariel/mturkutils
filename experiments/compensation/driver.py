import math
import numpy as np

import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment

userid = 'A1J98D0GPAKZN4'
class CompensationExperiment(Experiment):
    def createTrials(self):
        self._trials = {'acceptID': [userid]}

from boto.mturk.qualification import Requirement


from boto.mturk.connection import MTurkConnection
conn = MTurkConnection(aws_access_key_id="AKIAI7LNZISMTBL77M3Q", aws_secret_access_key="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")


name = "For Sketchloop Special Compensation 0"
description = name

#qual_type = conn.create_qualification_type(name, description, 'Active')
#qtypeid = qual_type[0].QualificationTypeId
qtypeid = '3PO9K4KN94Q7ISTQ4FBHJTNC50KY7H'
print(qtypeid)
req = Requirement(qtypeid, 'Exists')
#conn.assign_qualification(qtypeid, userid, value=1, send_notification=True)

exp = CompensationExperiment(htmlsrc = 'compensate.html',
                              htmldst = 'compensate_n%04d.html',
                              sandbox = False,
                              title = 'Special Compensation',
                              reward = 0,
                              duration=1500,
                              description="***Compensation for invited workers only***",
                              comment="compensation, reimbursement",
                              collection_name = None,
                              max_assignments=1,
                              bucket_name='sketchloop_special_compensation',
                              trials_per_hit=1,
                              other_quals=[req])


if __name__ == '__main__':

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    exp.uploadHTMLs()
    exp.createHIT()

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
