"""Compare Vanguard index funds against a 4% savings account.

The headline output is the rolling-window table: how often the S&P 500
actually beat 4%/yr over 1, 5, 10, 20 and 30 year holding periods. That is
the real answer to "is this more reliable than my bank".

Run research/fetch_vanguard.py first.
"""
import csv,glob,os,numpy as np
TD=252.
NAMES={'VOO':'Vanguard S&P 500 (US-dom)','VTI':'Vanguard Total US Stock (US-dom)',
 'VT':'Vanguard Total World (US-dom)','VXUS':'Vanguard Intl ex-US (US-dom)',
 'BND':'Vanguard Total US Bond (US-dom)','VWCE.DE':'FTSE All-World UCITS acc (Irish)',
 'VWRL.AS':'FTSE All-World UCITS dist (Irish)','VUAA.DE':'S&P500 UCITS acc (Irish)',
 'VAS.AX':'Vanguard Aus Shares (AU)','VGS.AX':'Vanguard Intl Shares (AU)',
 'VDHG.AX':'Diversified High Growth (AU)','^GSPC':'S&P 500 PRICE index (no div)'}
D={}
for f in sorted(glob.glob('vg/*.csv')):
    t=os.path.basename(f)[:-4]; d=[];p=[]
    for r in csv.DictReader(open(f)):
        try: v=float(r['AdjClose'])
        except: continue
        if v>0: d.append(r['Date']); p.append(v)
    D[t]=(d,np.array(p))

def met(p,rf=0.04):
    r=np.diff(p)/p[:-1]; yrs=len(r)/TD
    cagr=(p[-1]/p[0])**(1/yrs)-1
    v=np.std(r)*np.sqrt(TD)
    e=np.cumprod(1+r); dd=float(np.max(1-e/np.maximum.accumulate(e)))
    return dict(yrs=yrs,cagr=cagr*100,vol=v*100,dd=dd*100,sharpe=(cagr-rf)/v if v>0 else 0)

print("="*104)
print("VANGUARD FUNDS -- TOTAL RETURN (dividends reinvested), each over its own full history")
print("="*104)
print(f"{'ticker':9s} {'fund':35s} {'yrs':>5s} {'CAGR%':>7s} {'vol%':>6s} {'maxDD%':>7s} {'Sharpe*':>8s}")
for t in ['VOO','VTI','VT','VXUS','BND','VWCE.DE','VWRL.AS','VAS.AX','VGS.AX','VDHG.AX']:
    if t not in D: continue
    m=met(D[t][1])
    print(f"{t:9s} {NAMES[t][:35]:35s} {m['yrs']:5.1f} {m['cagr']:7.2f} {m['vol']:6.1f} {m['dd']:7.1f} {m['sharpe']:8.2f}")
print("  *Sharpe vs a 4% cash rate. Currencies differ: .AX figures are AUD, .DE/.AS are EUR.")

# common window comparison
print("\n"+"="*104); print("SAME WINDOW (since VGS.AX starts, 2014-11) -- apples to apples"); print("="*104)
common=set(D['VGS.AX'][0])
for t in ['VOO','VTI','VT','VXUS','BND','VWRL.AS','VAS.AX','VGS.AX']:
    if t in D: common &= set(D[t][0])
cd=sorted(common)
print(f"  window: {cd[0]} .. {cd[-1]}  ({len(cd)/TD:.1f} yrs)")
print(f"  {'ticker':9s} {'CAGR%':>7s} {'vol%':>6s} {'maxDD%':>7s}")
for t in ['VOO','VTI','VT','VXUS','BND','VWRL.AS','VAS.AX','VGS.AX']:
    if t not in D: continue
    dd,pp=D[t]; ix={x:i for i,x in enumerate(dd)}
    sel=np.array([pp[ix[x]] for x in cd]); m=met(sel)
    print(f"  {t:9s} {m['cagr']:7.2f} {m['vol']:6.1f} {m['dd']:7.1f}")

# RELIABILITY: rolling windows vs 4%
print("\n"+"="*104)
print("RELIABILITY: how often does the S&P 500 actually beat 4%/yr?")
print("Rolling windows, 1928-2026 price return + 2.0%/yr assumed dividend")
print("="*104)
dd,pp=D['^GSPC']; lr=np.log(pp)
DIV=0.02
for years in [1,3,5,10,15,20,30]:
    n=int(years*TD)
    if n>=len(pp): continue
    rets=(np.exp((lr[n:]-lr[:-n])/years)-1)+DIV
    beat=np.mean(rets>0.04)*100; neg=np.mean(rets<0)*100
    print(f"  {years:2d}-yr windows: median {np.median(rets)*100:6.2f}%/yr | "
          f"worst {np.min(rets)*100:7.2f}% | best {np.max(rets)*100:6.2f}% | "
          f"beat 4%: {beat:5.1f}% | lost money: {neg:5.1f}%")
print("\n  Same, but starting only from 1970 (post-Bretton Woods, modern era):")
i70=next(i for i,x in enumerate(dd) if x>='1970-01-01')
lr7=np.log(pp[i70:])
for years in [1,5,10,20,30]:
    n=int(years*TD)
    if n>=len(lr7): continue
    rets=(np.exp((lr7[n:]-lr7[:-n])/years)-1)+DIV
    print(f"  {years:2d}-yr windows: median {np.median(rets)*100:6.2f}%/yr | "
          f"worst {np.min(rets)*100:7.2f}% | beat 4%: {np.mean(rets>0.04)*100:5.1f}%")

print("\n"+"="*104); print("THE FULL LADDER, ranked"); print("="*104)
rows=[("Bank savings / high-yield",4.10,0.0,0.0,"insured, instant access"),
      ("Vanguard VMFXX money market",3.65,0.2,0.0,"not insured, T-bill backed"),
      ("Vanguard BND (US bonds)",met(D['BND'][1])['cagr'],met(D['BND'][1])['vol'],met(D['BND'][1])['dd'],"18yr history"),
      ("MY TREND BOT, best config",6.41,10.0,33.4,"multi-asset long-only CFD"),
      ("Vanguard VT (total world)",met(D['VT'][1])['cagr'],met(D['VT'][1])['vol'],met(D['VT'][1])['dd'],"18yr history"),
      ("Vanguard VTI (total US)",met(D['VTI'][1])['cagr'],met(D['VTI'][1])['vol'],met(D['VTI'][1])['dd'],"25yr history"),
      ("Vanguard VOO (S&P 500)",met(D['VOO'][1])['cagr'],met(D['VOO'][1])['vol'],met(D['VOO'][1])['dd'],"16yr history")]
rows.sort(key=lambda r:r[1])
print(f"  {'option':32s} {'ret%':>6s} {'vol%':>6s} {'maxDD%':>7s}  note")
for nm,r,v,d_,note in rows:
    print(f"  {nm:32s} {r:6.2f} {v:6.1f} {d_:7.1f}  {note}")
