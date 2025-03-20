"""Translate an actual WordPress journey export into a separate observed-test mart."""
import argparse, csv, json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .build import ROOT, FIELDS, calculate, validate_files, write_json, digest

def ingest(path, destination):
    events=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(events,list): raise ValueError('Expected the WordPress event array')
    rows=[]
    for e in events:
        if e.get('provenance')!='observed_test' or e.get('kind') not in {'page_view','cta_click','registration'}: raise ValueError('Invalid observed event')
        if e['kind']=='cta_click': continue
        kind='session' if e['kind']=='page_view' else 'registration'
        rows.append(dict(zip(FIELDS,[e['event_id'],kind,e['campaign_id'],e['market'],e['timestamp'],e['session_id'],'','0' if kind=='session' else '',f"1|landing|{e['device']}" if kind=='session' else '', 'observed_test'])))
    destination=Path(destination); destination.mkdir(parents=True,exist_ok=True)
    staged=destination/'events-v1.csv'
    with staged.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    mappings=json.loads((ROOT/'data/reference/mappings.json').read_text(encoding='utf-8'))
    accepted,rejected,audit=validate_files([staged],mappings,cutoff=datetime.now(timezone.utc)+timedelta(minutes=5),provenance='observed_test')
    dates=[datetime.fromisoformat(r['occurred_at']).date() for r in accepted]
    ps=[dict(id='observed-test',start=str(min(dates)),end=str(max(dates)+timedelta(days=1)))] if dates else []
    metrics=calculate(accepted,ps) if ps else []
    for metric in metrics:
        # The journey collector does not measure dwell time, email or attendance.
        # A schema placeholder must never become a claimed observed measurement.
        for key in ['engagement_rate','engaged','email_click_rate','attendance_rate','delivered','clicked','registrants','attendees','unmatched_attendees']:
            metric[key]=None
    result=dict(provenance='observed_test',available_metrics=['registration_rate'],input_sha256=digest(Path(path).read_bytes()),metrics=metrics,rejected=rejected,audit=audit)
    write_json(destination/'observed-metrics.json',result); return result

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('file'); p.add_argument('--output',default=str(ROOT/'runtime/observed')); args=p.parse_args()
    print(json.dumps(ingest(args.file,args.output),indent=2))
