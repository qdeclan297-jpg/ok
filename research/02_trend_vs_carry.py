"""Trend vs carry vs blend on real EUR/USD, WITH carry accrual in P&L."""
import csv, numpy as np
from datetime import date

FAST=[16,32,64]; SLOW=[64,128,256]; SCALARS=[4.10,2.79,1.91]; TW=[0.30,0.40,0.30]
CAP=20.0; FDM=1.25; AVG=10.0; TD=252.0; PIP=1e-4; PIPVAL=1e-4

def load_fx():
    rows=[]
    for r in csv.DictReader(open('eurofxref-hist.csv')):
        v=r.get('USD','').strip()
        if v and v!='N/A': rows.append((r['Date'].strip(),float(v)))
    rows.sort(); return [d for d,_ in rows], np.array([p for _,p in rows])

def load_rate(fn,col):
    out={}
    for r in csv.DictReader(open(fn)):
        v=r[col].strip()
        if v not in ('','.'):
            try: out[r['observation_date'].strip()]=float(v)
            except ValueError: pass
    return out

dates,px=load_fx()
usd=load_rate('DFF.csv','DFF'); eur=load_rate('ECBDFR.csv','ECBDFR')

def align(series,dates):
    out=np.empty(len(dates)); keys=sorted(series); ki=0; last=np.nan
    for i,d in enumerate(dates):
        while ki<len(keys) and keys[ki]<=d: last=series[keys[ki]]; ki+=1
        out[i]=last
    return out

r_usd=align(usd,dates); r_eur=align(eur,dates)
ok=~np.isnan(r_usd)&~np.isnan(r_eur)
dates=[d for d,k in zip(dates,ok) if k]; px=px[ok]; r_usd=r_usd[ok]; r_eur=r_eur[ok]
print(f"{len(px)} days {dates[0]}..{dates[-1]}")
print(f"Latest: EUR depo {r_eur[-1]:.2f}%  USD FF {r_usd[-1]:.2f}%  -> carry of LONG EURUSD = {r_eur[-1]-r_usd[-1]:+.2f}%/yr\n")

# carry of a long EURUSD position, %/yr
carry_pct = r_eur - r_usd

def ema(x,s):
    a=2/(s+1); o=np.empty_like(x); o[0]=x[0]
    for i in range(1,len(x)): o[i]=o[i-1]+a*(x[i]-o[i-1])
    return o

def vol(px,span=32,blend=0.30,lr=2500):
    d=np.diff(px,prepend=px[0]); d[0]=0; a=2/(span+1)
    v=np.empty_like(px); v[0]=0
    for i in range(1,len(px)): v[i]=v[i-1]+a*(d[i]**2-v[i-1])
    rec=np.sqrt(np.maximum(v,0)); cs=np.cumsum(d**2); o=np.empty_like(px)
    for i in range(len(px)):
        s=max(1,i-lr+1); n=i-s+1; o[i]=np.sqrt((cs[i]-cs[s-1])/n) if n>0 else rec[i]
    return rec*(1-blend)+o*blend

sigma=vol(px)
ann_vol_pct=sigma/px*np.sqrt(TD)*100

def trend_fc(px,sigma):
    e={s:ema(px,s) for s in set(FAST+SLOW)}; tot=np.zeros_like(px)
    for f,s,sc,w in zip(FAST,SLOW,SCALARS,TW):
        with np.errstate(divide='ignore',invalid='ignore'):
            raw=(e[f]-e[s])/np.where(sigma>0,sigma,np.nan)
        tot+=np.clip(np.nan_to_num(raw)*sc,-CAP,CAP)*w
    return np.clip(tot/sum(TW)*FDM,-CAP,CAP)

def carry_fc(carry_pct,ann_vol_pct,scalar=30.0):
    with np.errstate(divide='ignore',invalid='ignore'):
        raw=carry_pct/np.where(ann_vol_pct>0,ann_vol_pct,np.nan)
    return np.clip(np.nan_to_num(raw)*scalar,-CAP,CAP)

