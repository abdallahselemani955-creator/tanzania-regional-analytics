import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

# 1. Muundo wa Ukurasa wa Streamlit
st.set_page_config(
    page_title="Tanzania Regional Analytics",
    layout="wide",
    page_icon="🇹🇿",
    initial_sidebar_state="collapsed",
)
st.subheader("Tanzania Regional Analytics")

# 2. Unganisha na PostgreSQL Database yako
# Hifadhi URL ya database kwenye Streamlit Secrets au env var, kamwe ndani ya source.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    try:
        DATABASE_URL = st.secrets["database"]["url"]
    except Exception:
        DATABASE_URL = None

@st.cache_data # Inasaidia app iwe na kasi kwa kutovuta data kila sekunde
def load_data():
    try:
        # Pin SQLAlchemy to the installed psycopg2 driver regardless of URL defaults.
        database_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        engine = create_engine(database_url)
        df = pd.read_sql("SELECT * FROM regional_analytics", engine)
        return df
    except Exception as e:
        st.error(f"❌ Imeshindwa kuunganisha database: {e}")
        return pd.DataFrame()

# Vuta data

df = load_data()

st.markdown("""
<style>
.block-container {max-width: 1480px; padding: 3.5rem 2rem 1rem;}
h3 {font-size: 1.25rem !important; line-height: 1.15 !important; padding: 0 !important; margin: 0 0 0.2rem !important;}
h4 {font-size: 1rem !important; line-height: 1.15 !important; padding: 0 !important; margin: 0.2rem 0 !important;}
[data-testid="stMetricValue"] > div {font-size: 1.4rem !important; line-height: 1.15 !important;}
@media (max-width: 640px) {
    .block-container {padding: 4.25rem 1rem 1rem;}
    h3 {font-size: 1.15rem !important;}
    h4 {font-size: 1rem !important;}
}
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e1e8ed;
    border-top: 4px solid #167d88;
    border-radius: 12px;
    padding: 4px 12px;
}
[data-testid="stMetricLabel"] {color: #526475;}
[data-testid="stMetricValue"] {color: #142b3a;}
[data-testid="stMetricLabel"] p {white-space: normal; overflow-wrap: anywhere;}
[data-testid="stMetricValue"] {overflow-wrap: anywhere;}
</style>
""", unsafe_allow_html=True)

