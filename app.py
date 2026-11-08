import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Muundo wa Ukurasa wa Streamlit
st.set_page_config(page_title="Tanzania Regional Analytics", layout="wide", page_icon="🇹🇿")
st.title("🇹🇿 Tanzania Regional Economic & Fuel Analytics")
st.markdown("Mfumo wa majaribio unaochanganua bei za mafuta na shughuli za kiuchumi kwa mikoa ya Tanzania.")

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
        engine = create_engine(DATABASE_URL)
        df = pd.read_sql("SELECT * FROM regional_analytics", engine)
        return df
    except Exception as e:
        st.error(f"❌ Imeshindwa kuunganisha database: {e}")
        return pd.DataFrame()

# Vuta data

df = load_data()

st.markdown("""
<style>
.block-container {padding-top: 1.35rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {
    background: #f4f7f6;
    border: 1px solid #e1e9e6;
    border-top: 4px solid #456f78;
    border-radius: 10px;
    padding: 16px 18px;
}
[data-testid="stMetricLabel"] {color: #53656a;}
[data-testid="stMetricValue"] {color: #20343a;}
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
            st.caption("Muhtasari wa bei za mafuta kwa mikoa ya Tanzania")

            # Kadi za viashiria muhimu ziko mstari mmoja juu ya chati.
            kadi1, kadi2, kadi3 = st.columns(3)
            kadi1.metric("Wastani wa Petroli", f"TZS {data['bei_petroli'].mean():,.0f}")
            kadi2.metric("Wastani wa Dizeli", f"TZS {data['bei_dizeli'].mean():,.0f}")
            kadi3.metric("Mikoa yenye data", f"{data['mkoa'].nunique():,}")

            st.markdown("### Mwenendo na mgawanyo wa bei")
            chati_mstari, chati_donati = st.columns([1.7, 1], gap="large")

            with chati_mstari:
                if "mwezi_mwaka" in data.columns:
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
                    fig_line = px.line(
                        mwenendo,
                        x="mwezi_mwaka",
                        y="Bei (TZS)",
                        color="Aina ya mafuta",
                        markers=True,
                        color_discrete_sequence=["#456f78", "#d0af4e"],
                        labels={"mwezi_mwaka": "Mwezi", "Bei (TZS)": "Bei (TZS)"},
                    )
                    fig_line.update_layout(
                        template="plotly_white", height=360, margin=dict(l=10, r=10, t=25, b=10),
                        legend_title_text="", hovermode="x unified",
                    )
                    st.plotly_chart(fig_line, width="stretch")
                else:
                    st.info("Nguzo ya mwezi_mwaka haipo; mwenendo wa kila mwezi hauwezi kuonyeshwa.")

            with chati_donati:
                wastani_mkoa = data.groupby("mkoa", as_index=False)["bei_petroli"].mean()
                fig_donut = px.pie(
                    wastani_mkoa,
                    names="mkoa",
                    values="bei_petroli",
                    hole=0.58,
                    color_discrete_sequence=["#456f78", "#d0af4e", "#c96e55", "#8a9c78", "#8795a1", "#b18a62"],
                    labels={"mkoa": "Mkoa", "bei_petroli": "Wastani wa petroli (TZS)"},
                )
                fig_donut.update_traces(textposition="inside", textinfo="percent", hovertemplate="%{label}<br>TZS %{value:,.0f}<extra></extra>")
                fig_donut.update_layout(
                    template="plotly_white", height=360, margin=dict(l=10, r=10, t=25, b=10),
                    legend_title_text="Mkoa",
                )
                st.plotly_chart(fig_donut, width="stretch")

            st.markdown("### Ulinganisho wa wastani wa bei kwa mkoa")
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
                x="mkoa",
                y="Bei ya wastani (TZS)",
                color="Aina ya mafuta",
                barmode="group",
                color_discrete_sequence=["#456f78", "#d0af4e"],
                labels={"mkoa": "Mkoa"},
            )
            fig_bar.update_layout(
                template="plotly_white", height=400, margin=dict(l=10, r=10, t=25, b=10),
                legend_title_text="", hovermode="x unified",
            )
            st.plotly_chart(fig_bar, width="stretch")

            with st.expander("Angalia data ghafi"):
                st.dataframe(data, width="stretch", hide_index=True)
else:
    st.warning("Hakuna data zilizopatikana kwenye database. Hakikisha umeendesha 'data_pipeline.py' kwanza ili kuingiza data!")
