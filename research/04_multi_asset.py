"""Multi-asset trend following on IC Markets-style CFDs.

Answers three questions:
  1. Does trading something other than EUR/USD beat 4%?
  2. How much does IC Markets' CFD financing (benchmark +/- 250bp) cost?
  3. Does the trend bot beat simply OWNING the same assets?

Mirrors the logic in src/CarryTrendFx.cs. See research/README.md for data setup.
"""
import csv, os, glob, sys
import numpy as np

FAST=[16,32,64]; SLOW=[64,128,256]; SC=[4.10,2.79,1.91]; TW=[.30,.40,.30]
CAP=20.; FDM=1.25; AVG=10.; TD=252.; WARM=max(SLOW)+50

# Annual holding markup on |notional|, charged in BOTH directions.
# IC Markets cash index CFDs finance at overnight benchmark +/- 250bp, so the
# 2.5% markup is paid whether you are long or short. Futures-based CFDs pay
# roll costs instead. These mirror AnnualHoldingCostFraction() in the cBot.
MARKUP={'index':.025,'metal':.025,'energy':.010,'ag':.010,'bond':.005,
        'crypto':.150,'fx':.0075}
TCOST={'index':.00010,'metal':.00012,'energy':.00035,'ag':.00040,'bond':.00008,
       'crypto':.00150,'fx':.00008}
CLS={'US500':'index','NAS100':'index','US30':'index','GER40':'index','UK100':'index',
 'JP225':'index','AUS200':'index','EU50':'index','HK50':'index','XAUUSD':'metal',
 'XAGUSD':'metal','COPPER':'metal','WTI':'energy','BRENT':'energy','NATGAS':'energy',
 'UST10Y':'bond','UST30Y':'bond','BTCUSD':'crypto','ETHUSD':'crypto',
 'CORN':'ag','WHEAT':'ag','SOYBEAN':'ag'}

def load_universe():
    series={}
    for f in sorted(glob.glob('yf/*.csv')):
        n=os.path.basename(f)[:-4]; d=[];p=[]
        for r in csv.DictReader(open(f)):
            try: v=float(r['Close'])
            except (ValueError,KeyError): continue
            if v>0: d.append(r['Date']); p.append(v)
        if len(p)>1200: series[n]=(d,np.array(p),CLS.get(n,'index'))
    if os.path.exists('eurofxref-hist.csv'):
        rows=sorted(csv.DictReader(open('eurofxref-hist.csv')),key=lambda r:r['Date'].strip())
        dts=[r['Date'].strip() for r in rows]
        for c in ['USD','JPY','GBP','CHF','AUD','CAD','SEK','NOK','NZD']:
            v=np.array([float(r[c]) if r.get(c,'').strip() not in ('','N/A') else np.nan
                        for r in rows])
            m=~np.isnan(v)
            if m.sum()>4000:
                series['EUR'+c]=([d for d,k in zip(dts,m) if k], v[m], 'fx')
    return series

def ema(x,s):
    a=2/(s+1); o=np.empty_like(x); o[0]=x[0]
    for i in range(1,len(x)): o[i]=o[i-1]+a*(x[i]-o[i-1])
    return o

def vol(p,span=32,blend=.30,lr=2500):
    """EWMA vol of daily % returns, blended with a long-run average."""
    r=np.diff(p,prepend=p[0])/p; r[0]=0; a=2/(span+1)
    v=np.empty_like(p); v[0]=0
    for i in range(1,len(p)): v[i]=v[i-1]+a*(r[i]**2-v[i-1])
    rec=np.sqrt(np.maximum(v,0)); cs=np.cumsum(r**2); o=np.empty_like(p)
    for i in range(len(p)):
        s=max(1,i-lr+1); n=i-s+1
        o[i]=np.sqrt((cs[i]-cs[s-1])/n) if n>0 else rec[i]
    return rec*(1-blend)+o*blend

def forecast(p,sg):
    lp=np.log(p); e={s:ema(lp,s) for s in set(FAST+SLOW)}; t=np.zeros_like(p)
    for f,sl,sc,w in zip(FAST,SLOW,SC,TW):
        with np.errstate(divide='ignore',invalid='ignore'):
            r=(e[f]-e[sl])/np.where(sg>0,sg,np.nan)
        t+=np.clip(np.nan_to_num(r)*sc,-CAP,CAP)*w
    return np.clip(t/sum(TW)*FDM,-CAP,CAP)

def stream(p,cls,tv=.10,buf=.15,longonly=False,shortonly=False,markup_scale=1.0):
    """Daily net return stream, vol-targeted, after transaction + financing cost."""
    sg=vol(p); fc=forecast(p,sg); pos=0.
    R=np.zeros(len(p)); mk=MARKUP[cls]*markup_scale; tc=TCOST[cls]
    for i in range(WARM,len(p)-1):
        av=tv/(sg[i]*np.sqrt(TD)) if sg[i]>0 else 0
        f=fc[i]
        if longonly and f<0: f=0
        if shortonly and f>0: f=0
        t=float(np.clip(f/AVG*av,-5,5)); b=abs(av)*buf
        new=t+b if pos>t+b else (t-b if pos<t-b else pos)
        d=new-pos; cost=0.
        if abs(d)>1e-4: cost+=abs(d)*tc/2.; pos=new
        cost+=abs(pos)*mk/TD
        R[i+1]=pos*(p[i+1]-p[i])/p[i]-cost
    return R

