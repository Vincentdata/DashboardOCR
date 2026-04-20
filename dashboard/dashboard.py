import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Asile Europe Dashboard", layout="wide")
st.title("🗺️ Asile Europe - Dashboard interactif")

# ----------------------------
# DATA
# ----------------------------
df_sudan = pd.read_csv("/home/vincent/Documents/Associatif/Observatoire_des_Camps_de_Refugies/Stat_soudan/notebook/df_sudan.csv")

# ----------------------------
# PREP DATA
# ----------------------------
@st.cache_data
def load_data(df):

    df_long = df.melt(
        id_vars=["geo", "sex", "age", "pays_fr"],
        value_vars=[col for col in df.columns if "-" in col],
        var_name="month",
        value_name="value"
    )

    # nettoyage
    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    df_long = df_long.dropna(subset=["value"])

    # date
    df_long["month"] = pd.to_datetime(df_long["month"])

    # agrégation
    df_long = df_long.groupby(
        ["geo", "sex", "age", "month", "pays_fr"]
    )["value"].sum().reset_index()

    # mapping ISO2 → ISO3 (clé pour la carte)
    iso2_to_iso3 = {
        "FR":"FRA","DE":"DEU","IT":"ITA","ES":"ESP","BE":"BEL","NL":"NLD",
        "PL":"POL","SE":"SWE","CH":"CHE","AT":"AUT","PT":"PRT","RO":"ROU",
        "BG":"BGR","CZ":"CZE","DK":"DNK","FI":"FIN","HU":"HUN","IE":"IRL",
        "EL":"GRC","SK":"SVK","SI":"SVN","HR":"HRV","LT":"LTU","LV":"LVA",
        "EE":"EST","NO":"NOR","IS":"ISL","UK":"GBR"
    }

    df_long["iso3"] = df_long["geo"].map(iso2_to_iso3)

    # on garde même EU27_2020 (utile pour pyramide)
    df_long["month_str"] = df_long["month"].dt.strftime("%Y-%m")

    return df_long


df = load_data(df_sudan)

# ----------------------------
# FILTRE PRINCIPAL
# ----------------------------
st.sidebar.header("Filtres")

country_name = st.sidebar.selectbox(
    "Pays",
    sorted(df["pays_fr"].unique())
)

df_country = df[df["pays_fr"] == country_name]

# ----------------------------
# SLIDER TEMPS (PROPRE)
# ----------------------------
months = sorted(df["month_str"].unique())

selected_month = st.sidebar.select_slider(
    "Temps",
    options=months,
    value=months[0]
)

# =========================================================
# 🔝 TOP : 3 TIME SERIES (F / M / T)
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
# 🗺️ MAP + PYRAMIDE
# =========================================================
col_map, col_pyr = st.columns([2, 1])

# ---------- CARTE ----------
with col_map:
    st.subheader("🗺️ Carte Europe")

    dff_map = df[
        (df["sex"] == "T") &
        (df["age"] == "Total") &
        (df["month_str"] == selected_month) &
        (df["iso3"].notna())   # 🔥 évite EU27
    ]

    fig_map = px.choropleth(
        dff_map,
        locations="iso3",
        color="value",
        scope="europe",
        color_continuous_scale="Blues",
        range_color=(0, df["value"].quantile(0.95))
    )

    fig_map.update_traces(marker_line_width=0.5)
    fig_map.update_layout(height=600)

    st.plotly_chart(fig_map, use_container_width=True)

# ---------- PYRAMIDE ----------
with col_pyr:
    st.subheader("👥 Pyramide des âges (Europe)")

    pyramid = df[
        (df["geo"] == "EU27_2020") &
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

# =========================================================
# 🎛️ FILTRES BAS
# =========================================================
st.sidebar.subheader("Filtres (graphiques du bas)")

sex_bottom = st.sidebar.selectbox("Sexe", df["sex"].unique())
age_bottom = st.sidebar.selectbox("Âge", sorted(df["age"].unique()))

# =========================================================
# 📉 BAS : 2 GRAPHIQUES
# =========================================================
colb1, colb2 = st.columns(2)

# TOTAL
with colb1:
    st.subheader("📈 Total (tous âges)")

    ts_all = df_country[
        df_country["sex"] == sex_bottom
    ].groupby("month_str")["value"].sum().reset_index()

    fig_all = px.line(ts_all, x="month_str", y="value")
    st.plotly_chart(fig_all, use_container_width=True)

# AGE SPECIFIQUE
with colb2:
    st.subheader(f"📊 Âge : {age_bottom}")

    ts_age = df_country[
        (df_country["sex"] == sex_bottom) &
        (df_country["age"] == age_bottom)
    ].groupby("month_str")["value"].sum().reset_index()

    fig_age = px.line(ts_age, x="month_str", y="value")
    st.plotly_chart(fig_age, use_container_width=True)