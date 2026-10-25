#!/usr/bin/env python3
"""Transparent, dependency-free research pipeline. No fabricated empirical findings."""
import argparse, csv, datetime as dt, hashlib, json, math, pathlib, statistics, urllib.parse, urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'outputs'; DATA=ROOT/'data'
HYPOTHESES={
'H1':{'question':'Do household-demand interventions produce more job-years per fiscal dollar than business tax incentives, conditional on economic slack?','design':'Narrative policy shocks and local projections; pre-trends and placebo timing; inflation-adjusted fiscal costs','outcomes':['employment','hours','real_wages','job_years_per_fiscal_billion'],'confounders':['monetary_policy','recessions','demographics','energy_shocks']},
'H2':{'question':'Does AI adoption weaken the investment-to-employment elasticity?','design':'Firm/industry adoption panel with staggered-treatment diagnostics; avoid naive two-way fixed effects','outcomes':['employment','labor_share','investment','value_added'],'confounders':['industry_demand','offshoring','firm_selection']},
'H3':{'question':'Do skills, competition and digital access moderate AI effects on labor share and wages?','design':'Pre-registered heterogeneous treatment analysis with country and industry holdouts','outcomes':['real_wages','labor_share','productivity'],'confounders':['income_level','education','industry_mix']},
'H4':{'question':'Which fiscal and insurance systems are resilient to declining labor income shares?','design':'Transparent microsimulation and scenario sensitivity, not causal estimates','outcomes':['fiscal_balance','poverty','inequality'],'confounders':['demographics','behavioral_response']},
'H5':{'question':'Do emerging economies experience different employment and productivity responses to AI exposure?','design':'Comparable country-industry panels with measurement sensitivity and matched controls','outcomes':['employment','productivity','wages'],'confounders':['internet_access','informality','structural_change']}}
SOURCES=[('OpenAlex','https://api.openalex.org/works','literature','metadata; not full text'),('World Bank WDI','https://api.worldbank.org/v2/','macro','indicator availability varies'),('ILOSTAT','https://ilostat.ilo.org/data/','labor','definitions and informality differ'),('OECD','https://sdmx.oecd.org/','macro','coverage concentrates on richer countries'),('IMF','https://www.imf.org/en/Data','fiscal','revisions and fiscal definitions'),('FRED','https://fred.stlouisfed.org/','us','series revisions'),('BLS','https://www.bls.gov/data/','us','payroll vs household surveys'),('Penn World Table','https://www.rug.nl/ggdc/productivity/pwt/','productivity','PPP measurement uncertainty')]
WDI={'employment_ratio':'SL.EMP.TOTL.SP.ZS','unemployment':'SL.UEM.TOTL.ZS','gdp_per_capita_constant':'NY.GDP.PCAP.KD','gdp_growth':'NY.GDP.MKTP.KD.ZG','gini':'SI.POV.GINI','tax_revenue_gdp':'GC.TAX.TOTL.GD.ZS','internet_users':'IT.NET.USER.ZS','gross_capital_formation_gdp':'NE.GDI.TOTL.ZS'}
COUNTRIES=['USA','CAN','GBR','DEU','FRA','JPN','KOR','AUS','SWE','DNK','ZAF','NGA','KEN','GHA','RWA','ETH','IND','BRA','IDN','MEX']
def get_json(url):
    req=urllib.request.Request(url,headers={'User-Agent':'EconomicPolicyAIResearch/0.2 (transparent academic prototype)'})
    with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
def openalex(query,limit):
    url='https://api.openalex.org/works?'+urllib.parse.urlencode({'search':query,'per-page':limit,'sort':'relevance_score:desc'})
    obj=get_json(url)
    return [{'id':w.get('id'),'title':w.get('title'),'year':w.get('publication_year'),'doi':w.get('doi'),'citations':w.get('cited_by_count'),'url':(w.get('primary_location') or {}).get('landing_page_url'),'abstract_status':'not reviewed'} for w in obj.get('results',[])]
def worldbank(indicator,countries):
    url='https://api.worldbank.org/v2/country/'+ ';'.join(countries)+'/indicator/'+indicator+'?format=json&per_page=20000&date=1990:2025'
    pages=get_json(url)
    if not isinstance(pages,list) or len(pages)<2:raise ValueError('Unexpected World Bank response')
    if pages[0].get('pages',1)>1:raise ValueError('Incomplete pagination; narrow request')
    return [{'country':r['countryiso3code'],'year':int(r['date']),'value':r['value'],'indicator':indicator,'source':'World Bank WDI'} for r in pages[1] if r.get('value') is not None and r.get('countryiso3code')]
def write_csv(path,rows,fields):
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def profile(rows):
    out=[]
    for name,code in WDI.items():
        a=[r for r in rows if r['indicator']==code]
        out.append({'indicator':name,'code':code,'observations':len(a),'countries':len(set(r['country'] for r in a)),'first_year':min((r['year'] for r in a),default=None),'last_year':max((r['year'] for r in a),default=None)})
    return out
