"""HAC local-projection estimation with falsification tests. No automatic causal claims."""
import math
import numpy as np
import pandas as pd
import statsmodels.api as sm

def local_projection(df, outcome='outcome', shock='shock', horizon=0, lags=2, maxlags=None):
 """Single-country time-series LP: change y[t+h]-y[t-1] on shock[t] and lagged shock and delta-y.
 Assumes shock is externally identified; estimate is association unless identification verified.
 """
 if horizon<0 or lags<1:raise ValueError('Invalid horizon/lags')
 if not {'period',outcome,shock}.issubset(df.columns):raise ValueError('Missing columns')
 d=df[['period',outcome,shock]].copy().sort_values('period')
 if d['period'].duplicated().any():raise ValueError('Duplicate periods')
 if not np.isfinite(d[[outcome,shock]].to_numpy(dtype=float)).all():raise ValueError('Nonfinite data')
 if len(d)<max(30,8*(lags+1)+horizon):raise ValueError('Too few observations')
 d['target']=d[outcome].shift(-horizon)-d[outcome].shift(1)
 d['delta_y']=d[outcome].diff()
 regressors=[shock]
 for lag in range(1,lags+1):
  for name in [shock,'delta_y']:
   col=f'{name}_lag{lag}';d[col]=d[name].shift(lag);regressors.append(col)
 d=d.dropna(subset=['target']+regressors)
 if len(d)<20:raise ValueError('Too few complete observations')
 X=sm.add_constant(d[regressors],has_constant='add')
 if np.linalg.matrix_rank(X.to_numpy())<X.shape[1]:raise ValueError('Rank deficient design')
 result=sm.OLS(d['target'],X).fit(cov_type='HAC',cov_kwds={'maxlags':maxlags if maxlags is not None else max(1,horizon+1)})
 ci=result.conf_int().loc[shock]
 return {'horizon':horizon,'estimate':float(result.params[shock]),'se':float(result.bse[shock]),'ci95':[float(ci.iloc[0]),float(ci.iloc[1])],'p_value':float(result.pvalues[shock]),'n':len(d),'covariance':'HAC','causal':False,'identification':'requires separately validated exogenous policy shock','warning':'Estimate is not causal without verified shock identification, correct specification, and robustness.'}

def future_shock_placebo(df, outcome='outcome', shock='shock', lags=2):
 """Lead-shock falsification: future policy shock should not predict current outcome change under no anticipation."""
 d=df.copy();d['future_shock']=d[shock].shift(-1)
 d=d.dropna(subset=['future_shock'])
 return local_projection(d,outcome,'future_shock',horizon=0,lags=lags)

def estimate_horizons(df, horizons=(0,1,2,3,4),**kw):
 return [local_projection(df,horizon=h,**kw) for h in horizons]
