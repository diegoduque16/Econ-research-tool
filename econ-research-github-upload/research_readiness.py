"""Honest capability/readiness report, based on evidence on disk."""
import json,pathlib,datetime
from panel_integrity import audit_folder
ROOT=pathlib.Path(__file__).resolve().parent

def report(root=ROOT):
    root=pathlib.Path(root); data=root/'data'/'multi_source'
    files=audit_folder(data) if data.exists() else {}
    manifest=data/'ingestion_manifest.json'; ing=json.loads(manifest.read_text()) if manifest.exists() else {}
    sources=ing.get('sources',{})
    retrieved=[k for k,v in sources.items() if v.get('status')=='retrieved']
    validated=[name for name,result in files.items() if not result['errors'] and result['valid_rows']>0]
    return {'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'data_files':len(files),'validated_nonempty_files':validated,'retrieved_sources_reported':retrieved,'live_retrieval_verified_this_run':False,'causal_findings':0,'autonomous_llm_agents_running':False,'capabilities':{'source_registry':'available','strict_panel_validation':'available','did_preanalysis_diagnostic':'available_not_causal','policy_shock_database':'not_implemented','causal_inference_with_uncertainty':'not_implemented','independent_replication':'not_implemented','novelty_verification':'not_implemented','production_scheduler':'not_implemented'}}
if __name__=='__main__':
    p=ROOT/'outputs'/'readiness.json';p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(report(),indent=2));print(p)
