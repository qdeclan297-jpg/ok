"""Backtest the CarryTrendFx logic on real ECB EUR/USD daily fixings (1999-2026).
Mirrors the C# implementation. ECB fixings are not tradeable closes -- this
validates scaling/turnover/vol behaviour, it is not a substitute for a cTrader
backtest on broker tick data."""
import csv, numpy as np

FAST=[16,32,64]; SLOW=[64,128,256]
SCALARS=[4.10,2.79,1.91]; TW=[0.30,0.40,0.30]
CAP=20.0; FDM=1.25; AVG_FC=10.0; TD=252.0
PIP=1e-4; PIPVAL=1e-4; LOT=100000.0

rows=[]
with open('eurofxref-hist.csv') as f:
    r=csv.DictReader(f)
    for row in r:
        v=row.get('USD','').strip()
        if v and v!='N/A':
            rows.append((row['Date'].strip(), float(v)))
rows.sort()
dates=[d for d,_ in rows]; px=np.array([p for _,p in rows])
print(f"Loaded {len(px)} daily EUR/USD fixings: {dates[0]} .. {dates[-1]}")
print(f"Price range {px.min():.4f} - {px.max():.4f}\n")

def ema(x,span):
    a=2.0/(span+1.0); o=np.empty_like(x); o[0]=x[0]
    for i in range(1,len(x)): o[i]=o[i-1]+a*(x[i]-o[i-1])
    return o

def ewma_vol(px,span=32,blend=0.30,lr=2500):
    d=np.diff(px,prepend=px[0]); d[0]=0.0
    a=2.0/(span+1.0); var=np.empty_like(px); var[0]=0.0
    for i in range(1,len(px)): var[i]=var[i-1]+a*(d[i]**2-var[i-1])
    recent=np.sqrt(np.maximum(var,0))
    out=np.empty_like(px); csum=np.cumsum(d**2)
    for i in range(len(px)):
        s=max(1,i-lr+1); n=i-s+1
        out[i]=np.sqrt((csum[i]-csum[s-1])/n) if n>0 else recent[i]
    return recent*(1-blend)+out*blend

def forecast(px,sigma):
    e={s:ema(px,s) for s in set(FAST+SLOW)}
    tot=np.zeros_like(px)
    for f,s,sc,w in zip(FAST,SLOW,SCALARS,TW):
        with np.errstate(divide='ignore',invalid='ignore'):
            raw=(e[f]-e[s])/np.where(sigma>0,sigma,np.nan)
        tot+=np.clip(np.nan_to_num(raw)*sc,-CAP,CAP)*w
    return np.clip(tot/sum(TW)*FDM,-CAP,CAP)

