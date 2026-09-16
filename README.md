# CarryTrendFx — a cost-aware EUR/USD cBot for cTrader

A volatility-targeted trend + carry cBot for cTrader Automate, built for the
IC Markets Raw cost structure ($6/lot round turn, 0.0–0.1 pip spreads).

**Two things to know before you read further.**

**1. cTrader bots are written in C#, not C.** The platform (cTrader Automate,
formerly cAlgo) runs .NET. `src/CarryTrendFx.cs` is a `.cs` file you paste
into cTrader's code editor. There is no C option.

**2. I backtested this on 27 years of real EUR/USD data and it did not beat
your bank.** Net 1.89%/yr at 10% volatility with a 26% drawdown, against your
savings account's 4% with no drawdown at all. Diversifying across 17 pairs
made it worse, not better. The full evidence is in
**[docs/RESEARCH.md](docs/RESEARCH.md)** — please read it before risking money.

I built the bot anyway because you asked for it and because the engineering is
sound and reusable. But I'm not going to tell you it clears 4% when my own
testing says otherwise.

---

## The one finding that surprised me

Your cheap commissions are real, and they are **not** what stands between you
and a profitable bot.

At this bot's turnover, all-in costs came to **0.024% of capital per year**.
Raising the assumed round-turn cost from 0.8 pips to 6.0 pips — more than
seven times worse — changed net return by 0.16%/yr. Cost is a rounding error
here.

What kills retail bots is *turnover*, not the per-trade rate. A scalper doing
5 round turns a day on a $25k account burns ~12% of capital per year in
costs. This bot makes one decision a day, holds for about seven weeks, and
uses a no-trade buffer so small signal wobbles never fire an order.

So the design is right. The edge just isn't there on one currency pair.

---

## What's in here

```
src/CarryTrendFx.cs     the cBot (compiles clean; ~900 lines, commented)
docs/RESEARCH.md        the evidence, the numbers, and the honest conclusion
research/               scripts that reproduce every number, free data
```

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
4. Attach to a **EUR/USD** chart — any timeframe, decisions are made off the
   daily series regardless
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
| Trend / carry weight | 0.75 / 0.25 | Carry alone tested at ~zero Sharpe |
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

## Known limitations

- **The measured edge is weak.** Net Sharpe 0.19 over 1999–2026, and negative
  out-of-sample in the multi-pair test. Treat it as a research platform.
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
