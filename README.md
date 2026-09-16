# CarryTrendFx — a cost-aware EUR/USD cBot for cTrader

A volatility-targeted trend + carry cBot for cTrader Automate, built for the
IC Markets Raw cost structure ($6/lot round turn, 0.0–0.1 pip spreads).

**Two things to know before you read further.**

**1. cTrader bots are written in C#, not C.** The platform (cTrader Automate,
formerly cAlgo) runs .NET. `src/CarryTrendFx.cs` is a `.cs` file you paste
into cTrader's code editor. There is no C option.

**2. One configuration beats 4%, and it isn't EUR/USD.** Tested across 31
instruments and 41 years:

| Configuration | Return | Vol | Max DD | vs 4% |
|---|---|---|---|---|
| EUR/USD trend (the original) | 1.89%/yr | 10% | 25.7% | loses |
| Multi-asset long/short | 3.70%/yr | 10% | 43.5% | loses |
| **Multi-asset, no FX, LONG ONLY** | **6.41%/yr** | 10% | 33.4% | **beats** |
| Just owning the same assets | 8.42%/yr | 10% | 33.4% | beats |

So: run it **long-only across many non-FX instruments** and it clears your
hurdle. But buy-and-hold beat it in every period I tested, by roughly the
1.9%/yr that CFD financing costs. The full evidence is in
**[docs/RESEARCH.md](docs/RESEARCH.md)** — read it before risking money.

---

## The findings that matter

**1. Your cheap commissions are real, and they are not the problem.** At this
bot's turnover, FX transaction costs came to 0.024% of capital per year.
Raising the assumed round-turn cost from 0.8 to 6.0 pips changed net return by
0.16%/yr. Commission is a rounding error at this speed. What kills retail bots
is *turnover*: a scalper doing 5 round turns a day on a $25k account burns
~12% of capital per year. This bot decides once a day and holds ~7 weeks.

**2. Outside FX, financing is the whole game.** IC Markets finances cash index
CFDs at the overnight benchmark **+250bp on longs and −250bp on shorts** — you
pay the 2.5% markup in either direction, and it never appears in your trade
list. On a vol-targeted book that is ~1.9%/yr off the top:

| Financing assumption | Net return | Sharpe |
|---|---|---|
| Zero (fantasy) | 8.30%/yr | 0.83 |
| **IC Markets, ±250bp** | **6.41%/yr** | **0.64** |
| ETF-like, ~0.1%/yr | 8.23%/yr | 0.82 |

The bot models this per asset class, warns at startup, and reports accrued
financing separately from commission when it stops.

**3. Direction matters more than instrument choice.** Across 22 non-FX
instruments: long-only 6.41%/yr (Sharpe 0.64), long/short 3.70% (0.37),
short-only **−6.49%**. These assets drift up; shorting fights the risk
premium and pays financing to do it.

---

## What's in here

```
src/CarryTrendFx.cs     the cBot (compiles clean, ~1,160 lines, commented)
docs/RESEARCH.md        Part 1: FX. Part 2: 31 instruments, 41 years
docs/INDEX_FUNDS.md     Part 3: Vanguard funds -- what actually beat 4%
docs/EMERGING_MARKETS.md Part 4: emerging markets, growth stories, bonds
docs/UK_300_A_MONTH.md  Part 5: UK, £300/month -- the practical answer
docs/PHILIPPINES_PLAN.md Part 6: dividends, and the Philippines goal
research/01..03         EUR/USD and multi-pair FX studies
research/04             multi-asset study; fetch_data.py downloads the data
research/05             Vanguard index funds; fetch_vanguard.py downloads the data
research/06             emerging markets vs GDP growth; EM and global bonds
research/07             UK £300/month projections: wrappers, platforms, fees
research/08             the same in real terms; validates 6.6%/yr real equities
research/09             dividend funds vs broad market; acc vs dist
research/10             Philippines: pot needed, when £300/mo gets there
```

> **Read [docs/INDEX_FUNDS.md](docs/INDEX_FUNDS.md) before this one.** Across all
> three studies, a plain global index fund beat the bot on every measure. The bot
> is here because it is good engineering and you asked for it, not because it won.

## How it works

- **Signal** — EWMAC trend at three speeds (16/64, 32/128, 64/256-day EMA
  pairs), each divided by price volatility, scaled so the average absolute
  forecast is 10, capped at ±20, then blended. Three speeds rather than one
  tuned lookback, because a single tuned lookback is how you overfit a
  backtest. Optionally blended with a carry forecast built from the broker's
  own posted swap rates.
- **Sizing** — volatility targeting. Position size is inversely proportional
  to realised volatility, so risk stays near constant instead of ballooning
  when EUR/USD gets wild. Verified: mean absolute forecast measured 9.62 on
  real data against a design target of 10.0.
- **Turnover control** — a no-trade buffer around the target position. Inside
  the band, nothing happens. Outside it, the bot trades back to the *edge* of
  the band, never to the exact target.
- **Risk** — realised-vol governor, drawdown kill switch, daily loss limit,
  hard leverage cap, spread guard, rollover blackout.

### The realised-vol governor

This one came out of testing rather than theory. Volatility targeting sizes
from the *instrument's* volatility, but when the forecast sits near its cap
for months, realised risk drifts above target anyway — I measured 11.7%
against a 10% target, and 15.4% in a strongly trending synthetic series.

The governor tracks the strategy's own realised equity volatility and scales
the book down when it runs hot. It only ever scales down. On EUR/USD history
it brought realised vol from 11.7% to 9.98% and cut max drawdown from 35.3%
to 25.7%, for 0.06%/yr of return. On by default.

