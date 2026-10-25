#!/usr/bin/env python3
"""Auditable multi-provider economic data ingestion. No silently fabricated values."""
import argparse, csv, datetime, hashlib, json, os, pathlib, time, urllib.parse, urllib.request, urllib.error
ROOT=pathlib.Path(__file__).resolve().parent
REGISTRY={
 'world_bank':{'access':'open','format':'World Bank JSON','endpoint':'https://api.worldbank.org/v2/','status':'implemented','coverage':'Global WDI, national annual'},
 'fred':{'access':'api_key','format':'FRED JSON','endpoint':'https://api.stlouisfed.org/fred/series/observations','status':'implemented','coverage':'US and international economic series'},
 'bls':{'access':'open_limited','format':'BLS JSON','endpoint':'https://api.bls.gov/publicAPI/v2/timeseries/data/','status':'implemented','coverage':'US labor, payroll, CPI'},
 'eurostat':{'access':'open','format':'JSON-stat','endpoint':'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/','status':'implemented','coverage':'European employment and economy'},
 'oecd':{'access':'open','format':'SDMX-CSV','endpoint':'https://sdmx.oecd.org/public/rest/v1/data/','status':'generic_sdmx_connector','coverage':'OECD and partner countries; dataset flow/key required'},
 'imf':{'access':'open_or_portal','format':'SDMX-CSV','endpoint':'https://api.imf.org/external/sdmx/3.0/','status':'generic_sdmx_connector_unverified','coverage':'IMF macro, fiscal and financial series; verify dataset URLs'},
 'ilostat':{'access':'open','format':'SDMX-CSV','endpoint':'https://sdmx.ilo.org/rest/v1/data/','status':'generic_sdmx_connector_unverified','coverage':'International labor and wages; verify endpoint'},
 'un_sdg':{'access':'open','format':'SDMX-CSV','endpoint':'https://unstats.un.org/SDGAPI/v1/sdg/','status':'catalog_only','coverage':'SDG indicators'},
 'world_bank_data360':{'access':'open','format':'JSON','endpoint':'https://data360api.worldbank.org/','status':'catalog_only','coverage':'Additional World Bank sources'},
 'penn_world_table':{'access':'download','format':'Excel','endpoint':'https://www.rug.nl/ggdc/productivity/pwt/','status':'manual_download','coverage':'PPP, productivity, capital'},
 'wiid':{'access':'download','format':'CSV/Excel','endpoint':'https://www.wider.unu.edu/database/world-income-inequality-database-wiid','status':'manual_download','coverage':'Income inequality'},
 'wid':{'access':'review_terms','format':'API/CSV','endpoint':'https://wid.world/data/','status':'catalog_only','coverage':'Income and wealth distribution'},
 'comtrade':{'access':'api_limits','format':'JSON','endpoint':'https://comtradeapi.un.org/public/v1/preview/C/A/','status':'catalog_only','coverage':'International trade'},
 'bis':{'access':'open','format':'SDMX-CSV','endpoint':'https://stats.bis.org/api/v1/','status':'generic_sdmx_connector_unverified','coverage':'Credit, financial stability'},
 'ai_index':{'access':'download','format':'CSV','endpoint':'https://hai.stanford.edu/ai-index','status':'manual_download','coverage':'AI adoption and investment'},
 'openalex':{'access':'open','format':'JSON','endpoint':'https://api.openalex.org/works','status':'literature_in_research_py','coverage':'Published research metadata'},
}
WDI={'employment_to_population':'SL.EMP.TOTL.SP.ZS','unemployment_rate':'SL.UEM.TOTL.ZS','gdp_growth':'NY.GDP.MKTP.KD.ZG','gdp_per_capita_real':'NY.GDP.PCAP.KD','gdp_real':'NY.GDP.MKTP.KD','gini':'SI.POV.GINI','tax_revenue_gdp':'GC.TAX.TOTL.GD.ZS','investment_gdp':'NE.GDI.TOTL.ZS','household_consumption_gdp':'NE.CON.PRVT.ZS','government_consumption_gdp':'NE.CON.GOVT.ZS','trade_gdp':'NE.TRD.GNFS.ZS','internet_users':'IT.NET.USER.ZS','population':'SP.POP.TOTL','labor_force':'SL.TLF.TOTL.IN','manufacturing_value_added_gdp':'NV.IND.MANF.ZS','labor_productivity_growth':'SL.GDP.PCAP.EM.KD.ZG'}
FRED={'PAYEMS':'all_employees_nonfarm','USPRIV':'private_payroll','UNRATE':'unemployment','CPIAUCSL':'cpi','GDPC1':'real_gdp','A191RL1Q225SBEA':'real_gdp_growth','PCECC96':'real_consumption','GPDIC1':'real_investment','OPHNFB':'nonfarm_productivity','PRS85006173':'nonfarm_labor_share'}
BLS={'CES0000000001':'nonfarm_payroll_thousands','CES0500000001':'private_payroll_thousands','LNS14000000':'unemployment_percent'}
EUROSTAT={'une_rt_a':'annual_unemployment','nama_10_gdp':'national_accounts_gdp'}
def fetch(url, method='GET', body=None, headers=None, retries=2):
 req=urllib.request.Request(url,data=body,method=method,headers={'User-Agent':'EconomicAIResearch/0.3 (research contact: configure locally)',**(headers or {})})
 for attempt in range(retries+1):
  try:
   with urllib.request.urlopen(req,timeout=35) as r:return r.read(),dict(r.headers)
  except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError):
   if attempt==retries:raise
   time.sleep(attempt+1)
