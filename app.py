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
st.header("Tanzania Regional Analytics")
st.caption("UCHAMBUZI WA BEI ZA MAFUTA · TANZANIA")

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
.block-container {max-width: 1480px; padding: 1.5rem 2rem 2.5rem;}
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e1e8ed;
    border-top: 4px solid #167d88;
    border-radius: 12px;
    padding: 14px 18px;
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
            st.markdown("#### Muhtasari wa soko")

            # Kadi za viashiria muhimu ziko mstari mmoja juu ya chati.
            kadi1, kadi2, kadi3 = st.columns(3, gap="medium", wrap=True)
            kadi1.metric("Wastani wa Petroli", f"TZS {data['bei_petroli'].mean():,.0f}")
            kadi2.metric("Wastani wa Dizeli", f"TZS {data['bei_dizeli'].mean():,.0f}")
            kadi3.metric("Mikoa yenye data", f"{data['mkoa'].nunique():,}")

            st.markdown("#### Bei za mafuta")
            chati_mstari, chati_donati = st.columns([1.35, 1], gap="large", wrap=True)

            with chati_mstari:
                st.markdown("**Mwenendo wa bei**")
                if "mwezi_mwaka" in data.columns and data["mwezi_mwaka"].nunique() > 1:
                    mwenendo = (
                        data.groupby("mwezi_mwaka", as_index=False)[["bei_petroli", "bei_dizeli"]]
                        .mean()
                        .sort_values("mwezi_mwaka")
                    )
                    mwenendo = mwenendo.melt(
                        id_vars="mwezi_mwaka",
                        value_vars=["bei_petroli", "bei_dizeli"],
                        var_name="Aina ya mafuta",
                        value_name="Bei (TZS)",
                    )
                    mwenendo["Aina ya mafuta"] = mwenendo["Aina ya mafuta"].map(
                        {"bei_petroli": "Petroli", "bei_dizeli": "Dizeli"}
                    )
                    x_axis = "mwezi_mwaka"
                    x_label = "Mwezi"
                else:
                    mwenendo = (
                        data.groupby("mkoa", as_index=False)[["bei_petroli", "bei_dizeli"]]
                        .mean()
                        .melt(
                            id_vars="mkoa",
                            value_vars=["bei_petroli", "bei_dizeli"],
                            var_name="Aina ya mafuta",
                            value_name="Bei (TZS)",
                        )
                    )
                    mwenendo["Aina ya mafuta"] = mwenendo["Aina ya mafuta"].map(
                        {"bei_petroli": "Petroli", "bei_dizeli": "Dizeli"}
                    )
                    x_axis = "mkoa"
                    x_label = "Mkoa"
                    st.caption("Kwa sasa data zina mwezi mmoja; chati inaonyesha ulinganisho wa mikoa.")

                if "mwezi_mwaka" not in data.columns:
                    st.caption("Ongeza nguzo ya mwezi ili kuona mabadiliko ya muda.")
                fig_line = px.line(
                    mwenendo,
                    x=x_axis,
                    y="Bei (TZS)",
                    color="Aina ya mafuta",
                    markers=True,
                    color_discrete_sequence=["#167d88", "#d2a83e"],
                    labels={x_axis: x_label, "Bei (TZS)": "Bei (TZS)"},
                )
                fig_line.update_layout(
                    template="plotly_white", height=300, autosize=True,
                    margin=dict(l=8, r=8, t=12, b=8), legend_title_text="", hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                )
                fig_line.update_xaxes(automargin=True)
                st.plotly_chart(fig_line, width="stretch", config={"responsive": True, "displayModeBar": False})

            with chati_donati:
                st.markdown("**Mgawanyo kwa aina ya mafuta**")
                wastani_mafuta = pd.DataFrame({
                    "Aina ya mafuta": ["Petroli", "Dizeli"],
                    "Bei ya wastani (TZS)": [data["bei_petroli"].mean(), data["bei_dizeli"].mean()],
                })
                fig_donut = px.pie(
                    wastani_mafuta,
                    names="Aina ya mafuta",
                    values="Bei ya wastani (TZS)",
                    hole=0.64,
                    color="Aina ya mafuta",
                    color_discrete_map={"Petroli": "#167d88", "Dizeli": "#d2a83e"},
                )
                fig_donut.update_traces(
                    textposition="inside", textinfo="percent", sort=False,
                    hovertemplate="%{label}<br>TZS %{value:,.0f}<extra></extra>",
                )
                fig_donut.update_layout(
                    template="plotly_white", height=300, autosize=True,
                    margin=dict(l=8, r=8, t=12, b=36), legend_title_text="",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.05, xanchor="center", x=0.5),
                    annotations=[dict(text="Wastani<br>wa bei", x=0.5, y=0.5, showarrow=False, font=dict(size=13, color="#526475"))],
                )
                st.plotly_chart(fig_donut, width="stretch", config={"responsive": True, "displayModeBar": False})

            st.markdown("#### Ulinganisho wa bei kwa mkoa")
            ulinganisho = (
                data.groupby("mkoa", as_index=False)[["bei_petroli", "bei_dizeli"]]
                .mean()
                .melt(id_vars="mkoa", var_name="Aina ya mafuta", value_name="Bei ya wastani (TZS)")
            )
            ulinganisho["Aina ya mafuta"] = ulinganisho["Aina ya mafuta"].map(
                {"bei_petroli": "Petroli", "bei_dizeli": "Dizeli"}
            )
            fig_bar = px.bar(
                ulinganisho,
                x="Bei ya wastani (TZS)",
                y="mkoa",
                color="Aina ya mafuta",
                barmode="group",
                orientation="h",
                color_discrete_map={"Petroli": "#167d88", "Dizeli": "#d2a83e"},
                labels={"mkoa": "Mkoa", "Bei ya wastani (TZS)": "Bei (TZS)"},
            )
            fig_bar.update_layout(
                template="plotly_white", height=330, autosize=True, margin=dict(l=8, r=8, t=12, b=8),
                legend_title_text="", hovermode="y unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            )
            fig_bar.update_yaxes(categoryorder="total ascending", automargin=True)
            st.plotly_chart(fig_bar, width="stretch", config={"responsive": True, "displayModeBar": False})

            with st.expander("Angalia data ghafi"):
                st.dataframe(data, width="stretch", hide_index=True)
else:
    st.warning("Hakuna data zilizopatikana kwenye database. Hakikisha umeendesha 'data_pipeline.py' kwanza ili kuingiza data!")
