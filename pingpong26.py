import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Pingpong Verseny Dashboard", layout="wide")

# --- 1. ADATOK ÉS LOGIKA ---
if 'teams' not in st.session_state:
    st.session_state.teams = []
if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = None
if 'tournament_started' not in st.session_state:
    st.session_state.tournament_started = False

def calculate_standings(df, teams):
    """Kiszámolja a tabellát az asztalonkénti győzelmek alapján."""
    # Kezdeti pontszámok (csak a valódi csapatoknak)
    points = {t: 0 for t in teams if t != 'Pihenő'}
    
    for _, row in df.iterrows():
        h_team = row["Hazai Csapat"]
        v_team = row["Vendég Csapat"]
        
        # Csak akkor számolunk, ha nem pihenőnapos a meccs
        if h_team in points and v_team in points:
            # Piros asztal
            if row["🔴 Piros H"] > row["🔴 Piros V"]: points[h_team] += 1
            elif row["🔴 Piros V"] > row["🔴 Piros H"]: points[v_team] += 1
            
            # Szürke asztal
            if row["⚪ Szürke H"] > row["⚪ Szürke V"]: points[h_team] += 1
            elif row["⚪ Szürke V"] > row["⚪ Szürke H"]: points[v_team] += 1
            
            # Zöld asztal
            if row["🟢 Zöld H"] > row["🟢 Zöld V"]: points[h_team] += 1
            elif row["🟢 Zöld V"] > row["🟢 Zöld H"]: points[v_team] += 1
            
    # DataFrame-mé alakítjuk a pontokat
    tabella = pd.DataFrame(list(points.items()), columns=['Csapat', 'Összes asztal-győzelem'])
    return tabella.sort_values(by='Összes asztal-győzelem', ascending=False).reset_index(drop=True)

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
                    "Hazai": t1, "Vendég": t2,
                    "🔴 Piros H": 0, "🔴 Piros V": 0,
                    "⚪ Szürke H": 0, "⚪ Szürke V": 0,
                    "🟢 Zöld H": 0, "🟢 Zöld V": 0
                })
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    
    df = pd.DataFrame(schedule)
    df.columns = ["Hazai Csapat", "Vendég Csapat", "🔴 Piros H", "🔴 Piros V", "⚪ Szürke H", "⚪ Szürke V", "🟢 Zöld H", "🟢 Zöld V"]
    return df

# --- 2. FELÜLET ---

st.title("🏓 3-Asztalos Csapatbajnokság")

if not st.session_state.tournament_started:
    # --- NEVEZÉSI RÉSZ ---
    st.subheader("Csapatok nevezése")
    col1, col2 = st.columns([1, 2])
    with col1:
        new_team = st.text_input("Csapat neve:")
        if st.button("Hozzáadás"):
            if new_team and new_team not in st.session_state.teams:
                st.session_state.teams.append(new_team)
                st.rerun()
    with col2:
        st.write(f"**Eddigi csapatok:** {', '.join(st.session_state.teams)}")
        if len(st.session_state.teams) >= 2:
            if st.button("Verseny Indítása 🚀", type="primary"):
                st.session_state.schedule_df = generate_optimized_schedule(st.session_state.teams)
                st.session_state.tournament_started = True
                st.rerun()

else:
    # --- ÉLŐ DASHBOARD RÉSZ ---
    col_left, col_right = st.columns([3, 1]) # Bal oldalon a pontok, jobb oldalon a tabella
    
    with col_left:
        st.subheader("📝 Meccsek és Pontok")
        # Itt történik a varázslat: az edited_df-be kerül minden változtatás
        edited_df = st.data_editor(
            st.session_state.schedule_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Hazai Csapat": st.column_config.TextColumn(disabled=True),
                "Vendég Csapat": st.column_config.TextColumn(disabled=True),
            }
        )
        # Frissítjük a session state-et
        st.session_state.schedule_df = edited_df

    with col_right:
        st.subheader("🏆 Tabella")
        # Meghívjuk a számoló függvényt az aktuális adatokkal
        tabella_df = calculate_standings(edited_df, st.session_state.teams)
        
        # Megjelenítjük a tabellát
        st.dataframe(
            tabella_df, 
            hide_index=True, 
            use_container_width=True
        )
        
        if st.button("Új verseny (Reset)"):
            st.session_state.clear()
            st.rerun()
