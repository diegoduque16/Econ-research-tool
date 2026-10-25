"""Evidence-backed intervention registry. Bibliographic records are NOT numeric shocks."""
import csv, json, pathlib
REQUIRED={'event_id','country','policy_type','start_date','end_date','identification','source_url','source_title','status','shock_value','shock_unit','anticipation','notes'}
ALLOWED={'source_identified','awaiting_numeric_extraction','extracted_unverified','verified'}
def validate_event(event):
 missing=REQUIRED-set(event)
 if missing: raise ValueError(f'Missing fields: {sorted(missing)}')
 if event['status'] not in ALLOWED: raise ValueError('Invalid status')
 if event['status']=='verified' and (event['shock_value'] in ('',None) or not event['shock_unit']):raise ValueError('Verified events require magnitude and units')
 if event['status']!='verified' and event['shock_value'] not in ('',None):raise ValueError('Unverified shock cannot have a numerical value')
 if not event['source_url'].startswith('https://'):raise ValueError('Source URL required')
 return event
def load_events(path):
 with open(path,newline='') as f: rows=list(csv.DictReader(f))
 ids=set()
 for row in rows:
  validate_event(row)
  if row['event_id'] in ids:raise ValueError('Duplicate event ID')
  ids.add(row['event_id'])
 return rows