if not df.empty:
    # Hakikisha nguzo zinazohitajika zipo kabla ya kuchora dashboard.
    required_columns = {"mkoa", "bei_petroli", "bei_dizeli"}
    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        st.error("Data haina nguzo zinazohitajika: " + ", ".join(sorted(missing_columns)))
    else:
        data = df.copy()
        data["bei_petroli"] = pd.to_numeric(data["bei_petroli"], errors="coerce")
        data["bei_dizeli"] = pd.to_numeric(data["bei_dizeli"], errors="coerce")
        data = data.dropna(subset=["mkoa", "bei_petroli", "bei_dizeli"])

        if data.empty:
            st.warning("Hakuna bei halali zilizopatikana za kuonyesha.")
        else:
            # Kadi za viashiria muhimu ziko mstari mmoja juu ya chati.
            kadi1, kadi2, kadi3 = st.columns(3, gap="medium", wrap=True)
            kadi1.metric("Wastani wa Petroli", f"TZS {data['bei_petroli'].mean():,.0f}")
            kadi2.metric("Wastani wa Dizeli", f"TZS {data['bei_dizeli'].mean():,.0f}")
            kadi3.metric("Mikoa yenye data", f"{data['mkoa'].nunique():,}")

            regional = data.groupby("mkoa", as_index=False)[["bei_petroli", "bei_dizeli"]].mean()
            chati_mstari, chati_donati = st.columns([1.7, 1], gap="large", wrap=True)

            with chati_mstari:
                with st.container(border=True):
                    st.markdown("**Bei za petroli na dizeli kwa mkoa**")
                    mwenendo = regional.melt(
                        id_vars="mkoa",
                        value_vars=["bei_petroli", "bei_dizeli"],
                        var_name="Aina ya mafuta",
                        value_name="Bei (TZS)",
                    )
                    mwenendo["Aina ya mafuta"] = mwenendo["Aina ya mafuta"].map(
                        {"bei_petroli": "Petroli", "bei_dizeli": "Dizeli"}
                    )
                    fig_line = px.line(
                        mwenendo,
                        x="mkoa",
                        y="Bei (TZS)",
                        color="Aina ya mafuta",
                        markers=True,
                        color_discrete_map={"Petroli": "#167d88", "Dizeli": "#d2a83e"},
                        labels={"mkoa": "Mkoa", "Bei (TZS)": "Wastani (TZS)"},
                    )
                    fig_line.update_layout(
                        template="plotly_white", height=150, autosize=True,
                        margin=dict(l=8, r=8, t=12, b=8), legend_title_text="", hovermode="x unified",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                    )
                    fig_line.update_xaxes(automargin=True)
                    st.plotly_chart(fig_line, width="stretch", config={"responsive": True, "displayModeBar": False})

            with chati_donati:
                with st.container(border=True):
                    st.markdown("**Wastani wa petroli kwa mkoa**")
                    fig_donut = px.pie(
                        regional,
                        names="mkoa",
                        values="bei_petroli",
                        hole=0.62,
                        color="mkoa",
                        color_discrete_sequence=["#167d88", "#d2a83e", "#c96e55", "#8a9c78", "#8795a1"],
                        labels={"mkoa": "Mkoa", "bei_petroli": "Petroli (TZS)"},
                    )
                    fig_donut.update_traces(
                        textposition="inside", texttemplate="%{percent}",
                        hovertemplate="%{label}<br>TZS %{value:,.0f}<extra></extra>",
                    )
                    idadi_mikoa = regional["mkoa"].nunique()
                    fig_donut.update_layout(
                        template="plotly_white", height=150, autosize=True,
                        margin=dict(l=18, r=18, t=12, b=8), legend_title_text="",
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0),
                        annotations=[dict(
                            text=f"{idadi_mikoa}<br>Mikoa",
                            x=0.43, y=0.5, showarrow=False,
                            font=dict(size=14, color="#142b3a"),
                        )],
                    )
                    st.plotly_chart(fig_donut, width="stretch", config={"responsive": True, "displayModeBar": False})

            st.markdown("#### Ulinganisho wa wastani wa bei kwa mkoa")
            ulinganisho = regional.melt(
                id_vars="mkoa", var_name="Aina ya mafuta", value_name="Bei (TZS)"
            )
            ulinganisho["Aina ya mafuta"] = ulinganisho["Aina ya mafuta"].map(
                {"bei_petroli": "Petroli", "bei_dizeli": "Dizeli"}
            )
            fig_bar = px.bar(
                ulinganisho,
                x="mkoa",
                y="Bei (TZS)",
                color="Aina ya mafuta",
                barmode="group",
                color_discrete_map={"Petroli": "#167d88", "Dizeli": "#d2a83e"},
                labels={"mkoa": "Mkoa"},
            )
            fig_bar.update_layout(
                template="plotly_white", height=150, autosize=True, margin=dict(l=8, r=8, t=12, b=8),
                legend_title_text="", hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            )
            fig_bar.update_xaxes(tickangle=-10, automargin=True)
            with st.container(border=True):
                st.plotly_chart(fig_bar, width="stretch", config={"responsive": True, "displayModeBar": False})

            with st.expander("Angalia data ghafi"):
                st.dataframe(data, width="stretch", hide_index=True)
else:
    st.warning("Hakuna data zilizopatikana kwenye database. Hakikisha umeendesha 'data_pipeline.py' kwanza ili kuingiza data!")
