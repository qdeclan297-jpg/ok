"""Everything in REAL (inflation-adjusted) terms. Age 26, UK, £300/month."""
import csv,numpy as np

# --- verify the long-run real equity return from actual data ---
def load_fred(fn,col):
    out={}
    for r in csv.DictReader(open(fn)):
        v=r[col].strip()
        if v not in ('','.'):
            try: out[r['observation_date'].strip()]=float(v)
            except ValueError: pass
    return out
cpi=load_fred('CPIAUCSL.csv','CPIAUCSL')
sp={}
for r in csv.DictReader(open('vg/^GSPC.csv')):
    try: sp[r['Date']]=float(r['AdjClose'])
    except: pass
ks=sorted(sp); kc=sorted(cpi)
def cpi_at(d):
    prev=None
    for k in kc:
        if k<=d[:8]+'01': prev=k
        else: break
    return cpi[prev] if prev else None
# CPI starts 1947, S&P data starts 1927 -- restrict to the overlap
ks=[k for k in ks if k>=kc[0]]
d0,d1=ks[0],ks[-1]
c0,c1=cpi_at(d0),cpi_at(d1)
yrs=(int(d1[:4])-int(d0[:4]))+(int(d1[5:7])-int(d0[5:7]))/12
nom=(sp[d1]/sp[d0])**(1/yrs)-1
infl=(c1/c0)**(1/yrs)-1
real_price=(1+nom)/(1+infl)-1
print("="*88)
print(f"SANITY CHECK: S&P 500 {d0} to {d1} ({yrs:.1f} yrs)")
print("="*88)
print(f"  nominal price return   {nom*100:6.2f}%/yr")
print(f"  US inflation           {infl*100:6.2f}%/yr")
print(f"  REAL price return      {real_price*100:6.2f}%/yr")
print(f"  + ~2%/yr dividends  ->  REAL total return ~{(real_price+0.02)*100:.1f}%/yr")
print(f"  UBS/DMS Yearbook 2026 (126 yrs, 35 markets): equities 6.6% real, bonds 1.6% real")

# --- real projections ---
M=300.0
def fv_real(monthly,real_rate,years,index_contribs=False):
    """Value in TODAY'S money. If index_contribs, contributions rise with inflation
    (i.e. stay constant in real terms) -- otherwise they erode."""
    b=0.0; r=(1+real_rate)**(1/12)-1
    for m in range(int(years*12)):
        c=monthly if index_contribs else monthly/((1+INFL)**(m/12))
        b=b*(1+r)+c
    return b

INFL=0.03
print("\n"+"="*88)
print("£300/MONTH IN TODAY'S MONEY  (3% inflation assumed)")
print("="*88)
print("  A) contributions stay £300 forever (their real value shrinks)")
print("  B) contributions rise with inflation (£300 in today's money every month)")
print(f"\n  {'yrs':>4s} {'paid in(A)':>11s} | {'A @1% real':>11s} {'A @5% real':>11s} {'A @6.6% real':>13s} | {'B @5% real':>11s} {'B @6.6% real':>13s}")
for y in [10,20,30,34,39]:
    paid=M*12*y
    a1=fv_real(M,0.01,y); a5=fv_real(M,0.05,y); a66=fv_real(M,0.066,y)
    b5=fv_real(M,0.05,y,True); b66=fv_real(M,0.066,y,True)
    print(f"  {y:4d} {paid:11,.0f} | {a1:11,.0f} {a5:11,.0f} {a66:13,.0f} | {b5:11,.0f} {b66:13,.0f}")
print("\n  1% real ~ your savings account (4.1% minus ~3.1% UK inflation)")
print("  5-6.6% real ~ global equities, long run")
print("  You are 26: age 60 is 34 years away, age 65 is 39.")

# --- what my earlier nominal number really meant ---
nom30=0.0; r=(1.08)**(1/12)-1
for _ in range(360): nom30=nom30*(1+r)+300
print("\n"+"="*88); print("THE CORRECTION TO WHAT I TOLD YOU EARLIER"); print("="*88)
print(f"  I said: £300/mo at 8% for 30 years = £{nom30:,.0f}")
for i in [0.02,0.03,0.04]:
    print(f"    at {i*100:.0f}% inflation that buys what £{nom30/((1+i)**30):,.0f} buys today")
print("  The pound figure was right. Its purchasing power is roughly half what it looks like.")

# --- cash vs equities in real terms: the real point ---
print("\n"+"="*88); print("WHY INFLATION STRENGTHENS THE CASE FOR EQUITIES"); print("="*88)
print(f"  {'':28s} {'nominal':>9s} {'inflation':>10s} {'REAL':>8s}")
for lbl,n,i in [("Savings account (today)",4.10,3.10),
                ("Savings (long-run avg cash)",None,None),
                ("UK bonds/gilts long run",None,None),
                ("Global equities long run",None,None)]:
    if n is None: continue
    print(f"  {lbl:28s} {n:8.2f}% {i:9.2f}% {n-i:7.2f}%")
print(f"  {'Cash/bills, 1900-2025':28s} {'':>9s} {'':>10s} {'~0.5-0.9%':>8s}   (UBS/DMS)")
print(f"  {'Bonds, 1900-2025':28s} {'':>9s} {'':>10s} {'1.6%':>8s}   (UBS/DMS)")
print(f"  {'Equities, 1900-2025':28s} {'':>9s} {'':>10s} {'6.6%':>8s}   (UBS/DMS)")
print("\n  Over 34 years to age 60, £1 becomes, in today's money:")
for lbl,rr in [("cash at 0.9% real",0.009),("your 4.1% savings at 1.0% real",0.010),
               ("bonds at 1.6% real",0.016),("equities at 6.6% real",0.066)]:
    print(f"    {lbl:34s} £{(1+rr)**34:6.2f}")

# --- LISA in real terms, age 26 ---
print("\n"+"="*88); print("LISA AT 26 -- the bonus is inflation-proof"); print("="*88)
print("  You can contribute until 50: that's 24 more years x up to £1,000/yr bonus.")
print("  At £300/mo (£3,600/yr) you'd collect £900/yr -> £21,600 of free money by 50.")
for y,lbl in [(34,"to age 60")]:
    isa=fv_real(300,0.05,y,True); lisa_yrs=24
    # LISA: £375/mo effective for 24 yrs, then grows; ISA-equivalent after
    b=0.0; r=(1.05)**(1/12)-1
    for m in range(y*12):
        c=375.0 if m<lisa_yrs*12 else 300.0
        b=b*(1+r)+c
    print(f"\n  {lbl} at 5% real, contributions held constant in today's money:")
    print(f"    plain S&S ISA   £{isa:,.0f}")
    print(f"    LISA (25% bonus to 50, then ISA)  £{b:,.0f}")
    print(f"    difference      £{b-isa:,.0f}  in today's money")
