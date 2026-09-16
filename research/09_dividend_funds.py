import csv,glob,os,numpy as np
TD=252.
N={'VWRL_L':'All-World DISTRIBUTING (GBP)','VWRP_L':'All-World ACCUMULATING (GBP)',
 'VHYL_L':'All-World HIGH DIV YIELD (GBP)','VUKE_L':'FTSE 100 (GBP)','IUKD_L':'UK Dividend (GBp)',
 'VYM':'US High Dividend Yield','VIG':'US Dividend Appreciation','SCHD':'Schwab US Dividend',
 'DGRO':'iShares Dividend Growth','NOBL':'S&P Dividend Aristocrats','SDY':'SPDR S&P Dividend',
 'VT':'Total World','VTI':'Total US','VOO':'S&P 500'}
D={}
for f in sorted(glob.glob('div/*.csv')):
    t=os.path.basename(f)[:-4]; d=[];p=[]
    for r in csv.DictReader(open(f)):
        try: v=float(r['AdjClose'])
        except: continue
        if v>0: d.append(r['Date']); p.append(v)
    D[t]=(d,np.array(p))
def met(p):
    r=np.diff(p)/p[:-1]; y=len(r)/TD
    c=(p[-1]/p[0])**(1/y)-1; v=np.std(r)*np.sqrt(TD)
    e=np.cumprod(1+r); dd=float(np.max(1-e/np.maximum.accumulate(e)))
    return y,c*100,v*100,dd*100
def win(t,s):
    d,p=D[t]; i=next((k for k,x in enumerate(d) if x>=s),None)
    return (d[i:],p[i:]) if i is not None and len(p)-i>250 else None

print("="*96)
print("1. ACCUMULATING vs DISTRIBUTING -- same fund, same index (VWRP vs VWRL, GBP)")
print("="*96)
S='2019-07-26'
for t in ['VWRP_L','VWRL_L']:
    w=win(t,S)
    if w: y,c,v,dd=met(w[1]); print(f"  {N[t]:34s} {y:5.1f}y  {c:6.2f}%/yr  vol {v:5.1f}%  maxDD {dd:5.1f}%")
print("  -> Total return is the SAME. The only difference is whether the dividend")
print("     lands in your account as cash or is reinvested inside the fund for you.")

print("\n"+"="*96)
print("2. DO DIVIDEND-FOCUSED FUNDS BEAT THE MARKET? (total return, dividends reinvested)")
print("="*96)
print("  US funds, common window since SCHD launched (2011-10):")
S2='2011-10-21'
rows=[]
for t in ['SCHD','VYM','VIG','DGRO','NOBL','SDY','VTI','VOO','VT']:
    w=win(t,S2)
    if w: y,c,v,dd=met(w[1]); rows.append((N[t],t,c,v,dd))
for n,t,c,v,dd in sorted(rows,key=lambda r:-r[2]):
    mark='  <- broad market' if t in ('VTI','VOO','VT') else ''
    print(f"    {n:32s} {c:6.2f}%/yr  vol {v:5.1f}%  maxDD {dd:5.1f}%{mark}")

print("\n  GBP funds, common window since VHYL launched (2013-05):")
S3='2013-05-22'
rows=[]
for t in ['VHYL_L','VWRL_L','VUKE_L','IUKD_L']:
    w=win(t,S3)
    if w: y,c,v,dd=met(w[1]); rows.append((N[t],t,c,v,dd))
for n,t,c,v,dd in sorted(rows,key=lambda r:-r[2]):
    mark='  <- broad market' if t=='VWRL_L' else ''
    print(f"    {n:32s} {c:6.2f}%/yr  vol {v:5.1f}%  maxDD {dd:5.1f}%{mark}")

print("\n"+"="*96)
print("3. THE COST OF THE DIVIDEND TILT, compounded")
print("="*96)
w1=win('VHYL_L',S3); w2=win('VWRL_L',S3)
y,c1,_,_=met(w1[1]); _,c2,_,_=met(w2[1])
print(f"  High-dividend All-World {c1:.2f}%/yr vs plain All-World {c2:.2f}%/yr over {y:.1f} years")
gap=c2-c1
print(f"  Gap: {gap:+.2f} percentage points per year")
for yrs in [20,34]:
    a=(1+c2/100)**yrs; b=(1+c1/100)**yrs
    print(f"    £10,000 over {yrs} yrs: plain £{a*10000:,.0f} vs high-div £{b*10000:,.0f}"
          f"  (difference £{(a-b)*10000:,.0f})")
