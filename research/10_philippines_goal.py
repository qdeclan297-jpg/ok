"""How big a pot do you need to live in the Philippines, and when do you get there?
Age 26, UK, GBP300/month. All figures in TODAY'S money (real terms)."""
GBPUSD=1.27
def years_to(target,monthly,real_rate,index=True,start=0.0):
    b=start; r=(1+real_rate)**(1/12)-1; m=0
    while b<target and m<12*80:
        b=b*(1+r)+monthly; m+=1
    return m/12 if b>=target else None
def fv(monthly,real_rate,years,start=0.0):
    b=start; r=(1+real_rate)**(1/12)-1
    for _ in range(int(years*12)): b=b*(1+r)+monthly
    return b

print("="*92); print("1. WHAT IT COSTS TO LIVE THERE (2026 expat budgets)"); print("="*92)
LS=[("Lean, provincial (Bacolod/Dumaguete)",1000),
    ("Comfortable, Cebu",1500),
    ("Comfortable, Manila (Makati/BGC)",2200),
    ("Premium, Manila",3000)]
print(f"  {'lifestyle':38s} {'USD/mo':>8s} {'GBP/mo':>8s} {'GBP/yr':>9s}")
for n,u in LS: print(f"  {n:38s} {u:8,} {u/GBPUSD:8,.0f} {u*12/GBPUSD:9,.0f}")

print("\n"+"="*92); print("2. THE POT YOU NEED (safe withdrawal rate, today's money)"); print("="*92)
print("  A 4% withdrawal rate is the classic rule for a ~30yr retirement.")
print("  Retiring early means a 40-50yr horizon, so 3.5% or 3% is the safer planning number.\n")
print(f"  {'lifestyle':38s} {'GBP/yr':>9s} | {'@4%':>10s} {'@3.5%':>10s} {'@3%':>10s}")
for n,u in LS:
    y=u*12/GBPUSD
    print(f"  {n:38s} {y:9,.0f} | {y/0.04:10,.0f} {y/0.035:10,.0f} {y/0.03:10,.0f}")

print("\n"+"="*92); print("3. WHEN £300/MONTH GETS YOU THERE (indexed to inflation, 5% real)"); print("="*92)
print(f"  {'target pot':>12s} {'at 5% real':>14s} {'at 6.6% real':>14s}")
for lbl,tgt in [("£271,000  (lean, 3.5%)",271000),("£355,000  (Cebu, 4%)",355000),
                ("£406,000  (Cebu, 3.5%)",406000),("£475,000  (Cebu, 3%)",475000)]:
    a=years_to(tgt,300,0.05); b=years_to(tgt,300,0.066)
    aa=f"age {26+a:.0f}" if a else "never"; bb=f"age {26+b:.0f}" if b else "never"
    print(f"  {lbl:28s} {aa:>14s} {bb:>14s}")

print("\n"+"="*92); print("4. WHAT IF YOU CAN RAISE THE CONTRIBUTION?"); print("="*92)
print("  You are 26. Earnings usually rise a lot between 26 and 40.")
print(f"  {'monthly':>9s} | " + " | ".join(f"{t:>18s}" for t in ['£271k (lean)','£355k (Cebu 4%)','£406k (Cebu 3.5%)']))
for m in [300,400,500,750,1000,1500]:
    out=[]
    for tgt in [271000,355000,406000]:
        y=years_to(tgt,m,0.05)
        out.append(f"age {26+y:.0f}" if y else "never")
    print(f"  £{m:8,} | " + " | ".join(f"{o:>18s}" for o in out))

print("\n"+"="*92); print("5. THE VISA CONSTRAINT"); print("="*92)
print("  SRRV (retiree visa) minimum age is now 40, deposit from USD 1,500 (refundable).")
print("  So the earliest the retiree route opens to you is age 40 -- 14 years away.")
print(f"  At £300/mo indexed, 5% real, by age 40 you'd have £{fv(300,0.05,14):,.0f} (today's money)")
print(f"  which supports £{fv(300,0.05,14)*0.035:,.0f}/yr at 3.5%  = ${fv(300,0.05,14)*0.035*GBPUSD/12:,.0f}/month.")
print(f"  At £750/mo:  £{fv(750,0.05,14):,.0f} -> ${fv(750,0.05,14)*0.035*GBPUSD/12:,.0f}/month")
print(f"  At £1,000/mo: £{fv(1000,0.05,14):,.0f} -> ${fv(1000,0.05,14)*0.035*GBPUSD/12:,.0f}/month")

print("\n"+"="*92); print("6. THE DIVIDEND TILT, COSTED AGAINST YOUR GOAL"); print("="*92)
print("  High-dividend All-World returned 9.23%/yr vs 11.23%/yr for plain All-World")
print("  over 13.3 years -- a 2.00 point/yr gap.\n")
for m in [300,750]:
    a=years_to(355000,m,0.05); b=years_to(355000,m,0.03)
    print(f"  £{m}/mo to a £355,000 pot: at 5% real age {26+a:.0f}, at 3% real "
          f"age {26+b:.0f} -- {b-a:.0f} years later")
print("\n  A 2-point drag doesn't just cost you money, it costs you YEARS in the Philippines.")
