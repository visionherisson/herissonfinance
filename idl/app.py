import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import os

# Fonction pour récupérer et normaliser les données
def get_normalized_data(ticker, start, end):
    try:
        raw_data = yf.download(ticker, start=start, end=end)
        if raw_data.empty:
            st.warning(f"Aucune donnée disponible pour {ticker} dans la période sélectionnée.")
            return None
        if ('Close', ticker) in raw_data.columns:
            data = raw_data[('Close', ticker)]
        else:
            data = raw_data['Close']
        if data.empty:
            st.warning(f"Aucune donnée de clôture disponible pour {ticker}.")
            return None
        normalized = (data / data.iloc[0]) * 100
        return normalized
    except Exception as e:
        st.error(f"Erreur lors du chargement des données pour {ticker} : {str(e)}")
        return None

# Interface Streamlit
# Ajout de CSS pour ajuster la sidebar et optimiser l'espace pour le graphique
st.markdown(
    """
    <style>
    /* Réduire la largeur de la sidebar */
    .sidebar .sidebar-content {
        width: 180px !important;
    }
    /* Mettre le graphique en valeur et minimiser les marges */
    .stPlotlyChart {
        width: 100% !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        border: 2px solid #d0d0d0 !important;
        border-radius: 10px !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
        background-color: #f9f9f9 !important;
    }
    /* Supprimer les paddings inutiles autour du conteneur principal */
    .main .block-container {
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    /* Ajuster la hauteur minimale de la page pour éviter les espaces blancs */
    .main {
        min-height: 100vh !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Menu latéral à gauche avec le titre en haut
st.sidebar.title("📈 Comparaison des valeurs financières")
st.sidebar.markdown("Comparez les évolutions normalisées (base 100) d'actifs financiers.")
st.sidebar.header("Paramètres")

# Période personnalisable
start_date = st.sidebar.date_input("Date de début", value=datetime(2010, 1, 1), min_value=datetime(2000, 1, 1), max_value=datetime.now())
end_date = st.sidebar.date_input("Date de fin", value=datetime.now(), min_value=start_date, max_value=datetime(2025, 12, 31))
start_datetime = datetime.combine(start_date, datetime.min.time())
end_datetime = datetime.combine(end_date, datetime.min.time())

# Catégories et actifs disponibles
assets_by_category = {
    "Métaux précieux": {
        "Or": "GC=F",
        "Argent": "SI=F",
        "Cuivre": "HG=F"
    },
    "Actions": {
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Microsoft (MSFT)": "MSFT"
    },
    "Obligations": {
        "Obligations US Long Terme (TLT)": "TLT"
    },
    "Devises": {
        "Euro (EUR/USD)": "EURUSD=X",
        "Livre Sterling (GBP/USD)": "GBPUSD=X"
    },
    "ETF Populaires": {
        "Vanguard FTSE All-World (VWCE)": "VEUR.AS",
        "iShares MSCI World (IWDA)": "IWDA.AS",
        "Vanguard S&P 500 (VUSA)": "VUSA.AS",
        "iShares Core S&P 500 (CSPX)": "CSPX.AS"
    },
    "Actions Françaises": {
        "Accor": "AC.PA",
        "Air Liquide": "AI.PA",
        "Schneider Electric": "SU.PA",
        "LVMH": "MC.PA",
        "Hermès": "RMS.PA",
        "L'Oréal": "OR.PA",
        "Pernod Ricard": "RI.PA",
        "Capgemini": "CAP.PA",
        "Sodexo": "SW.PA",
        "TotalEnergies": "TTE.PA",
        "Danone": "BN.PA"
    }
}

# Liste déroulante pour chaque catégorie avec placeholder personnalisé
selected_assets = {}
for category, assets in assets_by_category.items():
    # Créer une liste déroulante sans valeur par défaut pour simuler "Choisir une option"
    options = list(assets.keys())
    selected = st.sidebar.multiselect(
        f"{category}",
        options=options,
        default=[] if category != "Métaux précieux" else ["Or"],
        key=category,
        help="Sélectionnez un ou plusieurs actifs"
    )
    if not selected and category == "Métaux précieux":
        st.sidebar.markdown(f"*Choisir une option*")
    elif not selected:
        st.sidebar.markdown(f"*Choisir une option*")
    selected_assets[category] = selected

# Fusionner toutes les sélections dans une liste unique de tickers
all_selected_tickers = []
ticker_to_name = {}
for category, selections in selected_assets.items():
    for asset in selections:
        ticker = assets_by_category[category][asset]
        all_selected_tickers.append(ticker)
        ticker_to_name[ticker] = asset

# Récupérer les données pour les actifs sélectionnés
data = {}
for ticker in all_selected_tickers:
    st.write(f"Chargement des données pour {ticker}...")
    result = get_normalized_data(ticker, start_datetime.strftime("%Y-%m-%d"), end_datetime.strftime("%Y-%m-%d"))
    if result is not None and not result.empty:
        data[ticker] = result
    else:
        st.error(f"Échec du chargement des données pour {ticker}.")

# Vérifier les données
if not data:
    st.error("Aucune donnée valide récupérée. Essayez d'autres actifs ou une période différente.")
else:
    # Créer un DataFrame avec toutes les séries
    df = pd.DataFrame(data)
    df.columns = [ticker_to_name.get(ticker, ticker) for ticker in df.columns]

    # Ajouter des annotations pour les dates historiques (présidents français et Trump)
    historical_events = {
        "Début 2e mandat Chirac (16/05/2002)": datetime(2002, 5, 16),
        "Début mandat Sarkozy (16/05/2007)": datetime(2007, 5, 16),
        "Début mandat Hollande (15/05/2012)": datetime(2012, 5, 15),
        "Début mandat Macron (17/05/2017)": datetime(2017, 5, 17),
        "Début 1er mandat Trump (20/01/2017)": datetime(2017, 1, 20),
        "Début 2e mandat Trump (20/01/2025)": datetime(2025, 1, 20)
    }
    st.sidebar.header("Événements historiques")
    show_events = st.sidebar.checkbox("Afficher les événements historiques", value=True)

    # Définir les périodes de récession
    recessions = [
        {"start": datetime(2007, 12, 1), "end": datetime(2009, 6, 30), "label": "Grande Récession"},
        {"start": datetime(2020, 2, 1), "end": datetime(2020, 6, 30), "label": "Récession COVID-19"}
    ]

    # Création du graphique interactif avec Plotly
    fig = go.Figure()
    for column in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[column], mode='lines', name=column, line=dict(width=2)))

    # Ajouter les zones de récession (sans hatch, avec remplissage semi-transparent)
    for recession in recessions:
        if start_datetime <= recession["end"] and end_datetime >= recession["start"]:
            fig.add_shape(
                type="rect",
                x0=max(recession["start"], start_datetime),
                x1=min(recession["end"], end_datetime),
                y0=0,
                y1=df.max().max() * 1.1,
                fillcolor="gray",
                opacity=0.2,
                line_width=0,
                layer="below"
            )
            fig.add_annotation(
                x=max(recession["start"], start_datetime),
                y=df.max().max() * 1.05,
                text=recession["label"],
                showarrow=False,
                font=dict(size=10),
                align="left",
                bgcolor="white",
                opacity=0.8
            )

    # Ajouter les lignes verticales pour les événements historiques
    if show_events:
        for event_name, event_date in historical_events.items():
            if start_datetime <= event_date <= end_datetime:
                fig.add_vline(x=event_date, line_dash="dash", line_color="red", opacity=0.5)
                fig.add_annotation(
                    x=event_date, y=df.max().max() * 0.95,
                    text=event_name, showarrow=True, arrowhead=0,
                    ax=20, ay=-30, bgcolor="white", opacity=0.8
                )

    # Ajuster la taille, les marges et la légende du graphique
    fig.update_layout(
        title="Évolution normalisée des actifs sélectionnés",
        xaxis_title="Date",
        yaxis_title="Valeur normalisée (base 100)",
        hovermode="x unified",
        showlegend=True,
        template="plotly_white",
        height=1000,  # Augmenter la hauteur pour utiliser l'espace vertical
        margin=dict(l=0, r=0, t=40, b=20),  # Réduire les marges pour minimiser l'espace blanc
        legend=dict(
            x=0.8,  # Placer la légende en haut à droite
            y=0.98,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="Black",
            borderwidth=1,
            font=dict(size=16)  # Police plus grande pour la lisibilité
        )
    )

    # Afficher le graphique
    st.plotly_chart(fig, use_container_width=True)

    # Calculer le rendement total
    st.write("Rendement total (%) sur la période :")
    returns = {}
    for column in df.columns:
        if df[column].iloc[-1] and df[column].iloc[0]:
            return_value = (df[column].iloc[-1] - df[column].iloc[0]) / df[column].iloc[0] * 100
            returns[column] = round(return_value, 2)
    if returns:
        for asset, return_value in returns.items():
            st.write(f"{asset}: {return_value}")
    else:
        st.write("Aucun rendement calculable pour les actifs sélectionnés.")

    # Centrer le bouton de téléchargement
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        csv = df.to_csv(index=True)
        st.download_button(
            label="📥 Télécharger les données (CSV)",
            data=csv,
            file_name=f"financial_comparison_{end_date}.csv",
            mime="text/csv"
        )

# Afficher le logo de hérisson en bas à droite
if os.path.exists("hedgehog_logo.png"):
    col1, col2 = st.columns([4, 1])
    with col2:
        st.image("hedgehog_logo.png", width=150)

