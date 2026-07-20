import streamlit as st
import pandas as pd
import pydeck as pdk
from pathlib import Path

st.set_page_config(
    page_title="Analyse d'un habitant",
    page_icon="🏡",
    layout="wide"
)

st.title("Analyse individuelle de l’exposition thermique des habitants")

st.markdown("""
### Objectif de l’outil
Cet outil permet d’analyser les interactions entre un habitant et les installations susceptibles de l'influencer dans un scénario d’aménagement.

Chaque lien représente un score de proximité thermique (`d_ijc`) calculé à partir de la distance entre l’installation et l’habitant.

⚠️ Important :

- Le score **d_ijc** varie entre **0 et 1**
- Il est calculé à partir de la distance entre l’installation et l’habitant dans un rayon maximal de 300 mètres
- Plus une installation est proche de l’habitant, plus le score est élevé
- Plus le score est élevé, plus l’installation est susceptible d'avoir un effet sur cet habitant
""")

# === Paramètres ===
ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "../data/processed"

center_bounds = {
    "lat_min": 44.82, "lat_max": 44.86,
    "lon_min": -0.57, "lon_max": -0.53
}

# === Chargement des données ===
@st.cache_data
def load_data():
    df_h = pd.read_parquet(PROCESSED_DIR / "habitants/habitants.parquet")

    df_h = df_h[
        (df_h["lat"].between(center_bounds["lat_min"], center_bounds["lat_max"])) &
        (df_h["lon"].between(center_bounds["lon_min"], center_bounds["lon_max"]))
    ]

    df_d = pd.read_parquet(PROCESSED_DIR / "matrices/d_ijc.parquet")
    df_d = df_d[df_d["id_c"].isin(df_h["id"])]

    df_j = pd.read_parquet(PROCESSED_DIR / "matrices/j_options.parquet")

    df_e = pd.read_parquet(
        PROCESSED_DIR / "emplacements/emplacements_final.parquet"
    )[["id", "lon", "lat"]].rename(columns={"id": "id_i"})

    df_j = df_j.merge(df_e, on="id_i", how="left")
    df_dj = df_d.merge(df_j, on=["id_i", "id_j"], how="left")
    df_dc = df_dj.merge(df_h, left_on="id_c", right_on="id", suffixes=("_j", "_c"))

    return df_dc, df_h


with st.spinner("📦 Chargement des données..."):
    df_dc, df_h = load_data()

st.markdown("________________")

# === Sélection habitant ===
# habitants avec interactions + population > 0
valid_habitants = df_dc.groupby("id_c").size()
valid_habitants = valid_habitants[valid_habitants > 0].index

df_h_valid = df_h[
    (df_h["id"].isin(valid_habitants)) &
    (df_h["nb_habitants"].fillna(0) > 0)
]

id_selected = st.selectbox(
    "Sélectionne un habitant",
    sorted(df_h_valid["id"].unique())
)

with st.expander("Comprendre l'indice de vulnérabilité thermique"):
    st.markdown("""
    **Indice de vulnérabilité thermique**

    Les secteurs résidentiels sont classés selon leur niveau de vulnérabilité :
    - **3** : Vulnérabilité plutôt faible
    - **4** : Vulnérabilité plutôt forte
    - **5** : Forte vulnérabilité
    - **6** : Très forte vulnérabilité

    Les niveaux les plus élevés correspondent aux secteurs les plus sensibles aux épisodes de chaleur.
    """)

df_focus = df_dc[df_dc["id_c"] == id_selected]

hab = df_focus.iloc[0]

nb_habitants = hab.get("nb_habitants", 0)

if pd.isna(nb_habitants) or nb_habitants == 0:
    st.warning("Cet habitant n’a aucune population associée (nb_habitants = 0).")
    st.stop()

