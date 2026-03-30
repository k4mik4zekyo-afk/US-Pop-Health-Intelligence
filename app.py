import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "places2024release.csv")
SHP_PATH = os.path.join(BASE_DIR, "tl_2025_us_county", "tl_2025_us_county.shp")

# ── Data loaders (cached) ──────────────────────────────────────────────────────
@st.cache_data
def load_places(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype={"LocationID": str}, low_memory=False)
    # Use most recent year and crude prevalence only (one row per county per measure)
    latest = df["Year"].max()
    df = df[(df["Year"] == latest) & (df["Data_Value_Type"] == "Crude prevalence")]
    df["LocationID"] = df["LocationID"].str.zfill(5)
    df["Data_Value"] = pd.to_numeric(df["Data_Value"], errors="coerce")
    df["Low_Confidence_Limit"] = pd.to_numeric(df["Low_Confidence_Limit"], errors="coerce")
    df["High_Confidence_Limit"] = pd.to_numeric(df["High_Confidence_Limit"], errors="coerce")
    df["TotalPopulation"] = pd.to_numeric(
        df["TotalPopulation"].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    ).astype("Int64")
    return df


@st.cache_data
def load_counties(shp_path: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(shp_path)
    gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.05, preserve_topology=True)
    return gdf[["GEOID", "STATEFP", "NAME", "geometry"]]


# ── App ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="US Health Atlas", layout="wide")
st.title("United States Health Atlas")
st.caption("CDC PLACES 2024 · County-level health prevalence")

# Load data
places = load_places(CSV_PATH)
counties = load_counties(SHP_PATH)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Options")

    states = ["All"] + sorted(places["StateAbbr"].dropna().unique())
    selected_state = st.selectbox("State", states)

    state_places = places if selected_state == "All" else places[places["StateAbbr"] == selected_state]

    categories = sorted(state_places["Category"].dropna().unique())
    selected_cat = st.selectbox("Category", ["All"] + categories)

    filtered = state_places if selected_cat == "All" else state_places[state_places["Category"] == selected_cat]
    measures = sorted(filtered["Measure"].dropna().unique())

    selected_measure = st.selectbox("Health Measure", measures)

    st.markdown("---")
    st.markdown(
        "**Data year:** "
        + str(places["Year"].max())
        + "\n\n**Source:** [CDC PLACES](https://www.cdc.gov/places)"
    )

# ── Filter to selected measure ────────────────────────────────────────────────
measure_df = filtered[filtered["Measure"] == selected_measure][
    ["LocationID", "LocationName", "StateAbbr", "Data_Value", "Low_Confidence_Limit",
     "High_Confidence_Limit", "TotalPopulation"]
].copy()

# ── Filter counties shapefile by state if selected ────────────────────────────
if selected_state != "All" and not measure_df.empty:
    state_fips = measure_df["LocationID"].str[:2].mode()[0]
    counties_view = counties[counties["STATEFP"] == state_fips]
else:
    counties_view = counties

# ── Join shapefile + PLACES ───────────────────────────────────────────────────
merged = counties_view.merge(measure_df, left_on="GEOID", right_on="LocationID", how="left")

# ── Build Folium map ──────────────────────────────────────────────────────────
m = folium.Map(tiles="CartoDB positron")

# Choropleth layer (only counties with data)
has_data = merged.dropna(subset=["Data_Value"])

# Fit map bounds to visible counties
if not has_data.empty:
    b = has_data.total_bounds  # [minx, miny, maxx, maxy]
    m.fit_bounds([[b[1], b[0]], [b[3], b[2]]])
else:
    m.location = [38.5, -96.0]
    m.zoom_start = 4

choropleth = folium.Choropleth(
    geo_data=has_data.__geo_interface__,
    data=has_data[["GEOID", "Data_Value"]],
    columns=["GEOID", "Data_Value"],
    key_on="feature.properties.GEOID",
    fill_color="YlOrRd",
    fill_opacity=0.75,
    line_opacity=0.4,
    legend_name=f"{selected_measure} (%)",
    nan_fill_color="lightgray",
    nan_fill_opacity=0.4,
    highlight=True,
).add_to(m)

# Gray fill for missing counties
no_data = merged[merged["Data_Value"].isna()]
if not no_data.empty:
    folium.GeoJson(
        no_data.__geo_interface__,
        style_function=lambda _: {
            "fillColor": "#cccccc",
            "color": "#888888",
            "weight": 0.5,
            "fillOpacity": 0.5,
        },
        tooltip=folium.GeoJsonTooltip(fields=["NAME"], aliases=["County:"], labels=True),
    ).add_to(m)

# Attach tooltip directly to the choropleth's geojson — avoids sending geometry twice
choropleth.geojson.add_child(
    folium.GeoJsonTooltip(
        fields=["NAME", "Data_Value", "Low_Confidence_Limit",
                "High_Confidence_Limit", "TotalPopulation"],
        aliases=["County:", "Prevalence (%):", "Low CI (%):",
                 "High CI (%):", "Population:"],
        localize=True,
        sticky=True,
        style="font-size:13px;",
    )
)

# ── Render map ────────────────────────────────────────────────────────────────
st_folium(m, width="100%", height=600, returned_objects=[])

# ── Summary stats ─────────────────────────────────────────────────────────────
st.subheader("Summary Statistics")

if measure_df["Data_Value"].notna().any():
    stats = measure_df[["Data_Value", "Low_Confidence_Limit",
                         "High_Confidence_Limit", "TotalPopulation"]].describe().loc[
        ["count", "mean", "min", "max"]
    ].T

    stats.index = ["Prevalence (%)", "Low CI (%)", "High CI (%)", "Population"]
    stats.columns = ["Count", "Mean", "Min", "Max"]
    stats = stats.round(2)
    stats["Count"] = stats["Count"].astype(int)
    st.dataframe(stats, use_container_width=True)

    # ── State Data Table ──────────────────────────────────────────────────────
    st.subheader("State Data")
    state_table = measure_df.groupby("StateAbbr").agg(
        Counties_With_Data=("Data_Value", "count"),
        Mean_Prevalence=("Data_Value", "mean"),
        Min_Prevalence=("Data_Value", "min"),
        Max_Prevalence=("Data_Value", "max"),
    ).round(2).reset_index().sort_values("Mean_Prevalence", ascending=False)
    state_table.columns = ["State", "Counties w/ Data", "Mean Prevalence (%)", "Min (%)", "Max (%)"]
    st.dataframe(state_table, use_container_width=True)

    # ── County Data Table ─────────────────────────────────────────────────────
    st.subheader("County Data Table")
    display_df = measure_df.rename(columns={
        "StateAbbr": "State",
        "LocationName": "County",
        "Data_Value": "Prevalence (%)",
        "Low_Confidence_Limit": "Low CI (%)",
        "High_Confidence_Limit": "High CI (%)",
        "TotalPopulation": "Population",
    }).drop(columns=["LocationID"]).sort_values("Prevalence (%)").reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("No data available for this measure.")