## Installing

1. cTrader → **Automate** → **New cBot**
2. Paste `src/CarryTrendFx.cs` over the template
3. Build (F6)
4. Attach to a chart — any instrument, any timeframe; decisions are made off
   the daily series regardless. **Set `Asset class` to match the instrument**;
   it drives the financing model and the startup warnings
5. Scroll the daily chart back far enough to load **300+ daily bars**, or the
   256-day EMA has nothing to work with. The bot warns you if history is short.
6. **Run on demo first.** Set `Dry run` = true to watch it decide without
   sending orders.

## Key parameters

| Parameter | Default | Notes |
|---|---|---|
| Target volatility %/yr | 10.0 | Your actual risk dial. 10% ≈ 20–26% worst-case drawdown |
| Instrument weight | 1.0 | Set to 1/N if you run it on N pairs |
| Realised-vol governor | on | Scales down when realised risk runs hot |
| Kill switch drawdown % | 20.0 | Flattens and halts |
| Daily loss limit % | 4.0 | Flattens for the day |
| Max gross leverage | 5.0 | Hard notional cap |
| Asset class | Fx | Drives financing model + warnings. **Set this** |
| Allow short positions | true | **Set false for non-FX** — see finding 3 |
| Annual holding cost % | 0 (auto) | Override the per-class financing estimate |
| Diversification multiplier | 1.0 | Raise when running many instruments |
| Trend / carry weight | 0.75 / 0.25 | Carry is ignored outside FX (there it's just financing) |
| No-trade buffer | 0.15 | Wider = less turnover. 0.15–0.40 all tested fine |
| Max spread to trade | 1.0 pips | Skips the trade if the spread is wider |
| Commission per lot RT | 6.0 | Your IC Markets Raw rate |
| Use ATR stop loss | **off** | See below |
| Dry run | off | Log decisions, send no orders |

### Why stops are off by default

In a continuous-forecast system the forecast *is* the exit — as a trend
decays the forecast shrinks and the bot trims the position automatically. A
hard stop that fires independently leaves your book out of line with the
signal until the next daily rebalance, and on a 10%-vol system a stop tight
enough to matter gets hit by noise.

Capital protection here comes from the drawdown kill switch and the vol
governor, which act on the portfolio. The ATR stop is available
(`Use ATR stop loss`) if you want it — it's a wide, ratcheting 6×ATR stop that
never loosens.

## Verifying it

The bot compiles clean with zero warnings. You can type-check it without
cTrader installed, using the API stub in `research/`:

```bash
apt-get install -y mono-mcs
cd research
mcs -target:library -out:calgo_stub.dll calgo_stub.cs
mcs -target:library -r:calgo_stub.dll -out:bot.dll ../src/CarryTrendFx.cs
```

To reproduce the backtests, see [research/README.md](research/README.md).

## Running it multi-instrument

This is the configuration that cleared 4%. Attach the bot to several charts:

- Set **`Asset class`** per instrument (Index for US500/NAS100/GER40, Metal for
  XAUUSD/XAGUSD, Energy for WTI, and so on).
- Set **`Allow short positions` = false** on everything except FX.
- Set **`Instrument weight` = 1/N** across N charts, so the combined book still
  targets your chosen volatility rather than N times it.
- Raise **`Diversification multiplier`** if the combined book runs under
  target — with uncorrelated instruments, 1/N weighting under-risks you.

A reasonable starting universe from the tested set: US500, NAS100, GER40,
JP225, XAUUSD, XAGUSD, COPPER, WTI — eight instruments, weight 0.125 each,
long-only.

## Known limitations

- **The long-only result is mostly beta, not alpha.** It is the risk premium of
  the underlying assets captured through an expensive wrapper. Buy-and-hold beat
  it in every period tested. What the trend filter genuinely buys is smaller
  equity drawdowns (37.2% vs 53.1% on indices), not more return.
- **Indices-only degraded badly out of sample**: 5.89%/yr in 1985–2012 versus
  1.82%/yr in 2013–2026, while buy-and-hold held near 6.3%.
- **FX is the worst asset class tested** — negative mean Sharpe across 9 pairs.
  The EUR/USD config is kept for reference, not as a recommendation.
- **Commodity and bond backtests use Yahoo front-month splices**, whose roll
  gaps appear as returns that were not tradeable. Index results are clean;
  treat commodity numbers as noisier.
- **Backtested on ECB reference fixings**, which are daily reference rates,
  not tradeable bid/ask closes. Re-run it in cTrader's backtester on IC
  Markets tick data before drawing conclusions.
- **The carry leg depends on your broker's swap quoting convention.**
  `Symbol.SwapLong`/`SwapShort` interpretation varies by server configuration;
  verify the sign and magnitude in the log before trusting it, or set carry
  weight to 0.
- **Single instrument.** The `Instrument weight` parameter exists so you can
  run it across several pairs, but my testing says that doesn't help for FX.
- **No news filter.** `AccessRights.None` means no internet access, so there's
  a configurable time-of-day blackout but nothing event-driven.
- **Not tested against a live broker.** No live or demo run has happened.

## Risk

Retail CFD loss rates run 74–89% under ESMA-mandated disclosure. Leverage
scales losses as readily as gains. This code is provided as engineering work,
not financial advice — I have no idea what your circumstances are, and a
26% drawdown means different things to different people. Run it on demo,
size it so a total loss doesn't hurt, and read
[docs/RESEARCH.md](docs/RESEARCH.md) first.
