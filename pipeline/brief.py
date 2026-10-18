"""Optional local Gemini generation. Never exposes a live endpoint in the demo."""
import argparse, json, os, re, urllib.request, uuid
from datetime import datetime, timezone
from .build import ROOT, REGISTRY, digest, write_json

PROMPT_VERSION='brief-v1'
def validate(draft):
    if set(draft)!={'headline','observations','actions'}: raise ValueError('Unexpected brief fields')
    if not isinstance(draft['headline'],str) or not 1<=len(draft['headline'])<=180:raise ValueError('Invalid headline')
    if not isinstance(draft['observations'],list) or not 1<=len(draft['observations'])<=4:raise ValueError('Invalid observations')
    for o in draft['observations']:
        if set(o)!={'metric_id','interpretation'} or o['metric_id'] not in REGISTRY or not isinstance(o['interpretation'],str) or len(o['interpretation'])>600:raise ValueError('Unknown metric reference')
    if not isinstance(draft['actions'],list) or not 1<=len(draft['actions'])<=4 or any(not isinstance(a,str) or not a or len(a)>500 for a in draft['actions']):raise ValueError('Invalid actions')
    # The application, rather than the model, renders numbers from verified facts.
    if re.search(r'\d|%',json.dumps(draft)):raise ValueError('Draft contains model-written numbers')
    return draft

def generate(campaign='all',market='all',period='all'):
    key=os.environ.get('GEMINI_API_KEY');model=os.environ.get('GEMINI_MODEL','gemini-3.5-flash-lite')
    if not key:raise ValueError('Set GEMINI_API_KEY in your local environment. The regular reports need no API key.')
    data=json.loads((ROOT/'public/data/dashboard.json').read_text(encoding='utf-8'));scope=dict(campaign=campaign,market=market,period=period)
    metric=next((m for m in data['metrics'] if all(m[k]==v for k,v in scope.items())),None)
    if metric is None:raise ValueError('No populated snapshot for that scope')
    facts=dict(scope=scope,provenance='synthetic',metrics={k:dict(value=metric[k],numerator=metric[v['numerator']],denominator=metric[v['denominator']],definition=v['definition']) for k,v in REGISTRY.items()},issues=[i for i in data['issues'] if campaign=='all' or i['campaign'] in {'all',campaign}])
    prompt='Write a cautious operational analyst draft for a synthetic portfolio demo. Use only the supplied facts. Do not claim causality, real business lift or clinical advice. Never write digits, percentages or numerical words as measurements; the app renders the facts. Reference metric IDs. Mention quality limitations and propose review actions. Return JSON: {headline:string,observations:[{metric_id:one of the supplied metric IDs,interpretation:string}],actions:[string]}. Facts: '+json.dumps(facts)
    payload=dict(contents=[dict(parts=[dict(text=prompt)])],generationConfig=dict(responseMimeType='application/json',temperature=.2))
    request=urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','x-goog-api-key':key},method='POST')
    with urllib.request.urlopen(request,timeout=90) as response: raw=json.load(response);provider_status=response.status
    text=''.join(p.get('text','') for p in raw['candidates'][0]['content']['parts']);draft=validate(json.loads(text))
    receipt=dict(run_id=str(uuid.uuid4()),created_at=datetime.now(timezone.utc).isoformat(),status='validated',provider='Google Gemini',provider_status=provider_status,model=model,prompt_version=PROMPT_VERSION,prompt_sha256=digest(prompt.encode()),facts_sha256=digest(json.dumps(facts,sort_keys=True).encode()),data_hash=data['manifest']['data_hash'],scope=scope,draft=draft,provider_response=raw)
    receipts=ROOT/'public/data/brief-receipts';write_json(receipts/f"{receipt['run_id']}.json",receipt)
    path=ROOT/'public/data/briefs.json';items=json.loads(path.read_text(encoding='utf-8')) if path.exists() else [];items=[b for b in items if b['scope']!=scope];items.append({k:v for k,v in receipt.items() if k!='provider_response'});write_json(path,items)
    print(json.dumps({k:receipt[k] for k in ['run_id','model','status','data_hash','scope']},indent=2));return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--campaign',default='all');p.add_argument('--market',default='all');p.add_argument('--period',default='all');a=p.parse_args();generate(a.campaign,a.market,a.period)
