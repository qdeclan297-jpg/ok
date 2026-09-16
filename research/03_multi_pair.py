"""Does diversifying across FX pairs rescue trend following? Real ECB data."""
import csv, numpy as np
FAST=[16,32,64]; SLOW=[64,128,256]; SC=[4.10,2.79,1.91]; TW=[.30,.40,.30]
CAP=20.; FDM=1.25; AVG=10.; TD=252.

raw={}; dates=[]
rdr=csv.DictReader(open('eurofxref-hist.csv'))
cols=[c for c in rdr.fieldnames if c and c!='Date']
rows=list(rdr); rows.sort(key=lambda r:r['Date'].strip())
for r in rows:
    dates.append(r['Date'].strip())
    for c in cols:
        v=r[c].strip(); raw.setdefault(c,[]).append(float(v) if v and v!='N/A' else np.nan)
raw={k:np.array(v) for k,v in raw.items()}

# Liquid majors/crosses IC Markets quotes. Build as USD-base or EUR-base series.
wanted=['USD','JPY','GBP','CHF','AUD','CAD','SEK','NOK','NZD']
pairs={}
for c in wanted:
    if c in raw and np.sum(~np.isnan(raw[c]))>5000: pairs['EUR'+c]=raw[c]
# USD crosses derived: USDJPY = (EURJPY)/(EURUSD) etc.
for c in ['JPY','CHF','CAD','SEK','NOK']:
    if c in raw and 'USD' in raw:
        s=raw[c]/raw['USD']
        if np.sum(~np.isnan(s))>5000: pairs['USD'+c]=s
for c in ['GBP','AUD','NZD']:
    if c in raw and 'USD' in raw:
        s=raw['USD']/raw[c]      # GBPUSD = EURUSD/EURGBP
        if np.sum(~np.isnan(s))>5000: pairs[c+'USD']=s

# keep rows where all present
names=sorted(pairs); M=np.column_stack([pairs[n] for n in names])
keep=~np.isnan(M).any(axis=1); M=M[keep]; dates=[d for d,k in zip(dates,keep) if k]
print(f"{len(names)} instruments, {len(dates)} common days {dates[0]}..{dates[-1]}")
print("  "+", ".join(names)+"\n")

def ema(x,s):
    a=2/(s+1); o=np.empty_like(x); o[0]=x[0]
    for i in range(1,len(x)): o[i]=o[i-1]+a*(x[i]-o[i-1])
    return o
def vol(p,span=32,blend=.30,lr=2500):
    d=np.diff(p,prepend=p[0]); d[0]=0; a=2/(span+1); v=np.empty_like(p); v[0]=0
    for i in range(1,len(p)): v[i]=v[i-1]+a*(d[i]**2-v[i-1])
    rec=np.sqrt(np.maximum(v,0)); cs=np.cumsum(d**2); o=np.empty_like(p)
    for i in range(len(p)):
        s=max(1,i-lr+1); n=i-s+1; o[i]=np.sqrt((cs[i]-cs[s-1])/n) if n>0 else rec[i]
    return rec*(1-blend)+o*blend
def tfc(p,sg):
    e={s:ema(p,s) for s in set(FAST+SLOW)}; t=np.zeros_like(p)
    for f,s,sc,w in zip(FAST,SLOW,SC,TW):
        with np.errstate(divide='ignore',invalid='ignore'):
            r=(e[f]-e[s])/np.where(sg>0,sg,np.nan)
        t+=np.clip(np.nan_to_num(r)*sc,-CAP,CAP)*w
    return np.clip(t/sum(TW)*FDM,-CAP,CAP)

warm=max(SLOW)+50
# per-instrument vol-targeted return stream, 10% vol each, buffered, cost 0.8 pips
def stream(p,tv=.10,buf=.15,cost_frac=0.8e-4/1.0):
    sg=vol(p); fc=tfc(p,sg); pos=0.; R=np.zeros(len(p)); C=np.zeros(len(p))
    for i in range(warm,len(p)-1):
        av=(tv)/ (sg[i]/p[i]*np.sqrt(TD)) if sg[i]>0 else 0   # notional as x capital
        t=fc[i]/AVG*av; t=float(np.clip(t,-5,5)); b=abs(av)*buf
        new=t+b if pos>t+b else (t-b if pos<t-b else pos)
        d=new-pos
        if abs(d)>1e-4:
            C[i]=abs(d)*(0.8*1e-4/p[i])/2.0*1   # 0.8 pip on notional
            pos=new
        R[i+1]=pos*(p[i+1]-p[i])/p[i]
    return R,C

streams={}; costs={}
for n,col in zip(names,M.T):
    R,C=stream(col); streams[n]=R; costs[n]=C

def stats(R,C,lo=warm,hi=None):
    hi=len(R) if hi is None else hi
    r=R[lo:hi]-C[lo:hi]; yrs=(hi-lo)/TD
    v=np.std(r)*np.sqrt(TD); m=np.sum(r)/yrs
    e=np.cumsum(r); dd=float(np.max(np.maximum.accumulate(e)-e))
    return v*100, m*100, (m/v if v>0 else 0), dd*100

print("Per-instrument (each vol-targeted to 10%):")
sh={}
for n in names:
    v,m,s,dd=stats(streams[n],costs[n]); sh[n]=s
    print(f"  {n}  vol {v:5.2f}%  net {m:6.2f}%/yr  Sharpe {s:6.2f}  maxDD {dd:5.1f}%")
print(f"\n  mean single-instrument Sharpe: {np.mean(list(sh.values())):.3f}\n")

print("Equal-weight portfolios (risk scaled back to 10% total vol):")
mid=next(i for i,d in enumerate(dates) if d>='2013-01-01')
for k in [1,2,3,5,8,len(names)]:
    sel=names[:k] if k<len(names) else names
    R=np.mean([streams[n] for n in sel],axis=0); C=np.mean([costs[n] for n in sel],axis=0)
    v,m,s,dd=stats(R,C)
    # scale to 10% vol
    sc=10.0/v if v>0 else 1
    vo,mo,so,ddo=stats(R,C,lo=mid)
    print(f"  N={k:2d}: vol {v:5.2f}% -> scaled net {m*sc:5.2f}%/yr  Sharpe {s:5.2f}  maxDD {dd*sc:5.1f}%   | OOS Sharpe {so:5.2f}")

print("\nAll-instrument portfolio, in-sample vs out-of-sample:")
R=np.mean([streams[n] for n in names],axis=0); C=np.mean([costs[n] for n in names],axis=0)
for lbl,lo,hi in [("1999-2012",warm,mid),("2013-2026",mid,None)]:
    v,m,s,dd=stats(R,C,lo,hi); sc=10.0/v if v>0 else 1
    print(f"  {lbl}: vol {v:5.2f}% | scaled to 10% vol -> {m*sc:5.2f}%/yr | Sharpe {s:5.2f} | maxDD {dd*sc:5.1f}%")

cm=np.corrcoef(np.array([streams[n][warm:] for n in names]))
iu=np.triu_indices(len(names),1)
print(f"\nMean pairwise correlation of instrument return streams: {np.mean(cm[iu]):.3f}")
print(f"  (low correlation is what makes diversification pay; FX pairs share USD/risk factors)")
