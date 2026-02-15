import streamlit as st
import pandas as pd
import os, json
from streamlit_gsheets import GSheetsConnection

# --- KONFIGURACE ---
KLUB_NAZEV = "Club přátel pétanque HK - LIVE VÝSLEDKY"
st.set_page_config(page_title=KLUB_NAZEV, layout="wide")

# --- PŘIPOJENÍ KE GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("Nepodařilo se připojit k databázi výsledků.")
    st.stop()

def nacti_data():
    try:
        df = conn.read(worksheet="Stav", ttl=0)
        if not df.empty and "stav_json" in df.columns:
            r = df.iloc[0]["stav_json"]
            if r and r != "{}" and not pd.isna(r):
                return json.loads(r)
    except: pass
    return None

data = nacti_data()

# --- ZOBRAZENÍ ---
if os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=100)

if not data or data.get("kolo") == 0:
    st.info("⌛ Turnaj zatím nebyl zahájen. Čekáme na první kolo...")
else:
    st.title(f"📊 {data['nazev_akce']}")
    
    # Rozhodnutí, zda je turnaj u konce
    je_konec = data['kolo'] > data['max_kol']
    
    if je_konec:
        st.success("🏁 Turnaj byl ukončen - Konečné výsledky")
    else:
        st.warning(f"🏟️ Probíhá {data['kolo']}. kolo z {data['max_kol']}")

    # Příprava tabulky
    df_t = pd.DataFrame(data['tymy'])
    # Odfiltrování volného losu pro tabulku
    df_t = df_t[df_t["Hráč/Tým"] != "VOLNÝ LOS"].copy()
    df_t["Rozdíl"] = df_t["Skóre +"] - df_t["Skóre -"]
    
    # Seřazení podle pravidel (Výhry > Buchholz > Rozdíl)
    df_t = df_t.sort_values(by=["Výhry", "Buchholz", "Rozdíl"], ascending=False).reset_index(drop=True)
    df_t.index += 1

    # Zobrazení tabulky (včetně sloupce Buchholz, aby hráči viděli proč jsou tam kde jsou)
    st.subheader("Aktuální pořadí")
    st.table(df_t[["Hráč/Tým", "Výhry", "Buchholz", "Skóre +", "Skóre -", "Rozdíl"]])

    # Historie zápasů
    st.subheader("📊 Odehrané zápasy")
    if not data['historie']:
        st.write("Zatím nebyly odehrány žádné zápasy.")
    else:
        # Otočíme historii, aby nejnovější kola byla nahoře
        historie_df = pd.DataFrame(data['historie'])
        for k in sorted(historie_df["Kolo"].unique(), reverse=True):
            with st.expander(f"Kolo {k}", expanded=(k == data['kolo']-1 or je_konec)):
                kol_zápasy = historie_df[historie_df["Kolo"] == k]
                for _, z in kol_zápasy.iterrows():
                    # Vizuální zvýraznění vítěze
                    if z["S1"] > z["S2"]:
                        st.write(f"🏆 **{z['Hráč/Tým 1']}** {z['S1']} : {z['S2']} {z['Hráč/Tým 2']}")
                    elif z["S2"] > z["S1"]:
                        st.write(f"{z['Hráč/Tým 1']} {z['S1']} : {z['S2']} **{z['Hráč/Tým 2']}** 🏆")
                    else:
                        st.write(f"{z['Hráč/Tým 1']} {z['S1']} : {z['S2']} {z['Hráč/Tým 2']}")

st.caption("Data se aktualizují automaticky po každém kole. Pro ruční aktualizaci obnovte stránku.")
