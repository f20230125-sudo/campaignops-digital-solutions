import unittest
from pipeline.brief import validate
class BriefValidation(unittest.TestCase):
    def test_unknown_metric_and_written_numbers_rejected(self):
        draft=dict(headline='Review tracking first',observations=[dict(metric_id='made_up',interpretation='Investigate the tag mapping.')],actions=['Check the mobile journey.'])
        with self.assertRaises(ValueError):validate(draft)
        draft['observations'][0]['metric_id']='registration_rate';draft['observations'][0]['interpretation']='Rate increased by 20%.'
        with self.assertRaises(ValueError):validate(draft)
    def test_bounded_draft_validates(self):
        self.assertTrue(validate(dict(headline='Review tracking first',observations=[dict(metric_id='registration_rate',interpretation='Unmapped tags limit interpretation.')],actions=['Check the mobile journey.'])))
