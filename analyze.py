"""
Bitcoin Market Sentiment vs Hyperliquid Trader Performance
Comprehensive Data Analysis Pipeline
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────────────────────────
FEAR_GREED_PATH = "fear_greed_index.csv"
HISTORICAL_PATH = "historical_data.csv"
OUTPUT_DIR = "dashboard_data"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 1. LOAD DATA ────────────────────────────────────────────────────────────
print("Loading datasets...")
fg = pd.read_csv(FEAR_GREED_PATH)
trades = pd.read_csv(HISTORICAL_PATH)

print(f"  Fear/Greed Index: {len(fg):,} rows")
print(f"  Historical Trades: {len(trades):,} rows")

# ── 2. CLEAN & PARSE DATES ──────────────────────────────────────────────────
print("Cleaning data...")

# Fear/Greed
fg["date"] = pd.to_datetime(fg["date"])
fg = fg.rename(columns={"value": "sentiment_value", "classification": "sentiment_class"})
fg = fg.sort_values("date").drop_duplicates(subset="date", keep="last").reset_index(drop=True)

# Historical trades
trades.columns = trades.columns.str.strip()

# Parse the IST timestamp  (format: DD-MM-YYYY HH:MM)
trades["trade_date"] = pd.to_datetime(
    trades["Timestamp IST"], format="%d-%m-%Y %H:%M", errors="coerce"
)
trades["date"] = trades["trade_date"].dt.normalize()  # date only

# Numeric conversions
for col in ["Execution Price", "Size Tokens", "Size USD", "Closed PnL", "Fee"]:
    trades[col] = pd.to_numeric(trades[col], errors="coerce")

# Drop rows with unparseable dates
before = len(trades)
trades = trades.dropna(subset=["date"])
print(f"  Dropped {before - len(trades)} rows with bad dates")

# ── 3. MERGE ─────────────────────────────────────────────────────────────────
print("Merging datasets...")
df = trades.merge(fg[["date", "sentiment_value", "sentiment_class"]], on="date", how="inner")
print(f"  Merged dataset: {len(df):,} rows ({df['date'].min().date()} to {df['date'].max().date()})")

# ── 4. HELPER: classify sentiment buckets ────────────────────────────────────
SENTIMENT_ORDER = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]

def safe_json(obj):
    """Make numpy types JSON-serializable."""
    if isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return round(float(obj), 4) if not np.isnan(obj) else 0
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (np.ndarray,)):
        return safe_json(obj.tolist())
    return obj


# ── 5. SENTIMENT DISTRIBUTION (during trading period) ────────────────────────
print("Computing sentiment distribution...")
trading_dates = df["date"].unique()
fg_trading = fg[fg["date"].isin(trading_dates)].copy()

sentiment_dist = (
    fg_trading["sentiment_class"]
    .value_counts()
    .reindex(SENTIMENT_ORDER, fill_value=0)
    .to_dict()
)

# Timeline of sentiment
sentiment_timeline = (
    fg_trading.sort_values("date")
    .assign(date_str=lambda x: x["date"].dt.strftime("%Y-%m-%d"))
    [["date_str", "sentiment_value", "sentiment_class"]]
    .to_dict(orient="records")
)

# ── 6. PNL BY SENTIMENT REGIME ──────────────────────────────────────────────
print("Analyzing PnL by sentiment regime...")

# Only closed trades have meaningful PnL
closed = df[df["Direction"].str.contains("Close", case=False, na=False)].copy()

pnl_by_sentiment = {}
for s in SENTIMENT_ORDER:
    subset = closed[closed["sentiment_class"] == s]["Closed PnL"]
    if len(subset) == 0:
        continue
    pnl_by_sentiment[s] = {
        "count": int(len(subset)),
        "total_pnl": round(float(subset.sum()), 2),
        "mean_pnl": round(float(subset.mean()), 4),
        "median_pnl": round(float(subset.median()), 4),
        "std_pnl": round(float(subset.std()), 4),
        "win_rate": round(float((subset > 0).sum() / len(subset) * 100), 2),
        "total_winners": int((subset > 0).sum()),
        "total_losers": int((subset <= 0).sum()),
        "avg_win": round(float(subset[subset > 0].mean()), 4) if (subset > 0).any() else 0,
        "avg_loss": round(float(subset[subset <= 0].mean()), 4) if (subset <= 0).any() else 0,
        "best_trade": round(float(subset.max()), 2),
        "worst_trade": round(float(subset.min()), 2),
        "q25": round(float(subset.quantile(0.25)), 4),
        "q75": round(float(subset.quantile(0.75)), 4),
    }

# ── 7. DIRECTIONAL ANALYSIS (Long vs Short) ─────────────────────────────────
print("Analyzing long vs short by sentiment...")

directional = {}
for s in SENTIMENT_ORDER:
    subset = closed[closed["sentiment_class"] == s]
    if len(subset) == 0:
        continue
    longs = subset[subset["Direction"].str.contains("Long", case=False, na=False)]
    shorts = subset[subset["Direction"].str.contains("Short", case=False, na=False)]
    directional[s] = {
        "long_count": int(len(longs)),
        "short_count": int(len(shorts)),
        "long_total_pnl": round(float(longs["Closed PnL"].sum()), 2),
        "short_total_pnl": round(float(shorts["Closed PnL"].sum()), 2),
        "long_mean_pnl": round(float(longs["Closed PnL"].mean()), 4) if len(longs) > 0 else 0,
        "short_mean_pnl": round(float(shorts["Closed PnL"].mean()), 4) if len(shorts) > 0 else 0,
        "long_win_rate": round(float((longs["Closed PnL"] > 0).sum() / len(longs) * 100), 2) if len(longs) > 0 else 0,
        "short_win_rate": round(float((shorts["Closed PnL"] > 0).sum() / len(shorts) * 100), 2) if len(shorts) > 0 else 0,
    }

# ── 8. VOLUME & ACTIVITY BY SENTIMENT ───────────────────────────────────────
print("Computing volume by sentiment...")

volume_by_sentiment = {}
for s in SENTIMENT_ORDER:
    subset = df[df["sentiment_class"] == s]
    if len(subset) == 0:
        continue
    volume_by_sentiment[s] = {
        "total_volume_usd": round(float(subset["Size USD"].sum()), 2),
        "avg_trade_size_usd": round(float(subset["Size USD"].mean()), 2),
        "trade_count": int(len(subset)),
        "unique_traders": int(subset["Account"].nunique()),
        "unique_coins": int(subset["Coin"].nunique()),
    }

# ── 9. DAILY AGGREGATES ─────────────────────────────────────────────────────
print("Computing daily aggregates...")

daily_closed = closed.groupby("date").agg(
    total_pnl=("Closed PnL", "sum"),
    trade_count=("Closed PnL", "count"),
    win_count=("Closed PnL", lambda x: (x > 0).sum()),
    total_volume=("Size USD", "sum"),
    avg_pnl=("Closed PnL", "mean"),
).reset_index()

daily_all = df.groupby("date").agg(
    all_trade_count=("Size USD", "count"),
    all_volume=("Size USD", "sum"),
    unique_traders=("Account", "nunique"),
).reset_index()

daily = daily_closed.merge(daily_all, on="date", how="outer").fillna(0)
daily["win_rate"] = np.where(daily["trade_count"] > 0, daily["win_count"] / daily["trade_count"] * 100, 0)

# Merge sentiment
daily = daily.merge(fg[["date", "sentiment_value", "sentiment_class"]], on="date", how="left")
daily = daily.sort_values("date")

daily_data = (
    daily.assign(date_str=lambda x: x["date"].dt.strftime("%Y-%m-%d"))
    [["date_str", "total_pnl", "trade_count", "win_rate", "all_volume",
      "unique_traders", "sentiment_value", "sentiment_class", "avg_pnl"]]
    .to_dict(orient="records")
)

# ── 10. TOP TRADER PROFILES ─────────────────────────────────────────────────
print("Profiling top traders...")

trader_stats = closed.groupby("Account").agg(
    total_pnl=("Closed PnL", "sum"),
    trade_count=("Closed PnL", "count"),
    win_count=("Closed PnL", lambda x: (x > 0).sum()),
    total_volume=("Size USD", "sum"),
    total_fees=("Fee", "sum"),
    avg_trade_size=("Size USD", "mean"),
    best_trade=("Closed PnL", "max"),
    worst_trade=("Closed PnL", "min"),
).reset_index()

trader_stats["win_rate"] = np.where(
    trader_stats["trade_count"] > 0,
    trader_stats["win_count"] / trader_stats["trade_count"] * 100, 0
)
trader_stats["net_pnl"] = trader_stats["total_pnl"] - trader_stats["total_fees"]

# Top 10 most profitable
top_profitable = trader_stats.nlargest(10, "total_pnl")

# Add favorite sentiment regime for each top trader
top_profiles = []
for _, row in top_profitable.iterrows():
    acct = row["Account"]
    acct_trades = closed[closed["Account"] == acct]
    fav_sentiment = acct_trades["sentiment_class"].mode()
    fav_coin = acct_trades["Coin"].mode()

    # Performance by sentiment for this trader
    perf_by_sent = {}
    for s in SENTIMENT_ORDER:
        s_trades = acct_trades[acct_trades["sentiment_class"] == s]
        if len(s_trades) > 0:
            perf_by_sent[s] = {
                "pnl": round(float(s_trades["Closed PnL"].sum()), 2),
                "count": int(len(s_trades)),
                "win_rate": round(float((s_trades["Closed PnL"] > 0).sum() / len(s_trades) * 100), 2)
            }

    top_profiles.append({
        "account": acct[:10] + "..." + acct[-6:],
        "total_pnl": round(float(row["total_pnl"]), 2),
        "trade_count": int(row["trade_count"]),
        "win_rate": round(float(row["win_rate"]), 2),
        "total_volume": round(float(row["total_volume"]), 2),
        "best_trade": round(float(row["best_trade"]), 2),
        "worst_trade": round(float(row["worst_trade"]), 2),
        "favorite_sentiment": fav_sentiment.iloc[0] if len(fav_sentiment) > 0 else "Unknown",
        "favorite_coin": fav_coin.iloc[0] if len(fav_coin) > 0 else "Unknown",
        "performance_by_sentiment": perf_by_sent,
    })

# Bottom 10 (worst performers)
bottom_profiles = []
bottom_losers = trader_stats.nsmallest(10, "total_pnl")
for _, row in bottom_losers.iterrows():
    acct = row["Account"]
    acct_trades = closed[closed["Account"] == acct]
    fav_sentiment = acct_trades["sentiment_class"].mode()

    bottom_profiles.append({
        "account": acct[:10] + "..." + acct[-6:],
        "total_pnl": round(float(row["total_pnl"]), 2),
        "trade_count": int(row["trade_count"]),
        "win_rate": round(float(row["win_rate"]), 2),
        "total_volume": round(float(row["total_volume"]), 2),
        "favorite_sentiment": fav_sentiment.iloc[0] if len(fav_sentiment) > 0 else "Unknown",
    })

# ── 11. COIN ANALYSIS ───────────────────────────────────────────────────────
print("Analyzing coins...")

top_coins = df["Coin"].value_counts().head(15).index.tolist()

coin_analysis = {}
for coin in top_coins:
    coin_trades = closed[closed["Coin"] == coin]
    if len(coin_trades) == 0:
        continue
    by_sent = {}
    for s in SENTIMENT_ORDER:
        st = coin_trades[coin_trades["sentiment_class"] == s]
        if len(st) > 0:
            by_sent[s] = {
                "count": int(len(st)),
                "total_pnl": round(float(st["Closed PnL"].sum()), 2),
                "win_rate": round(float((st["Closed PnL"] > 0).sum() / len(st) * 100), 2),
            }
    coin_analysis[coin] = {
        "total_trades": int(len(coin_trades)),
        "total_pnl": round(float(coin_trades["Closed PnL"].sum()), 2),
        "win_rate": round(float((coin_trades["Closed PnL"] > 0).sum() / len(coin_trades) * 100), 2),
        "by_sentiment": by_sent,
    }

# ── 12. CORRELATION ANALYSIS ────────────────────────────────────────────────
print("Computing correlations...")

corr_data = daily[["sentiment_value", "total_pnl", "trade_count", "all_volume", "win_rate"]].dropna()
correlation_matrix = {}
for col in ["total_pnl", "trade_count", "all_volume", "win_rate"]:
    if corr_data["sentiment_value"].std() > 0 and corr_data[col].std() > 0:
        correlation_matrix[col] = round(float(corr_data["sentiment_value"].corr(corr_data[col])), 4)
    else:
        correlation_matrix[col] = 0

# ── 13. SENTIMENT TRANSITION ANALYSIS ───────────────────────────────────────
print("Analyzing sentiment transitions...")

fg_sorted = fg_trading.sort_values("date").reset_index(drop=True)
fg_sorted["prev_class"] = fg_sorted["sentiment_class"].shift(1)
fg_sorted["transition"] = fg_sorted["prev_class"] + " → " + fg_sorted["sentiment_class"]

transitions_with_pnl = []
for i, row in fg_sorted.dropna(subset=["prev_class"]).iterrows():
    d = row["date"]
    day_trades = closed[closed["date"] == d]
    if len(day_trades) > 0:
        transitions_with_pnl.append({
            "transition": row["transition"],
            "total_pnl": float(day_trades["Closed PnL"].sum()),
            "trade_count": int(len(day_trades)),
        })

transition_df = pd.DataFrame(transitions_with_pnl)
if len(transition_df) > 0:
    transition_summary = (
        transition_df.groupby("transition")
        .agg(
            avg_pnl=("total_pnl", "mean"),
            total_pnl=("total_pnl", "sum"),
            occurrences=("trade_count", "count"),
        )
        .sort_values("avg_pnl", ascending=False)
        .head(15)
        .reset_index()
        .to_dict(orient="records")
    )
else:
    transition_summary = []


# ── 14. HOURLY PATTERNS ─────────────────────────────────────────────────────
print("Analyzing hourly trading patterns...")

df["hour"] = df["trade_date"].dt.hour
hourly_by_sentiment = {}
for s in SENTIMENT_ORDER:
    subset = closed[closed["sentiment_class"] == s].copy()
    subset["hour"] = subset["trade_date"].dt.hour
    if len(subset) == 0:
        continue
    hourly = subset.groupby("hour").agg(
        count=("Closed PnL", "count"),
        total_pnl=("Closed PnL", "sum"),
    ).reset_index()
    hourly_by_sentiment[s] = hourly.to_dict(orient="records")


# ── 15. SUMMARY STATS ───────────────────────────────────────────────────────
print("Building summary stats...")

summary = {
    "total_trades": int(len(df)),
    "closed_trades": int(len(closed)),
    "unique_traders": int(df["Account"].nunique()),
    "unique_coins": int(df["Coin"].nunique()),
    "date_range": f"{df['date'].min().strftime('%b %d, %Y')} – {df['date'].max().strftime('%b %d, %Y')}",
    "total_volume_usd": round(float(df["Size USD"].sum()), 2),
    "total_pnl": round(float(closed["Closed PnL"].sum()), 2),
    "overall_win_rate": round(float((closed["Closed PnL"] > 0).sum() / len(closed) * 100), 2),
    "avg_sentiment": round(float(fg_trading["sentiment_value"].mean()), 1),
    "total_fees": round(float(df["Fee"].sum()), 2),
}


# ── 16. PNL DISTRIBUTION DATA (for box plots) ───────────────────────────────
print("Building PnL distribution data...")

pnl_distributions = {}
for s in SENTIMENT_ORDER:
    subset = closed[closed["sentiment_class"] == s]["Closed PnL"]
    if len(subset) > 0:
        # Cap at 500 samples for performance; use random sample
        sample = subset.sample(min(500, len(subset)), random_state=42)
        pnl_distributions[s] = [round(float(v), 4) for v in sample.values]


# ── 17. WRITE ALL JSON FILES ────────────────────────────────────────────────
print("Writing JSON outputs...")

outputs = {
    "summary.json": summary,
    "sentiment_distribution.json": sentiment_dist,
    "sentiment_timeline.json": sentiment_timeline,
    "pnl_by_sentiment.json": pnl_by_sentiment,
    "directional_analysis.json": directional,
    "volume_by_sentiment.json": volume_by_sentiment,
    "daily_data.json": daily_data,
    "top_traders.json": top_profiles,
    "bottom_traders.json": bottom_profiles,
    "coin_analysis.json": coin_analysis,
    "correlations.json": correlation_matrix,
    "transition_analysis.json": transition_summary,
    "hourly_patterns.json": hourly_by_sentiment,
    "pnl_distributions.json": pnl_distributions,
}

for fname, data in outputs.items():
    path = os.path.join(OUTPUT_DIR, fname)
    with open(path, "w") as f:
        json.dump(safe_json(data), f, indent=2)
    print(f"  [OK] {fname}")

print(f"\nAnalysis complete! {len(outputs)} files written to '{OUTPUT_DIR}/'")
print(f"   Summary: {summary['total_trades']:,} trades, {summary['unique_traders']} traders, "
      f"{summary['unique_coins']} coins, ${summary['total_volume_usd']:,.0f} volume")
