"""What £300/month actually becomes, and what the wrapper is worth."""
M=300.0
def fv(monthly,rate,years,start=0.0):
    b=start; r=(1+rate)**(1/12)-1
    for _ in range(int(years*12)): b=b*(1+r)+monthly
    return b

print("="*86)
print("£300/MONTH -- what it becomes (net return after fund fees)")
print("="*86)
print(f"  {'years':>5s} {'paid in':>10s} | " + " | ".join(f"{r:>10}" for r in ['4%/yr','6%/yr','8%/yr','10%/yr']))
for y in [5,10,15,20,25,30,35]:
    paid=M*12*y
    vals=[fv(M,r,y) for r in (0.04,0.06,0.08,0.10)]
    print(f"  {y:5d} {paid:10,.0f} | " + " | ".join(f"{v:10,.0f}" for v in vals))
print("\n  4% = your savings account. 8% = roughly what global equities have done")
print("  long run. The gap at 30 years is the entire argument for investing.")

print("\n"+"="*86); print("WHAT THE PLATFORM FEE COSTS YOU (£300/mo, 8%/yr, 30 years)"); print("="*86)
base=fv(M,0.08,30)
for lbl,plat_annual,ocf in [("Trading 212 / InvestEngine ISA",0.0,0.0014),
                            ("Vanguard UK ISA (£4/mo under £32k)",48.0,0.0014),
                            ("Typical 0.25% platform",None,0.0014),
                            ("Typical 0.45% platform + 0.22% fund",None,0.0022)]:
    # approximate: subtract percentage drags from the growth rate
    if lbl.startswith("Typical 0.25"): drag=0.0025+ocf
    elif lbl.startswith("Typical 0.45"): drag=0.0045+ocf
    else: drag=ocf
    v=fv(M,0.08-drag,30)
    extra=""
    if plat_annual:
        # flat fee: approximate by reducing monthly contribution
        v=fv(M-plat_annual/12,0.08-drag,30); extra=f" (flat £{plat_annual:.0f}/yr)"
    print(f"  {lbl:38s} £{v:10,.0f}{extra}")
print(f"\n  Spread between best and worst: £{fv(M,0.08-0.0014,30)-fv(M,0.08-0.0067,30):,.0f}")

print("\n"+"="*86); print("WHAT THE TAX WRAPPER IS WORTH"); print("="*86)
gross=fv(M,0.08,30); paid=M*12*30; gain=gross-paid
print(f"  30 years at 8%: paid in £{paid:,.0f}, ends at £{gross:,.0f}, gain £{gain:,.0f}")
print(f"  Inside an ISA:            £0 tax on that gain")
print(f"  Outside, CGT at 24%:      up to £{gain*0.24:,.0f} potentially taxable on disposal")
print(f"  -> the ISA wrapper is worth more than any fund choice on this list.")

print("\n"+"="*86); print("LISA: the 25% bonus, if eligible (under 40, first home or age 60+)"); print("="*86)
print(f"  {'years':>5s} {'£300/mo ISA':>14s} {'£300/mo LISA':>14s} {'difference':>12s}")
for y in [10,20,30]:
    isa=fv(300,0.08,y); lisa=fv(375,0.08,y)   # £300 + 25% bonus = £375
    print(f"  {y:5d} {isa:14,.0f} {lisa:14,.0f} {lisa-isa:12,.0f}")
print("  £300/mo = £3,600/yr, under the £4,000 LISA cap, so the full 25% applies.")
print("  That is a guaranteed +25% on every pound, before any market return.")

print("\n"+"="*86); print("PENSION (salary sacrifice), if your employer matches"); print("="*86)
print("  Basic-rate taxpayer: £1 into pension costs you 72p (20% tax + 8% NI saved).")
print("  So £300 of take-home becomes ~£417 in the pension before any employer match.")
for lbl,eff in [("ISA (£300 net = £300 invested)",300.0),
                ("Pension, no match (~£417)",417.0),
                ("Pension, employer matches (~£834)",834.0)]:
    print(f"  {lbl:36s} 30yr @8%: £{fv(eff,0.08,30):,.0f}")
print("  Locked until 57/58, and taxable on the way out beyond the 25% tax-free part.")
