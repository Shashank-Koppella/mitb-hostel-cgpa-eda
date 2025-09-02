import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels.formula.api as smf
from pathlib import Path

plt.ioff()

DATA_PATH = Path("Data.xlsx")
OUT_DIR = Path("mit_hostel_cgpa_project")
OUT_DIR.mkdir(exist_ok=True, parents=True)

df_raw = pd.read_excel(DATA_PATH, sheet_name=0)

year_map = {
    1: {"cgpa": "First Year CGPA (Sem 1 & 2 average)",
        "hostel_stay": "Did you stay in Hostel for First Year?",
        "hostel_block": "Hostel Block",
        "roommates": "Number of Roomates",
        "study_loc": "Where did you spend the most time studying?",
    },
    2: {"cgpa": "Second Year CGPA ( Sem 3 & 4 average )",
        "hostel_stay": "Did you stay in Hostel for Second Year?",
        "hostel_block": "Hostel Block2",
        "roommates": "Number of Roomates2",
        "study_loc": "Where did you spend the most time studying?2",
    },
    3: {"cgpa": "Third Year CGPA (Sem 5 & 6 average)",
        "hostel_stay": "Did you stay in Hostel for Third Year?",
        "hostel_block": "Hostel Block3",
        "roommates": "Number of Roomates3",
        "study_loc": "Where did you spend the most time studying?3",
    },
    4: {"cgpa": "Fourth Year CGPA ( Sem 7 & 8 average)",
        "hostel_stay": "Did you stay in Hostel for Fourth Year?",
        "hostel_block": "Hostel Block4",
        "roommates": "Number of Roomates4",
        "study_loc": "Where did you spend the most time studying?4",
    },
}

# Drop missing columns gracefully
for y in list(year_map.keys()):
    for k, col in list(year_map[y].items()):
        if col not in df_raw.columns:
            del year_map[y][k]
    if "cgpa" not in year_map[y]:
        del year_map[y]

# Build long format
rows = []
for y, m in year_map.items():
    for idx, row in df_raw.iterrows():
        rec = {"row_id": idx, "year": y}
        rec["cgpa"] = pd.to_numeric(row.get(m.get("cgpa")), errors="coerce")
        rec["hostel_stay"] = row.get(m.get("hostel_stay"))
        rec["hostel_block"] = row.get(m.get("hostel_block"))
        rec["roommates"] = pd.to_numeric(row.get(m.get("roommates")), errors="coerce")
        rec["study_loc"] = row.get(m.get("study_loc"))
        rows.append(rec)

long_df = pd.DataFrame(rows)

for c in ["hostel_stay","hostel_block","study_loc"]:
    if c in long_df.columns:
        long_df[c] = long_df[c].astype("string").str.strip()

long_df.to_csv(OUT_DIR / "long_student_year_data.csv", index=False)

# Plots
for y in sorted(long_df["year"].unique()):
    tmp = long_df.query("year == @y and cgpa.notna()")
    if tmp.empty: continue
    plt.figure(figsize=(6,4))
    plt.hist(tmp["cgpa"], bins=10)
    plt.xlabel("CGPA"); plt.ylabel("Count"); plt.title(f"Year {y} - CGPA Distribution")
    plt.tight_layout(); plt.savefig(OUT_DIR / f"cgpa_hist_year{y}.png", dpi=150); plt.close()

if "hostel_block" in long_df.columns:
    for y in sorted(long_df["year"].unique()):
        tmp = long_df.query("year == @y and cgpa.notna() and hostel_block.notna()")
        if tmp.empty: continue
        groups = [g["cgpa"].values for _, g in tmp.groupby("hostel_block")]
        labels = list(tmp.groupby("hostel_block").groups.keys())
        plt.figure(figsize=(6,4))
        plt.boxplot(groups, labels=labels, vert=True)
        plt.xlabel("Hostel Block"); plt.ylabel("CGPA"); plt.title(f"Year {y} - CGPA by Hostel Block")
        plt.tight_layout(); plt.savefig(OUT_DIR / f"cgpa_by_block_year{y}.png", dpi=150); plt.close()

# Stats
from scipy import stats
tests = []
for y in sorted(long_df["year"].unique()):
    tmp = long_df.query("year == @y")
    # hostel stay
    if "hostel_stay" in tmp.columns:
        g = tmp.groupby("hostel_stay")["cgpa"].apply(lambda s: s.dropna().values)
        if len(g) >= 2:
            vals = list(g.values)
            if len(vals[0])>=3 and len(vals[1])>=3:
                u, p = stats.mannwhitneyu(vals[0], vals[1], alternative="two-sided")
                tests.append({"year": y, "test": "Mann-Whitney hostel_stay", "stat": u, "p": p})
    # block anova
    if "hostel_block" in tmp.columns:
        groups = [v["cgpa"].dropna().values for k,v in tmp.groupby("hostel_block")]
        if len(groups) >= 2 and all(len(g)>=2 for g in groups):
            F, p = stats.f_oneway(*groups)
            tests.append({"year": y, "test": "ANOVA hostel_block", "stat": F, "p": p})
    # roommates corr
    if "roommates" in tmp.columns:
        vals = tmp[["cgpa","roommates"]].dropna()
        if len(vals) >= 3:
            r, p = stats.pearsonr(vals["cgpa"], vals["roommates"])
            tests.append({"year": y, "test": "Pearson roommates", "stat": r, "p": p})
pd.DataFrame(tests).to_csv(OUT_DIR / "stat_tests.csv", index=False)

# OLS
for y in sorted(long_df["year"].unique()):
    tmp = long_df.query("year == @y")[["cgpa","hostel_block","roommates","study_loc"]].dropna(subset=["cgpa"])
    # reduce sparse cats
    for c in ["hostel_block","study_loc"]:
        if c in tmp.columns:
            vc = tmp[c].value_counts()
            keep = vc[vc>=3].index
            tmp.loc[~tmp[c].isin(keep), c] = pd.NA
    terms = []
    if "hostel_block" in tmp.columns and tmp["hostel_block"].notna().any():
        terms.append("C(hostel_block)")
    if "study_loc" in tmp.columns and tmp["study_loc"].notna().any():
        terms.append("C(study_loc)")
    if "roommates" in tmp.columns:
        terms.append("roommates")
    if not terms: 
        continue
    formula = "cgpa ~ " + " + ".join(terms)
    model = smf.ols(formula, data=tmp).fit()
    (OUT_DIR / f"ols_year{y}.txt").write_text(model.summary().as_text(), encoding="utf-8")
print("Done. Outputs in", OUT_DIR)