def run(px,target_vol=0.10,buffer_frac=0.15,cost_pips=0.8,maxlev=5.0,
        governor=False,gov_window=64,gov_max=1.0,equity=25000.0,lo=None,hi=None):
    sigma=ewma_vol(px); fc=forecast(px,sigma)
    warm=max(SLOW)+50
    lo=warm if lo is None else max(lo,warm); hi=len(px) if hi is None else hi
    pos=0.0; traded=0.0; nreb=0; cost=0.0
    P=np.zeros(len(px)); daily_ret=np.zeros(len(px)); scales=[]
    for i in range(lo,hi):
        cvu=(sigma[i]/PIP)*PIPVAL*np.sqrt(TD)
        if cvu<=0: P[i]=pos; continue
        avg=(equity*target_vol)/cvu
        tgt=fc[i]/AVG_FC*avg
        # --- realised-vol governor ---
        if governor and i-lo>gov_window:
            rv=np.std(daily_ret[i-gov_window:i])*np.sqrt(TD)
            if rv>0:
                sc=min(gov_max,target_vol/rv); scales.append(sc); tgt*=sc
        mu=equity*maxlev/px[i]; tgt=float(np.clip(tgt,-mu,mu))
        band=abs(avg)*buffer_frac
        new = tgt+band if pos>tgt+band else (tgt-band if pos<tgt-band else pos)
        d=new-pos
        if abs(d)>=1000:
            traded+=abs(d); nreb+=1; cost+=abs(d)*PIPVAL*cost_pips/2.0; pos=new
        P[i]=pos
        if i+1<len(px): daily_ret[i+1]=(pos*(px[i+1]-px[i]))/equity
    seg=slice(lo,hi)
    pnl=P[lo:hi-1]*np.diff(px[lo:hi])
    gross=pnl/equity
    yrs=(hi-lo)/TD
    cost_ret=cost/equity/yrs
    avgpos=np.mean(np.abs(P[seg]))
    turnover=(traded/yrs)/avgpos if avgpos>0 else 0
    vol=np.std(gross)*np.sqrt(TD)
    g_cagr=np.sum(gross)/yrs
    n_cagr=g_cagr-cost_ret
    eq=np.cumsum(gross)-np.linspace(0,cost_ret*yrs,len(gross))
    dd=float(np.max(np.maximum.accumulate(eq)-eq))
    return dict(years=yrs, mean_abs_fc=float(np.mean(np.abs(fc[seg]))),
        pct_cap=float(np.mean(np.abs(fc[seg])>=CAP*0.999)*100),
        realised_vol=vol*100, gross_ret=g_cagr*100, net_ret=n_cagr*100,
        cost_drag=cost_ret*100, sharpe_net=(n_cagr/vol if vol>0 else 0),
        max_dd=dd*100, turnover_x_yr=turnover, rebal_yr=nreb/yrs,
        avg_notional_x=float(avgpos*np.mean(px[seg])/equity),
        mean_gov_scale=float(np.mean(scales)) if scales else 1.0)

def show(t,r):
    print(f"--- {t} ---")
    print(f"  years {r['years']:.1f} | mean|fc| {r['mean_abs_fc']:.2f} | at cap {r['pct_cap']:.1f}%")
    print(f"  realised vol {r['realised_vol']:.2f}%/yr  (target 10.00%)   avg notional {r['avg_notional_x']:.2f}x equity")
    print(f"  gross {r['gross_ret']:.2f}%/yr | cost {r['cost_drag']:.3f}%/yr | NET {r['net_ret']:.2f}%/yr")
    print(f"  net Sharpe {r['sharpe_net']:.2f} | max DD {r['max_dd']:.1f}% | turnover {r['turnover_x_yr']:.1f}x/yr | {r['rebal_yr']:.0f} rebalances/yr")
    if r['mean_gov_scale']<1.0: print(f"  governor avg scale {r['mean_gov_scale']:.2f}")
    print()

print("="*74); print("FULL SAMPLE 1999-2026, no governor"); print("="*74)
show("baseline buffer=0.15", run(px))
print("="*74); print("BUFFER SENSITIVITY (turnover / cost trade-off)"); print("="*74)
for b in [0.0,0.05,0.10,0.15,0.20,0.30,0.40]:
    r=run(px,buffer_frac=b)
    print(f"  buffer {b:0.2f}: turnover {r['turnover_x_yr']:5.1f}x/yr | {r['rebal_yr']:4.0f} rebal/yr | "
          f"cost {r['cost_drag']:.3f}%/yr | net {r['net_ret']:5.2f}%/yr | Sharpe {r['sharpe_net']:.2f}")
print()
print("="*74); print("REALISED-VOL GOVERNOR"); print("="*74)
show("governor ON", run(px,governor=True))
print("="*74); print("OUT-OF-SAMPLE SPLIT"); print("="*74)
mid=next(i for i,d in enumerate(dates) if d>='2013-01-01')
show("in-sample 1999-2012", run(px,hi=mid,governor=True))
show("out-of-sample 2013-2026", run(px,lo=mid,governor=True))
print("="*74); print("COST SENSITIVITY (net %/yr, governor on)"); print("="*74)
for c in [0.0,0.8,1.5,3.0,6.0]:
    r=run(px,cost_pips=c,governor=True)
    print(f"  {c:4.1f} pips round turn: cost {r['cost_drag']:.3f}%/yr -> net {r['net_ret']:5.2f}%/yr | Sharpe {r['sharpe_net']:.2f}")
