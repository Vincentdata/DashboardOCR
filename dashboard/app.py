import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Donnees eurostat premieres demandes d asile personnes de nationalité soudanaise",
    layout="wide"
)

st.title("🗺️ Dashboard interactif")

# =========================================================
# DATA
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "df_sudan.csv")

df_sudan = pd.read_csv(DATA_PATH)

@st.cache_data
def load_data(df):

    df_long = df.melt(
        id_vars=["geo", "sex", "age", "pays_fr"],
        value_vars=[col for col in df.columns if "-" in col],
        var_name="month",
        value_name="value"
    )

    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    df_long = df_long.dropna(subset=["value"])
    df_long["month"] = pd.to_datetime(df_long["month"])

    # harmonisation EU27
    df_long["pays_fr"] = df_long["pays_fr"].replace({
        "Union européenne (27 pays)": "EU27"
    })

    df_long["geo"] = df_long["geo"].replace({
        "EU27_2020": "EU27"
    })

    df_long = df_long.groupby(
        ["geo", "sex", "age", "month", "pays_fr"]
    )["value"].sum().reset_index()

    iso2_to_iso3 = {
        "FR":"FRA","DE":"DEU","IT":"ITA","ES":"ESP","BE":"BEL","NL":"NLD",
        "PL":"POL","SE":"SWE","CH":"CHE","AT":"AUT","PT":"PRT","RO":"ROU",
        "BG":"BGR","CZ":"CZE","DK":"DNK","FI":"FIN","HU":"HUN","IE":"IRL",
        "EL":"GRC","SK":"SVK","SI":"SVN","HR":"HRV","LT":"LTU","LV":"LVA",
        "EE":"EST","NO":"NOR","IS":"ISL","UK":"GBR"
    }

    df_long["iso3"] = df_long["geo"].map(iso2_to_iso3)
    df_long["month_str"] = df_long["month"].dt.strftime("%Y-%m")

    return df_long


df = load_data(df_sudan)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("🌍 Filtres evolution temporelle")

countries = ["EU27"] + sorted([x for x in df["pays_fr"].unique() if x != "EU27"])
months = sorted(df["month_str"].unique())

country_name = st.sidebar.selectbox("Zone géographique", countries, index=0)

st.sidebar.markdown("### 🗺️ Carte Europe")

selected_month = st.sidebar.select_slider(
    "Temps",
    options=months,
    value=months[0]
)

st.sidebar.markdown("---")
st.sidebar.header("📉 Graphiques age sexe evolution temporelle")

sex_bottom = st.sidebar.selectbox("Sexe", ["T", "F", "M"], index=0)

age_bottom = st.sidebar.selectbox(
    "Âge",
    sorted(df["age"].unique()),
    index=0
)

# =========================================================
# FILTER
# =========================================================
df_country = df[df["pays_fr"] == country_name]

# =========================================================
# TIME SERIES
# =========================================================
st.subheader(f"📊 Évolution temporelle - {country_name}")

col1, col2, col3 = st.columns(3)

for sex_val, col in zip(["F", "M", "T"], [col1, col2, col3]):

    with col:
        ts = df_country[df_country["sex"] == sex_val] \
            .groupby("month_str")["value"].sum().reset_index()

        fig = px.line(ts, x="month_str", y="value", title=sex_val)
        fig.update_layout(height=300)

        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# MAP + PYRAMIDE
# =========================================================
col_map, col_pyr = st.columns([2, 1])

with col_map:
    st.subheader("🗺️ Carte Europe")

    dff_map = df[
        (df["sex"] == "T") &
        (df["age"] == "Total") &
        (df["month_str"] == selected_month) &
        (df["iso3"].notna())
    ]

    fig_map = px.choropleth(
        dff_map,
        locations="iso3",
        color="value",
        scope="europe",
        color_continuous_scale="Blues",
        range_color=(0, df["value"].quantile(0.95))
    )

    fig_map.update_layout(height=600)
    st.plotly_chart(fig_map, use_container_width=True)

# =========================================================
# PYRAMIDE DES AGES (FIXÉE)
# =========================================================
with col_pyr:
    st.subheader("👥 Pyramide des âges (Europe)")

    pyramid = df[
        (df["geo"] == "EU27") &
        (df["month_str"] == selected_month)
    ].copy()

    # enlever bruit
    pyramid = pyramid[~pyramid["age"].isin(["Total", "Unknown"])]

    # normalisation des âges
    age_map = {
        "<14": "0-14",
        "<18": "0-17",
        "14-17": "14-17",
        "18-34": "18-34",
        "35-64": "35-64",
        "65+": "65+"
    }

    pyramid["age"] = pyramid["age"].replace(age_map)

    pyramid = pyramid.groupby(["age", "sex"])["value"].sum().reset_index()

    age_order = ["0-14", "0-17", "14-17", "18-34", "35-64", "65+"]

    pyramid["age"] = pd.Categorical(
        pyramid["age"],
        categories=age_order,
        ordered=True
    )

    pyramid = pyramid.sort_values("age")

    fig_pyr = px.bar(
        pyramid,
        x="value",
        y="age",
        color="sex",
        orientation="h",
        barmode="relative"
    )

    fig_pyr.update_layout(height=600)

    st.plotly_chart(fig_pyr, use_container_width=True)

# =========================================================
# BOTTOM GRAPHS
# =========================================================
st.markdown("---")
st.subheader("📉 Graphiques age sexe evolution temporelle")

colb1, colb2 = st.columns(2)

with colb1:
    st.markdown("### 📈 Total (tous âges)")

    ts_all = df_country[
        df_country["sex"] == sex_bottom
    ].groupby("month_str")["value"].sum().reset_index()

    fig_all = px.line(ts_all, x="month_str", y="value")

    st.plotly_chart(fig_all, use_container_width=True)

with colb2:
    st.markdown(f"### 📊 Âge : {age_bottom}")

    ts_age = df_country[
        (df_country["sex"] == sex_bottom) &
        (df_country["age"] == age_bottom)
    ].groupby("month_str")["value"].sum().reset_index()

    fig_age = px.line(ts_age, x="month_str", y="value")

    st.plotly_chart(fig_age, use_container_width=True)