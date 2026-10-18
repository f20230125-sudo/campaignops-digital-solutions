import csv, json, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
from pipeline.generate import FIELDS
from pipeline.build import calculate, validate_files
from pipeline.observed import ingest

def event(i,kind,entity,value=0,flag='',time='2026-04-07T12:00:00+00:00',parent=''):
    return dict(event_id=i,kind=kind,campaign='health',campaign_raw='health',market='AE',occurred_at=time,entity_id=entity,parent_id=parent,value=value,flag=flag,provenance='synthetic',source_file='oracle.csv',source_line=2)

class MetricOracles(unittest.TestCase):
    def test_message_clicks_sessions_and_rejoins(self):
        records=[event('d1','delivered','m1'),event('d2','delivered','m2'),event('c1','click','m1',flag='human'),event('c2','click','m1',flag='human'),event('c3','click','m2',flag='bot'),event('s1','session','s1',10,'1|landing|mobile'),event('s2','session','s2',11,'1|landing|desktop'),event('s3','session','s3',2,'2|landing|mobile'),event('r1','registration','s1'),event('r2','registration','s1'),event('orphan','registration','missing'),event('w1','webinar_registration','p1',parent='w'),event('w2','webinar_registration','p2',parent='w'),event('a1','attendance','p1',120,'attendee',parent='w'),event('a2','attendance','p1',90,'attendee',parent='w'),event('a3','attendance','p2',60,'presenter',parent='w'),event('a4','attendance','p3',60,'attendee',parent='w')]
        rows=calculate(records,[dict(id='all',start='2026-04-01',end='2026-04-30')])
        total=next(r for r in rows if r['campaign']==r['market']=='all')
        self.assertEqual((total['delivered'],total['clicked'],total['sessions'],total['engaged'],total['registrations'],total['registrants'],total['attendees'],total['unmatched_attendees']),(2,1,3,3,1,2,1,1))
        self.assertEqual(total['email_click_rate'],.5); self.assertEqual(total['registration_rate'],1/3);self.assertEqual(total['attendance_rate'],.5)
    def test_dubai_boundary_and_zero_denominator(self):
        rows=calculate([event('s','session','s',10,'1|landing|mobile','2026-04-06T21:30:00+00:00')],[dict(id='day',start='2026-04-07',end='2026-04-07')])
        row=next(r for r in rows if r['campaign']==r['market']=='all');self.assertEqual(row['sessions'],1);self.assertEqual(row['engagement_rate'],0);self.assertIsNone(row['email_click_rate'])
    def test_distincts_are_not_summed_across_days(self):
        records=[event('a','delivered','same',time='2026-04-06T12:00:00+00:00'),event('b','delivered','same',time='2026-04-07T12:00:00+00:00')]
        total=next(r for r in calculate(records,[dict(id='all',start='2026-04-01',end='2026-04-30')]) if r['campaign']==r['market']=='all');self.assertEqual(total['delivered'],1)

class ImportOracles(unittest.TestCase):
    def write(self,path,rows):
        with path.open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
    def raw(self,**overrides):
        return dict(dict(zip(FIELDS,['e1','session','health','AE','2026-04-07T12:00:00+00:00','s1','','10','1|landing|mobile','synthetic'])),**overrides)
    def test_identical_file_and_event_reimports_are_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.csv';b=Path(d)/'b.csv';c=Path(d)/'c.csv';self.write(a,[self.raw()]);b.write_bytes(a.read_bytes());self.write(c,[self.raw(),self.raw(event_id='e2')])
            accepted,rejected,audit=validate_files([a,b,c],{'health':'health'});self.assertEqual(len(accepted),2);self.assertFalse(rejected);self.assertTrue(audit['imports'][1]['duplicate']);self.assertEqual(audit['duplicate_events'],1)
    def test_conflict_quarantines_both_payloads(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';self.write(p,[self.raw(),self.raw(value='12')]);a,r,_=validate_files([p],{'health':'health'});self.assertFalse(a);self.assertEqual([x['reason'] for x in r],['conflicting_event_id']*2)
    def test_mapping_preserves_raw_and_naive_time_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';self.write(p,[self.raw(campaign_raw='Health'),self.raw(event_id='naive',timestamp='2026-04-07T12:00:00')]);a,r,_=validate_files([p],{'Health':'health','health':'health'});self.assertEqual(a[0]['campaign_raw'],'Health');self.assertEqual(a[0]['campaign'],'health');self.assertEqual(r[0]['reason'],'invalid_timestamp')
    def test_observed_history_stays_separate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.json';e=dict(event_id='abcdefgh',kind='page_view',session_id='session-123',campaign_id='health',market='AE',device='mobile',timestamp=datetime.now(timezone.utc).isoformat(),provenance='observed_test');p.write_text(json.dumps([e,dict(e,event_id='register-123',kind='registration')]))
            result=ingest(p,Path(d)/'out');self.assertEqual(result['provenance'],'observed_test');self.assertFalse(result['rejected']);self.assertEqual(result['metrics'][0]['registration_rate'],1);self.assertIsNone(result['metrics'][0]['engagement_rate']);self.assertEqual(result['available_metrics'],['registration_rate'])

if __name__=='__main__':unittest.main()
