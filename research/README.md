# Research scripts

These reproduce every number quoted in `docs/RESEARCH.md`. They mirror the
C# logic in `src/CarryTrendFx.cs` so the backtest and the live bot agree.

## Data (free, no API key)

```bash
# EUR/USD and 40+ other pairs, daily, 1999-present (ECB reference rates)
curl -O https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip
unzip eurofxref-hist.zip

# Policy rates, for the carry leg
curl -o DFF.csv    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF"
curl -o ECBDFR.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=ECBDFR"
```

```bash
# Multi-asset: 22 indices, metals, energy, ags, bonds and crypto from Yahoo
pip install numpy
python3 fetch_data.py          # writes yf/*.csv
```

## Run

```bash
python3 01_eurusd_trend.py    # EUR/USD trend: scaling, turnover, buffer sweep, cost sweep
python3 02_trend_vs_carry.py  # trend vs carry vs blend, with carry accrual in P&L
python3 03_multi_pair.py      # does diversifying across 17 FX pairs rescue it?
python3 04_multi_asset.py     # 31 instruments: direction, financing, vs buy-and-hold

python3 fetch_vanguard.py     # writes vg/*.csv (Vanguard fund total returns)
python3 05_index_funds.py     # Vanguard funds vs 4%: the rolling-window reliability table

python3 fetch_em.py           # EM equity + global bond ETFs -> em/*.csv
python3 fetch_gdp.py          # World Bank real GDP growth -> wb/gdp.json
python3 06_emerging_markets.py  # does fast GDP growth pay investors? (it doesn't)

python3 07_uk_300_per_month.py  # UK: what £300/mo becomes; ISA/LISA/pension maths
```

`07` needs no data download -- it is pure projection arithmetic.

`04_multi_asset.py` is the one that answers "what beats 4%". It needs both the
ECB file and `yf/`.

## Compile-checking the cBot without cTrader

`calgo_stub.cs` is a minimal stub of the cAlgo API surface (signatures taken
from help.ctrader.com). It is not a runtime implementation -- it exists so the
bot can be type-checked on a machine with no cTrader install:

```bash
apt-get install -y mono-mcs
mcs -target:library -out:calgo_stub.dll calgo_stub.cs
mcs -target:library -r:calgo_stub.dll -out:bot.dll ../src/CarryTrendFx.cs
```

## Caveats

- ECB rates are daily reference fixings, not tradeable bid/ask closes, and the
  derived crosses in `03_multi_pair.py` compound two fixings.
- Yahoo's futures series (`GC=F`, `CL=F`, `ZN=F` …) are front-month splices.
  Roll gaps show up as returns that were not tradeable, so commodity and bond
  results are noisier than the index results, which are clean.
- Yahoo silently downgrades to monthly bars on `range=max`; `fetch_data.py`
  requests bounded windows to keep daily granularity.
- Financing is modelled as a constant per-class markup matching the cBot's
  `AnnualHoldingCostFraction()`. Real rates track the overnight benchmark.

These scripts establish whether an edge exists at all. They are not a
substitute for a cTrader backtest on broker tick data.
