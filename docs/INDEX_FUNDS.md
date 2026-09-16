# Part 3: Vanguard index funds — the thing that actually beat 4%

Parts 1 and 2 built a trading bot and found that, at best, it returned 6.41%/yr
while **simply owning the assets returned 8.42%/yr at the same risk.** This part
researches that alternative properly.

Data: Yahoo adjusted closes (dividends reinvested), fetched by
`research/fetch_vanguard.py`. Analysis in `research/05_index_funds.py`.

---

## 1. The question that actually matters: how *reliable* is this?

You asked for something "more reliable" than 4%. Equities are not more reliable
than a savings account — they are more *rewarding*, and only if you hold them
long enough. Here is the honest shape of it.

S&P 500, every rolling window 1928–2026 (price return + 2%/yr assumed dividend):

| Holding period | Median | Worst | Beat 4%/yr | Lost money |
|---|---|---|---|---|
| 1 year | 11.6% | **−69.1%** | 66.3% | 27.1% |
| 3 years | 10.1% | −44.0% | 74.4% | 17.2% |
| 5 years | 10.0% | −20.9% | 74.4% | 12.3% |
| 10 years | 9.6% | −7.8% | 80.4% | 6.4% |
| 15 years | 9.1% | −3.9% | 91.6% | 3.0% |
| 20 years | 9.1% | −1.4% | **95.7%** | 1.2% |
| 30 years | 9.3% | +4.0% | **100%** | 0% |

From 1970 onward the picture is a bit stronger: 89.3% of 10-year windows beat
4%, and **every** 20-year and 30-year window did, with the worst 20-year period
still returning 4.37%/yr.

**So the answer is entirely about your horizon.**

- Money you need within ~3 years: the savings account wins. A 27% chance of
  losing money over one year is not a risk worth taking for a few extra points.
- Money you won't touch for 10+ years: equities beat 4% about 80–90% of the
  time, historically.
- Money you won't touch for 20+ years: historically it has never failed.

That is the real trade. Not "more reliable" — *more rewarding, if you can wait,
and genuinely painful sometimes if you can't.*

---

## 2. What the funds actually returned

Total return, dividends reinvested, over each fund's full history:

| Ticker | Fund | Years | CAGR | Vol | Max DD |
|---|---|---|---|---|---|
| VOO | Vanguard S&P 500 (US-dom) | 16.0 | 14.86% | 17.0% | 34.0% |
| VTI | Vanguard Total US Stock (US-dom) | 25.2 | 9.76% | 19.0% | **55.5%** |
| VT | Vanguard Total World (US-dom) | 18.2 | 8.86% | 20.5% | 50.2% |
| VXUS | Vanguard Intl ex-US (US-dom) | 15.6 | 6.73% | 17.7% | 36.0% |
| BND | Vanguard Total US Bond (US-dom) | 19.4 | 2.92% | 5.2% | 18.6% |
| VWCE | FTSE All-World UCITS acc (Irish) | 7.2 | 12.37% | 16.0% | 33.4% |
| VWRL | FTSE All-World UCITS dist (Irish) | 14.5 | 10.17% | 19.5% | 33.3% |
| VAS | Vanguard Australian Shares (AU) | 17.4 | 8.02% | 14.9% | 35.8% |
| VGS | Vanguard Intl Shares (AU) | 11.9 | 13.13% | 13.1% | 23.4% |
| VDHG | Diversified High Growth (AU) | 8.9 | 9.50% | 11.8% | 28.3% |

**Do not read VOO's 14.86% as the expected return.** VOO's price history starts
in September 2010, near the bottom of the post-GFC recovery. Start-date luck is
doing most of that work. VTI's **9.76% over 25 years** includes the dot-com
crash and 2008, and is the more honest number. Note its 55.5% max drawdown.

Over an identical window (2014-11 to 2026-09) so start dates can't distort:

| Ticker | CAGR | Vol | Max DD |
|---|---|---|---|
| VOO | 15.79% | 18.1% | 34.0% |
| VTI | 15.26% | 18.5% | 35.0% |
| VWRL | 13.17% | 17.0% | 33.3% |
| VT | 12.44% | 17.6% | 34.2% |
| VAS (AUD) | 9.53% | 15.1% | 33.4% |
| VXUS | 8.96% | 18.0% | 35.6% |
| BND | 2.00% | 5.8% | 18.6% |

The VTI-vs-VXUS gap (15.26% vs 8.96%) is the last decade of US outperformance.
Betting it repeats is a real bet, not a neutral default.

---

## 3. Domicile is worth more than expense ratio

**IC Markets does not accept US clients** — it isn't CFTC/NFA registered, and
retail CFDs are prohibited for US residents. Since you trade there, you are
almost certainly not a US person, and that makes fund domicile the single most
important decision here. Much more important than a 0.08% fee difference.

### The US estate tax trap

US-domiciled ETFs (VOO, VTI, VT) are **US-situs assets**. For a non-US person,
anything above **$60,000** is exposed to US estate tax at **18–40%** on death.
US citizens get a multi-million-dollar exemption; you do not.

Irish-domiciled UCITS ETFs holding the identical stocks are *not* US-situs, and
are not caught. Same exposure, opposite treatment, decided purely by where the
fund is registered.

### Dividend withholding

An Irish-domiciled fund pays **15%** US withholding on US dividends under the
Ireland–US treaty, instead of 30% for funds in non-treaty jurisdictions. It is
applied inside the fund, so you never see it and cannot reclaim it — but it
compounds.

