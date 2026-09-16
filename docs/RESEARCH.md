# Can a EUR/USD cBot reliably beat a 4% savings account?

**Short answer: on the evidence I could gather, no.** Not on one pair, and not
on seventeen. This document shows the work, because the negative result is
more valuable to you than the code is.

Everything below is reproducible with the scripts in `research/`, using free
data from the ECB and FRED.

---

## 1. The cost structure is not the problem

This was my starting hypothesis, and it was wrong — worth stating because it
is the thing most retail strategy write-ups get wrong in the other direction.

Your IC Markets Raw cTrader costs on EUR/USD:

| Component | Cost |
|---|---|
| Commission | $3.00/side per 100k, $6.00 round turn per lot |
| Commission in pips | 0.60 pips (1 pip on 100k = $10) |
| Spread | 0.0–0.1 pips peak, ~0.1–0.3 pips 24h average |
| **All-in round turn** | **~0.8 pips ≈ $8 per lot** |

Whether this matters depends entirely on turnover:

| Style | Round turns/yr | Cost as % of a $25k account |
|---|---|---|
| Scalper, 5 round turns/day | ~1,250 | **~12%/yr** |
| This bot (slow trend) | ~7 book turnovers | **0.024%/yr** |

At the turnover this design runs, cost is *negligible* — I measured 0.024% of
capital per year on real data. The cost sensitivity test confirms it: pushing
the round-turn cost from 0.8 pips all the way to 6.0 pips moved net return by
only 0.16%/yr and Sharpe from 0.19 to 0.17.

**So the cheap commissions are real, and they are not the bottleneck.** The
bottleneck is that the edge isn't there.

---

## 2. What I tested

A properly built systematic strategy, not a toy:

- **Signal:** EWMAC trend at three speeds (16/64, 32/128, 64/256-day EMA
  pairs), each risk-normalised and capped, blended. Multi-speed blending is
  the standard institutional defence against picking one lucky lookback.
- **Sizing:** volatility targeting to a constant 10%/yr risk.
- **Turnover control:** a no-trade buffer, so small forecast wobbles never
  generate an order.
- **Carry:** rate differential between the ECB deposit rate and Fed funds,
  risk-normalised the same way.
- **Data:** ECB daily EUR/USD reference rates, 1999-01-04 to 2026-09-15 —
  7,093 observations, 26.9 years, covering the dot-com bust, 2008, the euro
  crisis, ZIRP, COVID, and the 2022–24 hiking cycle.

### Sanity checks that passed

The forecast scaling is correct: mean absolute forecast came out at **10.07**
on a synthetic random walk and **9.62** on real EUR/USD, against a design
target of 10.0, with 8.3% of observations at the cap. The machinery works.

---

## 3. The results

### EUR/USD, trend only, 1999–2026

| Metric | Value |
|---|---|
| Realised volatility | 9.98%/yr (target 10%) |
| Gross return | 1.91%/yr |
| Cost drag | 0.024%/yr |
| **Net return** | **1.89%/yr** |
| **Net Sharpe** | **0.19** |
| Max drawdown | 25.7% |
| Turnover | 7.3× book/yr (~7 week average hold) |

**1.89% per year, with a 26% drawdown, against your bank's 4% with none.**

### Does carry help?

Right now short EUR/USD earns positive carry — ECB deposit rate 2.25% vs Fed
funds 3.63%, so **long EUR/USD carries −1.38%/yr** and the short side earns
it. That is a real, bankable number. But as a *strategy* it does not work:

| Strategy | Vol | Net/yr | Sharpe | Max DD |
|---|---|---|---|---|
| Trend only | 9.98% | 1.82% | 0.18 | 27.7% |
| Carry only | 5.31% | −0.05% | −0.01 | 43.4% |
| Blend 75/25 | 8.15% | 1.40% | 0.17 | 23.5% |
| Blend 50/50 | 6.12% | 0.92% | 0.15 | 22.0% |

And the blend is not robust across time — the 50/50 blend scores Sharpe 0.04
in 1999–2012 and 0.28 in 2013–2026. That instability is the signature of a
result you cannot lean on.

The intuition on carry is worth stating plainly: to harvest ~1.4%/yr you take
on the full ~8%/yr volatility of EUR/USD spot. You are risking 8 to earn 1.4,
before the broker's swap markup — which on a retail account typically eats
0.5–1.5% of that 1.38%. It is a bad trade at your size.

### Does diversifying across pairs rescue it?

This was the strongest remaining hypothesis. Trend following is known to work
at the *portfolio* level even when single instruments are marginal. I built 17
FX pairs from the ECB file and ran the identical strategy on each:

```
mean single-instrument Sharpe:  -0.026
```

| Portfolio | Full-sample Sharpe | 2013–2026 Sharpe |
|---|---|---|
| 1 pair | 0.11 | −0.05 |
| 5 pairs | −0.05 | −0.16 |
| 8 pairs | −0.13 | −0.25 |
| 17 pairs | −0.03 | −0.19 |

Diversification cannot rescue an edge that averages zero. Mean pairwise
correlation between the return streams was 0.21 — the pairs *are* reasonably
independent, so the diversification machinery works fine. There is simply
nothing to diversify.

This is consistent with the published work: one parameter study found FX
needed **60+ pairs to reach Sharpe 0.24**, versus 0.73 for 80 futures
contracts, noting "currency trends are shorter-lived and more frequently
interrupted by central bank intervention."

---

## 4. Reconciling with the more optimistic literature

A walk-forward study of major FX pairs reports EUR/USD time-series momentum at
**Sharpe 0.54**. I got 0.19 for a related construction. The gap is worth
understanding rather than picking whichever number you prefer:

