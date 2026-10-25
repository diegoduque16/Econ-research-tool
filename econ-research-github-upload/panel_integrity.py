"""Strict economic panel validation; never silently aggregate or reconcile incompatible observations."""
import csv, json, math, pathlib, hashlib, re
from collections import defaultdict
REQUIRED=('provider','series','geo','period','value','unit','frequency')
ISO3=re.compile(r'^[A-Z]{3}$')
PERIOD={'A':re.compile(r'^\d{4}$'),'Q':re.compile(r'^\d{4}-Q[1-4]$'),'M':re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')}

def validate_file(path):
    path=pathlib.Path(path); problems=[]; valid=[]; seen={}
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        missing=set(REQUIRED)-set(reader.fieldnames or [])
        if missing:return {'valid_rows':0,'errors':[{'type':'missing_columns','columns':sorted(missing)}],'warnings':[],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        for line,r in enumerate(reader,2):
            reasons=[]
            try:
                v=float(r['value']);
                if not math.isfinite(v):reasons.append('nonfinite_value')
            except (ValueError,TypeError):reasons.append('invalid_value');v=None
            freq=r['frequency']
            if freq not in PERIOD:reasons.append('unknown_frequency')
            elif not PERIOD[freq].fullmatch(r['period']):reasons.append('frequency_period_mismatch')
            if not ISO3.fullmatch(r['geo']):reasons.append('geo_not_iso3')
            if not r['unit']:reasons.append('missing_unit')
            if not r['series'] or not r['provider']:reasons.append('missing_identifier')
            key=(r['provider'],r['series'],r['geo'],r['period'],r['unit'],freq)
            if key in seen:reasons.append('duplicate_key' if seen[key]==v else 'conflicting_duplicate')
            else:seen[key]=v
            if reasons:problems.append({'line':line,'issues':reasons})
            else:valid.append(r)
    return {'valid_rows':len(valid),'errors':problems,'warnings':[],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def compatible(left,right):
    """Explicitly require matching concepts/units/frequency; provider is allowed to differ."""
    return all(left.get(k) and left.get(k)==right.get(k) for k in ('concept_id','unit','frequency','price_basis','seasonal_adjustment'))

def audit_folder(folder):
    folder=pathlib.Path(folder)
    return {p.name:validate_file(p) for p in sorted(folder.glob('*.csv'))}
