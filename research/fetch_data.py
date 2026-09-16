"""Download the multi-asset daily history used by 04_multi_asset.py.

Yahoo silently downgrades to monthly bars on range=max, so this requests
bounded windows to keep 1d granularity, and starts each instrument at its
own firstTradeDate (earlier windows return HTTP 400).
"""
import json, urllib.request, urllib.parse, time, os

UNIVERSE = {
    '^GSPC':'US500', '^NDX':'NAS100', '^DJI':'US30', '^GDAXI':'GER40',
    '^FTSE':'UK100', '^N225':'JP225', '^AXJO':'AUS200', '^STOXX50E':'EU50',
    '^HSI':'HK50', 'GC=F':'XAUUSD', 'SI=F':'XAGUSD', 'HG=F':'COPPER',
    'CL=F':'WTI', 'BZ=F':'BRENT', 'NG=F':'NATGAS', 'ZN=F':'UST10Y',
    'ZB=F':'UST30Y', 'BTC-USD':'BTCUSD', 'ETH-USD':'ETHUSD',
    'ZC=F':'CORN', 'ZW=F':'WHEAT', 'ZS=F':'SOYBEAN',
}
BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"
EARLIEST = 473385600   # 1985-01-01

def get(url):
    rq = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(rq, timeout=60))

def main():
    os.makedirs('yf', exist_ok=True)
    now = int(time.time())

    for ticker, name in UNIVERSE.items():
        q = urllib.parse.quote(ticker)
        try:
            meta = get(f"{BASE}{q}?range=1mo&interval=1d")
            first = meta['chart']['result'][0]['meta'].get('firstTradeDate') or EARLIEST
        except Exception as e:
            print(f"  {name:9s} metadata failed: {e}")
            continue

        rows = {}
        p = max(int(first), EARLIEST)
        while p < now:
            nxt = min(p + 5 * 365 * 86400, now)
            try:
                r = get(f"{BASE}{q}?period1={p}&period2={nxt}&interval=1d")['chart']['result'][0]
                if 'timestamp' in r:
                    for ts, close in zip(r['timestamp'], r['indicators']['quote'][0]['close']):
                        if close is not None:
                            rows[time.strftime('%Y-%m-%d', time.gmtime(ts))] = close
            except Exception:
                pass          # windows before listing return 400; skip them
            p = nxt
            time.sleep(0.25)

        if len(rows) < 500:
            print(f"  {name:9s} too few rows ({len(rows)})")
            continue

        srt = sorted(rows.items())
        with open(f'yf/{name}.csv', 'w') as f:
            f.write('Date,Close\n')
            for d, c in srt:
                f.write(f'{d},{c}\n')
        print(f"  {name:9s} {len(srt):6d} rows  {srt[0][0]} .. {srt[-1][0]}")

if __name__ == '__main__':
    main()
