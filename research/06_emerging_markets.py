"""Emerging markets: does fast GDP growth pay investors?

Tests Ritter (2012) -- who found a -0.39 cross-sectional correlation between
real GDP growth and real equity returns -- against 13 country ETFs and World
Bank GDP data. Also compares EM vs global bonds against a 4% cash rate.

Run fetch_em.py and fetch_gdp.py first.
"""
import csv,glob,os,json,numpy as np
TD=252.
D={}
for f in sorted(glob.glob('em/*.csv')):
    t=os.path.basename(f)[:-4]; d=[];p=[]
    for r in csv.DictReader(open(f)):
        try: v=float(r['AdjClose'])
        except: continue
        if v>0: d.append(r['Date']); p.append(v)
    D[t]=(d,np.array(p))
G={k:{int(a):b for a,b in v.items()} for k,v in json.load(open('wb/gdp.json')).items()}
CTRY={'EPHE':'Philippines','EIDO':'Indonesia','INDA':'India','MCHI':'China',
 'EWY':'South Korea','THD':'Thailand','EWM':'Malaysia','VNM':'Vietnam','EWZ':'Brazil',
 'EZA':'South Africa','EWT':'Taiwan','TUR':'Turkey','EWW':'Mexico','VOO':'United States'}

def met(p):
    r=np.diff(p)/p[:-1]; yrs=len(r)/TD
    cagr=(p[-1]/p[0])**(1/yrs)-1; v=np.std(r)*np.sqrt(TD)
    e=np.cumprod(1+r); dd=float(np.max(1-e/np.maximum.accumulate(e)))
    return yrs,cagr*100,v*100,dd*100

def window(t,start=None):
    d,p=D[t]
    if start:
        i=next((k for k,x in enumerate(d) if x>=start),None)
        if i is None or len(p)-i<250: return None
        d,p=d[i:],p[i:]
    return d,p

print("="*104)
print("1. GDP GROWTH vs WHAT INVESTORS ACTUALLY EARNED  (USD total return, each ETF's full life)")
print("="*104)
print(f"  {'country':15s} {'ticker':7s} {'yrs':>5s} {'GDP growth':>11s} {'USD return':>11s} {'vol%':>7s} {'maxDD%':>7s}")
rows=[]
for t,name in CTRY.items():
    if t not in D: continue
    d,p=D[t]; yrs,cagr,vol,dd=met(p)
    y0=int(d[0][:4]); y1=int(d[-1][:4])
    if t in G:
        g=[v for k,v in G[t].items() if y0<=k<=y1]
        gg=float(np.mean(g)) if g else float('nan')
    else: gg=float('nan')
    rows.append((name,t,yrs,gg,cagr,vol,dd))
rows.sort(key=lambda r:-(r[3] if r[3]==r[3] else -99))
for name,t,yrs,gg,cagr,vol,dd in rows:
    gs=f"{gg:10.2f}%" if gg==gg else "       n/a"
    print(f"  {name:15s} {t:7s} {yrs:5.1f} {gs} {cagr:10.2f}% {vol:7.1f} {dd:7.1f}")
val=[(r[3],r[4]) for r in rows if r[3]==r[3]]
if len(val)>3:
    a=np.array(val); c=np.corrcoef(a[:,0],a[:,1])[0,1]
    print(f"\n  Correlation between average GDP growth and investor return: {c:+.3f}")
    print(f"  (Ritter 2012 found -0.39 across 19 countries 1900-2011, -0.41 for EM 1988-2011)")

print("\n"+"="*104)
print("2. SAME WINDOW for all (since INDA starts 2012-02) -- removes start-date luck")
print("="*104)
START='2012-02-06'
print(f"  {'country':15s} {'ticker':7s} {'USD return':>11s} {'vol%':>7s} {'maxDD%':>7s}")
srows=[]
for t,name in CTRY.items():
    w=window(t,START)
    if not w: continue
    yrs,cagr,vol,dd=met(w[1]); srows.append((name,t,cagr,vol,dd))
for name,t,cagr,vol,dd in sorted(srows,key=lambda r:-r[2]):
    print(f"  {name:15s} {t:7s} {cagr:10.2f}% {vol:7.1f} {dd:7.1f}")
for t,lbl in [('VWO','EM index (VWO)'),('VEA','Developed ex-US'),('VT','World'),('VOO','S&P 500')]:
    w=window(t,START)
    if w: yrs,c,v,dd=met(w[1]); print(f"  {'-- '+lbl:22s}         {c:10.2f}% {v:7.1f} {dd:7.1f}")

print("\n"+"="*104); print("3. BONDS ACROSS MARKETS (USD total return, full history each)"); print("="*104)
print(f"  {'fund':7s} {'what it is':32s} {'yrs':>5s} {'return':>9s} {'vol%':>7s} {'maxDD%':>7s}")
BN={'EMB':'EM govt bonds, USD-denominated','EMLC':'EM govt bonds, local currency',
 'VWOB':'Vanguard EM govt bond, USD','BNDX':'Global bonds ex-US, USD-hedged',
 'BND':'US total bond market','TIP':'US inflation-linked'}
for t,desc in BN.items():
    if t not in D: continue
    yrs,c,v,dd=met(D[t][1])
    print(f"  {t:7s} {desc:32s} {yrs:5.1f} {c:8.2f}% {v:7.1f} {dd:7.1f}")
print("\n  Same window (since EMLC starts 2010-07):")
S2='2010-08-02'
for t,desc in BN.items():
    w=window(t,S2)
    if w: yrs,c,v,dd=met(w[1]); print(f"  {t:7s} {desc:32s} {yrs:5.1f} {c:8.2f}% {v:7.1f} {dd:7.1f}")

print("\n"+"="*104); print("4. DOES EM EQUITY ADD ANYTHING TO A WORLD FUND?"); print("="*104)
S3='2010-08-02'
wv=window('VWO',S3); wt=window('VT',S3); wo=window('VOO',S3)
for t,lbl,w in [('VWO','EM only',wv),('VT','World (incl ~10% EM)',wt),('VOO','S&P 500 only',wo)]:
    if w: yrs,c,v,dd=met(w[1]); print(f"  {lbl:24s} {c:7.2f}%/yr  vol {v:5.1f}%  maxDD {dd:5.1f}%  ({yrs:.1f} yrs)")
dv,pv=wv; dt,pt=wt
ix={x:i for i,x in enumerate(dt)}; common=[x for x in dv if x in ix]
rv=np.diff([pv[dv.index(x)] for x in common]); 
a=np.array([pv[dv.index(x)] for x in common]); b=np.array([pt[ix[x]] for x in common])
ra=np.diff(a)/a[:-1]; rb=np.diff(b)/b[:-1]
print(f"\n  Correlation of EM (VWO) with World (VT) daily returns: {np.corrcoef(ra,rb)[0,1]:+.3f}")
print("  (high correlation = limited diversification benefit from holding EM separately)")