def get_json(url,**kw):return json.loads(fetch(url,**kw)[0])
def record(provider,series,geo,period,value,unit='',frequency='',metadata=None):
 return {'provider':provider,'series':series,'geo':geo,'period':str(period),'value':value,'unit':unit,'frequency':frequency,'metadata':json.dumps(metadata or {},sort_keys=True)}
def world_bank(countries,start,end):
 out=[]
 for name,indicator in WDI.items():
  page=1
  while True:
   url=f'https://api.worldbank.org/v2/country/{";".join(countries)}/indicator/{indicator}?'+urllib.parse.urlencode({'format':'json','date':f'{start}:{end}','per_page':20000,'page':page})
   obj=get_json(url)
   if not isinstance(obj,list) or len(obj)<2:raise ValueError(f'Invalid WDI response {indicator}')
   for x in obj[1] or []:
    if x.get('value') is not None and x.get('countryiso3code'):
     out.append(record('world_bank',name,x['countryiso3code'],x['date'],x['value'],frequency='A',metadata={'original_series':indicator,'source':(x.get('indicator') or {}).get('value')}))
   if page>=int(obj[0].get('pages',1)):break
   page+=1
 return out
def fred(start,end):
 key=os.getenv('FRED_API_KEY')
 if not key:raise RuntimeError('FRED_API_KEY required; no key stored in project')
 out=[]
 for sid,name in FRED.items():
  q=urllib.parse.urlencode({'series_id':sid,'api_key':key,'file_type':'json','observation_start':f'{start}-01-01','observation_end':f'{end}-12-31'})
  for x in get_json('https://api.stlouisfed.org/fred/series/observations?'+q).get('observations',[]):
   if x['value']!='.':out.append(record('fred',name,'USA',x['date'],float(x['value']),metadata={'original_series':sid,'realtime_start':x.get('realtime_start'),'realtime_end':x.get('realtime_end')}))
 return out
def bls(start,end):
 out=[]
 for lo in range(start,end+1,10):
  payload=json.dumps({'seriesid':list(BLS),'startyear':str(lo),'endyear':str(min(end,lo+9))}).encode()
  obj=get_json(REGISTRY['bls']['endpoint'],method='POST',body=payload,headers={'Content-Type':'application/json'})
  if obj.get('status')!='REQUEST_SUCCEEDED':raise RuntimeError(f'BLS API response: {obj.get("message")}')
  for s in obj['Results']['series']:
   for x in s['data']:
    if x['period'].startswith('M') and x['period']!='M13':out.append(record('bls',BLS[s['seriesID']],'USA',f'{x["year"]}-{x["period"][1:]}',float(x['value'].replace(',','')),frequency='M',metadata={'original_series':s['seriesID']}))
 return out
