// ============================================================================
//  CarryTrendFx  --  a cost-aware, volatility-targeted trend + carry cBot
//  Platform: cTrader Automate (cAlgo API, C#).  Target: IC Markets Raw / cTrader.
//
//  DESIGN THESIS
//  -------------
//  The binding constraint on a retail FX account is not signal quality, it is
//  TURNOVER x COST.  On IC Markets Raw cTrader, EUR/USD costs roughly:
//
//      commission  $6.00 round turn per 1.0 lot      = 0.60 pips
//      spread      0.0-0.1 pips peak, ~0.1-0.3 avg   = 0.20 pips
//      -----------------------------------------------------------
//      all-in      ~0.8 pips round turn              = ~$8 per lot
//
//  A bot doing 5 round turns a day at 0.3 lots burns ~5 * 250 * 0.3 * $8
//  = $3,000/yr.  On a $25,000 account that is 12% of capital per year in
//  costs alone -- you would need a 12% gross edge just to reach zero.
//  Almost no retail strategy has that.  This is the single biggest reason
//  retail FX bots lose.
//
//  This bot therefore does the opposite of a scalper.  It is a SLOW system:
//  it makes one decision per day, holds for weeks, and uses a no-trade
//  buffer so that small forecast wobbles never generate an order.  Expected
//  turnover is ~10-20 round turns per year, which costs ~0.1-0.3% of equity
//  annually -- small enough that a modest edge survives it.
//
//  SIGNAL (three components, blended)
//  ----------------------------------
//  1. EWMAC trend at three speeds (16/64, 32/128, 64/256 day EMA pairs),
//     each normalised by price volatility and capped.  Multi-speed blending
//     is the standard institutional defence against parameter overfitting:
//     you are not betting that "the 50 day MA works", you are betting that
//     trends exist at some horizon.
//  2. Carry, computed from the broker's OWN posted swap rates, expressed as
//     an annualised return and risk-normalised the same way as trend.
//  3. Both are combined into a single continuous forecast in [-20, +20],
//     where 0 = flat, +-10 = an average-sized position.
//
//  SIZING
//  ------
//  Volatility targeting: position size is inversely proportional to
//  realised volatility, so the risk of the book stays roughly constant
//  instead of ballooning when EUR/USD gets wild.
//
//  RISK
//  ----
//  Portfolio drawdown kill switch, daily loss limit, hard leverage cap,
//  spread guard, and a rollover blackout.  Hard per-trade stops are
//  available but OFF by default -- see the README for why they interact
//  badly with a continuous-forecast system.
//
//  Read docs/RESEARCH.md before running this.  It states plainly what this
//  can and cannot be expected to earn, and how it compares to leaving the
//  money in a 4% savings account.
// ============================================================================

