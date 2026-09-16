# Part 4: emerging markets, growth stories, and bonds

Three questions: are markets like the Philippines worth it, does a fast-growing
economy pay investors, and what about bonds in other markets.

The first two have the same answer, and it is one of the most counterintuitive
results in finance.

Reproduce with `research/fetch_em.py`, `research/fetch_gdp.py`, then
`research/06_emerging_markets.py`.

---

## 1. Fast-growing economies have paid investors *worse*, not better

I took 13 country ETFs, measured what a USD investor actually earned over each
fund's full life, and set it against that country's average real GDP growth over
the same years (World Bank data).

| Country | Ticker | Yrs | GDP growth | **Investor return** | Vol | Max DD |
|---|---|---|---|---|---|---|
| China | MCHI | 15.4 | 6.36%/yr | **2.13%/yr** | 26.4% | 62.8% |
| Vietnam | VNM | 17.1 | 6.19%/yr | **−0.77%/yr** | 25.2% | 63.3% |
| India | INDA | 14.6 | 6.14%/yr | **5.08%/yr** | 21.7% | 45.1% |
| **Philippines** | **EPHE** | **15.9** | **5.22%/yr** | **0.85%/yr** | **22.2%** | **53.8%** |
| Turkey | TUR | 18.4 | 4.79%/yr | 1.04%/yr | 37.3% | 72.3% |
| Indonesia | EIDO | 16.3 | 4.77%/yr | −1.31%/yr | 26.9% | 63.2% |
| Malaysia | EWM | 30.4 | 4.61%/yr | 1.99%/yr | 27.4% | 89.2% |
| South Korea | EWY | 26.3 | 3.66%/yr | 10.14%/yr | 33.6% | 74.1% |
| **United States** | **VOO** | **16.0** | **2.40%/yr** | **14.86%/yr** | 17.0% | 34.0% |
| Thailand | THD | 18.4 | 2.40%/yr | 4.63%/yr | 26.2% | 64.2% |
| Brazil | EWZ | 26.1 | 2.38%/yr | 6.57%/yr | 37.2% | 77.2% |
| Mexico | EWW | 30.4 | 2.16%/yr | 9.03%/yr | 29.5% | 64.9% |
| South Africa | EZA | 23.6 | 2.00%/yr | 9.39%/yr | 33.3% | 64.6% |

**Correlation between GDP growth and investor return in this sample: −0.716.**

The table is sorted by growth, fastest at the top. The returns column runs
roughly the *opposite* way. The four fastest-growing economies — China, Vietnam,
India, the Philippines — paid 2.13%, −0.77%, 5.08% and 0.85%. Three of the four
slowest — the US, Mexico, South Africa — paid 14.86%, 9.03% and 9.39%.

