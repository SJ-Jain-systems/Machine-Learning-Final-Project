import pandas as pd, numpy as np, os, hashlib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(REPO, "Data")
os.makedirs(OUT, exist_ok=True)

SEED = 4021
day  = pd.read_csv(os.path.join(REPO, "day.csv"),  parse_dates=["dteday"])
hour = pd.read_csv(os.path.join(REPO, "hour.csv"), parse_dates=["dteday"])

# Split unit = calendar DAY, so hourly records never straddle the split (no leakage).
# Stratify by year-month so the reporting set keeps the same seasonal composition.
day["ym"] = day["dteday"].dt.to_period("M").astype(str)
rng = np.random.default_rng(SEED)
report_dates = []
for ym, g in day.groupby("ym"):
    n = int(round(0.20 * len(g)))
    report_dates += list(rng.choice(g["dteday"].values, size=n, replace=False))
report_dates = pd.to_datetime(pd.Series(report_dates)).sort_values()

mask_d = day["dteday"].isin(report_dates)
mask_h = hour["dteday"].isin(report_dates)

day_rep,  day_ana  = day[mask_d].drop(columns="ym"),  day[~mask_d].drop(columns="ym")
hour_rep, hour_ana = hour[mask_h],                    hour[~mask_h]

for name, df in [("reporting_set_day", day_rep), ("reporting_set_hour", hour_rep),
                 ("analysis_set_day",  day_ana), ("analysis_set_hour",  hour_ana)]:
    p = os.path.join(OUT, name + ".csv")
    df.to_csv(p, index=False, date_format="%Y-%m-%d")
    with open(p, "rb") as f: h = hashlib.sha256(f.read()).hexdigest()
    print(f"{name:22s} rows={len(df):6d}  sha256={h}")

report_dates.dt.strftime("%Y-%m-%d").to_csv(os.path.join(OUT, "reporting_set_dates.txt"),
                                            index=False, header=False)
print("\n--- split check ---")
print("days total", len(day), "| reporting", len(day_rep), f"({len(day_rep)/len(day):.1%})",
      "| analysis", len(day_ana))
print("hours total", len(hour), "| reporting", len(hour_rep), f"({len(hour_rep)/len(hour):.1%})",
      "| analysis", len(hour_ana))
print("date overlap:", set(day_rep.dteday) & set(day_ana.dteday))
print("cnt mean  rep %.1f  ana %.1f" % (day_rep.cnt.mean(), day_ana.cnt.mean()))