def buyhold(p):
    r=np.zeros(len(p)); r[1:]=np.diff(p)/p[:-1]; r[:WARM]=0
    return r

def stats(r,lo,hi):
    x=r[lo:hi]; yrs=(hi-lo)/TD
    if yrs<=0 or np.std(x)==0: return None
    v=np.std(x)*np.sqrt(TD); m=np.sum(x)/yrs
    e=np.cumsum(x); dd=float(np.max(np.maximum.accumulate(e)-e))
    return dict(vol=v*100,ret=m*100,sharpe=m/v,dd=dd*100,yrs=yrs)

def main():
    series=load_universe()
    if not series:
        sys.exit("No data. See research/README.md for the download commands.")
    alld=sorted(set().union(*[set(d) for d,_,_ in series.values()]))
    idx={d:i for i,d in enumerate(alld)}
    print(f"Universe: {len(series)} instruments, {len(alld)} dates "
          f"{alld[0]} .. {alld[-1]}\n")

    def align(fn,names,**kw):
        acc=np.zeros(len(alld)); cnt=np.zeros(len(alld))
        for n in names:
            d,p,cls=series[n]; r=fn(p,cls,**kw) if fn is stream else fn(p)
            for k,dt in enumerate(d):
                if k>=WARM: acc[idx[dt]]+=r[k]; cnt[idx[dt]]+=1
        return np.where(cnt>0,acc/np.maximum(cnt,1),0.), np.where(cnt>0)[0]

    def report(names,lo=None,hi=None,**kw):
        R,w=align(stream,names,**kw)
        a=w[0] if lo is None else max(lo,w[0]); b=w[-1]+1 if hi is None else min(hi,w[-1]+1)
        st=stats(R,a,b); sc=10./st['vol'] if st['vol']>0 else 1
        return dict(ret=st['ret']*sc,sharpe=st['sharpe'],dd=st['dd']*sc,yrs=(b-a)/TD)

    def report_bh(names,lo=None,hi=None):
        R,w=align(buyhold,names)
        a=w[0] if lo is None else max(lo,w[0]); b=w[-1]+1 if hi is None else min(hi,w[-1]+1)
        st=stats(R,a,b); sc=10./st['vol'] if st['vol']>0 else 1
        return dict(ret=st['ret']*sc,sharpe=st['sharpe'],dd=st['dd']*sc,yrs=(b-a)/TD)

    names=sorted(series); nofx=[n for n in names if series[n][2]!='fx']
    indices=[n for n in names if series[n][2]=='index']
    mid=idx.get('2013-01-02') or idx.get('2013-01-03')

    print("="*92); print("1. DIRECTION: does giving up the short side help?"); print("="*92)
    for lbl,kw in [("long/short",{}),("long only",dict(longonly=True)),
                   ("short only",dict(shortonly=True))]:
        r=report(nofx,**kw)
        print(f"  no-FX, {lbl:11s} net {r['ret']:6.2f}%/yr | Sharpe {r['sharpe']:6.2f} "
              f"| maxDD {r['dd']:5.1f}%")

    print("\n"+"="*92); print("2. FINANCING: what the CFD wrapper costs"); print("="*92)
    for lbl,sc in [("zero financing (fantasy)",0.),("IC Markets (bench+/-250bp)",1.),
                   ("ETF-like, ~0.1%/yr",0.04),("2x markup",2.)]:
        r=report(nofx,longonly=True,markup_scale=sc)
        print(f"  {lbl:28s} net {r['ret']:6.2f}%/yr | Sharpe {r['sharpe']:6.2f}")

    print("\n"+"="*92)
    print("3. THE REAL TEST: trend bot vs simply OWNING the assets, both at 10% vol")
    print("="*92)
    print(f"  {'universe':24s} {'period':>11s} {'trend%':>8s} {'B&H%':>8s} {'trendSh':>8s} {'B&H Sh':>8s}")
    for nm,ns in [("no-FX (22)",nofx),("equity indices (9)",indices)]:
        for lbl,lo,hi in [("full",None,None),("1985-2012",None,mid),("2013-2026",mid,None)]:
            t=report(ns,lo,hi,longonly=True); b=report_bh(ns,lo,hi)
            print(f"  {nm:24s} {lbl:>11s} {t['ret']:8.2f} {b['ret']:8.2f} "
                  f"{t['sharpe']:8.2f} {b['sharpe']:8.2f}")

    print("\n"+"="*92); print("4. THE 4% HURDLE"); print("="*92)
    rows=[("Bank savings",4.0,0.0,0.0)]
    for lbl,ns,kw in [("Trend bot, all instruments",names,{}),
                      ("Trend bot, no-FX long/short",nofx,{}),
                      ("Trend bot, no-FX LONG ONLY",nofx,dict(longonly=True))]:
        r=report(ns,**kw); rows.append((lbl,r['ret'],10.0,r['dd']))
    b=report_bh(nofx); rows.append(("Owning the same assets",b['ret'],10.0,b['dd']))
    for nm,ret,v,dd in rows:
        print(f"  {nm:30s} {ret:6.2f}%/yr  vol {v:5.1f}%  maxDD {dd:5.1f}%   "
              f"{'BEATS 4%' if ret>4 else 'loses to 4%'}")

if __name__=='__main__':
    main()
