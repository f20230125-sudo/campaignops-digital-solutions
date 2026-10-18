"""Deterministic, fictional campaign exports. No real audience data."""
import csv, json, random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS = [
    ('health', 'World Health Day', '2026-04-07', 'world-health-day', 'Make reliable health information easier to find.'),
    ('immunization', 'World Immunization Week', '2026-04-24', 'world-immunization-week', 'Prepare clear questions for a conversation about immunization.'),
    ('tobacco', 'World No Tobacco Day', '2026-05-31', 'world-no-tobacco-day', 'Explore public information about tobacco prevention.'),
    ('blood', 'World Blood Donor Day', '2026-06-14', 'world-blood-donor-day', 'Find public resources about blood donation.'),
    ('hepatitis', 'World Hepatitis Day', '2026-07-28', 'world-hepatitis-day', 'Connect with public awareness and prevention resources.'),
    ('safety', 'World Patient Safety Day', '2026-09-17', 'world-patient-safety-day', 'Use clear questions and reliable information to support safer care.'),
]
FIELDS = ['event_id', 'kind', 'campaign_raw', 'market', 'timestamp', 'entity_id', 'parent_id', 'value', 'flag', 'provenance']

def generate():
    out = ROOT/'data/raw'; out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(73129); rows = {'email': [], 'web': [], 'webinar': []}; metadata = []; assets = []
    for ci, (cid, title, date, slug, summary) in enumerate(CAMPAIGNS):
        center = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        metadata.append(dict(id=cid, title=title, date=date, source=f'https://www.who.int/campaigns/{slug}/2026', summary=summary, provenance='public_reference'))
        for typ in ['landing', 'resource']:
            assets.append(dict(asset_id=f'{cid}-{typ}', campaign_id=cid, title=f'{title} · {typ.title()}', status='pending' if cid=='safety' and typ=='resource' else 'publish', owner='Content operations', review_date='2026-10-01', summary=summary, source=metadata[-1]['source'], mobile_ready=cid!='hepatitis', provenance='synthetic'))
        for market in ['AE', 'SA', 'QA']:
            prefix = f'{cid}-{market}'
            def add(channel, kind, n, entity, parent='', value='', flag='', day=0, raw=None):
                if cid=='health': day=max(day,-6)  # Keep the fixture inside the declared April-September window.
                row = dict(zip(FIELDS, [f'{prefix}-{kind}-{n}', kind, raw or cid, market, (center+timedelta(days=day, minutes=int(str(n).split('-')[0])%600 if str(n).split('-')[0].isdigit() else 0)).isoformat(), entity, parent, str(value), flag, 'synthetic']))
                rows[channel].append(row); return row
            for n in range(180):
                message=f'{prefix}-msg-{n}'; day=rng.randint(-10, 6)
                add('email','delivered',n,message,day=day)
                if rng.random()<.18+ci*.012:
                    add('email','click',n,message,flag='human',day=day)
                    if n%7==0: add('email','click',f'{n}-repeat',message,flag='human',day=day)
                if n%23==0: add('email','click',f'{n}-bot',message,flag='bot',day=day)
            for n in range(120):
                session=f'{prefix}-session-{n}'; day=rng.randint(-10,6)
                raw='Hepatitis_2026' if cid=='hepatitis' and n<20 else cid
                duration=rng.randint(1,160); pageviews=2 if n%3==0 else 1
                add('web','session',n,session,value=duration,flag=f'{pageviews}|landing|{"mobile" if n%2==0 else "desktop"}',day=day,raw=raw)
                # Intentional broken mobile CTA: this is a scenario, not observed conversion lift.
                if rng.random()<.23 and not(cid=='hepatitis' and n%2==0):
                    add('web','registration',n,session,day=day,raw=raw)
            for n in range(65):
                person=f'{prefix}-person-{n}'; webinar=f'{cid}-webinar'
                add('webinar','webinar_registration',n,person,parent=webinar)
                if n%4!=0:
                    add('webinar','attendance',n,person,parent=webinar,value=1800,flag='attendee')
                    if n%7==0: add('webinar','attendance',f'{n}-rejoin',person,parent=webinar,value=300,flag='attendee')
            add('webinar','attendance','presenter',f'{prefix}-presenter',parent=f'{cid}-webinar',value=3600,flag='presenter')
    # Exact duplicate export, conflicting event ID, unmapped UTM, invalid timestamp, late arrival.
    for key, data in rows.items():
        with (out/f'{key}.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS); writer.writeheader(); writer.writerows(data)
    defects=[dict(rows['web'][0]), dict(rows['web'][1]), dict(rows['web'][2]), dict(rows['web'][3])]
    defects[0]['value']='999'; defects[1]['event_id']='unmapped-1'; defects[1]['campaign_raw']='unmapped_campaign'
    defects[2]['event_id']='invalid-time'; defects[2]['timestamp']='yesterday'
    defects[3]['event_id']='late-feed'; defects[3]['timestamp']='2026-10-05T12:00:00+00:00'
    with (out/'defects.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS); writer.writeheader(); writer.writerows(defects)
    (out/'webinar-reexport.csv').write_bytes((out/'webinar.csv').read_bytes())
    config=ROOT/'data/reference'; config.mkdir(parents=True,exist_ok=True)
    (config/'campaigns.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    (config/'assets.json').write_text(json.dumps(assets,indent=2)+'\n',encoding='utf-8')
    if not (config/'mappings.json').exists():
        (config/'mappings.json').write_text(json.dumps({c[0]:c[0] for c in CAMPAIGNS},indent=2)+'\n',encoding='utf-8')
    print(f'Generated {sum(map(len,rows.values()))} fictional event rows; seed 73129.')

if __name__=='__main__': generate()