This is not a quirk of my sample. [Ritter (2012)](https://site.warrington.ufl.edu/ritter/files/2015/04/Economic-growth-and-equity-returns-2005.pdf)
found a cross-sectional correlation of **−0.39** across 19 countries from
1900–2011, and **−0.41** for emerging markets specifically over 1988–2011.
Dimson, Marsh and Staunton found the same thing over a century of data.

### Why growth doesn't reach you

- **Dilution.** Growth gets financed by issuing new shares. The economy's output
  rises, but it is split across more shares, so earnings *per share* — the only
  thing you own — grows far slower than GDP.
- **New companies capture it.** Much of the growth accrues to firms that don't
  exist yet, or are private. Buying today's index doesn't buy tomorrow's winners.
- **Competition erodes it.** Technological and economic progress raises output
  but not profits, unless firms hold lasting monopolies, which is rare.
- **You pay for it in advance.** Everyone can see the Philippines is growing.
  That expectation is already in the price. You only win if growth exceeds what
  was already priced in — and by definition that is a coin flip.

---

## 2. So: is the Philippines any good?

**On the evidence, no — not as a concentrated bet.**

Over 15.9 years EPHE returned **0.85%/yr** in USD while the economy grew 5.22%/yr.
Over the common window since 2012 it returned **0.26%/yr**, third from bottom of
the 13 countries. You took a 53.8% drawdown and 22.2% volatility to earn less
than your savings account.

Same window (2012-02 to 2026-09), every country ranked:

| | Return | | | Return |
|---|---|---|---|---|
| Taiwan | 14.96% | | Vietnam | 1.57% |
| **S&P 500** | **14.63%** | | Malaysia | 0.60% |
| South Korea | 9.83% | | Brazil | 0.32% |
| India | 5.14% | | **Philippines** | **0.26%** |
| South Africa | 4.27% | | Turkey | 0.15% |
| Mexico | 3.78% | | Indonesia | −3.91% |
| Thailand | 3.33% | | | |
| China | 3.05% | | | |

Benchmarks over the same window: **EM index 4.98%**, developed ex-US 8.63%,
**World 11.11%**, S&P 500 14.63%.

### The honest counter-argument

Everything above is backward-looking, and there is a real case for EM today:
after 15 years of underperformance, EM trades at much lower valuations than the
US. Cheaper starting valuations have historically meant higher future returns.
If the US's run reverses, EM is where the recovery shows up.

I am not going to tell you that can't happen. What I will say is that
**"the economy is growing fast" is not the reason to own it** — that specific
argument is the one the data most clearly refutes. The valuation argument is
different and stronger.

### The practical resolution

You don't have to choose. **`VWCE` already holds emerging markets at roughly
10–12% of the fund**, including the Philippines, and rebalances that weight
automatically as markets move. You get the exposure at its true global weight
without making a country bet.

Holding EM separately adds little anyway: **VWO's daily returns correlate +0.863
with VT**. It is not the diversifier people assume.

---

## 3. "Pies"

If you mean the **Trading 212 / InvestEngine "Pie"** feature: a Pie is a
portfolio split into slices with target percentages, and new money is
automatically allocated to keep those proportions. Paired with AutoInvest it
handles rebalancing and fractional shares for you.

**It's a good mechanism.** Automatic rebalancing and scheduled investing are
genuinely useful, and they enforce discipline.

**But it's a wrapper, not a strategy.** A Pie containing one global fund and a
Pie containing eight hot growth countries both look equally tidy. Everything in
section 1 says the second one would have hurt you. The container doesn't change
what's inside it.

If you want a Pie, the boring version is the one the evidence supports: one
slice, 100% global equity fund, AutoInvest monthly. Community Pies with a dozen
thematic slices are where the growth-story trap lives.

*(If you meant a New Zealand **PIE fund** — Portfolio Investment Entity, the NZ
tax structure that caps fund tax at 28% — that's a different thing entirely and
tax-specific. Tell me and I'll research it properly.)*

---

## 4. Bonds across different markets

Total return in USD, each fund's full history:

| Fund | What it is | Yrs | Return | Vol | Max DD |
|---|---|---|---|---|---|
| EMB | EM govt bonds, USD-denominated | 18.7 | 4.53%/yr | 10.7% | 34.7% |
| VWOB | Vanguard EM govt bond, USD | 13.3 | 3.33%/yr | 8.6% | 27.0% |
| TIP | US inflation-linked | 22.7 | 3.42%/yr | 6.1% | 14.5% |
| BND | US total bond market | 19.4 | 2.92%/yr | 5.2% | 18.6% |
| BNDX | Global bonds ex-US, USD-hedged | 13.3 | 2.19%/yr | 3.9% | 16.2% |
| **EMLC** | **EM govt bonds, local currency** | 16.1 | **1.15%/yr** | 10.1% | 32.3% |

**Look at that against your 4.10% savings account.** Every one of these returned
*less* than cash currently pays, except EMB at 4.53% — and EMB came with a 34.7%
drawdown, which is equity-like risk for a bond-like return.

Two things explain it. Bonds were crushed by the 2022 rate-hike cycle, which
sits inside every one of these histories. And cash yields right now are unusually
high relative to bonds.

### Hard currency vs local currency

This is the key distinction in EM debt, and the numbers are stark: **EMB
(USD-denominated) 4.53%/yr vs EMLC (local currency) 1.15%/yr** over comparable
windows.

- **Hard currency** bonds are issued in USD. You take the country's *credit*
  risk — the risk it can't repay — but no currency risk.
- **Local currency** bonds are issued in pesos, rupiah, real. You take credit
  risk *plus* currency risk. Over the last 16 years EM currencies depreciated
  against the dollar, and that difference — 3.4%/yr — is almost entirely FX.

For someone holding USD, local-currency EM debt is a bet on EM currencies rising
against the dollar. That is a separate bet from "I want higher bond yields," and
it hasn't paid.

### What this means for you

If you want the safe part of a portfolio, **your 4.10% insured savings account
currently beats every broad bond fund here**, with no volatility and no
drawdown. That is an unusual situation, but it's the one you're in. Bonds become
more compelling when cash rates fall — which is when a bond fund's existing
holdings gain value and cash stops paying.

---

## 5. Where this leaves everything

| Option | Return | Vol | Max DD |
|---|---|---|---|
| EM local-currency bonds (EMLC) | 1.15% | 10.1% | 32.3% |
| Global bonds hedged (BNDX) | 2.19% | 3.9% | 16.2% |
| US bonds (BND) | 2.92% | 5.2% | 18.6% |
| **Philippines (EPHE)** | **0.85%** | **22.2%** | **53.8%** |
| EM equity index (VWO) | ~4.9% | 20.1% | 36.4% |
| EM bonds USD (EMB) | 4.53% | 10.7% | 34.7% |
| **Your savings account** | **4.10%** | **0%** | **0%** |
| My trend bot, best config | 6.41% | 10.0% | 33.4% |
| **World equity (VT / VWCE)** | **~8.9%** | **20.5%** | **50.2%** |

The conclusion hasn't moved across four studies: **one global equity fund, held
long enough, has beaten everything else I've tested** — including the bot I
built you, including every single-country bet, including every bond fund. It
already contains the Philippines, at the weight the world market assigns it.

---

## 6. Caveats

- All of it is history, over windows of 13–30 years. That is enough to say
  "fast growth did not pay investors," not enough to guarantee the next decade.
- Country ETFs carry their own costs and tracking issues, and returns are in USD,
  so they blend local market returns with currency moves.
- The EM valuation argument in section 2 is real and I have not tested it.
- Taiwan has no World Bank GDP series (not a member), so it's excluded from the
  correlation.
- I'm not a financial adviser and don't know your tax residence, horizon, or
  currency needs — all three can change these conclusions.

---

## Sources

- [Ritter, *Is Economic Growth Good for Investors?* (2012)](https://site.warrington.ufl.edu/ritter/files/2015/04/Economic-growth-and-equity-returns-2005.pdf)
- [Ritter, *Economic Growth and Equity Returns* — SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=667507)
- [MSCI, *Is There a Link Between GDP Growth and Equity Returns?*](https://www.msci.com/documents/10199/a134c5d5-dca0-420d-875d-06adb948f578)
- [iShares MSCI Philippines ETF (EPHE)](https://www.ishares.com/us/products/239675/ishares-msci-philippines-etf)
- [Philippine stock market data — Trading Economics](https://tradingeconomics.com/philippines/stock-market)
- [Hard currency vs local currency EM bonds — VanEck](https://www.vaneck.com/us/en/blogs/emerging-markets-bonds/hard-currency-vs-local-currency-em-bonds-what-is-the-difference-and-which-one-is-right-for-you/)
- [EM debt: local or hard currency? — Robeco](https://www.robeco.com/en-int/insights/2025/10/emerging-market-debt-local-or-hard-currency)
- [Pies & AutoInvest — Trading 212 Help Centre](https://helpcentre.trading212.com/hc/en-us/articles/30661163244317-Pies-AutoInvest-Introduction)
- [World Bank, real GDP growth (NY.GDP.MKTP.KD.ZG)](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG)
