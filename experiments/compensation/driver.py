import math
import numpy as np

from mturkutils.base import Experiment

userid = 'A1378TVZLWPT2Z'
class CompensationExperiment(Experiment):
    def createTrials(self):
        self._trials = {'acceptID': [userid]}

from boto.mturk.qualification import Requirement


from boto.mturk.connection import MTurkConnection
conn = MTurkConnection(aws_access_key_id="AKIAI7LNZISMTBL77M3Q", aws_secret_access_key="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")


name = "New Sketchloop Special Compensation %s 4" % userid
description = name


qual_type = conn.create_qualification_type(name, description, 'Active')
qtypeid = qual_type[0].QualificationTypeId
print(qtypeid)
req = Requirement(qtypeid, 'Exists')
conn.assign_qualification(qtypeid, userid, value=1, send_notification=True)

exp = CompensationExperiment(htmlsrc = 'compensate.html',
                              htmldst = 'compensate_n%04d.html',
                              sandbox = False,
                              title = 'Special Compensation for %s, Again 2' % userid,
                              reward = 0,
                              duration = 3500,
                              description = "***Compensation for invited workers only***",
                              comment = "compensation, reimbursement",
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
