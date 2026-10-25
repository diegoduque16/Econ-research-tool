"""Pre-analysis diagnostics and transparent difference-in-differences prototype.
Not a causal attribution engine: parallel trends and treatment exogeneity are unverified.
"""
import math, statistics
from collections import defaultdict

def did_diagnostic(rows,treated,intervention_year,outcome,pre_years=4,post_years=3):
    """rows: geo, year, outcome, value. Balanced sample required per country."""
    if pre_years<3 or post_years<1:raise ValueError('Need >=3 pre-years and >=1 post-year')
    by=defaultdict(dict)
    for r in rows:
        if r['outcome']!=outcome:continue
        geo=str(r['geo']); year=int(r['year']); val=float(r['value'])
        if not math.isfinite(val):raise ValueError('Nonfinite value')
        if year in by[geo]:raise ValueError('Duplicate country-year observation')
        by[geo][year]=val
    years=list(range(intervention_year-pre_years,intervention_year+post_years))
    balanced={g:v for g,v in by.items() if all(y in v for y in years)}
    treatment=set(treated); t=sorted(treatment&balanced.keys());c=sorted(balanced.keys()-treatment)
    if not t or not c:return {'status':'insufficient_balanced_groups','treated':len(t),'controls':len(c),'causal':False}
    def mean(group,period):return statistics.mean(balanced[g][y] for g in group for y in period)
    pre=range(intervention_year-pre_years,intervention_year);post=range(intervention_year,intervention_year+post_years)
    effect=(mean(t,post)-mean(t,pre))-(mean(c,post)-mean(c,pre))
    # Compare linear pre-trend slopes for treated/control, purely diagnostic.
    def slope(group):
        values=[statistics.mean(balanced[g][y] for g in group) for y in pre]
        xs=list(range(len(values)));mx=statistics.mean(xs);my=statistics.mean(values)
        return sum((x-mx)*(v-my) for x,v in zip(xs,values))/sum((x-mx)**2 for x in xs)
    trend_gap=slope(t)-slope(c)
    # An early-period placebo uses only pre-treatment observations.
    early=list(pre)[:2];late=list(pre)[2:]
    placebo=(mean(t,late)-mean(t,early))-(mean(c,late)-mean(c,early))
    return {'status':'diagnostic_only','outcome':outcome,'treated':len(t),'controls':len(c),'estimate':effect,'pretrend_slope_gap':trend_gap,'pretreatment_placebo':placebo,'causal':False,'warning':'Not identified causally without justified parallel trends, exogeneity, uncertainty estimation and robustness checks. Do not report as a policy effect.'}