- They re-select parameters in each walk-forward window from a menu of 3
  lookbacks × 4 vol targets. Choosing per-window from a menu is not fully
  out-of-sample, even under walk-forward discipline.
- Their own note is that selecting for stability rather than peak Sharpe
  *reduced* out-of-sample performance — the honest direction of the bias.
- 0.54 is the result for the single best pair out of seven; only 2 of 7
  cleared their 0.5 bar. Picking the winner after the fact inflates it.
- Their best *multi-currency* portfolio came in at **0.43 Sharpe and 1.24%
  CAGR** — which is much closer to what I measured, and still under 4%.

Even taking their most favourable published number at face value, the
multi-currency result of 1.24%/yr does not beat your bank.

---

## 5. What this means for you

Your savings account pays 4%, government-insured, zero volatility, instant
access. That is a genuinely strong risk-free rate, and it is the reason this
is hard: **you are not trying to beat zero, you are trying to beat 4%
risk-free.** Rejecting it for a strategy with a 26% drawdown and a measured
1.9% return is a bad trade.

Three further facts specific to your setup:

1. **Cash at IC Markets earns nothing.** They do not pay interest on free
   margin. Every dollar you move from the bank to the broker starts the year
   4% behind before you place a single trade.
2. **The base rates are brutal.** ESMA-mandated disclosures put retail CFD
   loss rates at 74–89% across EU brokers; roughly 10–15% of accounts are
   still profitable after a year.
3. **Leverage does not fix a weak edge**, it scales it — including the sign.
   Doubling size on a 0.19 Sharpe doubles the drawdown too.

### If you still want exposure to this, the sane structure

Don't replace the 4%, stack on top of it. FX is margin-traded, so a 1×
notional position needs only a fraction of capital posted:

- Keep the bulk of the money in the savings account earning 4%.
- Fund the broker with a small slice — enough for margin plus drawdown buffer.
- Size the bot so that losing the entire broker balance is survivable.
- Judge it after **a year or more**, on Sharpe and drawdown, not on P&L.

With 85% in the bank and 15% at the broker, you keep 3.4% guaranteed and risk
15%. That is a defensible way to run an experiment. It is not a way to turn 4%
into 12%.

### Boring things that actually beat 4% more reliably

Not advice, just the honest landscape — all carry real risk, none are
insured the way your savings account is:

- Money-market funds and T-bill ladders: roughly the same 4%, sometimes a
  little more, with similar safety.
- Short-duration bond funds: ~4–6%, with modest interest-rate risk.
- Broad equity index funds: ~7–10% historically over decades, with 30–50%
  drawdowns and long flat periods. Beats 4% *on a long horizon*, not
  reliably year to year.
- Diversified managed futures funds: the professionally-run version of the
  strategy in this repo, across hundreds of instruments rather than one pair
  — which is exactly the diversification that makes it work.

---

## 6. So why ship the bot at all?

Because you asked for it, it is genuinely well-built, and a negative backtest
on ECB fixings is not the last word. The code is here so you can:

- Run it yourself in cTrader's backtester on **IC Markets' own tick data**,
  which is the test that actually counts;
- Use it as a correct, cost-aware skeleton — the volatility targeting, the
  buffering, the risk governors and the turnover accounting are the parts
  that are hard to get right, and they are reusable for any signal;
- Swap in your own signal and see immediately whether it survives costs.

Run it on demo first. The defaults are deliberately conservative. Read
`README.md` for the operational details and the known limitations.

---

## Sources

- [Robot class reference — cTrader Algo](https://help.ctrader.com/ctrader-algo/references/General/Robot/)
- [cBot code samples — cTrader Algo](https://help.ctrader.com/ctrader-algo/documentation/cbots/cbot-code-samples/)
- [Symbol class reference — cTrader Algo](https://help.ctrader.com/ctrader-algo/references/MarketData/Symbols/Symbol/)
- [RoundingMode — cTrader Algo](https://help.ctrader.com/ctrader-algo/references/MarketData/Symbols/RoundingMode/)
- [Code multi-timeframe strategies — cTrader Algo](https://help.ctrader.com/ctrader-algo/how-tos/cbots/code-multitimeframe-strategies/)
- [IC Markets trading costs](https://www.icmarkets.eu/en/trading-pricing/trading-costs)
- [IC Markets spreads and fees review 2026](https://www.compareforexbrokers.com/reviews/ic-markets-review/spreads-fees/)
- [IC Markets cash interest rate — BrokerChooser](https://brokerchooser.com/invest-long-term/learn/cash-yield-at-ic-markets)
- [Moskowitz, Ooi & Pedersen, *Time Series Momentum* (2012)](https://www.sciencedirect.com/science/article/pii/S0304405X11002613)
- [FX Trend-Following: A Walk-Forward Validation Study — QuantInsti](https://www.quantinsti.com/articles/trend-following-strategies-major-currency-markets-epat-project/)
- [Daily Long/Short Trend Following: Parameters, Asset Classes, and Universe Depth — Delphic Alpha](https://delphicalpha.substack.com/p/daily-longshort-trend-following-parameters)
- [The Impact of Volatility Targeting — Man Group](https://www.man.com/insights/the-impact-of-volatility-targeting)
- [Volatility Targeting Improves Risk-Adjusted Returns — Alpha Architect](https://alphaarchitect.com/volatility-targeting-improves-risk-adjusted-returns/)
- [Retail loss rates across 49 brokers (2026)](https://brokerrank.net/research/retail-loss-rates)
- [ECB euro foreign exchange reference rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
- [FRED — Federal Funds Effective Rate (DFF)](https://fred.stlouisfed.org/series/DFF)
- [FRED — ECB Deposit Facility Rate (ECBDFR)](https://fred.stlouisfed.org/series/ECBDFR)
