import os

import pandas as pd
import psycopg2
import streamlit as st


def database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        try:
            url = st.secrets["database"]["url"]
        except Exception as exc:
            raise RuntimeError("Weka DATABASE_URL au [database].url kwenye secrets.") from exc
    if not url:
        raise RuntimeError("Weka DATABASE_URL au [database].url kwenye secrets.")
    return url.replace("postgresql+psycopg2://", "postgresql://", 1)


def run_data_pipeline():
    print("⏳ Hatua ya 1: Tunakusanya na kusafisha data...")

    # Bei za mfano kwa majaribio tu; si bei rasmi za EWURA.
    raw_data = {
        "mkoa": ["dar es salaam", "ARUSHA", "mwanza", "geita", "dodoma"],
        "mwezi_mwaka": ["November 2026"] * 5,
        "bei_petroli": [3200, 3300, 3250, 3100, 3150],
        "bei_dizeli": [3400, 3500, 3420, 3300, 3350],
        "shughuli_kuu": ["Biashara/Bandari", "Utalii", "Uvuvi/Biashara", "Madini", "Serikali/Utawala"],
    }
    df = pd.DataFrame(raw_data)
    df["mkoa"] = df["mkoa"].str.title()

    print("⏳ Hatua ya 2: Tunaunganisha Python na PostgreSQL...")
    try:
        with psycopg2.connect(database_url()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS regional_analytics (
                        id BIGSERIAL PRIMARY KEY,
                        mkoa TEXT NOT NULL,
                        mwezi_mwaka TEXT,
                        bei_petroli NUMERIC,
                        bei_dizeli NUMERIC,
                        shughuli_kuu TEXT
                    )
                    """
                )
                for _, row in df.iterrows():
                    cursor.execute(
                        """
                        INSERT INTO regional_analytics
                            (mkoa, mwezi_mwaka, bei_petroli, bei_dizeli, shughuli_kuu)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            row["mkoa"], row["mwezi_mwaka"], int(row["bei_petroli"]),
                            int(row["bei_dizeli"]), row["shughuli_kuu"],
                        ),
                    )
        print("✅ Kazi imekamilika; data zimeingizwa PostgreSQL.")
    except Exception as exc:
        print(f"❌ Hitilafu imetokea: {exc}")


if __name__ == "__main__":
    run_data_pipeline()
