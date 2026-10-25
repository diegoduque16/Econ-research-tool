"""Research governance: pre-registration, evidence ledger, falsification gates."""
import json, pathlib, datetime, hashlib, argparse
ROOT=pathlib.Path(__file__).resolve().parent
REQUIRED=['hypothesis','treatment','outcome','population','period','identification','confounders','placebo_tests','sensitivity_tests','data_sources']

def preregister(spec,path):
    missing=[k for k in REQUIRED if not spec.get(k)]
    if missing:raise ValueError('Missing pre-registration fields: '+', '.join(missing))
    path=pathlib.Path(path)
    if path.exists():raise FileExistsError('Pre-registration is immutable; create a new version')
    payload={'registered_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'specification':spec}
    payload['sha256']=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(payload,indent=2))
    return payload

def assess_claim(claim):
    required=['statement','source_urls','data_hashes','method','uncertainty','limitations','replication_status','novelty_search_status']
    missing=[k for k in required if not claim.get(k)]
    if missing:return {'publishable':False,'reason':'Missing: '+', '.join(missing)}
    if claim.get('causal') and (claim['replication_status']!='independent_passed' or not claim.get('identification_validated')):
        return {'publishable':False,'reason':'Causal claim lacks validated identification and independent replication'}
    if claim.get('novel') and claim['novelty_search_status']!='full_review_completed':
        return {'publishable':False,'reason':'Novelty requires comprehensive prior-art review'}
    return {'publishable':True,'reason':'Metadata gate passed; human expert review still required'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--claim-json',required=True);a=p.parse_args();print(json.dumps(assess_claim(json.loads(pathlib.Path(a.claim_json).read_text())),indent=2))
