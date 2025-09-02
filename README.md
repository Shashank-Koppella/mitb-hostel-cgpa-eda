# MIT Bangalore Hostel Environment vs CGPA

This repository analyzes how the hostel environment and related factors (block, roommates, study location) relate to CGPA across years at **Manipal Institute of Technology, Bangalore**.

## Data
- Source: `Data.xlsx`
- Tidy version saved as: `mit_hostel_cgpa_project/long_student_year_data.csv` (one row per student-year).

## Methods
- Descriptive plots: CGPA distributions per year; CGPA by hostel block.
- Statistical tests: 
  - Mann–Whitney U test for CGPA between hostel stay (Yes/No) within each year.
  - One-way ANOVA for CGPA across hostel blocks within each year (fallbacks handled if group sizes are too small).
  - Pearson correlation between number of roommates and CGPA.
- OLS regression (per year): `cgpa ~ C(hostel_block) + C(study_loc) + roommates`, using categories with ≥3 observations.

Outputs saved under `mit_hostel_cgpa_project/`:
- Plots: `cgpa_hist_year*.png`, `cgpa_by_block_year*.png`
- Stats: `stat_tests.csv`
- Models: `ols_year*.txt` (regression summaries)

## Reproducibility
- Python 1.5.3 (pandas), statsmodels, scipy, matplotlib.
- See `requirements.txt` for exact packages.

## How to run
```bash
python analysis.py
```

Ensure `Data.xlsx` is in the project root.

## Notes
- Missing values are handled conservatively.
- Categorical levels with fewer than 3 observations are dropped from OLS to avoid unstable estimates.
