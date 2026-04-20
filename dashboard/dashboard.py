import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ----------------------------
# CONFIG PAGE
# ----------------------------
st.set_page_config(
    page_title="Asile Europe Dashboard",
    layout="wide"
)

st.title("🗺️ Asile Europe - Dashboard interactif")


# ----------------------------
# DATA
# ----------------------------
df_sudan = pd.read_csv("/home/vincent/Documents/Associatif/Observatoire_des_Camps_de_Refugies/Stat_soudan/notebook/df_sudan.csv")

# ----------------------------
# DATA PREP
# ----------------------------
@st.cache_data
def load_data(df_sudan):

    df_long = df_sudan.melt(
        id_vars=["geo", "sex", "age"],
        value_vars=[col for col in df_sudan.columns if "-" in col],
        var_name="month",
        value_name="value"
    )

    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    df_long = df_long.dropna(subset=["value"])

    df_long["month"] = pd.to_datetime(df_long["month"])

    df_long = df_long.groupby(
        ["geo", "sex", "age", "month"]
    )["value"].sum().reset_index()

    iso2_to_iso3 = {
        "FR":"FRA","DE":"DEU","IT":"ITA","ES":"ESP","BE":"BEL","NL":"NLD",
        "PL":"POL","SE":"SWE","CH":"CHE","AT":"AUT","PT":"PRT","RO":"ROU",
        "BG":"BGR","CZ":"CZE","DK":"DNK","FI":"FIN","HU":"HUN","IE":"IRL",
        "EL":"GRC","SK":"SVK","SI":"SVN","HR":"HRV","LT":"LTU","LV":"LVA",
        "EE":"EST","NO":"NOR","IS":"ISL","UK":"GBR"
    }

    df_long["iso3"] = df_long["geo"].map(iso2_to_iso3)
    df_long = df_long.dropna(subset=["iso3"])

    df_long["month_str"] = df_long["month"].dt.strftime("%Y-%m")

    return df_long


df = load_data(df_sudan)

# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("Filtres")

sex = st.sidebar.selectbox("Sexe", df["sex"].unique())
age = st.sidebar.selectbox("Âge", sorted(df["age"].unique()))
country = st.sidebar.selectbox("Pays", sorted(df["iso3"].unique()))

months = sorted(df["month_str"].unique())
month = st.sidebar.slider("Temps", 0, len(months)-1, 0)
selected_month = months[month]

# ----------------------------
# FILTERED DATA
# ----------------------------
dff = df[
    (df["sex"] == sex) &
    (df["age"] == age) &
    (df["month_str"] == selected_month)
]

# ----------------------------
# LAYOUT
# ----------------------------
col1, col2 = st.columns([2, 1])

# ============================
# 🗺️ MAP
# ============================
with col1:

    st.subheader("🗺️ Carte Europe")

    fig_map = px.choropleth(
        dff,
        locations="iso3",
        color="value",
        scope="europe",
        color_continuous_scale="Blues",
        range_color=(0, df["value"].quantile(0.95)),
        title=f"Demandes d'asile - {selected_month}"
    )

    fig_map.update_layout(height=600)
    st.plotly_chart(fig_map, use_container_width=True)

# ============================
# 📊 PYRAMIDE DES AGES
# ============================
with col2:

    st.subheader(f"👥 Pyramide des âges ({country})")

    pyramid = df[
        (df["iso3"] == country) &
        (df["month_str"] == selected_month)
    ].groupby(["age", "sex"])["value"].sum().reset_index()

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

# ============================
# 📈 TIME SERIES
# ============================
st.subheader("📈 Évolution temporelle")

ts = df[
    (df["iso3"] == country) &
    (df["sex"] == sex)
].groupby(["month_str", "age"])["value"].sum().reset_index()

fig_ts = px.line(
    ts,
    x="month_str",
    y="value",
    color="age",
    markers=True
)

fig_ts.update_layout(height=500)

st.plotly_chart(fig_ts, use_container_width=True)