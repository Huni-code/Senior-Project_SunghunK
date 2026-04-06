"""
Mapping Michigan's Digital Economy — Interactive Dashboard
Reads directly from CSV — no database required.
"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data"

st.set_page_config(
    page_title="Michigan's Digital Economy",
    page_icon="🗺️",
    layout="wide",
)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_companies():
    path = DATA_DIR / "companies_classified.csv"
    df = pd.read_csv(path)
    return df

companies = load_companies()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🗺️ Michigan's Digital Economy")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Map", "Learning", "Inventing", "Investing"],
)

# City → (lat, lon)
CITY_COORDS = {
    "Detroit":          (42.3314, -83.0458),
    "Ann Arbor":        (42.2808, -83.7430),
    "Grand Rapids":     (42.9634, -85.6681),
    "Kalamazoo":        (42.2917, -85.5872),
    "Troy":             (42.6064, -83.1498),
    "East Lansing":     (42.7368, -84.4839),
    "Lansing":          (42.7325, -84.5555),
    "Northville":       (42.4314, -83.4835),
    "Plymouth":         (42.3715, -83.4702),
    "Farmington Hills": (42.4989, -83.3677),
    "Rochester Hills":  (42.6584, -83.1499),
    "Rochester":        (42.6803, -83.1335),
    "Southfield":       (42.4734, -83.2219),
    "Livonia":          (42.3684, -83.3527),
    "Saline":           (42.1667, -83.7816),
    "Brighton":         (42.5295, -83.7799),
    "Houghton":         (47.1216, -88.5694),
    "Marquette":        (46.5436, -87.3954),
    "Calumet":          (47.2444, -88.4551),
    "Holland":          (42.7876, -86.1089),
    "Jackson":          (42.2459, -84.4013),
    "Traverse City":    (44.7631, -85.6206),
    "Monroe":           (41.9162, -83.3974),
    "Germantown":       (42.7073, -83.2213),
    "Okemos":           (42.7245, -84.4275),
}

# ── OVERVIEW ─────────────────────────────────────────────────────────────────
if page == "Overview":
    st.title("Mapping Michigan's Digital Economy")
    st.caption("An interactive map of Michigan's tech industry landscape — 134 Michigan-headquartered companies.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies", len(companies))
    col2.metric("Cities", companies["city"].nunique())
    col3.metric("Primary Functions", companies["primary_function"].nunique())
    col4.metric("Revenue Models", companies["revenue_model"].nunique())

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Sector Distribution")
        sector_series = companies["sectors"].dropna().str.split("•").explode().str.strip()
        sector_counts = sector_series.value_counts().head(12).reset_index()
        sector_counts.columns = ["sector", "count"]
        fig = px.bar(
            sector_counts, x="count", y="sector", orientation="h",
            color="count", color_continuous_scale="Blues",
            labels={"count": "Companies", "sector": ""},
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Primary Function")
        func_counts = companies["primary_function"].value_counts().reset_index()
        func_counts.columns = ["function", "count"]
        fig2 = px.pie(
            func_counts, names="function", values="count",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Company Table")
    st.dataframe(
        companies[["name", "city", "sectors", "primary_function", "revenue_model", "work_regime"]],
        use_container_width=True,
        hide_index=True,
    )

# ── MAP ──────────────────────────────────────────────────────────────────────
elif page == "Map":
    st.title("Company Locations")
    st.caption("Geographic distribution of Michigan-headquartered tech companies.")

    map_df = companies.copy()
    map_df["lat"] = map_df["city"].map(lambda c: CITY_COORDS.get(c, (None, None))[0])
    map_df["lon"] = map_df["city"].map(lambda c: CITY_COORDS.get(c, (None, None))[1])
    map_df = map_df.dropna(subset=["lat", "lon"])

    st.info(f"Showing {len(map_df)} of {len(companies)} companies (some cities not yet geocoded)")

    fig = px.scatter_mapbox(
        map_df,
        lat="lat", lon="lon",
        hover_name="name",
        hover_data={"city": True, "primary_function": True, "revenue_model": True, "lat": False, "lon": False},
        color="primary_function",
        size_max=15,
        zoom=6,
        center={"lat": 43.5, "lon": -84.5},
        height=600,
        mapbox_style="carto-positron",
    )
    fig.update_traces(marker=dict(size=12))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Companies by City")
    city_counts = map_df["city"].value_counts().reset_index()
    city_counts.columns = ["city", "count"]
    fig2 = px.bar(city_counts, x="city", y="count", color="count",
                  color_continuous_scale="Teal", labels={"count": "Companies", "city": ""})
    fig2.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

# ── LEARNING ─────────────────────────────────────────────────────────────────
elif page == "Learning":
    st.title("Learning — Sector Analysis")
    st.caption("What sectors are Michigan tech companies operating in?")

    sector_series = companies["sectors"].dropna().str.split("•").explode().str.strip()
    sector_counts = sector_series.value_counts().reset_index()
    sector_counts.columns = ["sector", "count"]

    col1, col2 = st.columns(4), None
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sectors", len(sector_counts))
    c2.metric("Most Common", sector_counts.iloc[0]["sector"])
    c3.metric("Companies in Top Sector", int(sector_counts.iloc[0]["count"]))

    st.divider()

    st.subheader("All Sectors")
    fig = px.bar(
        sector_counts.head(20), x="count", y="sector", orientation="h",
        color="count", color_continuous_scale="Blues",
        labels={"count": "Companies", "sector": ""},
    )
    fig.update_layout(coloraxis_showscale=False, height=550)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sector × Primary Function")
        top_sectors = sector_counts.head(8)["sector"].tolist()
        rows = []
        for _, company in companies.iterrows():
            for s in str(company["sectors"]).split("•"):
                s = s.strip()
                if s in top_sectors:
                    rows.append({"sector": s, "primary_function": company["primary_function"]})
        cross_df = pd.DataFrame(rows)
        cross_counts = cross_df.groupby(["sector", "primary_function"]).size().reset_index(name="count")
        fig2 = px.bar(cross_counts, x="sector", y="count", color="primary_function",
                      barmode="stack", labels={"count": "Companies", "sector": ""},
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("Sector × Revenue Model")
        rows2 = []
        for _, company in companies.iterrows():
            for s in str(company["sectors"]).split("•"):
                s = s.strip()
                if s in top_sectors:
                    rows2.append({"sector": s, "revenue_model": company["revenue_model"]})
        cross_df2 = pd.DataFrame(rows2)
        cross_counts2 = cross_df2.groupby(["sector", "revenue_model"]).size().reset_index(name="count")
        fig3 = px.bar(cross_counts2, x="sector", y="count", color="revenue_model",
                      barmode="stack", labels={"count": "Companies", "sector": ""},
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    st.subheader("Filter by Sector")
    selected_sector = st.selectbox("Sector", ["All"] + sector_counts["sector"].tolist())
    if selected_sector == "All":
        filtered = companies
    else:
        filtered = companies[companies["sectors"].str.contains(selected_sector, na=False)]
    st.dataframe(
        filtered[["name", "city", "sectors", "primary_function", "revenue_model"]],
        use_container_width=True, hide_index=True,
    )

# ── INVENTING ─────────────────────────────────────────────────────────────────
elif page == "Inventing":
    st.title("Inventing — What Are They Building?")
    st.caption("Technology domains Michigan companies are innovating in.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Primary Function")
        pf_counts = companies["primary_function"].value_counts().reset_index()
        pf_counts.columns = ["function", "count"]
        fig = px.pie(pf_counts, names="function", values="count",
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Secondary Function")
        sf_counts = companies["secondary_function"].value_counts().reset_index()
        sf_counts.columns = ["function", "count"]
        fig2 = px.bar(sf_counts, x="count", y="function", orientation="h",
                      color="count", color_continuous_scale="Greens",
                      labels={"count": "Companies", "function": ""})
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Primary × Secondary Function")
    cross = companies.groupby(["primary_function", "secondary_function"]).size().reset_index(name="count")
    fig3 = px.sunburst(cross, path=["primary_function", "secondary_function"], values="count",
                       color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    st.subheader("Filter Companies")
    selected = st.selectbox("Primary Function", ["All"] + sorted(companies["primary_function"].dropna().unique().tolist()))
    filtered = companies if selected == "All" else companies[companies["primary_function"] == selected]
    st.dataframe(filtered[["name", "city", "primary_function", "secondary_function", "description"]],
                 use_container_width=True, hide_index=True)

# ── INVESTING ─────────────────────────────────────────────────────────────────
elif page == "Investing":
    st.title("Investing — Capital & Revenue Models")
    st.caption("How Michigan tech companies generate revenue and are funded.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Revenue Model Distribution")
        rev_counts = companies["revenue_model"].value_counts().reset_index()
        rev_counts.columns = ["model", "count"]
        fig = px.pie(rev_counts, names="model", values="count",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(rev_counts, x="count", y="model", orientation="h",
                      color="count", color_continuous_scale="Oranges",
                      labels={"count": "Companies", "model": ""})
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Revenue Model by City")
    city_model = companies.groupby(["city", "revenue_model"]).size().reset_index(name="count")
    top_cities = companies["city"].value_counts().head(6).index.tolist()
    city_model_filtered = city_model[city_model["city"].isin(top_cities)]
    fig3 = px.bar(city_model_filtered, x="city", y="count", color="revenue_model",
                  barmode="stack", labels={"count": "Companies", "city": ""})
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    st.subheader("Company Details")
    st.dataframe(
        companies[["name", "city", "revenue_model", "work_regime", "primary_function"]],
        use_container_width=True, hide_index=True,
    )
