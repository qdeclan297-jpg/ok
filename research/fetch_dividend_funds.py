import json,urllib.request,urllib.parse,time,os
F={'VWRL.L':'Vanguard All-World DISTRIBUTING (LSE)','VWRP.L':'Vanguard All-World ACCUMULATING (LSE)',
 'VHYL.L':'Vanguard All-World HIGH DIVIDEND YIELD (LSE)',
 'VYM':'Vanguard High Dividend Yield (US)','VIG':'Vanguard Dividend Appreciation (US)',
 'SCHD':'Schwab US Dividend Equity','DGRO':'iShares Core Dividend Growth',
 'NOBL':'ProShares S&P500 Dividend Aristocrats','SDY':'SPDR S&P Dividend',
 'VT':'Vanguard Total World','VTI':'Vanguard Total US','VOO':'Vanguard S&P 500',
 'IUKD.L':'iShares UK Dividend (LSE)','VUKE.L':'Vanguard FTSE 100 (LSE)'}
BASE="https://query1.finance.yahoo.com/v8/finance/chart/"
os.makedirs('div',exist_ok=True); now=int(time.time())
def get(u):
    rq=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(rq,timeout=60))
for t,desc in F.items():
    q=urllib.parse.quote(t); rows={}; cur='?'
    try:
        m=get(f"{BASE}{q}?range=1mo&interval=1d")['chart']['result'][0]['meta']
        first=m.get('firstTradeDate') or 946684800; cur=m.get('currency','?')
    except Exception: print(f"  {t:9s} meta failed"); continue
    p=int(first)
    while p<now:
        nxt=min(p+5*365*86400,now)
        try:
            r=get(f"{BASE}{q}?period1={p}&period2={nxt}&interval=1d")['chart']['result'][0]
            if 'timestamp' in r:
                adj=r.get('indicators',{}).get('adjclose',[{}])[0].get('adjclose')
                use=adj if adj else r['indicators']['quote'][0]['close']
                for ts,v in zip(r['timestamp'],use):
                    if v is not None: rows[time.strftime('%Y-%m-%d',time.gmtime(ts))]=v
        except Exception: pass
        p=nxt; time.sleep(0.2)
    if len(rows)<250: print(f"  {t:9s} too few ({len(rows)})"); continue
    srt=sorted(rows.items())
    with open(f"div/{t.replace('.','_')}.csv",'w') as f:
        f.write('Date,AdjClose\n')
        for d,c in srt: f.write(f'{d},{c}\n')
    print(f"  {t:9s} {cur:3s} {len(srt):5d} rows {srt[0][0]} .. {srt[-1][0]}  {desc}")
