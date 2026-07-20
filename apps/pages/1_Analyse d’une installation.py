import streamlit as st
import pandas as pd
import pydeck as pdk
from pathlib import Path
import altair as alt

st.set_page_config(
    page_title="Analyse d'une installation",
    page_icon="⛲",
    layout="wide"
)

st.title("Analyse des scénarios d’implantation d’espaces de fraîcheur")

st.subheader("Objectif de l’outil")
st.markdown("Cette interface permet d’analyser les solutions d’implantation d’installations sélectionnées par un algorithme d’optimisation dans le cadre d’une étude de vulnérabilité thermique.")
st.subheader("Ce que vous pouvez explorer")
st.markdown("""
- Les caractéristiques techniques et économiques de chaque installation
- Les secteurs résidentiels concernés
- La population potentiellement impactée
- La distribution spatiale des zones couvertes
            
Les résultats affichés correspondent à des scénarios d’aménagement et non à des réalisations existantes.
""")

st.markdown("________________")

# === Paramètres ===
ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "../data/processed"
center_bounds = {"lat_min": 44.82, "lat_max": 44.86, "lon_min": -0.57, "lon_max": -0.53}

@st.cache_data
def load_data():
    df_hab = pd.read_parquet(PROCESSED_DIR / "habitants/habitants.parquet")
    df_res = pd.read_csv(PROCESSED_DIR / "resultats/resultats_glouton.csv")
    df_a = pd.read_parquet(PROCESSED_DIR / "matrices/a_ijc.parquet")
    df_e = pd.read_parquet(PROCESSED_DIR / "emplacements/emplacements_final.parquet")[["id", "lon", "lat"]].rename(columns={"id": "id_i"})

    # Ajout des coordonnées manquantes
    df_res = df_res.merge(df_e, on="id_i", how="left")

    # Filtrage zone centre
    df_hab = df_hab[
        (df_hab["lat"].between(center_bounds["lat_min"], center_bounds["lat_max"])) &
        (df_hab["lon"].between(center_bounds["lon_min"], center_bounds["lon_max"]))
    ]

    df_res["key"] = df_res["id_i"].astype(str) + "_" + df_res["id_j"].astype(str)
    df_a["key"] = df_a["id_i"].astype(str) + "_" + df_a["id_j"].astype(str)
    df_a = df_a[df_a["key"].isin(df_res["key"])]

    return df_res, df_a, df_hab

with st.spinner("📦 Chargement des données..."):
    df_res, df_a, df_hab = load_data()
    

# ________________ Analyse installation ________________
# Sélection d’une installation
st.subheader("📍 Analyse d’une installation")

installation_options = df_res[["id_i", "id_j"]].drop_duplicates()

# On calcule les options valides (avec au moins un habitant couvert)
valid_options = []

for _, row in installation_options.iterrows():
    id_i = str(row["id_i"])
    id_j = str(row["id_j"])

    df_covered = df_a[(df_a["id_i"].astype(str) == id_i) & (df_a["id_j"].astype(str) == id_j)]
    df_covered_habs = df_hab[df_hab["id"].isin(df_covered["id_c"])]

    if len(df_covered_habs) > 0:
        valid_options.append((id_i, id_j))

# reconstruction dataframe filtré
installation_options_valid = pd.DataFrame(valid_options, columns=["id_i", "id_j"])
installation_options_valid["label"] = (installation_options_valid["id_i"].astype(str) + " – " + installation_options_valid["id_j"].astype(str))

selection = st.selectbox(
    "Sélectionnez une solution d’implantation pour visualiser son impact territorial :",
    installation_options_valid["label"].unique()
)

id_i_sel, id_j_sel = selection.split(" – ")
df_install = df_res[(df_res["id_i"].astype(str) == id_i_sel) & (df_res["id_j"].astype(str) == id_j_sel)]
df_covered = df_a[(df_a["id_i"].astype(str) == id_i_sel) & (df_a["id_j"].astype(str) == id_j_sel)]
df_covered_habs = df_hab[df_hab["id"].isin(df_covered["id_c"])]

# Caractéristiques
total_pop = df_covered_habs["nb_habitants"].sum()

# Liste des habitants couverts
st.info(f"""
Synthèse d’impact :

- Secteurs résidentiels concernés : **{len(df_covered_habs)}**
- Population totale estimée : **{int(total_pop):,} personnes**

Ces valeurs représentent une estimation agrégée de la population exposée dans les zones couvertes par l’installation.
""")

st.markdown("Le tableau ci-dessous présente les secteurs résidentiels couverts par l'installation sélectionnée. Chaque secteur est associé à une estimation de population et à une classe de vulnérabilité thermique.")

st.dataframe(df_covered_habs[["id", "nb_habitants", "classe", "lon", "lat"]], use_container_width=True)

# ________________ Barplot ________________
st.markdown("#### 🔥 Répartition des niveaux de vulnérabilité thermique")

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