### Accumulating vs distributing

- **Accumulating** (VWCE, VUAA): dividends reinvested inside the fund. No cash
  to handle, often no taxable event until you sell, depending on your country.
- **Distributing** (VWRL, VUSA): dividends paid to you as cash.

Accumulating is usually simpler and more tax-efficient — but a few countries
(Ireland, Brazil, some others) tax them unfavourably. This is the one thing you
must check locally.

---

## 4. The best option, and why

**For a non-US investor with a long horizon: `VWCE` — Vanguard FTSE All-World
UCITS ETF (USD) Accumulating, ISIN `IE00BK5BQT80`.**

| | |
|---|---|
| TER | 0.14%/yr |
| Holdings | 3,758 companies, ~50 countries, developed + emerging |
| Domicile | Ireland — no US estate tax exposure, 15% dividend withholding |
| Policy | Accumulating |
| Fund size | ~EUR 51bn |
| Base currency | USD (which matches your savings) |

Why this one over the alternatives:

- **Over VOO/VTI/VT:** same or better underlying exposure without the $60k US
  estate tax cliff. That risk dwarfs the 0.08% fee difference.
- **Over VUAA (S&P 500 UCITS, 0.07%):** VUAA is a bet that US outperformance
  continues. VWCE holds the US at its actual global weight (~60%) and rebalances
  automatically as that changes. You are not required to have a view.
- **Over VWRL (the distributing twin):** accumulating avoids handling and
  re-investing dividend cash. Pick VWRL if your country taxes accumulating funds
  badly, or if you want income.
- **Over anything more complicated:** one fund, one decision, nothing to
  rebalance. The evidence for beating a global market-cap index after costs is
  weak, which is the same lesson Parts 1 and 2 taught the hard way.

**If you are an Australian resident**, check `VDHG` or `VGS`+`VAS` on the ASX
first. Franking credits on Australian dividends materially change the maths, and
ASX-listed Vanguard funds sidestep the US estate tax question. VDHG returned
9.50%/yr with a 28.3% max drawdown and is a single all-in-one fund.

**If your horizon is under ~3 years**, none of this applies. Keep the 4%.

---

## 5. The whole ladder, ranked

| Option | Return | Vol | Max DD | Notes |
|---|---|---|---|---|
| Vanguard BND (US bonds) | 2.92% | 5.2% | 18.6% | hurt by the rate-hike cycle |
| Vanguard VMFXX money market | ~3.65% | ~0% | 0% | not insured; T-bill backed |
| **Your savings account** | **4.10%** | **0%** | **0%** | insured, instant access |
| My trend bot, best config | 6.41% | 10.0% | 33.4% | 22 CFDs, long-only |
| Vanguard VT / VWCE (world) | ~8.9% | 20.5% | 50.2% | 18yr history |
| Vanguard VTI (total US) | 9.76% | 19.0% | 55.5% | 25yr history |

The through-line across all three parts of this research: **the index fund beat
the trading bot I built for you,** and it beat it while being simpler, cheaper,
and not requiring a VPS to stay online.

---

## 6. Things I am not able to tell you

- **Your tax situation.** Everything in section 3 depends on your country of
  residence. Accumulating-fund treatment, capital gains rates, and local
  wrappers (ISA, SIPP, PEA, superannuation) can swamp every number here.
- **Your horizon and circumstances.** The rolling-window table is the whole
  argument, and only you know which row you are in.
- **Whether the future resembles the past.** Every figure here is history. The
  1928–2026 sample contains one country's unusually good century.
- **Currency.** VWCE is USD-denominated but holds global assets; if you spend in
  another currency you carry FX risk that none of these figures show.

I am not a financial adviser and this is research, not advice. The facts are
sourced below; the decision is yours.

---

## Sources

- [Vanguard FTSE All-World UCITS ETF (VWCE) profile — justETF](https://www.justetf.com/en/etf-profile.html?isin=IE00BK5BQT80)
- [VWCE factsheet — Vanguard](https://fund-docs.vanguard.com/FTSE_All-World_UCITS_ETF_USD_Accumulating_9679_EU_INT_EN.pdf)
- [Nonresident alien investors and Ireland domiciled ETFs — Bogleheads](https://www.bogleheads.org/wiki/Nonresident_alien_investors_and_Ireland_domiciled_ETFs)
- [Considerations for non-US investors: US vs Irish UCITS ETFs — State Street](https://www.ssga.com/us/en/institutional/insights/considerations-for-non-us-investors-us-etfs-vs-irish-ucits)
- [US estate tax rules for non-residents — Skybound Wealth](https://www.skyboundwealth.com/technical-guides/u-s-estate-tax-rules-for-non-residents)
- [UCITS ETF withholding tax & PFIC rules (2026)](https://www.taxesforexpats.com/articles/investments/ucits-etf-withholding-tax.html)
- [VOO vs VTI expense ratios and returns — Forbes](https://www.forbes.com/sites/investor-hub/article/vti-vs-voo-how-to-compare-vanguard-etfs/)
- [Vanguard Federal Money Market Fund (VMFXX)](https://advisors.vanguard.com/investments/products/vmfxx/vanguard-federal-money-market-fund)
- [Best high-yield savings rates, September 2026 — Bankrate](https://www.bankrate.com/banking/savings/best-high-yield-interests-savings-accounts/)
- [IC Markets does not accept US clients — ForexBrokers.com](https://www.forexbrokers.com/reviews/ic-markets)