TF=trend_fc(px,sigma); CF=carry_fc(carry_pct,ann_vol_pct)

def run(fc,tv=0.10,buf=0.15,cost=0.8,maxlev=5.0,gov=True,gw=64,eq=25000.0,lo=None,hi=None,include_carry=True):
    warm=max(SLOW)+50; lo=warm if lo is None else max(lo,warm); hi=len(px) if hi is None else hi
    pos=0.0; traded=0.0; c=0.0; P=np.zeros(len(px)); dr=np.zeros(len(px))
    for i in range(lo,hi):
        cvu=(sigma[i]/PIP)*PIPVAL*np.sqrt(TD)
        if cvu<=0: P[i]=pos; continue
        a=(eq*tv)/cvu; t=fc[i]/AVG*a
        if gov and i-lo>gw:
            rv=np.std(dr[i-gw:i])*np.sqrt(TD)
            if rv>0: t*=min(1.0,tv/rv)
        mu=eq*maxlev/px[i]; t=float(np.clip(t,-mu,mu))
        b=abs(a)*buf
        new=t+b if pos>t+b else (t-b if pos<t-b else pos)
        d=new-pos
        if abs(d)>=1000: traded+=abs(d); c+=abs(d)*PIPVAL*cost/2.0; pos=new
        P[i]=pos
        if i+1<len(px):
            spot=pos*(px[i+1]-px[i])
            cr=(pos*px[i])*(carry_pct[i]/100.0)/365.0 if include_carry else 0.0
            dr[i+1]=(spot+cr)/eq
    seg=slice(lo,hi); rets=dr[lo+1:hi]; yrs=(hi-lo)/TD
    cd=c/eq/yrs; v=np.std(rets)*np.sqrt(TD); g=np.sum(rets)/yrs; n=g-cd
    e=np.cumsum(rets)-np.linspace(0,cd*yrs,len(rets))
    dd=float(np.max(np.maximum.accumulate(e)-e))
    ap=np.mean(np.abs(P[seg]))
    return dict(vol=v*100,gross=g*100,net=n*100,cost=cd*100,
                sharpe=n/v if v>0 else 0,dd=dd*100,
                turn=(traded/yrs)/ap if ap>0 else 0,yrs=yrs)

def show(t,r):
    print(f"{t:38s} vol {r['vol']:5.2f}% | net {r['net']:6.2f}%/yr | Sharpe {r['sharpe']:5.2f} | maxDD {r['dd']:5.1f}% | turn {r['turn']:4.1f}x")

print("="*104); print("FULL SAMPLE (carry accrual included in P&L)"); print("="*104)
show("trend only",            run(TF))
show("carry only",            run(CF))
for w in [0.25,0.50,0.75]:
    show(f"blend trend {1-w:.0%} / carry {w:.0%}", run(np.clip((TF*(1-w)+CF*w),-CAP,CAP)))
print()
print("="*104); print("SPOT-ONLY P&L (carry accrual excluded) for comparison"); print("="*104)
show("trend only, no carry accrual", run(TF,include_carry=False))
show("carry only, no carry accrual", run(CF,include_carry=False))
print()
mid=next(i for i,d in enumerate(dates) if d>='2013-01-01')
print("="*104); print("OUT-OF-SAMPLE 2013-2026"); print("="*104)
show("trend only",  run(TF,lo=mid))
show("carry only",  run(CF,lo=mid))
show("blend 75/25", run(np.clip(TF*0.75+CF*0.25,-CAP,CAP),lo=mid))
show("blend 50/50", run(np.clip(TF*0.50+CF*0.50,-CAP,CAP),lo=mid))
print()
print("="*104); print("IN-SAMPLE 1999-2012"); print("="*104)
show("trend only",  run(TF,hi=mid))
show("carry only",  run(CF,hi=mid))
show("blend 50/50", run(np.clip(TF*0.50+CF*0.50,-CAP,CAP),hi=mid))