# préparation des données
df_plot = (
    df_covered_habs["classe"]
    .value_counts()
    .reset_index()
)

df_plot.columns = ["classe", "count"]
df_plot = df_plot.sort_values("classe")

# graphique
chart = (
    alt.Chart(df_plot)
    .mark_bar(color="#019de0")  # rouge propre
    .encode(
        x=alt.X(
            "classe:O",
            title="Classe de vulnérabilité",
            axis=alt.Axis(labelAngle=0)
        ),
        y=alt.Y("count:Q", title="Nombre de secteurs"),
        tooltip=["classe", "count"]
    )
    .properties(height=350)
)

st.altair_chart(chart, use_container_width=True)


# ________________ Carte ________________
st.subheader("🗺️ Carte de l'installation et des secteurs couverts")

st.markdown("La carte permet d’évaluer la cohérence spatiale de la solution et sa capacité à couvrir les zones les plus vulnérables.")

with st.expander("Légende"):
     st.markdown("""
    🔵 **Point bleu** : emplacement de l'installation sélectionnée           

    🟢🟡🟠🔴🟣 **Points colorés** : secteurs résidentiels couverts selon leur vulnérabilité  
                
    - 🟢 Classe 2 : faible vulnérabilité
    - 🟡 Classe 3 : vulnérabilité plutôt faible 
    - 🟠 Classe 4 : vulnérabilité plutôt forte  
    - 🔴 Classe 5 : forte vulnérabilité  
    - 🟣 Classe 6 : très forte vulnérabilité  

    Plus les points colorés sont nombreux autour d'une installation, plus sa zone d'influence est importante.
    """)

st.markdown("#### Caractéristiques de l’installation")

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
col1.metric("Surface", f"{df_install.iloc[0]['surface_m2']:.0f} m²")
col2.metric("Coût estimé", f"{df_install.iloc[0]['prix']:.0f} €")
col3.metric("Secteurs", f"{len(df_covered_habs)}")
col4.metric("Population", f"{int(total_pop)}")

categorie = df_install.iloc[0]["categorie_y"] if "categorie_y" in df_install.columns else "Non spécifiée"
col5.metric("Taille de l'installation", categorie)
if categorie == "petite":
    st.info(
        "Installation de **petite** taille : emprise foncière limitée, "
        "adaptée à des interventions ponctuelles ou de proximité."
    )

elif categorie == "moyenne":
    st.info(
        "Installation de taille **intermédiaire** : compromis entre "
        "coût d'aménagement et capacité de couverture."
    )

elif categorie == "grande":
    st.info(
        "Installation de **grande** taille : investissement plus important "
        "mais pouvant bénéficier à un nombre plus élevé de secteurs."
    )

cout_par_habitant = df_install.iloc[0]["prix"] / max(total_pop, 1)

col6.metric(
    "Coût par habitant couvert",
    f"{cout_par_habitant:.0f} €"
)

pop_moy = total_pop / max(len(df_covered_habs), 1)
col7.metric(
    "Population moyenne par secteur",
    f"{pop_moy:.0f}"
)

st.caption("Les chiffres présentés reposent sur une agrégation spatiale de la population et permettent d’estimer l’impact potentiel des installations sans représenter des individus réels.")

def couleur_vulnerabilite(classe):
    if classe == 2:
        return [170, 255, 82, 150]  
    if classe == 3:
        return [240, 208, 29, 150]   
    elif classe == 4:
        return [214, 121, 21, 150]
    elif classe == 5:
        return [214, 55, 28, 150]
    elif classe == 6:
        return [196, 2, 160, 150] 

df_covered_habs = df_covered_habs.copy()
df_covered_habs["color"] = df_covered_habs["classe"].apply(couleur_vulnerabilite)

layer_install = pdk.Layer(
    "ScatterplotLayer",
    data=df_install,
    get_position='[lon, lat]',
    get_fill_color='[60, 160, 255, 220]',
    get_radius=20,
    pickable=False
)

layer_habitants = pdk.Layer(
    "ScatterplotLayer",
    data=df_covered_habs,
    get_position='[lon, lat]',
    get_fill_color='color',
    get_radius="nb_habitants",
    radius_scale=2,
    radius_min_pixels=3,
    radius_max_pixels=17,
    opacity=0.6,
    pickable=True
)

view_state = pdk.ViewState(
    latitude=df_install.iloc[0]["lat"],
    longitude=df_install.iloc[0]["lon"],
    zoom=14
)

tooltip = {
    "html": """
    <b>Secteur :</b> {id}<br/>
    <b>Population :</b> {nb_habitants}<br/>
    <b>Classe :</b> {classe}
    """,
    "style": {
        "backgroundColor": "black",
        "color": "white"
    }
}

deck = pdk.Deck(
    layers=[layer_install, layer_habitants],
    initial_view_state=view_state,
    tooltip=tooltip,
    map_provider="carto",
    map_style="light"
)

st.pydeck_chart(deck)