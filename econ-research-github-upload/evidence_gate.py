"""Enforce honest labels in downstream research reports."""
def classify(estimate, source_event=None, replicated=False, sensitivity_passed=False):
 if not isinstance(estimate,dict) or 'estimate' not in estimate: return {'grade':'no_estimate','publish_as_causal':False}
 verified=bool(source_event and source_event.get('status')=='verified' and source_event.get('identification')=='narrative_exogenous')
 if verified and replicated and sensitivity_passed:
  return {'grade':'causal_candidate_needs_expert_review','publish_as_causal':False}
 return {'grade':'exploratory_association','publish_as_causal':False,'reasons':[k for k,v in [('verified_identification',verified),('independent_replication',replicated),('sensitivity_checks',sensitivity_passed)] if not v]}
