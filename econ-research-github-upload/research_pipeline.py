"""Offline deterministic demonstration. Synthetic outputs must never be presented as empirical findings."""
import argparse,json,pathlib
import numpy as np,pandas as pd
from causal_engine import estimate_horizons,future_shock_placebo
from policy_events import load_events
from evidence_gate import classify
ROOT=pathlib.Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--demo',action='store_true');p.add_argument('--input');p.add_argument('--output',default='outputs/v06_analysis.json');a=p.parse_args()
 if not a.demo and not a.input:p.error('Supply --input validated data CSV or --demo for synthetic tests')
 events=load_events(ROOT/'data/policy_event_sources.csv')
 if a.demo:
  rng=np.random.default_rng(1234);n=180;shock=rng.normal(size=n);y=np.zeros(n)
  for i in range(1,n):y[i]=.6*y[i-1]+.45*shock[i]+rng.normal(scale=.5)
  df=pd.DataFrame({'period':np.arange(n),'outcome':y,'shock':shock});source='SYNTHETIC_NOT_EMPIRICAL'
 else:
  df=pd.read_csv(a.input);source=str(a.input)
 estimates=estimate_horizons(df)
 placebo=future_shock_placebo(df)
 out={'source':source,'synthetic':a.demo,'policy_source_records':len(events),'results':estimates,'future_shock_placebo':placebo,'evidence_gate':classify(estimates[0]),'status':'exploratory_only','warning':'No verified real-world policy shock has been ingested; no policy recommendation or causal conclusion authorized.'}
 path=ROOT/a.output;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(out,indent=2));print(json.dumps({'output':str(path),'status':out['status'],'synthetic':a.demo,'horizons':len(estimates)}))
if __name__=='__main__':main()
