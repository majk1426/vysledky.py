import streamlit as st
import pandas as pd
import os, json
from streamlit_gsheets import GSheetsConnection

# --- KONFIGURACE ---
KLUB_NAZEV = "Club přátel pétanque HK"
st.set_page_config(page_title="LIVE Výsledky | Pétanque HK", layout="wide")

# Vlastní CSS pro vizuální styl
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-top: 4px solid #1e3a8a; }
    .stTable { background-color: white; border-radius: 10px; }
    h1 { color: #1e3a8a; margin-bottom: 0; }
    .system-badge { background-color: #e2e8f0; padding: 4px 12px; border-radius: 15px; font-size: 0.9em; font-weight: bold; color: #475569; }
    </style>
    """, unsafe_allow_html=True)

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

# --- LOGO A HLAVIČKA ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=120)
with col_r:
    if data:
        st.title(f"🏆 {data['nazev_akce']}")
        # Zobrazení systému turnaje v záhlaví
        st.markdown(f"<span class='system-badge'>⚙️ Systém: {data['system']}</span>", unsafe_allow_html=True)

# --- STAV TURNAJE ---
if not data or data.get("kolo") == 0:
    st.info("⌛ Turnaj zatím nebyl zahájen. Čekáme na první kolo...")
else:
    st.divider()
    
    # Horní lišta se statistikami
    c1, c2, c3, c4 = st.columns(4)
    je_konec = data['kolo'] > data['max_kol']
    
    with c1:
        st.metric("Stav", "Finále 🏁" if je_konec else f"Kolo {data['kolo']} 🏟️")
    with c2:
        st.metric("Formát", "Švýcar" if data['system'] == "Švýcar" else "Kombinace")
    with c3:
        st.metric("Plánováno kol", data['max_kol'])
    with c4:
        st.metric("Hráčů", len([t for t in data['tymy'] if t['Hráč/Tým'] != "VOLNÝ LOS"]))

    st.divider()

    # --- TABULKA POŘADÍ ---
    st.subheader("📊 Průběžné pořadí")
    df_t = pd.DataFrame(data['tymy'])
    df_t = df_t[df_t["Hráč/Tým"] != "VOLNÝ LOS"].copy()
    df_t["Rozdíl"] = df_t["Skóre +"] - df_t["Skóre -"]
    
    # Seřazení podle pétanque pravidel (Výhry > Buchholz > Rozdíl)
    df_t = df_t.sort_values(by=["Výhry", "Buchholz", "Rozdíl"], ascending=False).reset_index(drop=True)
    df_t.index += 1
    
    st.dataframe(
        df_t[["Hráč/Tým", "Výhry", "Buchholz", "Skóre +", "Skóre -", "Rozdíl"]],
        use_container_width=True,
        column_config={
            "Hráč/Tým": st.column_config.TextColumn("Hráč / Tým"),
            "Výhry": st.column_config.NumberColumn("Výhry 🥇"),
            "Buchholz": st.column_config.NumberColumn("Buchholz 🧠", help="Součet výher vašich soupeřů"),
            "Rozdíl": st.column_config.NumberColumn("Rozdíl skóre 📈"),
        }
    )

    # --- HISTORIE ZÁPASŮ ---
    st.subheader("🏟️ Odehrané zápasy")
    if not data['historie']:
        st.write("Zatím nebyly odehrány žádné zápasy.")
    else:
        historie_df = pd.DataFrame(data['historie'])
        for k in sorted(historie_df["Kolo"].unique(), reverse=True):
            with st.expander(f"Kolo {k}", expanded=(k == data['kolo']-1 or je_konec)):
                kol_zápasy = historie_df[historie_df["Kolo"] == k]
                for _, z in kol_zápasy.iterrows():
                    win1 = "**" if z["S1"] > z["S2"] else ""
                    win2 = "**" if z["S2"] > z["S1"] else ""
                    
                    st.markdown(f"""
                    <div style="padding:12px; border-radius:8px; background-color:white; border-left: 6px solid #1e3a8a; margin-bottom:8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <span style="font-size:1.1em; color: #334155;">{win1}{z['Hráč/Tým 1']}{win1}  <b style="color:#1e3a8a; margin: 0 15px;">{z['S1']} : {z['S2']}</b>  {win2}{z['Hráč/Tým 2']}{win2}</span>
                    </div>
                    """, unsafe_allow_html=True)

st.markdown("---")
st.caption(f"© 2024 {KLUB_NAZEV} | Data se aktualizují po uzavření kola organizátorem.")