def descriptive(rows):
    """Descriptive paired associations only. NEVER label as causal."""
    index={(r['country'],r['year'],r['indicator']):r['value'] for r in rows}
    out=[]
    for label in ['gdp_growth','internet_users','gross_capital_formation_gdp','tax_revenue_gdp']:
        pairs=[]
        for c in COUNTRIES:
            for y in range(1990,2026):
                x=index.get((c,y,WDI[label])); z=index.get((c,y,WDI['employment_ratio']))
                if isinstance(x,(int,float)) and isinstance(z,(int,float)):pairs.append((x,z))
        if len(pairs)>=10:
            xs,ys=zip(*pairs)
            if statistics.pstdev(xs)>0 and statistics.pstdev(ys)>0:
                corr=statistics.correlation(xs,ys)
                out.append({'variable':label,'outcome':'employment_ratio','pairs':len(pairs),'pooled_correlation':round(corr,4),'interpretation':'DESCRIPTIVE ONLY: pooled country-year correlation; confounded by trends, country effects and simultaneity'})
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');p.add_argument('--max-papers',type=int,default=6);p.add_argument('--refresh-data',action='store_true',help='Download selected World Bank WDI series');p.add_argument('--analyze',action='store_true',help='Profile local WDI data and report descriptive associations');a=p.parse_args()
    OUT.mkdir(exist_ok=True);DATA.mkdir(exist_ok=True)
    timestamp=dt.datetime.now(dt.timezone.utc).isoformat();errors=[];literature={}
    for key,h in HYPOTHESES.items():
        literature[key]=[]
        if not a.offline:
            try:literature[key]=openalex(h['question'],a.max_papers)
            except Exception as e:errors.append({'stage':'literature','hypothesis':key,'error':str(e)})
    raw=DATA/'wdi_observations.csv';data_status='not downloaded';rows=[]
    if a.refresh_data and not a.offline:
        for name,code in WDI.items():
            try:rows.extend(worldbank(code,COUNTRIES))
            except Exception as e:errors.append({'stage':'worldbank','indicator':name,'error':str(e)})
        if rows:write_csv(raw,rows,['country','year','value','indicator','source']);data_status='downloaded (check indicator errors)'
    if a.analyze and raw.exists():
        with raw.open(newline='',encoding='utf8') as f:
            rows=[{'country':r['country'],'year':int(r['year']),'value':float(r['value']),'indicator':r['indicator'],'source':r['source']} for r in csv.DictReader(f)]
        data_status='loaded local dataset'
    profiles=profile(rows) if rows else []
    associations=descriptive(rows) if rows and a.analyze else []
    manifest={'generated_utc':timestamp,'version':'0.2','offline':a.offline,'data_status':data_status,'raw_data_sha256':hashlib.sha256(raw.read_bytes()).hexdigest() if raw.exists() else None,'countries':COUNTRIES,'data_profiles':profiles,'descriptive_associations':associations,'hypotheses':HYPOTHESES,'literature':literature,'errors':errors,'causal_claims':'NONE; no policy shock design implemented','agent_status':'workflow specifications only; no independent LLM agents running'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    write_csv(OUT/'source_registry.csv',[{'name':n,'url':u,'category':c,'limitation':l} for n,u,c,l in SOURCES],['name','url','category','limitation'])
    lines=['# Global Economic Policy and AI Transition — Research Audit v0.2','',f'Generated (UTC): {timestamp}','','**Evidence standard:** literature search is metadata-only; correlations are not causal effects. No novel findings or policy effects are claimed.','','## Research scope','Historical U.S. and high-income comparison; dedicated Africa and emerging-market analysis.','','## Hypotheses and identification plans']
    for k,h in HYPOTHESES.items():
        lines += ['',f'### {k} — {h["question"]}',f'- Design: {h["design"]}',f'- Outcomes: {", ".join(h["outcomes"])}',f'- Major confounders: {", ".join(h["confounders"])}','- Novelty status: unverified; full-text review and citation tracing required.']
        for paper in literature[k]:lines.append(f'- Literature candidate: {paper["title"]} ({paper["year"]}) — {paper["doi"] or paper["id"]}')
    lines+=['','## Data coverage',f'Status: {data_status}']
    for r in profiles:lines.append(f'- {r["indicator"]}: {r["observations"]} country-years, {r["countries"]} countries, {r["first_year"]}–{r["last_year"]}')
    lines+=['','## Descriptive checks — not causal']
    for r in associations:lines.append(f'- {r["variable"]} vs {r["outcome"]}: r={r["pooled_correlation"]}, n={r["pairs"]}. Do not interpret as a policy effect.')
    if not associations:lines.append('- No analysis requested or no usable observations.')
    lines+=['','## Required next steps','1. Build licensed policy-shock and fiscal-cost datasets; specify treatment dates and policy counterfactuals.','2. Preregister outcomes, identification assumptions, treatment lags and placebo tests.','3. Implement difference-in-differences/local projections with uncertainty intervals and sensitivity analysis.','4. Add independent replication, publication-bias controls, country holdouts and a falsification ledger.','5. Add real independent model-backed agents, persistent orchestration and operational monitoring.','','## Errors']
    lines += [f'- {e}' for e in errors] or ['- None']
    (OUT/'audit.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print('Created outputs/audit.md and outputs/manifest.json; data status:',data_status)
if __name__=='__main__':main()