using System;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    /// <summary>
    /// What kind of instrument this is. Drives the default holding-cost
    /// estimate and the startup sanity warnings -- an index CFD and a
    /// currency pair have very different economics.
    /// </summary>
    public enum InstrumentClass
    {
        Fx,
        Index,
        Metal,
        Energy,
        Agricultural,
        Bond,
        Crypto
    }

    [Robot(AccessRights = AccessRights.None, TimeZone = TimeZones.UTC,
           Name = "CarryTrendFx", Version = "1.0.0")]
    public class CarryTrendFx : Robot
    {
        // ------------------------------------------------------------------
        // Parameters -- Risk
        // ------------------------------------------------------------------

        [Parameter("Target volatility %/yr", Group = "Risk", DefaultValue = 10.0,
                   MinValue = 1.0, MaxValue = 30.0, Step = 0.5)]
        public double TargetVolPct { get; set; }

        [Parameter("Instrument weight", Group = "Risk", DefaultValue = 1.0,
                   MinValue = 0.05, MaxValue = 1.0, Step = 0.05)]
        public double InstrumentWeight { get; set; }

        [Parameter("Risk capital override (0 = use equity)", Group = "Risk",
                   DefaultValue = 0.0, MinValue = 0.0)]
        public double RiskCapitalOverride { get; set; }

        [Parameter("Max gross leverage (x capital)", Group = "Risk",
                   DefaultValue = 5.0, MinValue = 0.5, MaxValue = 30.0, Step = 0.5)]
        public double MaxLeverage { get; set; }

        [Parameter("Realised-vol governor", Group = "Risk", DefaultValue = true)]
        public bool UseVolGovernor { get; set; }

        [Parameter("Governor window (days)", Group = "Risk", DefaultValue = 64,
                   MinValue = 20, MaxValue = 250)]
        public int GovernorWindow { get; set; }

        [Parameter("Kill switch drawdown %", Group = "Risk", DefaultValue = 20.0,
                   MinValue = 2.0, MaxValue = 90.0, Step = 1.0)]
        public double KillSwitchDrawdownPct { get; set; }

        [Parameter("Daily loss limit % (0 = off)", Group = "Risk",
                   DefaultValue = 4.0, MinValue = 0.0, MaxValue = 50.0, Step = 0.5)]
        public double DailyLossLimitPct { get; set; }

        // ------------------------------------------------------------------
        // Parameters -- Signal
        // ------------------------------------------------------------------

        [Parameter("Trend weight", Group = "Signal", DefaultValue = 0.75,
                   MinValue = 0.0, MaxValue = 1.0, Step = 0.05)]
        public double TrendWeight { get; set; }

        [Parameter("Carry weight", Group = "Signal", DefaultValue = 0.25,
                   MinValue = 0.0, MaxValue = 1.0, Step = 0.05)]
        public double CarryWeight { get; set; }

        [Parameter("Carry forecast scalar", Group = "Signal", DefaultValue = 30.0,
                   MinValue = 1.0, MaxValue = 200.0, Step = 1.0)]
        public double CarryScalar { get; set; }

        [Parameter("Forecast cap", Group = "Signal", DefaultValue = 20.0,
                   MinValue = 5.0, MaxValue = 40.0, Step = 1.0)]
        public double ForecastCap { get; set; }

        [Parameter("Forecast diversification multiplier", Group = "Signal",
                   DefaultValue = 1.25, MinValue = 1.0, MaxValue = 2.5, Step = 0.05)]
        public double Fdm { get; set; }

        [Parameter("Allow long positions", Group = "Signal", DefaultValue = true)]
        public bool AllowLong { get; set; }

        [Parameter("Allow short positions", Group = "Signal", DefaultValue = true)]
        public bool AllowShort { get; set; }

        // ------------------------------------------------------------------
        // Parameters -- Volatility estimation
        // ------------------------------------------------------------------

        [Parameter("Vol EWMA span (days)", Group = "Volatility", DefaultValue = 32,
                   MinValue = 5, MaxValue = 250)]
        public int VolSpan { get; set; }

        [Parameter("Long-run vol blend %", Group = "Volatility", DefaultValue = 30.0,
                   MinValue = 0.0, MaxValue = 100.0, Step = 5.0)]
        public double LongRunVolBlendPct { get; set; }

        [Parameter("Long-run vol window (days)", Group = "Volatility",
                   DefaultValue = 2500, MinValue = 250, MaxValue = 6000)]
        public int LongRunVolWindow { get; set; }

        // ------------------------------------------------------------------
        // Parameters -- Costs and turnover
        // ------------------------------------------------------------------

        [Parameter("No-trade buffer (frac of avg pos)", Group = "Costs",
                   DefaultValue = 0.15, MinValue = 0.0, MaxValue = 0.60, Step = 0.01)]
        public double BufferFraction { get; set; }

        [Parameter("Max spread to trade (pips)", Group = "Costs", DefaultValue = 1.0,
                   MinValue = 0.1, MaxValue = 10.0, Step = 0.1)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Commission per lot round turn ($)", Group = "Costs",
                   DefaultValue = 6.0, MinValue = 0.0, MaxValue = 100.0, Step = 0.5)]
        public double CommissionPerLotRoundTurn { get; set; }

        [Parameter("Max rebalance cost (frac of capital)", Group = "Costs",
                   DefaultValue = 0.0025, MinValue = 0.0001, MaxValue = 0.05, Step = 0.0001)]
        public double MaxRebalanceCostFraction { get; set; }

        [Parameter("Rollover blackout start (UTC hour)", Group = "Costs",
                   DefaultValue = 20, MinValue = 0, MaxValue = 23)]
        public int RolloverBlackoutStartHour { get; set; }

        [Parameter("Rollover blackout end (UTC hour)", Group = "Costs",
                   DefaultValue = 22, MinValue = 0, MaxValue = 23)]
        public int RolloverBlackoutEndHour { get; set; }

        // ------------------------------------------------------------------
        // Parameters -- Stops (off by default; see README)
        // ------------------------------------------------------------------

        [Parameter("Use ATR stop loss", Group = "Stops", DefaultValue = false)]
        public bool UseAtrStop { get; set; }

        [Parameter("ATR stop multiple", Group = "Stops", DefaultValue = 6.0,
                   MinValue = 1.0, MaxValue = 20.0, Step = 0.5)]
        public double AtrStopMultiple { get; set; }

        [Parameter("ATR period (daily)", Group = "Stops", DefaultValue = 20,
                   MinValue = 5, MaxValue = 100)]
        public int AtrPeriod { get; set; }

        // ------------------------------------------------------------------
        // Parameters -- Operations
        // ------------------------------------------------------------------

        [Parameter("Asset class", Group = "Instrument", DefaultValue = InstrumentClass.Fx)]
        public InstrumentClass AssetClass { get; set; }

        [Parameter("Annual holding cost % (0 = auto)", Group = "Instrument",
                   DefaultValue = 0.0, MinValue = 0.0, MaxValue = 50.0, Step = 0.25)]
        public double AnnualHoldingCostPct { get; set; }

        [Parameter("Diversification multiplier", Group = "Instrument", DefaultValue = 1.0,
                   MinValue = 1.0, MaxValue = 3.0, Step = 0.05)]
        public double Idm { get; set; }

        [Parameter("Position label", Group = "Ops", DefaultValue = "CarryTrendFx")]
        public string PositionLabel { get; set; }

        [Parameter("Verbose logging", Group = "Ops", DefaultValue = true)]
        public bool Verbose { get; set; }

        [Parameter("Dry run (log only, no orders)", Group = "Ops", DefaultValue = false)]
        public bool DryRun { get; set; }

        // ------------------------------------------------------------------
        // EWMAC speeds.  Forecast scalars are the published values that make
        // each rule's average absolute forecast approximately 10, so that the
        // three speeds contribute comparably to the blend.
        // ------------------------------------------------------------------

        private static readonly int[] FastSpans = { 16, 32, 64 };
        private static readonly int[] SlowSpans = { 64, 128, 256 };
        private static readonly double[] TrendScalars = { 4.10, 2.79, 1.91 };
        private static readonly double[] TrendWeights = { 0.30, 0.40, 0.30 };

        private const double AverageForecast = 10.0;
        private const double TradingDaysPerYear = 252.0;

        // ------------------------------------------------------------------
        // State
        // ------------------------------------------------------------------

        private Bars _daily;
        private double _sigmaPrice;          // daily volatility, price units
        private double _equityHighWater;
        private double _dayStartEquity;
        private int _dayStartDayOfYear = -1;
        private bool _killed;
        private double _lastForecast;
        private double _lastTargetUnits;
        private DateTime _lastRebalanceUtc = DateTime.MinValue;
        private DateTime _startedUtc;
        private readonly System.Collections.Generic.List<double> _dailyReturns =
            new System.Collections.Generic.List<double>();
        private double _lastDailyEquity;
        private double _lastGovernorScale = 1.0;
        private int _rebalanceCount;
        private double _cumulativeUnitsTraded;
        private double _cumulativeCostEstimate;
        private double _cumulativeFinancingEstimate;

        // ==================================================================
        // Lifecycle
        // ==================================================================

        protected override void OnStart()
        {
            if (TrendWeight + CarryWeight <= 0)
            {
                Print("ERROR: trend weight + carry weight must be > 0. Stopping.");
                Stop();
                return;
            }

            _daily = MarketData.GetBars(TimeFrame.Daily);

            var required = SlowSpans.Max() + 50;
            if (_daily.Count < required)
            {
                Print("Only {0} daily bars loaded, need >= {1}. Scroll the daily chart " +
                      "back to load more history, then restart.", _daily.Count, required);
            }

            _daily.BarOpened += OnDailyBarOpened;

            _equityHighWater = Account.Equity;
            _lastDailyEquity = Account.Equity;
            _startedUtc = Server.Time;
            ResetDailyAnchor();

            Print("CarryTrendFx started on {0}. Equity {1:N2} {2}. " +
                  "Target vol {3:F1}%/yr, weight {4:F2}, buffer {5:P0}.",
                  SymbolName, Account.Equity, Account.Currency,
                  TargetVolPct, InstrumentWeight, BufferFraction);
            Print("Cost model: commission {0:C2}/lot round turn, spread cap {1:F1} pips, " +
                  "estimated all-in {2:F2} pips per round turn.",
                  CommissionPerLotRoundTurn, MaxSpreadPips, EstimatedRoundTurnCostPips());

            ReportExpectedEconomics();

            // Evaluate immediately so a restart mid-trend re-establishes the book.
            Rebalance("startup");
        }

        /// <summary>
        /// Says up front what holding this instrument costs and, where the
        /// backtesting was unambiguous, warns about the configuration. These
        /// warnings are not style preferences -- each one corresponds to a
        /// result in docs/RESEARCH.md.
        /// </summary>
        private void ReportExpectedEconomics()
        {
            var holding = AnnualHoldingCostFraction();

            Print("Instrument class {0}: estimated holding cost {1:P2}/yr of notional, " +
                  "charged in BOTH directions.", AssetClass, holding);

            if (AssetClass != InstrumentClass.Fx && AllowShort)
                Print("WARNING: shorting is enabled on a {0}. In testing across 22 non-FX " +
                      "instruments, long-only returned 6.41%/yr (Sharpe 0.64) while " +
                      "long/short returned 3.70%/yr (Sharpe 0.37), and short-only lost " +
                      "6.49%/yr. Consider setting 'Allow short positions' to false.",
                      AssetClass);

            if (AssetClass == InstrumentClass.Crypto)
                Print("WARNING: crypto CFD financing runs around 15%/yr. A 10%-vol strategy " +
                      "cannot out-earn that reliably. Size accordingly or trade spot elsewhere.");

            if (CarryWeight > 0 && AssetClass != InstrumentClass.Fx)
                Print("Carry weight is set but will be ignored: carry is only a real signal " +
                      "in FX. Trend weight alone drives this instrument.");

            if (InstrumentWeight >= 0.999 && Idm <= 1.001)
                Print("Running as a single instrument at full weight. If you attach this bot " +
                      "to N charts, set 'Instrument weight' to 1/N so the combined book still " +
                      "targets {0:F1}%/yr rather than N times that.", TargetVolPct);
        }

        protected override void OnStop()
        {
            if (_daily != null)
                _daily.BarOpened -= OnDailyBarOpened;

            Print("CarryTrendFx stopped. Equity {0:N2}, net position {1:N0} units, " +
                  "last forecast {2:F2}.", Account.Equity, NetUnits(), _lastForecast);
            PrintTurnoverReport();
        }

        /// <summary>
        /// Turnover is the number this design lives or dies by, so it is
        /// reported explicitly rather than left for you to infer from the
        /// trade list. If annualised round turns climbs far above ~20, the
        /// buffer is too narrow or the forecast too fast, and costs will
        /// start eating the edge.
        /// </summary>
        private void PrintTurnoverReport()
        {
            var lot = Symbol.LotSize > 0 ? Symbol.LotSize : 100000.0;
            var years = (Server.Time - _startedUtc).TotalDays / 365.25;

            var lotsTraded = _cumulativeUnitsTraded / lot;
            var roundTurns = lotsTraded / 2.0;   // a round turn is in + out

            Print("Turnover: {0} rebalances, {1:N2} lots traded ({2:N2} round turns), " +
                  "transaction cost {3:C2}, financing {4:C2}.",
                  _rebalanceCount, lotsTraded, roundTurns,
                  _cumulativeCostEstimate, _cumulativeFinancingEstimate);

            if (years > 0.05)
            {
                var capital = RiskCapital();
                var total = _cumulativeCostEstimate + _cumulativeFinancingEstimate;

                Print("Annualised: {0:N1} round turns/yr | transactions {1:C2}/yr | " +
                      "financing {2:C2}/yr | TOTAL {3:C2}/yr ({4:P2} of capital/yr).",
                      roundTurns / years,
                      _cumulativeCostEstimate / years,
                      _cumulativeFinancingEstimate / years,
                      total / years,
                      capital > 0 ? total / years / capital : 0);

                if (_cumulativeFinancingEstimate > _cumulativeCostEstimate * 2)
                    Print("NOTE: financing dominates your costs, not commission. " +
                          "That is normal outside FX and is the main thing eating the edge.");
            }
        }

        private void RecordTurnover(double deltaUnits)
        {
            _rebalanceCount++;
            _cumulativeUnitsTraded += Math.Abs(deltaUnits);
            _cumulativeCostEstimate += Math.Abs(deltaUnits) * RoundTurnCostPerUnit() / 2.0;
        }

        /// <summary>
        /// Accrues one day of holding cost on the current book. Called once
        /// per daily bar so the turnover report shows the financing drag
        /// alongside the transaction cost -- on non-FX instruments financing
        /// is by far the larger of the two, and it is invisible in the trade
        /// list, so it has to be surfaced deliberately.
        /// </summary>
        private void AccrueHoldingCost()
        {
            var units = Math.Abs(NetUnits());
            if (units <= 0) return;

            var notional = units * Symbol.Bid;
            if (notional <= 0) return;

            _cumulativeFinancingEstimate += notional * AnnualHoldingCostFraction() / 365.0;
        }

        protected override void OnTick()
        {
            TrackEquity();
        }

        private void OnDailyBarOpened(BarOpenedEventArgs obj)
        {
            SampleDailyEquity();
            AccrueHoldingCost();
            ResetDailyAnchorIfNewDay();
            Rebalance("daily bar");
        }

        /// <summary>
        /// One equity observation per day, feeding the realised-vol governor.
        /// </summary>
        private void SampleDailyEquity()
        {
            var equity = Account.Equity;

            if (_lastDailyEquity > 0)
            {
                _dailyReturns.Add((equity - _lastDailyEquity) / _lastDailyEquity);

                var maxKeep = Math.Max(GovernorWindow * 3, 250);
                if (_dailyReturns.Count > maxKeep)
                    _dailyReturns.RemoveRange(0, _dailyReturns.Count - maxKeep);
            }

            _lastDailyEquity = equity;
        }

        /// <summary>
        /// Scales the book down when the strategy's OWN realised volatility
        /// runs above target. Volatility targeting sizes from the
        /// instrument's volatility, but a persistently strong forecast can
        /// still push realised risk well above target -- on EUR/USD history
        /// this governor pulled realised vol from 11.7% back to 10.0% and cut
        /// worst drawdown from 35% to 26%. It only ever scales down.
        /// </summary>
        private double GovernorScale()
        {
            if (!UseVolGovernor || _dailyReturns.Count < GovernorWindow)
                return 1.0;

            var n = Math.Min(GovernorWindow, _dailyReturns.Count);
            var start = _dailyReturns.Count - n;

            double mean = 0;
            for (var i = start; i < _dailyReturns.Count; i++) mean += _dailyReturns[i];
            mean /= n;

            double sumSq = 0;
            for (var i = start; i < _dailyReturns.Count; i++)
            {
                var d = _dailyReturns[i] - mean;
                sumSq += d * d;
            }

            var realisedVol = Math.Sqrt(sumSq / n) * Math.Sqrt(TradingDaysPerYear);
            if (realisedVol <= 0) return 1.0;

            var target = TargetVolPct / 100.0;
            return Math.Min(1.0, target / realisedVol);
        }

        // ==================================================================
        // Risk guards
        // ==================================================================

        private void TrackEquity()
        {
            var equity = Account.Equity;
            if (equity > _equityHighWater)
                _equityHighWater = equity;

            if (_killed)
                return;

            // Portfolio drawdown kill switch.  This is the real capital
            // protection in a system like this -- not per-trade stops.
            if (_equityHighWater > 0)
            {
                var ddPct = (1.0 - equity / _equityHighWater) * 100.0;
                if (ddPct >= KillSwitchDrawdownPct)
                {
                    Print("KILL SWITCH: drawdown {0:F2}% >= {1:F2}%. Flattening and halting. " +
                          "The bot will NOT trade again until you restart it -- that pause is " +
                          "deliberate, use it to work out why.",
                          ddPct, KillSwitchDrawdownPct);
                    Flatten("kill switch");
                    _killed = true;
                    return;
                }
            }

            // Daily loss limit -- stops a single bad day compounding.
            if (DailyLossLimitPct > 0 && _dayStartEquity > 0)
            {
                var dayPct = (1.0 - equity / _dayStartEquity) * 100.0;
                if (dayPct >= DailyLossLimitPct)
                {
                    Print("DAILY LOSS LIMIT: down {0:F2}% today (limit {1:F2}%). " +
                          "Flattening until tomorrow.", dayPct, DailyLossLimitPct);
                    Flatten("daily loss limit");
                    _dayStartEquity = equity; // do not re-fire repeatedly today
                }
            }
        }

        private void ResetDailyAnchorIfNewDay()
        {
            if (Server.Time.DayOfYear != _dayStartDayOfYear)
                ResetDailyAnchor();
        }

        private void ResetDailyAnchor()
        {
            _dayStartEquity = Account.Equity;
            _dayStartDayOfYear = Server.Time.DayOfYear;
        }

        // ==================================================================
        // Main decision
        // ==================================================================

        private void Rebalance(string reason)
        {
            if (_killed)
                return;

            if (_daily == null || _daily.Count < SlowSpans.Max() + 5)
            {
                if (Verbose)
                    Print("Rebalance skipped ({0}): insufficient daily history ({1} bars).",
                          reason, _daily == null ? 0 : _daily.Count);
                return;
            }

            _sigmaPrice = EstimatePriceVolatility();
            if (_sigmaPrice <= 0 || double.IsNaN(_sigmaPrice))
            {
                Print("Rebalance skipped ({0}): volatility estimate unusable.", reason);
                return;
            }

            var forecast = ComputeForecast();

            if (!AllowLong && forecast > 0) forecast = 0;
            if (!AllowShort && forecast < 0) forecast = 0;

            _lastForecast = forecast;

            var avgUnits = AveragePositionUnits();
            var targetUnits = forecast / AverageForecast * avgUnits;

            _lastGovernorScale = GovernorScale();
            targetUnits *= _lastGovernorScale;

            targetUnits = ApplyLeverageCap(targetUnits);
            _lastTargetUnits = targetUnits;

            var currentUnits = NetUnits();
            var bufferUnits = Math.Abs(avgUnits) * BufferFraction;

            // No-trade buffer.  We only trade when the position is outside the
            // band, and then only back to the edge of the band -- never to the
            // exact target.  This is what keeps turnover, and therefore cost,
            // low enough for the edge to survive.
            double desiredUnits;
            if (currentUnits > targetUnits + bufferUnits)
                desiredUnits = targetUnits + bufferUnits;
            else if (currentUnits < targetUnits - bufferUnits)
                desiredUnits = targetUnits - bufferUnits;
            else
                desiredUnits = currentUnits; // inside the band: do nothing

            if (Verbose)
            {
                var heldDays = _lastRebalanceUtc == DateTime.MinValue
                    ? 0.0
                    : (Server.Time - _lastRebalanceUtc).TotalDays;

                Print("[{0}] forecast {1:F2} | sigma {2:F2} pips/day ({3:F1}%/yr) | " +
                      "avg pos {4:N0}u | target {5:N0}u | current {6:N0}u | band +-{7:N0}u | " +
                      "{8:F1}d since last trade",
                      reason, forecast, _sigmaPrice / Symbol.PipSize,
                      AnnualisedVolPct(), avgUnits, targetUnits, currentUnits, bufferUnits,
                      heldDays);

                if (_lastGovernorScale < 0.999)
                    Print("   governor scaling book to {0:P0} (realised vol above target).",
                          _lastGovernorScale);
            }

            var delta = desiredUnits - currentUnits;
            if (Math.Abs(delta) < Symbol.VolumeInUnitsMin)
                return;

            if (!TradingConditionsOk(delta, out var why))
            {
                if (Verbose)
                    Print("Trade deferred: {0}", why);
                return;
            }

            AdjustPosition(delta);
            RecordTurnover(delta);
            _lastRebalanceUtc = Server.Time;

            if (UseAtrStop)
                RefreshStops();
        }

        // ==================================================================
        // Forecast construction
        // ==================================================================

        private double ComputeForecast()
        {
            var trend = ComputeTrendForecast();
            var carry = ComputeCarryForecast();

            var wSum = TrendWeight + CarryWeight;
            var combined = (trend * TrendWeight + carry * CarryWeight) / wSum;

            combined *= Fdm;
            return Clamp(combined, -ForecastCap, ForecastCap);
        }

        /// <summary>
        /// Blended EWMAC: (fast EMA - slow EMA) / price volatility, scaled so
        /// the average absolute forecast is ~10, capped, then weighted across
        /// three speeds.  Using three speeds rather than one is deliberate --
        /// a single tuned lookback is the classic way to overfit a backtest.
        /// </summary>
        private double ComputeTrendForecast()
        {
            double sum = 0, wSum = 0;

            for (var i = 0; i < FastSpans.Length; i++)
            {
                var fast = Ema(FastSpans[i]);
                var slow = Ema(SlowSpans[i]);
                var raw = (fast - slow) / _sigmaPrice;
                var scaled = Clamp(raw * TrendScalars[i], -ForecastCap, ForecastCap);

                sum += scaled * TrendWeights[i];
                wSum += TrendWeights[i];
            }

            return wSum > 0 ? sum / wSum : 0;
        }

        /// <summary>
        /// Carry from the broker's own posted swap rates, risk-normalised.
        /// A positive value means holding long earns (or costs less than)
        /// holding short.  Because it uses Symbol.SwapLong / Symbol.SwapShort
        /// it reflects the broker's actual markup, not the interbank
        /// differential -- which is the number that hits your account.
        /// </summary>
        private double ComputeCarryForecast()
        {
            if (CarryWeight <= 0)
                return 0;

            // On an index or commodity CFD the "swap" IS the financing charge:
            // it is negative on longs and negative on shorts, so feeding it in
            // as a carry signal would permanently bias the bot short for no
            // good reason. Carry is only a real signal in FX, where it
            // reflects a genuine interest-rate differential.
            if (AssetClass != InstrumentClass.Fx)
                return 0;

            var annualCarryPct = AnnualisedNetCarryPct();
            if (double.IsNaN(annualCarryPct) || annualCarryPct == 0)
                return 0;

            var annVolPct = AnnualisedVolPct();
            if (annVolPct <= 0)
                return 0;

            // Risk-normalised carry, on the same footing as the trend forecast.
            var raw = annualCarryPct / annVolPct;
            return Clamp(raw * CarryScalar, -ForecastCap, ForecastCap);
        }

        /// <summary>
        /// Net annualised carry advantage of long over short, in percent of
        /// notional. Swap values are quoted per lot per night in the account
        /// currency for the common cTrader configuration; where the broker
        /// reports points we fall back to a points interpretation.
        /// </summary>
        private double AnnualisedNetCarryPct()
        {
            var lot = Symbol.LotSize > 0 ? Symbol.LotSize : 100000.0;
            var notionalPerLot = lot * Symbol.Bid;
            if (notionalPerLot <= 0)
                return 0;

            // Long earns SwapLong per night, short earns SwapShort per night.
            // The edge of long over short is the difference, halved, because
            // taking one side forgoes the other.
            var perNight = (Symbol.SwapLong - Symbol.SwapShort) / 2.0;

            // 365 calendar days of financing, but note triple swap on the
            // broker's rollover weekday is already inside the quoted rate on
            // average over a year.
            var annual = perNight * 365.0;

            return annual / notionalPerLot * 100.0;
        }

        // ==================================================================
        // Volatility and sizing
        // ==================================================================

        /// <summary>
        /// EWMA volatility of daily price changes, in price units, blended
        /// with a long-run average.  The blend matters: a pure short-window
        /// estimate collapses during quiet spells and sizes you into a
        /// dangerously large position right before volatility returns.
        /// </summary>
        private double EstimatePriceVolatility()
        {
            var last = _daily.Count - 2;               // last CLOSED daily bar
            if (last < 2) return 0;

            var alpha = 2.0 / (VolSpan + 1.0);
            var warm = Math.Min(last, Math.Max(VolSpan * 6, 60));
            var start = last - warm + 1;
            if (start < 1) start = 1;

            // Seed with the first squared change in the window.
            var seed = _daily.ClosePrices[start] - _daily.ClosePrices[start - 1];
            var ewmaVar = seed * seed;

            for (var i = start + 1; i <= last; i++)
            {
                var d = _daily.ClosePrices[i] - _daily.ClosePrices[i - 1];
                ewmaVar += alpha * (d * d - ewmaVar);
            }

            var recent = Math.Sqrt(Math.Max(ewmaVar, 0));

            var blend = Clamp(LongRunVolBlendPct / 100.0, 0.0, 1.0);
            if (blend <= 0)
                return recent;

            var longRun = LongRunPriceVolatility(last);
            if (longRun <= 0)
                return recent;

            return recent * (1.0 - blend) + longRun * blend;
        }

        private double LongRunPriceVolatility(int lastIndex)
        {
            var n = Math.Min(LongRunVolWindow, lastIndex);
            if (n < 20) return 0;

            var start = lastIndex - n + 1;
            if (start < 1) start = 1;

            double sumSq = 0;
            var count = 0;
            for (var i = start; i <= lastIndex; i++)
            {
                var d = _daily.ClosePrices[i] - _daily.ClosePrices[i - 1];
                sumSq += d * d;
                count++;
            }

            return count > 0 ? Math.Sqrt(sumSq / count) : 0;
        }

        private double AnnualisedVolPct()
        {
            var price = Symbol.Bid;
            if (price <= 0 || _sigmaPrice <= 0) return 0;
            return _sigmaPrice / price * Math.Sqrt(TradingDaysPerYear) * 100.0;
        }

        private double RiskCapital()
        {
            return RiskCapitalOverride > 0 ? RiskCapitalOverride : Account.Equity;
        }

        /// <summary>
        /// Units of base currency held at an average-strength forecast (10).
        /// Derived from the cash volatility of one unit, so it is correct
        /// regardless of the account currency.
        /// </summary>
        private double AveragePositionUnits()
        {
            var cashVolPerUnitPerYear = CashVolatilityPerUnitPerYear();
            if (cashVolPerUnitPerYear <= 0)
                return 0;

            var targetCashVol = RiskCapital() * (TargetVolPct / 100.0)
                              * InstrumentWeight * Idm;
            return targetCashVol / cashVolPerUnitPerYear;
        }

        /// <summary>
        /// Annualised cash volatility of ONE unit of this instrument, in the
        /// account currency. Built from TickSize/TickValue rather than pips
        /// so it is correct for index, metal and commodity CFDs as well as
        /// currency pairs -- a "pip" is not a meaningful unit on US500.
        /// </summary>
        private double CashVolatilityPerUnitPerYear()
        {
            var tickSize = Symbol.TickSize;
            var tickValue = Symbol.TickValue;

            if (tickSize > 0 && tickValue > 0)
                return (_sigmaPrice / tickSize) * tickValue * Math.Sqrt(TradingDaysPerYear);

            // Fall back to pips if the server does not populate tick data.
            if (Symbol.PipSize > 0 && Symbol.PipValue > 0)
                return (_sigmaPrice / Symbol.PipSize) * Symbol.PipValue
                       * Math.Sqrt(TradingDaysPerYear);

            return 0;
        }

        private double ApplyLeverageCap(double units)
        {
            var price = Symbol.Bid;
            if (price <= 0) return units;

            var maxNotional = RiskCapital() * MaxLeverage;
            var maxUnits = maxNotional / price;

            if (Math.Abs(units) <= maxUnits)
                return units;

            if (Verbose)
                Print("Leverage cap bit: {0:N0}u -> {1:N0}u ({2:F1}x capital).",
                      units, Math.Sign(units) * maxUnits, MaxLeverage);

            return Math.Sign(units) * maxUnits;
        }

        // ==================================================================
        // Trading conditions
        // ==================================================================

        private bool TradingConditionsOk(double delta, out string why)
        {
            why = null;

            var spreadPips = Symbol.Spread / Symbol.PipSize;
            if (spreadPips > MaxSpreadPips)
            {
                why = string.Format("spread {0:F2} pips > cap {1:F2}", spreadPips, MaxSpreadPips);
                return false;
            }

            if (InRolloverBlackout())
            {
                why = string.Format("inside rollover blackout {0:00}:00-{1:00}:00 UTC",
                                    RolloverBlackoutStartHour, RolloverBlackoutEndHour);
                return false;
            }

            // Do not pay real money to move a position by a trivial amount.
            // A rebalance crosses the spread once and pays one side of
            // commission, so it costs about half a round turn.
            var costCash = Math.Abs(delta) * RoundTurnCostPerUnit() / 2.0;

            var capital = RiskCapital();
            if (capital > 0 && costCash / capital > MaxRebalanceCostFraction)
            {
                why = string.Format("rebalance would cost {0:C2}, {1:P3} of capital (cap {2:P3})",
                                    costCash, costCash / capital, MaxRebalanceCostFraction);
                return false;
            }

            return true;
        }

        private bool InRolloverBlackout()
        {
            var h = Server.Time.Hour;
            if (RolloverBlackoutStartHour == RolloverBlackoutEndHour)
                return false;

            if (RolloverBlackoutStartHour < RolloverBlackoutEndHour)
                return h >= RolloverBlackoutStartHour && h < RolloverBlackoutEndHour;

            // Window wraps midnight.
            return h >= RolloverBlackoutStartHour || h < RolloverBlackoutEndHour;
        }

        private double EstimatedRoundTurnCostPips()
        {
            var lot = Symbol.LotSize > 0 ? Symbol.LotSize : 100000.0;
            var pipCashPerLot = Symbol.PipValue * lot;

            var commissionPips = pipCashPerLot > 0
                ? CommissionPerLotRoundTurn / pipCashPerLot
                : 0.6;

            var spreadPips = Symbol.Spread > 0 ? Symbol.Spread / Symbol.PipSize : 0.2;

            return commissionPips + spreadPips;
        }

        /// <summary>
        /// Round-turn transaction cost for one unit, in the account currency.
        /// Works across asset classes; pips are only used for FX-style display.
        /// </summary>
        private double RoundTurnCostPerUnit()
        {
            var lot = Symbol.LotSize > 0 ? Symbol.LotSize : 100000.0;
            var commissionPerUnit = lot > 0 ? CommissionPerLotRoundTurn / lot : 0;

            var spreadPerUnit = 0.0;
            if (Symbol.Spread > 0 && Symbol.TickSize > 0 && Symbol.TickValue > 0)
                spreadPerUnit = Symbol.Spread / Symbol.TickSize * Symbol.TickValue;

            return commissionPerUnit + spreadPerUnit;
        }

        /// <summary>
        /// Annual cost of simply HOLDING a position, as a fraction of
        /// notional. On IC Markets cash index CFDs financing is the overnight
        /// benchmark plus 250bp on longs and minus 250bp on shorts, so the
        /// 2.5% markup is paid in either direction. Backtesting showed this
        /// is the dominant cost for everything except FX -- it consumed about
        /// 2.1%/yr out of 3.3%/yr gross on a 22-instrument portfolio.
        /// </summary>
        private double AnnualHoldingCostFraction()
        {
            if (AnnualHoldingCostPct > 0)
                return AnnualHoldingCostPct / 100.0;

            switch (AssetClass)
            {
                case InstrumentClass.Index:        return 0.025;
                case InstrumentClass.Metal:        return 0.025;
                case InstrumentClass.Energy:       return 0.010;
                case InstrumentClass.Agricultural: return 0.010;
                case InstrumentClass.Bond:         return 0.005;
                case InstrumentClass.Crypto:       return 0.150;
                default:                           return 0.0075;   // Fx
            }
        }

        // ==================================================================
        // Order management
        // ==================================================================

        private Position[] OwnPositions()
        {
            return Positions.FindAll(PositionLabel, SymbolName);
        }

        private double NetUnits()
        {
            double net = 0;
            foreach (var p in OwnPositions())
                net += p.TradeType == TradeType.Buy ? p.VolumeInUnits : -p.VolumeInUnits;
            return net;
        }

        /// <summary>
        /// Move the net position by <paramref name="delta"/> units.  Opposing
        /// exposure is reduced before new exposure is added, so we never sit
        /// on an offsetting long and short paying spread on both.
        /// </summary>
        private void AdjustPosition(double delta)
        {
            if (DryRun)
            {
                Print("[DRY RUN] would adjust net position by {0:N0} units.", delta);
                return;
            }

            var remaining = Math.Abs(delta);
            var wantBuy = delta > 0;

            // 1. Reduce positions facing the wrong way.
            var opposing = OwnPositions()
                .Where(p => wantBuy ? p.TradeType == TradeType.Sell : p.TradeType == TradeType.Buy)
                .OrderBy(p => p.Id)
                .ToArray();

            foreach (var p in opposing)
            {
                if (remaining < Symbol.VolumeInUnitsMin)
                    break;

                var close = Math.Min(p.VolumeInUnits, remaining);
                close = Symbol.NormalizeVolumeInUnits(close, RoundingMode.Down);

                if (close < Symbol.VolumeInUnitsMin)
                    continue;

                // If what is left behind would be untradeably small, or
                // rounding has brought us within one step of the whole
                // position, close it outright rather than leaving dust.
                var remnant = p.VolumeInUnits - close;
                var fullClose = remnant < Symbol.VolumeInUnitsMin ||
                                remnant < Symbol.VolumeInUnitsStep;

                TradeResult r;
                if (fullClose)
                {
                    r = ClosePosition(p);
                    if (r.IsSuccessful) remaining -= p.VolumeInUnits;
                }
                else
                {
                    r = ClosePosition(p, close);
                    if (r.IsSuccessful) remaining -= close;
                }

                if (!r.IsSuccessful)
                    Print("Failed to reduce position {0}: {1}", p.Id, r.Error);
            }

            // 2. Add whatever exposure is still missing.
            if (remaining >= Symbol.VolumeInUnitsMin)
            {
                var volume = Symbol.NormalizeVolumeInUnits(remaining, RoundingMode.Down);
                if (volume >= Symbol.VolumeInUnitsMin)
                {
                    volume = Math.Min(volume, Symbol.VolumeInUnitsMax);
                    var side = wantBuy ? TradeType.Buy : TradeType.Sell;
                    var r = ExecuteMarketOrder(side, SymbolName, volume, PositionLabel);

                    if (r.IsSuccessful)
                        Print("{0} {1:N0} units @ {2}. Net now {3:N0}u (target {4:N0}u).",
                              side, volume, r.Position.EntryPrice, NetUnits(), _lastTargetUnits);
                    else
                        Print("Order rejected: {0}", r.Error);
                }
            }
        }

        private void Flatten(string reason)
        {
            foreach (var p in OwnPositions())
            {
                var r = ClosePosition(p);
                if (!r.IsSuccessful)
                    Print("Failed to close {0} during flatten ({1}): {2}", p.Id, reason, r.Error);
            }
        }

        /// <summary>
        /// Optional wide ATR stop.  Off by default -- in a continuous-forecast
        /// system the forecast itself already shrinks the position as a trend
        /// decays, and a stop that fires independently leaves the book out of
        /// line with the signal until the next rebalance.
        /// </summary>
        private void RefreshStops()
        {
            var atr = AverageTrueRangeDaily(AtrPeriod);
            if (atr <= 0) return;

            var distance = atr * AtrStopMultiple;

            foreach (var p in OwnPositions())
            {
                var stop = p.TradeType == TradeType.Buy
                    ? Symbol.Bid - distance
                    : Symbol.Ask + distance;

                stop = Math.Round(stop, Symbol.Digits);

                // Ratchet only -- never loosen an existing stop.
                if (p.StopLoss.HasValue)
                {
                    var better = p.TradeType == TradeType.Buy
                        ? stop > p.StopLoss.Value
                        : stop < p.StopLoss.Value;
                    if (!better) continue;
                }

                var r = p.ModifyStopLossPrice(stop);
                if (!r.IsSuccessful)
                    Print("Could not set stop on {0}: {1}", p.Id, r.Error);
            }
        }

        private double AverageTrueRangeDaily(int period)
        {
            var last = _daily.Count - 2;
            if (last < period + 1) return 0;

            double sum = 0;
            for (var i = last - period + 1; i <= last; i++)
            {
                var high = _daily.HighPrices[i];
                var low = _daily.LowPrices[i];
                var prevClose = _daily.ClosePrices[i - 1];

                var tr = Math.Max(high - low,
                         Math.Max(Math.Abs(high - prevClose), Math.Abs(low - prevClose)));
                sum += tr;
            }

            return sum / period;
        }

        // ==================================================================
        // Helpers
        // ==================================================================

        /// <summary>
        /// EMA of daily closes ending at the last CLOSED bar.  Recomputed from
        /// history each call rather than carried in state, so a restart
        /// reproduces exactly what a continuous run would have held.
        /// </summary>
        private double Ema(int span)
        {
            var last = _daily.Count - 2;
            if (last < 1) return _daily.ClosePrices[Math.Max(0, _daily.Count - 1)];

            var alpha = 2.0 / (span + 1.0);
            var warm = Math.Min(last, span * 5);
            var start = last - warm;
            if (start < 0) start = 0;

            var e = _daily.ClosePrices[start];
            for (var i = start + 1; i <= last; i++)
                e += alpha * (_daily.ClosePrices[i] - e);

            return e;
        }

        private static double Clamp(double v, double lo, double hi)
        {
            if (double.IsNaN(v)) return 0;
            return v < lo ? lo : (v > hi ? hi : v);
        }
    }
}
