import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

# --- Load GSW zero-coupon yields ---
gsw = pd.read_csv("feds200628.csv", skiprows=9)
gsw["Date"] = pd.to_datetime(gsw["Date"])

# Convert zero-coupon yields to numeric
maturities = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
columns = ["SVENY01","SVENY02","SVENY03","SVENY04","SVENY05","SVENY06","SVENY07","SVENY08","SVENY09","SVENY10"]

for col in columns:
    gsw[col] = pd.to_numeric(gsw[col], errors="coerce")

# --- Load 3-month T-bill from H15 ---
h15 = pd.read_csv("FRB_H15.csv", skiprows=5)
h15["Date"] = pd.to_datetime(h15.iloc[:, 0])
h15["y_3month"] = pd.to_numeric(h15["RIFLGFCM03_N.B"], errors="coerce")
h15 = h15[["Date", "y_3month"]].dropna()

# --- Merge datasets ---
df = pd.merge(gsw, h15, on="Date", how="inner")

# --- Filter last 12 months ---
df = df[df["Date"] >= pd.Timestamp.now() - pd.Timedelta(days=365)]

# --- Compute 2-10 spread ---
df["spread_2_10"] = df["SVENY10"] - df["SVENY02"]

# --- Compute near-term forward spread using cubic spline ---
ntfs_list = []

for idx, row in df.iterrows():
    ylds = row[columns].values
    cs = CubicSpline(maturities, ylds)
    yld6 = cs(1.5)
    yld7 = cs(1.75)
    fwd6 = 7 * yld7 - 6 * yld6
    ntfs = fwd6 - row["y_3month"]
    ntfs_list.append(ntfs)

df["ntfs"] = ntfs_list

# --- Get most recent values ---
last_date = df["Date"].iloc[-1]
last_2_10 = df["spread_2_10"].iloc[-1]
last_ntfs = df["ntfs"].iloc[-1]

# --- Plot ---
fig, ax = plt.subplots(figsize=(14, 7))

# Plot lines
ax.plot(df["Date"], df["spread_2_10"], label="2–10 Spread (10Y - 2Y)", 
        color="steelblue", lw=2.5)
ax.plot(df["Date"], df["ntfs"], label="Near-Term Forward Spread", 
        color="coral", lw=2.5)
ax.axhline(0, color="black", linestyle="--", linewidth=1, alpha=0.7)

# Add annotations for most recent values
# For 2-10 spread
ax.annotate(f'{last_2_10:.2f}%', 
            xy=(last_date, last_2_10),
            xytext=(10, 0), textcoords='offset points',
            fontsize=11, fontweight='bold', color='steelblue',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                     edgecolor='steelblue', linewidth=2))

# For NTFS
ax.annotate(f'{last_ntfs:.2f}%', 
            xy=(last_date, last_ntfs),
            xytext=(10, 0), textcoords='offset points',
            fontsize=11, fontweight='bold', color='coral',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                     edgecolor='coral', linewidth=2))

# Add date label
ax.text(0.98, 0.02, f'As of: {last_date.strftime("%b %d, %Y")}',
        transform=ax.transAxes, fontsize=10, 
        verticalalignment='bottom', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.set_title("Yield Spreads: Last 12 Months", fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel("Date", fontsize=12)
ax.set_ylabel("Percentage Points", fontsize=12)
ax.legend(loc="upper left", fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# --- Print summary ---
print("\n" + "="*60)
print("MOST RECENT VALUES")
print("="*60)
print(f"Date: {last_date.strftime('%B %d, %Y')}")
print(f"2-10 Spread: {last_2_10:.2f}%")
print(f"Near-Term Forward Spread: {last_ntfs:.2f}%")
print("="*60)