st.info(f"""
**Classe thermique :** {hab.get('classe', 'N/A')}  
**Nombre d'habitants représentés :** {hab.get('nb_habitants', 0)}  
**Nombre d’installations situées dans le rayon d’influence :** {len(df_focus)}
""")


# === Tableau ===
st.subheader("Installations qui couvrent cet habitant")

df_tab = df_focus[[
    "id_i", "id_j", "surface_j", "d_ijc", "lon_j", "lat_j"
]].sort_values("d_ijc", ascending=False)

df_tab = df_tab.rename(columns={
    "id_i": "ID emplacement",
    "id_j": "ID installation",
    "surface_j": "Surface (m²)",
    "d_ijc": "Impact thermique",
    "lon_j": "Longitude",
    "lat_j": "Latitude"
})

st.dataframe(df_tab.reset_index(drop=True))
st.caption(
    "Les installations sont classées par score d’impact thermique décroissant. "
    "Les premières lignes correspondent aux installations les plus proches de l’habitant sélectionné."
)

# === Normalisation d_ijc ===
dmin, dmax = df_focus["d_ijc"].min(), df_focus["d_ijc"].max()
den = (dmax - dmin) if dmax != dmin else 1

def color_d(d):
    x = (d - dmin) / den

    # orange -> jaune -> vert
    if x < 0.33:
        return [232, 152, 5, 160]
    elif x < 0.66:
        return [224, 224, 0, 160]
    else:
        return [33, 163, 15, 160]


# === Lignes Arc ===
lines_df = df_focus.copy()
lines_df["from"] = lines_df[["lon_j", "lat_j"]].values.tolist()
lines_df["to"] = lines_df[["lon_c", "lat_c"]].values.tolist()
lines_df["color"] = lines_df["d_ijc"].apply(color_d)

st.subheader("🗺️ Carte de l'habitant et les installations qui l’impactent")

with st.expander("Légende"):
     st.markdown("""
    🔴 Le **point rouge** = l’habitant sélectionné  
                 
    🔵 Les **points bleus** = les installations qui l’impactent  
                 
    🟠🟡🟢 **Les arcs** = intensité de l’impact thermique
    - 🟠 faible impact  
    - 🟡 impact moyen  
    - 🟢 fort impact  

    Plus un arc est vert, plus le score d’impact thermique est élevé.
    Les scores élevés correspondent aux installations les plus proches de l’habitant.
    """)
     
layer_lines = pdk.Layer(
    "ArcLayer",
    data=lines_df,
    get_source_position="from",
    get_target_position="to",
    get_source_color="color",
    get_target_color="color",
    get_width=2,
    width_scale=1,
    pickable=True,
    auto_highlight=True
)


# === Points installations ===
layer_points = pdk.Layer(
    "ScatterplotLayer",
    data=df_focus,
    get_position='[lon_j, lat_j]',
    get_fill_color='[80, 140, 255, 140]',
    get_radius=6,
    pickable=True
)

# === Point habitant ===
layer_habitant = pdk.Layer(
    "ScatterplotLayer",
    data=df_focus.drop_duplicates("id_c"),
    get_position='[lon_c, lat_c]',
    get_fill_color='[255, 80, 80, 180]',
    get_radius=10,
    pickable=False
)


# === View ===
view_state = pdk.ViewState(
    latitude=hab["lat_c"],
    longitude=hab["lon_c"],
    zoom=14
)


# === Tooltip propre ===
tooltip = {
    "html": """
    <b>Impact thermique :</b> {d_ijc}<br/>
    <b>Installation :</b> {id_j}<br/>
    <b>Emplacement :</b> {id_i}
    """,
    "style": {
        "backgroundColor": "#1e293b",
        "color": "white",
        "fontSize": "12px"
    }
}


# === Carte ===
deck = pdk.Deck(
    layers=[layer_lines, layer_points, layer_habitant],
    initial_view_state=view_state,
    map_provider="carto",
    map_style="light",
    tooltip=tooltip
)
     
st.pydeck_chart(deck)