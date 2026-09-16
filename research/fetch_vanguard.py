"""Download Vanguard fund total-return history (adjusted closes) from Yahoo.

Writes vg/*.csv for research/05_index_funds.py. Adjusted closes reinvest
dividends, so these are total returns, not price returns.
"""
import json,urllib.request,urllib.parse,time,os
FUNDS={'VOO':'Vanguard S&P 500 (US)','VTI':'Vanguard Total US Stock (US)',
 'VT':'Vanguard Total World (US)','VXUS':'Vanguard Total Intl ex-US (US)',
 'BND':'Vanguard Total Bond (US)','VWCE.DE':'Vanguard FTSE All-World UCITS acc (IE)',
 'VUAA.DE':'Vanguard S&P500 UCITS acc (IE)','VWRL.AS':'Vanguard All-World UCITS dist (IE)',
 'VAS.AX':'Vanguard Australian Shares (AU)','VGS.AX':'Vanguard Intl Shares (AU)',
 'VDHG.AX':'Vanguard Diversified High Growth (AU)','^GSPC':'S&P 500 index (reference)'}
BASE="https://query1.finance.yahoo.com/v8/finance/chart/"
os.makedirs('vg',exist_ok=True); now=int(time.time())
def get(u):
    rq=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(rq,timeout=60))
for t,desc in FUNDS.items():
    q=urllib.parse.quote(t); rows={}
    try:
        m=get(f"{BASE}{q}?range=1mo&interval=1d")['chart']['result'][0]['meta']
        first=m.get('firstTradeDate') or 946684800; cur=m.get('currency','?')
    except Exception as e:
        print(f"  {t:9s} meta failed {e}"); continue
    p=int(first)
    while p<now:
        nxt=min(p+5*365*86400,now)
        try:
            r=get(f"{BASE}{q}?period1={p}&period2={nxt}&interval=1d&events=div")['chart']['result'][0]
            if 'timestamp' in r:
                adj=r.get('indicators',{}).get('adjclose',[{}])[0].get('adjclose')
                cl=r['indicators']['quote'][0]['close']
                use=adj if adj else cl
                for ts,v in zip(r['timestamp'],use):
                    if v is not None: rows[time.strftime('%Y-%m-%d',time.gmtime(ts))]=v
        except Exception: pass
        p=nxt; time.sleep(0.2)
    if len(rows)<250: print(f"  {t:9s} too few ({len(rows)})"); continue
    srt=sorted(rows.items())
    with open(f'vg/{t}.csv','w') as f:
        f.write('Date,AdjClose\n')
        for d,c in srt: f.write(f'{d},{c}\n')
    print(f"  {t:9s} {cur:3s} {len(srt):5d} rows  {srt[0][0]} .. {srt[-1][0]}  {desc}")