def jsonstat_rows(obj,dataset_id):
 ids=obj.get('id',[]); sizes=obj.get('size',[]);dims=obj.get('dimension',{});values=obj.get('value',{})
 if not ids or not sizes:raise ValueError('Unexpected JSON-stat dimensions')
 if len(values)>250000:raise ValueError('Dataset too large: add query filters')
 cats=[]
 for k in ids:
  idx=dims[k]['category']['index']; cats.append(list(idx) if isinstance(idx,dict) else [str(i) for i in range(len(idx))])
 out=[]
 for offset,v in (values.items() if isinstance(values,dict) else enumerate(values)):
  if v is None:continue
  n=int(offset); coords={}
  for k,size,labels in reversed(list(zip(ids,sizes,cats))):coords[k]=labels[n%size];n//=size
  geo=coords.get('geo','');period=coords.get('time','')
  if geo and period:out.append(record('eurostat',dataset_id,geo,period,v,frequency='A' if len(period)==4 else '',metadata={'dimensions':coords}))
 return out
def eurostat():
 out=[]
 for dataset in EUROSTAT:
  obj=get_json(REGISTRY['eurostat']['endpoint']+dataset+'?'+urllib.parse.urlencode({'lang':'EN','sinceTimePeriod':'2000'}))
  out.extend(jsonstat_rows(obj,dataset))
 return out
def sdmx_csv(provider,url):
 import io
 raw,headers=fetch(url,headers={'Accept':'csvfile, text/csv, application/vnd.sdmx.csv;version=2'})
 rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
 if not rows:raise ValueError('No SDMX CSV records')
 out=[]
 for x in rows:
  val=x.get('OBS_VALUE') or x.get('obs_value')
  if val in ('',None):continue
  try:val=float(val)
  except ValueError:continue
  out.append(record(provider,x.get('SERIES_KEY') or x.get('INDICATOR') or x.get('MEASURE') or 'sdmx_observation',x.get('REF_AREA') or x.get('LOCATION') or x.get('GEO') or '',x.get('TIME_PERIOD') or x.get('TIME') or '',val,metadata={'sdmx_dimensions':{k:v for k,v in x.items() if k not in ('OBS_VALUE','obs_value')}}))
 return out
def run(args):
 dest=ROOT/'data'/'multi_source';dest.mkdir(parents=True,exist_ok=True)
 report={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requested':args.providers,'sources':{},'notes':'No causal claims. Data retrieved from external APIs only when network accessible. Failures never treated as zeros.'}
 for provider in args.providers:
  if provider not in REGISTRY:report['sources'][provider]={'status':'unknown_source'};continue
  info=REGISTRY[provider];result={'access':info['access'],'connector_status':info['status']}
  try:
   if args.offline:result['status']='not_attempted_offline';report['sources'][provider]=result;continue
   if provider=='world_bank':rows=world_bank(args.countries,args.start,args.end)
   elif provider=='fred':rows=fred(args.start,args.end)
   elif provider=='bls':rows=bls(args.start,args.end)
   elif provider=='eurostat':rows=eurostat()
   elif provider in ('oecd','imf','ilostat','bis'):
    url=args.sdmx_url
    if not url or provider!=args.sdmx_provider:raise RuntimeError('Dataset-specific SDMX URL required via --sdmx-provider and --sdmx-url; unverified endpoints not assumed')
    rows=sdmx_csv(provider,url)
   else:result['status']='catalogued_only';report['sources'][provider]=result;continue
   target=dest/(provider+'.csv')
   with target.open('w',newline='',encoding='utf8') as f:
    writer=csv.DictWriter(f,fieldnames=['provider','series','geo','period','value','unit','frequency','metadata']);writer.writeheader();writer.writerows(rows)
   result.update(status='retrieved',observations=len(rows),file=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest())
  except Exception as e:result.update(status='failed',error=str(e))
  report['sources'][provider]=result
 (dest/'ingestion_manifest.json').write_text(json.dumps(report,indent=2))
 return report
def main():
 p=argparse.ArgumentParser(description='Multi-source economic research ingestion')
 p.add_argument('--providers',nargs='+',default=['world_bank','fred','bls','eurostat']);p.add_argument('--countries',nargs='+',default=['USA','CAN','GBR','DEU','FRA','JPN','KOR','AUS','SWE','DNK','ZAF','NGA','KEN','GHA','RWA','ETH','IND','BRA','IDN','MEX']);p.add_argument('--start',type=int,default=1960);p.add_argument('--end',type=int,default=2026);p.add_argument('--offline',action='store_true');p.add_argument('--sdmx-provider');p.add_argument('--sdmx-url');args=p.parse_args()
 print(json.dumps(run(args),indent=2))
if __name__=='__main__':main()
