import unittest
import sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hunter import classify,normalize_job

BASE={'company':'Mujin','title':'Intern Analyst','location':'Tokyo, Japan','description':'Strategy, DX, SCM','job_url':'https://jobs.lever.co/example/job','apply_url':'https://jobs.lever.co/example/job/apply','updated':'','date_meaning':'unknown','source':'lever:example','live':True,'commitment':'Internship'}
class HunterTests(unittest.TestCase):
    def test_priority(self):
        row=classify(BASE)
        self.assertEqual(row['review_status'],'priority_manual_review')
        self.assertEqual(row['recency'],'unknown')
    def test_reject_outside_region(self):
        self.assertEqual(classify(dict(BASE,location='Osaka, Japan'))['review_status'],'outside_target_or_unknown_location')
    def test_no_nonintern(self):
        self.assertEqual(classify(dict(BASE,title='Senior Product Manager',commitment='Full-Time'))['review_status'],'other_jobs')
    def test_event(self):
        self.assertEqual(classify(dict(BASE,title='Intern Meetup'))['review_status'],'not_a_job')
    def test_greenhouse_uses_updated_not_published(self):
        src={'provider':'greenhouse','board':'company','company':'Company'}
        job={'title':'Intern Analyst','updated_at':'2026-10-08T00:00:00Z','location':{'name':'Tokyo'},'absolute_url':'https://job-boards.greenhouse.io/company/jobs/1'}
        norm=normalize_job(src,job)
        self.assertEqual(norm['date_meaning'],'last_updated_not_published')
        self.assertEqual(classify(norm,datetime(2026,10,8,tzinfo=timezone.utc))['recency'],'updated_within_30_days')
    def test_nonmatch_location_unknown(self):
        self.assertEqual(classify(dict(BASE,location='Remote'))['review_status'],'outside_target_or_unknown_location')
    def test_apply_status(self):
        self.assertEqual(classify(dict(BASE,apply_url=''))['apply_url_status'],'job_detail_only_verify_apply_button')
if __name__=='__main__':unittest.main()
