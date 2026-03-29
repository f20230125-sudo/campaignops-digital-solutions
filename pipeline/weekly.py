"""Produce scoped weekly PDF summaries from the verified SQL artifact."""
import json
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
def build_weekly():
    data=json.loads((ROOT/'public/data/dashboard.json').read_text(encoding='utf-8'))
    periods={p['id']:p for p in data['periods']};out=ROOT/'public/downloads/weekly';out.mkdir(parents=True,exist_ok=True);index=[]
    for row in data['metrics']:
        if row['campaign']!='all' or row['market']!='all' or not row['period'].startswith('week-'):continue
        period=periods[row['period']];doc=pymupdf.open();page=doc.new_page(width=595,height=842)
        def text(y,s,size=11):page.insert_text((44,y),s,fontsize=size,color=(.09,.22,.16))
        text(55,'CAMPAIGNOPS / WEEKLY OPERATIONS REPORT',17);text(88,period['label'],14)
        text(112,f"{period['start']} to {period['end']} | Asia/Dubai | All campaigns and markets",10)
        text(147,'Synthetic demonstration activity. No real audience or commercial results.',10)
        y=196
        for key,m in data['registry'].items():
            value='Undefined (zero denominator)' if row[key] is None else f"{row[key]:.1%}"
            text(y,m['label']+': '+value,14);y+=24;text(y,f"Numerator: {row[m['numerator']]} | Denominator: {row[m['denominator']]}",10);y+=39
        text(485,'Input quality flags apply to the full snapshot, not just this week.',10)
        text(509,'Unmapped tags and conflicting event IDs are quarantined; duplicate files skipped.',10)
        text(550,'Cutoff: '+data['manifest']['cutoff'],10)
        text(575,'Calculation version: '+data['manifest']['version'],10)
        text(612,'Input fingerprint: '+data['manifest']['data_hash'],8)
        name=row['period']+'.pdf';doc.save(out/name);doc.close();index.append(dict(period=row['period'],label=period['label'],file='/downloads/weekly/'+name,data_hash=data['manifest']['data_hash']))
    (ROOT/'public/data/weekly-reports.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8');return index
if __name__=='__main__':print(f'Built {len(build_weekly())} weekly PDF reports.')
