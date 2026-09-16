// Minimal stub of the cAlgo API, used only to syntax/type-check CarryTrendFx.cs.
// Signatures mirror help.ctrader.com. NOT a runtime implementation.
using System;

namespace cAlgo.API.Internals
{
    public enum RoundingMode { ToNearest, Down, Up }
    public enum SymbolCommissionType { UsdPerMillionUsdVolume, UsdPerOneLot, PercentageOfTradingVolume, QuoteCurrencyPerOneLot }

    public abstract class Symbol
    {
        public abstract string Name { get; }
        public abstract double PipSize { get; }
        public abstract double PipValue { get; }
        public abstract double TickSize { get; }
        public abstract double TickValue { get; }
        public abstract int Digits { get; }
        public abstract double Spread { get; }
        public abstract double Bid { get; }
        public abstract double Ask { get; }
        public abstract double VolumeInUnitsMin { get; }
        public abstract double VolumeInUnitsMax { get; }
        public abstract double VolumeInUnitsStep { get; }
        public abstract long LotSize { get; }
        public abstract double Commission { get; }
        public abstract SymbolCommissionType CommissionType { get; }
        public abstract double SwapLong { get; }
        public abstract double SwapShort { get; }
        public abstract double UnrealizedNetProfit { get; }
        public abstract double NormalizeVolumeInUnits(double volume, RoundingMode roundingMode);
        public abstract double QuantityToVolumeInUnits(double quantity);
        public abstract double VolumeInUnitsToQuantity(double volume);
    }

    public abstract class Account
    {
        public abstract double Balance { get; }
        public abstract double Equity { get; }
        public abstract string Currency { get; }
    }
}

namespace cAlgo.API
{
    using cAlgo.API.Internals;

    public enum TradeType { Buy, Sell }
    public enum AccessRights { None, FullAccess }
    public enum TimeZones { UTC }
    public enum ErrorCode { TechnicalError }

    public class TimeFrame { public static readonly TimeFrame Daily = new TimeFrame(); }

    [AttributeUsage(AttributeTargets.Class)]
    public class RobotAttribute : Attribute
    {
        public AccessRights AccessRights { get; set; }
        public TimeZones TimeZone { get; set; }
        public string Name { get; set; }
        public string Version { get; set; }
    }

    [AttributeUsage(AttributeTargets.Property)]
    public class ParameterAttribute : Attribute
    {
        public ParameterAttribute() {}
        public ParameterAttribute(string name) {}
        public string Group { get; set; }
        public object DefaultValue { get; set; }
        public object MinValue { get; set; }
        public object MaxValue { get; set; }
        public object Step { get; set; }
    }

    public abstract class DataSeries { public abstract double this[int index] { get; } public abstract double Last(int i); public abstract int Count { get; } }

    public class BarOpenedEventArgs { public Bars Bars { get; set; } }

    public abstract class Bars
    {
        public abstract int Count { get; }
        public abstract DataSeries OpenPrices { get; }
        public abstract DataSeries HighPrices { get; }
        public abstract DataSeries LowPrices { get; }
        public abstract DataSeries ClosePrices { get; }
        public event Action<BarOpenedEventArgs> BarOpened;
        protected void Fire(BarOpenedEventArgs e) { if (BarOpened != null) BarOpened(e); }
    }

    public abstract class Position
    {
        public abstract int Id { get; }
        public abstract string Label { get; }
        public abstract string SymbolName { get; }
        public abstract TradeType TradeType { get; }
        public abstract double VolumeInUnits { get; }
        public abstract double EntryPrice { get; }
        public abstract double NetProfit { get; }
        public abstract double Pips { get; }
        public abstract double? StopLoss { get; }
        public abstract double? TakeProfit { get; }
        public abstract TradeResult ModifyStopLossPrice(double? stopLoss);
        public abstract TradeResult ModifyTakeProfitPrice(double? takeProfit);
        public abstract TradeResult Close();
    }

    public abstract class TradeResult
    {
        public abstract bool IsSuccessful { get; }
        public abstract ErrorCode? Error { get; }
        public abstract Position Position { get; }
    }

    public abstract class Positions : System.Collections.Generic.IEnumerable<Position>
    {
        public abstract Position Find(string label);
        public abstract Position[] FindAll(string label, string symbolName);
        public abstract System.Collections.Generic.IEnumerator<Position> GetEnumerator();
        System.Collections.IEnumerator System.Collections.IEnumerable.GetEnumerator() { return GetEnumerator(); }
    }

    public abstract class MarketData { public abstract Bars GetBars(TimeFrame timeFrame); }
    public abstract class Server { public abstract DateTime Time { get; } }

    public abstract class Robot
    {
        public Symbol Symbol { get; set; }
        public string SymbolName { get; set; }
        public Bars Bars { get; set; }
        public Positions Positions { get; set; }
        public Account Account { get; set; }
        public Server Server { get; set; }
        public MarketData MarketData { get; set; }
        public bool IsBacktesting { get; set; }

        protected virtual void OnStart() {}
        protected virtual void OnTick() {}
        protected virtual void OnBar() {}
        protected virtual void OnStop() {}

        public void Print(string message) {}
        public void Print(string format, params object[] args) {}
        public void Stop() {}

        public TradeResult ExecuteMarketOrder(TradeType tradeType, string symbolName, double volume) { return null; }
        public TradeResult ExecuteMarketOrder(TradeType tradeType, string symbolName, double volume, string label) { return null; }
        public TradeResult ExecuteMarketOrder(TradeType tradeType, string symbolName, double volume, string label, double? stopLossPips, double? takeProfitPips) { return null; }
        public TradeResult ClosePosition(Position position) { return null; }
        public TradeResult ClosePosition(Position position, double volume) { return null; }
        public TradeResult ModifyPosition(Position position, double? stopLoss, double? takeProfit) { return null; }
    }
}
