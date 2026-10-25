"""Executable deterministic research-stage orchestration; not autonomous LLM agents."""
import pathlib,json,datetime,argparse
from analysis_engine import build_report,ROOT
from research_governance import assess_claim
STAGES=['source_integrity','coverage_audit','descriptive_analysis','hypothesis_generation','causal_identification','independent_replication','novelty_review','policy_translation','adversarial_review']
def run(input_dir,output_dir):
    out=pathlib.Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    quality=build_report(input_dir,out/'quality_report.json')
    status={s:{'status':'not_run','reason':'Requires external data, research specification, or independent model execution'} for s in STAGES}
    status['source_integrity']={'status':'completed','invalid_rows':len(quality['invalid_rows']),'duplicates':len(quality['duplicate_keys'])}
    status['coverage_audit']={'status':'completed','series':len(quality['coverage'])}
    status['descriptive_analysis']={'status':'completed' if quality['observations'] else 'no_data','note':'Never causal'}
    result={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stages':status,'observations':quality['observations'],'autonomous_agents_running':False}
    (out/'workflow_status.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',default=str(ROOT/'data'/'multi_source'));p.add_argument('--output',default=str(ROOT/'outputs'));a=p.parse_args();print(json.dumps(run(a.input,a.output),indent=2))
