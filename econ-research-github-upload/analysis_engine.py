"""Dependency-free, auditable panel analysis. Associations are never causal estimates."""
import csv, json, math, hashlib, pathlib, statistics, argparse, datetime
from collections import defaultdict
ROOT=pathlib.Path(__file__).resolve().parent

def read_observations(folder):
    rows=[]; issues=[]
    for path in sorted(pathlib.Path(folder).glob('*.csv')):
        with path.open(newline='',encoding='utf8') as f:
            for i,r in enumerate(csv.DictReader(f),2):
                try:
                    val=float(r['value']); assert math.isfinite(val)
                    assert r['provider'] and r['series'] and r['geo'] and r['period']
                    rows.append({**r,'value':val,'file':path.name,'line':i})
                except (ValueError,AssertionError,KeyError,TypeError):issues.append({'file':path.name,'line':i,'issue':'invalid observation'})
    return rows,issues

def audit(rows):
    groups=defaultdict(list); duplicates=[]; bad_units=[]
    for r in rows:
        groups[(r['provider'],r['series'],r['geo'],r['period'])].append(r)
    for key,items in groups.items():
        if len(items)>1:duplicates.append({'key':key,'count':len(items),'conflicting_values':len(set(r['value'] for r in items))>1})
    coverage=[]
    for (provider,series), items in sorted(_group(rows,lambda r:(r['provider'],r['series'])).items()):
        coverage.append({'provider':provider,'series':series,'observations':len(items),'countries':len(set(r['geo'] for r in items)),'first_period':min(r['period'] for r in items),'last_period':max(r['period'] for r in items),'units':sorted(set(r['unit'] for r in items))})
    return {'observations':len(rows),'duplicate_keys':duplicates,'coverage':coverage,'warnings':['Do not combine differently defined series or units without documented harmonization.']}

def _group(rows,key):
    d=defaultdict(list)
    for r in rows:d[key(r)].append(r)
    return d

def within_country_association(rows, provider, xseries, yseries, min_pairs=12):
    """Country demeaned association; still confounded and NOT a causal estimate."""
    idx={(r['geo'],r['period'],r['series']):r['value'] for r in rows if r['provider']==provider}
    keys=set((geo,period) for geo,period,series in idx if series in (xseries,yseries))
    pairs=defaultdict(list)
    for geo,period in keys:
        x=idx.get((geo,period,xseries)); y=idx.get((geo,period,yseries))
        if x is not None and y is not None:pairs[geo].append((x,y))
    clean={g:p for g,p in pairs.items() if len(p)>=3}
    demeaned=[]
    for p in clean.values():
        mx=statistics.mean(x for x,y in p);my=statistics.mean(y for x,y in p)
        demeaned.extend((x-mx,y-my) for x,y in p)
    if len(demeaned)<min_pairs:return {'status':'insufficient_data','pairs':len(demeaned),'causal':False}
    xs,ys=zip(*demeaned)
    if statistics.pstdev(xs)==0 or statistics.pstdev(ys)==0:return {'status':'zero_variance','causal':False}
    return {'status':'descriptive_only','pairs':len(xs),'countries':len(clean),'within_country_correlation':round(statistics.correlation(xs,ys),5),'causal':False,'warning':'Country fixed effects alone do not address reverse causation, trends, time effects, omitted shocks or measurement error.'}

def build_report(folder, output, x='government_consumption_gdp', y='employment_to_population'):
    rows,issues=read_observations(folder); report=audit(rows)
    report.update({'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'invalid_rows':issues,'associations':{'world_bank':within_country_association(rows,'world_bank',x,y)},'policy_attribution':'NOT ESTIMATED','research_integrity':'No causal findings, novel discoveries, or AI agent execution claimed'})
    dest=pathlib.Path(output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,indent=2,default=str))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',default=str(ROOT/'data'/'multi_source'));p.add_argument('--output',default=str(ROOT/'outputs'/'quality_report.json'));p.add_argument('--x',default='government_consumption_gdp');p.add_argument('--y',default='employment_to_population');a=p.parse_args()
    r=build_report(a.input,a.output,a.x,a.y);print(json.dumps({'observations':r['observations'],'duplicates':len(r['duplicate_keys']),'association':r['associations']},indent=2))
