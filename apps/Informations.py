import streamlit as st

st.set_page_config(
    page_title="Métropole rafraîchissante",
    page_icon="🌳",
    layout="wide"
)

st.title("🌳 Métropole rafraîchissante – Projet académique")
st.subheader("Scénarios d’implantation d’espaces de fraîcheur à Bordeaux Métropole")

st.markdown("""
Cette application a été développée dans le cadre d’un **projet de Master 2 Informatique (parcours Recherche Opérationnelle)**, en collaboration avec **Bordeaux Métropole**.

**Équipe projet**
- Ahina DURRIEU
- Enzo QUATTROCHI
- Paul-Henri LEPLOMB

L’objectif général est d’étudier différentes stratégies d’implantation d’espaces de fraîcheur pour améliorer l’accès des habitants à des lieux de refuge lors des épisodes de fortes chaleurs.
""")

st.markdown("---")

st.markdown("""
### Contexte

Avec la multiplication des vagues de chaleur, Bordeaux Métropole a engagé le projet **“Métropole rafraîchissante”**. L’idée est simple : permettre à chaque habitant d’accéder à un espace de fraîcheur en moins de **300 mètres** de son domicile.

Ces espaces peuvent être très variés : parcs, zones végétalisées, lieux publics climatisés ou encore aménagements urbains pensés pour réduire l’effet de chaleur.

Dans ce cadre, une attention particulière est portée aux secteurs les plus exposés et aux populations les plus vulnérables.
""")

st.markdown("---")

st.markdown("""
### Objectif

Le travail présenté ici consiste à simuler et comparer plusieurs scénarios d’implantation.

Concrètement, le modèle essaie de trouver un équilibre entre plusieurs aspects :
- couvrir un maximum d’habitants
- mieux desservir les zones vulnérables
- rester dans des contraintes de coût
- éviter de concentrer les investissements sur quelques quartiers

Les résultats affichés sont donc des propositions issues d’un modèle d’optimisation, et non des décisions d’aménagement.
""")

st.markdown("---")

st.markdown("""
### Données utilisées

L’application repose sur des données géographiques représentant :
- les habitants (localisation et population estimée)
- les installations potentielles
- un indice de vulnérabilité thermique (ICTU)

Ces données permettent de comprendre comment les installations couvrent le territoire et quels habitants sont les plus exposés.

Elles servent ensuite de base au modèle pour simuler différents scénarios d’aménagement à l’échelle de Bordeaux Métropole.
""")

st.markdown("---")

st.markdown("""
### Navigation dans l’application

L’application est organisée en deux vues complémentaires :

**Analyse d’une installation**  
On explore ici une installation précise : coût, surface, population couverte et zones concernées, avec une visualisation sur carte.

**Analyse d’un habitant**  
Cette vue permet de comprendre quelles installations impactent un habitant donné et avec quelle intensité, via les indicateurs d’impact thermique.
""")

st.markdown("---")

st.markdown("""
### Ressources du projet

Les documents associés au projet sont disponibles ci-dessous.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.link_button("📄 Rapport", "https://gitlab.emi.u-bordeaux.fr/pleplomb/ter_2025/-/raw/main/docs/reference/rapport_ter_final.pdf?inline=true")

with col2:
    st.link_button("🖥️ Slides", "https://gitlab.emi.u-bordeaux.fr/pleplomb/ter_2025/-/raw/main/docs/reference/slides_point_etape_2025-03-12.pdf?inline=true")

with col3:
    st.link_button("💻 Code source", "https://gitlab.emi.u-bordeaux.fr/pleplomb/ter_2025")

st.markdown("---")

st.info("""
Ce projet est un prototype académique. Les résultats présentés correspondent à des simulations réalisées à partir d’un modèle d’optimisation et servent uniquement à l’analyse et à l’aide à la décision.
""")