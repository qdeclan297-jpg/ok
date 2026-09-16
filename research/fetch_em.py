"""Download EM equity and global bond ETF total-return history from Yahoo."""
import json,urllib.request,urllib.parse,time,os
EM={'VWO':'Vanguard EM equity','EEM':'iShares EM equity','EPHE':'Philippines',
 'EIDO':'Indonesia','INDA':'India','MCHI':'China','EWY':'South Korea','THD':'Thailand',
 'EWM':'Malaysia','VNM':'Vietnam','EWZ':'Brazil','EZA':'South Africa','EWT':'Taiwan',
 'TUR':'Turkey','EWW':'Mexico',
 'EMB':'EM bonds USD (hard ccy)','EMLC':'EM bonds local ccy','VWOB':'Vanguard EM bond USD',
 'BNDX':'Intl bonds USD-hedged','BND':'US total bond','TIP':'US TIPS',
 'VT':'World equity','VOO':'S&P 500','VEA':'Developed ex-US'}
BASE="https://query1.finance.yahoo.com/v8/finance/chart/"
os.makedirs('em',exist_ok=True); now=int(time.time())
def get(u):
    rq=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(rq,timeout=60))
for t,desc in EM.items():
    q=urllib.parse.quote(t); rows={}
    try:
        m=get(f"{BASE}{q}?range=1mo&interval=1d")['chart']['result'][0]['meta']
        first=m.get('firstTradeDate') or 946684800
    except Exception as e:
        print(f"  {t:6s} meta failed"); continue
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
    if len(rows)<250: print(f"  {t:6s} too few ({len(rows)})"); continue
    srt=sorted(rows.items())
    with open(f'em/{t}.csv','w') as f:
        f.write('Date,AdjClose\n')
        for d,c in srt: f.write(f'{d},{c}\n')
    print(f"  {t:6s} {len(srt):5d} rows {srt[0][0]} .. {srt[-1][0]}  {desc}")
