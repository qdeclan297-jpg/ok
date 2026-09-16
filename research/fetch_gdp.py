"""Download real GDP growth by country from the World Bank API (no key needed)."""
import json,urllib.request,csv,os,numpy as np
CTRY={'EPHE':('PHL','Philippines'),'EIDO':('IDN','Indonesia'),'INDA':('IND','India'),
 'MCHI':('CHN','China'),'EWY':('KOR','South Korea'),'THD':('THA','Thailand'),
 'EWM':('MYS','Malaysia'),'VNM':('VNM','Vietnam'),'EWZ':('BRA','Brazil'),
 'EZA':('ZAF','South Africa'),'EWT':('TWN','Taiwan'),'TUR':('TUR','Turkey'),
 'EWW':('MEX','Mexico'),'VOO':('USA','United States')}
os.makedirs('wb',exist_ok=True)
def gdp(iso):
    u=(f"https://api.worldbank.org/v2/country/{iso}/indicator/NY.GDP.MKTP.KD.ZG"
       f"?format=json&per_page=200")
    rq=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
    d=json.load(urllib.request.urlopen(rq,timeout=60))
    if len(d)<2 or not d[1]: return {}
    return {int(r['date']):r['value'] for r in d[1] if r['value'] is not None}
G={}
for t,(iso,name) in CTRY.items():
    try:
        g=gdp(iso)
        if g: G[t]=g; print(f"  {name:15s} {len(g)} years of GDP data, latest {max(g)}: {g[max(g)]:.2f}%")
        else: print(f"  {name:15s} no World Bank data (Taiwan is not a WB member)")
    except Exception as e: print(f"  {name:15s} failed {e}")
json.dump({k:{str(a):b for a,b in v.items()} for k,v in G.items()},open('wb/gdp.json','w'))
