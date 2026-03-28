# Bitcoin Market Sentiment × Hyperliquid Trader Performance Analysis

An end-to-end data analysis pipeline and interactive web dashboard that explores the relationship between **Bitcoin's Fear & Greed Index** and **Hyperliquid trader performance** — uncovering hidden patterns and delivering insights that drive smarter trading strategies.
U can view this : https://hemanthtempalli.github.io/Trader-Behavior-Insights/
---

## Table of Contents

- [Overview](#overview)
- [Datasets](#datasets)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Dashboard Sections](#dashboard-sections)
- [Key Findings](#key-findings)
- [Technologies Used](#technologies-used)

---

## Overview

This project merges two datasets — **Bitcoin Fear & Greed Index** (market sentiment) and **Hyperliquid historical trader data** — to analyze how market sentiment impacts trader behavior, profitability, and risk exposure.

### At a Glance

| Metric            | Value                          |
|-------------------|--------------------------------|
| Total Trades      | 211,218                        |
| Closed Trades     | 84,685                         |
| Unique Traders    | 32                             |
| Coins Traded      | 246                            |
| Total Volume      | $1.19 Billion                  |
| Total PnL         | $7.29 Million                  |
| Overall Win Rate  | 83.54%                         |
| Analysis Period   | May 2023 – May 2025            |

---

## Datasets

### 1. Bitcoin Fear & Greed Index (`fear_greed_index.csv`)

Daily sentiment classification for Bitcoin from February 2018 to May 2025.

| Column           | Description                                          |
|------------------|------------------------------------------------------|
| `timestamp`      | Unix timestamp                                       |
| `value`          | Sentiment score (0–100)                              |
| `classification` | Sentiment label: Extreme Fear, Fear, Neutral, Greed, Extreme Greed |
| `date`           | Date in YYYY-MM-DD format                            |

### 2. Hyperliquid Historical Trader Data (`historical_data.csv`)

Granular trade execution records from Hyperliquid DEX.

| Column            | Description                                |
|-------------------|--------------------------------------------|
| `Account`         | Trader wallet address                      |
| `Coin`            | Trading pair / token symbol                |
| `Execution Price` | Price at which trade was executed           |
| `Size Tokens`     | Trade size in token units                  |
| `Size USD`        | Trade size in USD                          |
| `Side`            | BUY or SELL                                |
| `Timestamp IST`   | Execution time (IST timezone)              |
| `Start Position`  | Position size before the trade             |
| `Direction`       | Trade direction (Buy, Close Long, Close Short, etc.) |
| `Closed PnL`      | Realized profit/loss for the trade         |
| `Fee`             | Transaction fee                            |
| `Crossed`         | Whether the trade crossed the spread       |

---

## Project Structure

```
prime/
├── fear_greed_index.csv        # Bitcoin sentiment dataset
├── historical_data.csv         # Hyperliquid trader dataset
├── analyze.py                  # Data processing & analysis pipeline
├── index.html                  # Interactive dashboard (single-page app)
├── style.css                   # Dashboard styling (dark glassmorphism theme)
├── dashboard_data/             # Generated JSON files (output of analyze.py)
│   ├── summary.json
│   ├── sentiment_distribution.json
│   ├── sentiment_timeline.json
│   ├── pnl_by_sentiment.json
│   ├── directional_analysis.json
│   ├── volume_by_sentiment.json
│   ├── daily_data.json
│   ├── top_traders.json
│   ├── bottom_traders.json
│   ├── coin_analysis.json
│   ├── correlations.json
│   ├── transition_analysis.json
│   ├── hourly_patterns.json
│   └── pnl_distributions.json
└── README.md
```

---

## Installation & Setup

### Prerequisites

- **Python 3.8+**
- Python packages: `pandas`, `numpy`

### Install Dependencies

```bash
pip install pandas numpy
```

> **Note:** The dashboard uses [Plotly.js](https://plotly.com/javascript/) loaded via CDN — no additional JavaScript dependencies need to be installed.

---

## Usage

### Step 1: Run the Analysis Pipeline

```bash
python analyze.py
```

This will:
- Load and clean both datasets
- Merge trades with daily sentiment data
- Compute metrics across 14 analysis dimensions
- Export results as JSON files to `dashboard_data/`

**Expected output:**
```
Loading datasets...
  Fear/Greed Index: 2,644 rows
  Historical Trades: 211,224 rows
Cleaning data...
Merging datasets...
  Merged dataset: 211,218 rows (2023-05-01 to 2025-05-01)
...
Analysis complete! 14 files written to 'dashboard_data/'
   Summary: 211,218 trades, 32 traders, 246 coins, $1,191,098,774 volume
```

### Step 2: Launch the Dashboard

```bash
python -m http.server 8080
```

### Step 3: Open in Browser

Navigate to **[http://localhost:8080](http://localhost:8080)** in your browser.

---

## Dashboard Sections

The interactive dashboard contains **12 sections** with **15+ charts**:

| #  | Section                   | Visualization Type          | Description                                                  |
|----|---------------------------|-----------------------------|--------------------------------------------------------------|
| 1  | Hero & Stats              | Stat cards                  | Key metrics — total trades, volume, PnL, win rate            |
| 2  | Sentiment Landscape       | Donut chart + Line chart    | Sentiment distribution and Fear/Greed timeline               |
| 3  | Performance by Sentiment  | Bar charts                  | Mean PnL and Win Rate per sentiment regime                   |
| 4  | PnL Distribution          | Box plots                   | PnL spread across sentiment regimes                          |
| 5  | Long vs Short Analysis    | Grouped bar charts          | Longs vs Shorts performance and win rates                    |
| 6  | Volume & Activity         | Bar charts + Dual axis      | Trading volume, active traders & coins per regime            |
| 7  | Correlation Analysis      | Metric cards with bars      | Sentiment correlation with PnL, volume, trade count, win rate|
| 8  | Daily Trends              | Time-series (bar + line)    | Daily PnL overlaid with sentiment index                      |
| 9  | Sentiment Transitions     | Horizontal bar chart        | PnL impact when sentiment shifts between regimes             |
| 10 | Top Traders               | Interactive table            | Leaderboard with top/worst performer toggle                  |
| 11 | Coin Analysis             | Bar charts + Heatmap        | Top coins by PnL and Coin × Sentiment heatmap               |
| 12 | Key Insights              | Insight cards               | 6 data-driven strategy recommendations                      |

---

## Key Findings

### 1. Fear = Opportunity
The **Fear** regime produces the highest mean PnL at **$126.41 per trade** with an **88.6% win rate**. The old adage *"Be greedy when others are fearful"* is validated by the data.

### 2. Greed = Higher Risk
The **Greed** regime has the **lowest win rate (76.1%)** and the worst single trade loss (**-$117,990**), indicating elevated risk when market confidence is high.

### 3. Traders Are More Active During Fear
Sentiment is **negatively correlated** with both trading volume (r = -0.264) and trade count (r = -0.262), meaning traders increase activity during fearful markets.

### 4. Longs Dominate
Long positions generate significantly more profit across **all** sentiment regimes. Shorts only outperform in specific transitional periods.

### 5. Contrarian Strategy Works
The data supports a **counter-sentiment trading** approach:
- **Increase** position sizes during **Fear** regimes
- **Reduce** exposure during **Greed** regimes
- Focus on **long positions** for maximum edge

### Correlation Summary

| Metric         | Correlation with Sentiment |
|----------------|---------------------------|
| Daily PnL      | -0.208                    |
| Trade Count    | -0.262                    |
| Trading Volume | -0.264                    |
| Win Rate       | +0.138                    |

---

## Technologies Used

| Technology    | Purpose                                    |
|---------------|--------------------------------------------|
| Python 3.12   | Data processing and analysis               |
| Pandas        | Data manipulation and aggregation          |
| NumPy         | Numerical computations                     |
| Plotly.js      | Interactive chart rendering (via CDN)      |
| HTML5 / CSS3  | Dashboard structure and styling            |
| JavaScript    | Dashboard logic and data loading           |

---

## Analysis Pipeline Details

The `analyze.py` script performs the following computations:

1. **Data Cleaning** — Parse dates, convert numerics, handle missing values
2. **Dataset Merging** — Inner join on date between trades and sentiment
3. **PnL by Sentiment** — Mean, median, std, win rate, best/worst trade per regime
4. **Directional Analysis** — Long vs Short performance per sentiment bucket
5. **Volume Metrics** — Total volume, avg trade size, unique traders/coins per regime
6. **Daily Aggregates** — Daily PnL, volume, trade count, win rate + sentiment overlay
7. **Trader Profiling** — Top 10 / Bottom 10 traders with per-regime breakdowns
8. **Coin Analysis** — Top 15 coins with sentiment-regime performance
9. **Correlations** — Pearson correlation between daily sentiment and trading metrics
10. **Sentiment Transitions** — PnL impact when sentiment shifts (e.g., Fear → Greed)
11. **Hourly Patterns** — Trade count distribution by hour across sentiment regimes
12. **PnL Distributions** — Sampled PnL values for box plot visualization

---

> **Built with data from the Bitcoin Fear & Greed Index and Hyperliquid DEX historical trades.**
