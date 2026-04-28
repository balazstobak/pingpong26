import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Pingpong Verseny Dashboard", layout="wide")

# --- 1. ADATOK INICIALIZÁLÁSA ---
if 'teams' not in st.session_state:
    st.session_state.teams = []
if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = None
if 'tournament_started' not in st.session_state:
    st.session_state.tournament_started = False
if 'scoring_type' not in st.session_state:
    st.session_state.scoring_type = "Asztali győzelem"

# --- 2. SZÁMÍTÁSI LOGIKA ---
def calculate_standings(df, teams, scoring_type):
    """Kiszámolja a tabellát a választott pontozási rendszer alapján."""
    points = {t: 0 for t in teams if t != 'Pihenő'}
    
    tables = [
        ("🔴 Piros H", "🔴 Piros V"),
        ("⚪ Szürke H", "⚪ Szürke V"),
        ("🟢 Zöld H", "🟢 Zöld V")
    ]
    
    for _, row in df.iterrows():
        h_team = row["Hazai Csapat"]
        v_team = row["Vendég Csapat"]
        
        if h_team in points and v_team in points:
            for h_col, v_col in tables:
                h_score = row[h_col]
                v_score = row[v_col]
                
                if scoring_type == "Asztali győzelem (1 pont a nyertesnek)":
                    # Csak a győztes kap 1 pontot asztalonként
                    if h_score > v_score: points[h_team] += 1
                    elif v_score > h_score: points[v_team] += 1
                else:
                    # Szett alapú: minden nyert szett 1 pontot ér
                    points[h_team] += h_score
                    points[v_team] += v_score
                
    tabella = pd.DataFrame(list(points.items()), columns=['Csapat', 'Összpontszám'])
    return tabella.sort_values(by='Összpontszám', ascending=False).reset_index(drop=True)

def generate_optimized_schedule(teams_list):
    teams = teams_list.copy()
    if len(teams) % 2 != 0:
        teams.append('Pihenő')
    
    n = len(teams)
    schedule = []
    for round_idx in range(n - 1):
        for i in range(n // 2):
            t1, t2 = teams[i], teams[n - 1 - i]
            if t1 != 'Pihenő' and t2 != 'Pihenő':
                schedule.append({
                    "Hazai Csapat": t1, "Vendég Csapat": t2,
                    "🔴 Piros H": 0, "🔴 Piros V": 0,
                    "⚪ Szürke H": 0, "⚪ Szürke V": 0,
                    "🟢 Zöld H": 0, "🟢 Zöld V": 0
                })
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    return pd.DataFrame(schedule)

# --- 3. FELÜLET ---

st.title("🏓 3-Asztalos Csapatbajnokság")

if not st.session_state.tournament_started:
    # --- NEVEZÉSI ÉS BEÁLLÍTÁSI RÉSZ ---
    st.subheader("1. Csapatok nevezése")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        new_team = st.text_input("Csapat neve:", placeholder="Pl. Janiék")
        if st.button("Hozzáadás"):
            if new_team and new_team not in st.session_state.teams:
                st.session_state.teams.append(new_team)
                st.rerun()
    
    with col2:
        st.write(f"**Nevezett csapatok ({len(st.session_state.teams)}):**")
        st.write(", ".join(st.session_state.teams) if st.session_state.teams else "Még nincs nevező.")

    if len(st.session_state.teams) >= 2:
        st.divider()
        st.subheader("2. Versenybeállítások")
        
        # Versenytípus kiválasztása
        scoring_choice = st.radio(
            "Válaszd ki a pontozási rendszert:",
            ["Asztali győzelem (1 pont a nyertesnek)", "Szett alapú (minden nyert szett 1 pont)"],
            help="Az asztali győzelemnél egy 2-1-es eredmény 1 pontot ér a nyertesnek. A szett alapúnál a nyertes 2, a vesztes 1 pontot kap."
        )
        
        if st.button("Verseny Indítása 🚀", type="primary"):
            st.session_state.scoring_type = scoring_choice
            st.session_state.schedule_df = generate_optimized_schedule(st.session_state.teams)
            st.session_state.tournament_started = True
            st.rerun()

else:
    # --- ÉLŐ DASHBOARD RÉSZ ---
    st.info(f"Aktív pontozás: **{st.session_state.scoring_type}**")
    
    col_left, col_right = st.columns([3, 1.2])
    
    with col_left:
        st.subheader("📝 Eredmények rögzítése")
        edited_df = st.data_editor(
            st.session_state.schedule_df,
            use_container_width=True,
            hide_index=True,
            key="eredmeny_editor"
            column_config={
                "Hazai Csapat": st.column_config.TextColumn(disabled=True),
                "Vendég Csapat": st.column_config.TextColumn(disabled=True),
            }
        )
        #st.session_state.schedule_df = edited_df

    with col_right:
        st.subheader("🏆 Ranglista")
        tabella_df = calculate_standings(edited_df, st.session_state.teams, st.session_state.scoring_type)
        st.dataframe(tabella_df, hide_index=True, use_container_width=True)
        
        if st.button("Vissza a nevezéshez (Reset)"):
            if st.checkbox("Biztosan törlöd az aktuális versenyt?"):
                st.session_state.clear()
                st.rerun()
