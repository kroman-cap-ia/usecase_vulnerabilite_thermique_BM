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

st.markdown(
"""
Cette interface permet d’analyser les solutions d’implantation
d’installations sélectionnées par un algorithme d’optimisation
dans le cadre d’une étude de vulnérabilité thermique.
"""
)


st.subheader("Ce que vous pouvez explorer")

st.markdown(
"""
- Les caractéristiques techniques et économiques de chaque installation
- Les secteurs résidentiels concernés
- La population potentiellement impactée
- La distribution spatiale des zones couvertes

Les résultats affichés correspondent à des scénarios d’aménagement
et non à des réalisations existantes.
"""
)


st.markdown("________________")


# =====================================================
# PARAMETRES
# =====================================================

ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT / "../data/processed"


center_bounds = {
    "lat_min":44.82,
    "lat_max":44.86,
    "lon_min":-0.57,
    "lon_max":-0.53
}



# =====================================================
# CHARGEMENT DONNEES
# =====================================================

@st.cache_data
def load_data():

    df_hab = pd.read_parquet(
        PROCESSED_DIR / "habitants/habitants.parquet",
        columns=[
            "id",
            "nb_habitants",
            "classe",
            "lat",
            "lon"
        ]
    )


    df_res = pd.read_csv(
        PROCESSED_DIR / "resultats/resultats_glouton.csv",
        usecols=[
            "id_i",
            "id_j",
            "surface_m2",
            "prix",
            "categorie_y"
        ]
    )


    df_a = pd.read_parquet(
        PROCESSED_DIR / "matrices/a_ijc.parquet",
        columns=[
            "id_i",
            "id_j",
            "id_c"
        ]
    )


    df_e = pd.read_parquet(
        PROCESSED_DIR / "emplacements/emplacements_final.parquet",
        columns=[
            "id",
            "lon",
            "lat"
        ]
    )


    df_e = df_e.rename(
        columns={"id":"id_i"}
    )


    # coordonnées installations

    df_res = df_res.merge(
        df_e,
        on="id_i",
        how="left"
    )


    # filtre géographique

    df_hab = df_hab[
        df_hab["lat"].between(
            center_bounds["lat_min"],
            center_bounds["lat_max"]
        )
        &
        df_hab["lon"].between(
            center_bounds["lon_min"],
            center_bounds["lon_max"]
        )
    ]


    # garder seulement les couples existants

    df_a = df_a.merge(
        df_res[["id_i","id_j"]],
        on=["id_i","id_j"],
        how="inner"
    )


    # index accélération

    df_hab = df_hab.set_index("id")


    df_a = df_a.set_index(
        ["id_i","id_j"]
    )


    df_res = df_res.set_index(
        ["id_i","id_j"]
    )


    return df_res, df_a, df_hab




with st.spinner("📦 Chargement des données..."):

    df_res, df_a, df_hab = load_data()



# =====================================================
# SELECTION INSTALLATION
# =====================================================


st.subheader("📍 Analyse d’une installation")



ids_habitants = set(df_hab.index)



installation_options_valid = (

    df_a[
        df_a["id_c"].isin(ids_habitants)
    ]
    .reset_index()[

        [
            "id_i",
            "id_j"
        ]

    ]
    .drop_duplicates()
    .sort_values(
        [
            "id_i",
            "id_j"
        ]
    )

)



if installation_options_valid.empty:

    st.error(
        "Aucune installation ne couvre la zone sélectionnée."
    )

    st.stop()



installation_options_valid["label"] = (

    installation_options_valid["id_i"].astype(str)

    + " – "

    + installation_options_valid["id_j"].astype(str)

)



selection = st.selectbox(

    "Sélectionnez une solution d’implantation pour visualiser son impact territorial :",

    installation_options_valid["label"].unique()

)



id_i_sel, id_j_sel = selection.split(" – ")


id_i_sel = int(id_i_sel)

id_j_sel = int(id_j_sel)



# =====================================================
# DONNEES INSTALLATION
# =====================================================


df_install = (

    df_res

    .loc[
        (id_i_sel,id_j_sel)
    ]

)



if isinstance(df_install,pd.Series):

    df_install = df_install.to_frame().T



try:

    df_covered = (
        df_a
        .loc[(id_i_sel,id_j_sel)]
        .reset_index()
    )


except KeyError:

    df_covered = pd.DataFrame(
        columns=[
            "id_i",
            "id_j",
            "id_c"
        ]
    )



if isinstance(df_covered,pd.Series):

    df_covered = df_covered.to_frame().T



df_covered_habs = (

    df_hab

    .loc[
        df_hab.index.intersection(
            df_covered["id_c"]
        )
    ]

    .reset_index()

)



total_pop = df_covered_habs["nb_habitants"].sum()

# =====================================================
# SYNTHESE IMPACT
# =====================================================


st.info(
f"""
Synthèse d’impact :

- Secteurs résidentiels concernés : **{len(df_covered_habs)}**
- Population totale estimée : **{int(total_pop):,} personnes**

Ces valeurs représentent une estimation agrégée de la population exposée
dans les zones couvertes par l’installation.
"""
)


st.markdown(
"""
Le tableau ci-dessous présente les secteurs résidentiels couverts par
l'installation sélectionnée. Chaque secteur est associé à une estimation
de population et à une classe de vulnérabilité thermique.
"""
)


