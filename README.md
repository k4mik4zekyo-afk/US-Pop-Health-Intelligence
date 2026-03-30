# How to Use the US Pop Health Intelligence Visualizer

## What This App Does

The dashboard an interactive map that visualizes CDC PLACES health data for US counties. You can explore how different health conditions (like asthma, diabetes, or smoking rates) vary across the state's 58 counties.

---

## Setup: Installing Dependencies

Before running the app for the first time, you need to install the required Python packages. Open your terminal and run:

```bash
pip install streamlit folium streamlit-folium geopandas pandas
```

---

## Running the App

1. Open your terminal
2. Navigate to the project folder:
   ```bash
   cd ~/Downloads/GIS\ Project
   ```
3. Start the app:
   ```bash
   streamlit run app.py
   ```
4. Your browser will open automatically at `http://localhost:8501`

---

## Using the Interface

### Sidebar (left panel)

| Control | What it does |
|---|---|
| **Category** | Filters measures by topic (e.g. "Health Outcomes", "Prevention") |
| **Health Measure** | Selects which metric to display on the map |

### The Map

![Dashboard screenshot](https://github.com/k4mik4zekyo-afk/US-Pop-Health-Intelligence/blob/main/Dashboard.png)

- **Color gradient** (yellow → red): Higher prevalence = darker red
- **Gray counties**: No data available for that county + measure combo
- **Hover** over any county to see a tooltip with:
  - County name
  - Prevalence percentage
  - 95% Confidence interval (Low CI – High CI)
  - Total county population

### Summary Statistics (below the map)

A table showing count, mean, min, and max across all CA counties for the selected measure — covering prevalence, confidence intervals, and population.

### County Data Table

A sortable table listing every California county's values for the selected measure. Useful for comparing counties side by side.

---

## Understanding the Data

- **Source**: [CDC PLACES 2024 Release](https://www.cdc.gov/places) — county-level estimates derived from BRFSS survey data
- **Data year**: 2022 (most recent available)
- **Prevalence**: Crude prevalence as a percentage of adults
- **Confidence Interval**: The range within which the true value likely falls (95% CI). A narrower range means a more precise estimate.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| App won't start | Make sure you're in the right folder and ran `pip install` |
| Map is blank | Check that `tl_2025_us_county/` folder is in the same directory as `app.py` |
| No data showing | Try a different measure — some measures may have limited county coverage |
| `ModuleNotFoundError` | Run `pip install <module-name>` for the missing package |

---

## File Structure

```
GIS Project/
├── app.py                    ← Main application
├── HOW_TO_USE.md             ← This file
├── places2024release.csv     ← CDC PLACES health data
└── tl_2025_us_county/        ← County boundary shapefiles
    ├── tl_2025_us_county.shp
    └── ...
```
