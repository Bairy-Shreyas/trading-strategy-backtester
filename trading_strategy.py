import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------
# 1. Fetch Data
# -------------------------------
data = yf.download("RELIANCE.NS", start="2022-01-01", end="2024-01-01")
data = data.dropna().reset_index(drop=True)

# -------------------------------
# 2. Pattern Detection
# -------------------------------

def detect_hammer(df):
    open_ = df['Open']
    close_ = df['Close']
    high_ = df['High']
    low_ = df['Low']

    body = abs(close_ - open_)
    lower_shadow = (open_.where(open_ < close_, close_)) - low_
    upper_shadow = high_ - (open_.where(open_ > close_, close_))

    return ((lower_shadow > 2 * body) & (upper_shadow < body)).fillna(False)

def detect_bullish_engulfing(df):
    prev_open = df['Open'].shift(1)
    prev_close = df['Close'].shift(1)

    return (
        (prev_close < prev_open) &
        (df['Close'] > df['Open']) &
        (df['Close'] > prev_open) &
        (df['Open'] < prev_close)
    ).fillna(False)

data['Hammer'] = detect_hammer(data)
data['Bullish_Engulfing'] = detect_bullish_engulfing(data)

# -------------------------------
# 3. Support Level
# -------------------------------
data['Support'] = data['Low'].rolling(window=5).min()

# -------------------------------
# 4. Strategy Logic
# -------------------------------
signals = []

for i in range(len(data)):
    hammer = bool(data['Hammer'].iloc[i])
    bullish = bool(data['Bullish_Engulfing'].iloc[i])

    if pd.notna(data['Support'].iloc[i]):
        support = data['Support'].iloc[i].item()
        close = data['Close'].iloc[i].item()

        if (hammer or bullish) and close <= support * 1.02:
            signals.append(1)
        else:
            signals.append(0)
    else:
        signals.append(0)

data['Signal'] = signals

# -------------------------------
# 5. Backtesting + Equity Curve
# -------------------------------
returns = []
equity = [1]  # start with 1 (100%)
buy_points_x = []
buy_points_y = []

for i in range(len(data) - 1):
    if data['Signal'].iloc[i] == 1:
        entry = data['Close'].iloc[i].item()
        exit_price = data['Close'].iloc[i + 1].item()
        ret = (exit_price - entry) / entry
        returns.append(ret)

        # equity update
        equity.append(equity[-1] * (1 + ret))

        # store buy marker
        buy_points_x.append(i)
        buy_points_y.append(entry)
    else:
        equity.append(equity[-1])

# -------------------------------
# 6. Results
# -------------------------------
if len(returns) > 0:
    win_rate = sum(1 for r in returns if r > 0) / len(returns)
    avg_return = sum(returns) / len(returns)

    print("\n📊 RESULTS")
    print("Total Trades:", len(returns))
    print("Win Rate:", round(win_rate * 100, 2), "%")
    print("Avg Return:", round(avg_return * 100, 2), "%")
else:
    print("\nNo trades found")

# -------------------------------
# 7. Plot (WITH MARKERS)
# -------------------------------
plt.figure(figsize=(12, 5))
plt.plot(data['Close'], label="Price")

# Buy signals
plt.scatter(buy_points_x, buy_points_y, marker="^", label="Buy", s=100)

plt.title("Stock Price with Buy Signals")
plt.legend()
plt.show()

# -------------------------------
# 8. Equity Curve
# -------------------------------
plt.figure(figsize=(12, 5))
plt.plot(equity)
plt.title("Equity Curve (Strategy Performance)")
plt.show()