st.dataframe(
    df_covered_habs[
        [
            "id",
            "nb_habitants",
            "classe",
            "lon",
            "lat"
        ]
    ],
    use_container_width=True
)



# =====================================================
# GRAPHIQUE VULNERABILITE
# =====================================================


st.markdown(
"#### 🔥 Répartition des niveaux de vulnérabilité thermique"
)


with st.expander(
    "Comprendre l'indice de vulnérabilité thermique"
):

    st.markdown(
"""
**Indice de vulnérabilité thermique**

Les secteurs résidentiels sont classés selon leur niveau de vulnérabilité :

- **3** : Vulnérabilité plutôt faible
- **4** : Vulnérabilité plutôt forte
- **5** : Forte vulnérabilité
- **6** : Très forte vulnérabilité

Les niveaux élevés correspondent aux secteurs les plus sensibles
aux épisodes de chaleur.
"""
)



df_plot = (

    df_covered_habs["classe"]

    .value_counts()

    .reset_index()

)


df_plot.columns = [
    "classe",
    "count"
]


df_plot = df_plot.sort_values(
    "classe"
)



chart = (

    alt.Chart(df_plot)

    .mark_bar(
        color="#019de0"
    )

    .encode(

        x=alt.X(
            "classe:O",
            title="Classe de vulnérabilité",
            axis=alt.Axis(
                labelAngle=0
            )
        ),

        y=alt.Y(
            "count:Q",
            title="Nombre de secteurs"
        ),

        tooltip=[
            "classe",
            "count"
        ]

    )

    .properties(
        height=350
    )

)



st.altair_chart(
    chart,
    use_container_width=True
)



# =====================================================
# INFORMATIONS INSTALLATION
# =====================================================


st.subheader(
    "🗺️ Carte de l'installation et des secteurs couverts"
)


st.markdown(
"""
La carte permet d’évaluer la cohérence spatiale de la solution
et sa capacité à couvrir les zones les plus vulnérables.
"""
)



st.markdown(
"#### Caractéristiques de l’installation"
)



installation = df_install.iloc[0]


col1,col2,col3,col4,col5,col6,col7 = st.columns(7)



col1.metric(
    "Surface",
    f"{installation['surface_m2']:.0f} m²"
)


col2.metric(
    "Coût estimé",
    f"{installation['prix']:.0f} €"
)


col3.metric(
    "Secteurs",
    len(df_covered_habs)
)


col4.metric(
    "Population",
    f"{int(total_pop)}"
)



categorie = installation["categorie_y"]


col5.metric(
    "Taille installation",
    categorie
)



cout_par_habitant = (

    installation["prix"]

    /

    max(total_pop,1)

)



col6.metric(
    "Coût/habitant",
    f"{cout_par_habitant:.0f} €"
)



pop_moy = (

    total_pop

    /

    max(len(df_covered_habs),1)

)



col7.metric(
    "Population moyenne/secteur",
    f"{pop_moy:.0f}"
)



if categorie == "petite":

    st.info(
"""
Installation de **petite taille** :
emprise foncière limitée, adaptée
aux interventions ponctuelles.
"""
)


elif categorie == "moyenne":

    st.info(
"""
Installation de taille **intermédiaire** :
compromis entre coût et capacité
de couverture.
"""
)


elif categorie == "grande":

    st.info(
"""
Installation de **grande taille** :
investissement plus important mais
capacité de couverture élevée.
"""
)



st.caption(
"""
Les chiffres présentés reposent sur une agrégation spatiale de la population
et permettent d’estimer l’impact potentiel des installations sans représenter
des individus réels.
"""
)



# =====================================================
# CARTE PYDECK
# =====================================================


def couleur_vulnerabilite(classe):

    couleurs = {

        2:[170,255,82,150],

        3:[240,208,29,150],

        4:[214,121,21,150],

        5:[214,55,28,150],

        6:[196,2,160,150]

    }


    return couleurs.get(
        classe,
        [150,150,150,150]
    )



df_covered_habs = df_covered_habs.copy()



df_covered_habs["color"] = (

    df_covered_habs["classe"]

    .apply(
        couleur_vulnerabilite
    )

)



layer_install = pdk.Layer(

    "ScatterplotLayer",

    data=df_install,

    get_position='[lon, lat]',

    get_fill_color='[60,160,255,220]',

    get_radius=25,

    pickable=False

)



layer_habitants = pdk.Layer(

    "ScatterplotLayer",

    data=df_covered_habs,

    get_position='[lon, lat]',

    get_fill_color="color",

    get_radius="nb_habitants",

    radius_scale=2,

    radius_min_pixels=3,

    radius_max_pixels=17,

    opacity=0.6,

    pickable=True

)



view_state = pdk.ViewState(

    latitude=installation["lat"],

    longitude=installation["lon"],

    zoom=14

)



tooltip = {

    "html":

    """

    <b>Secteur :</b> {id}<br/>

    <b>Population :</b> {nb_habitants}<br/>

    <b>Classe :</b> {classe}

    """,

    "style":

    {

        "backgroundColor":"black",

        "color":"white"

    }

}



deck = pdk.Deck(

    layers=[

        layer_install,

        layer_habitants

    ],

    initial_view_state=view_state,

    tooltip=tooltip,

    map_provider="carto",

    map_style="light"

)



st.pydeck_chart(deck)