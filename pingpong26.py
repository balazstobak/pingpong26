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

def generate_optimized_schedule(teams_list):
    teams = teams_list.copy()
    
    # 1. Alaposan megkeverjük a csapatokat rögtön az elején, hogy a sorsolás 
    # tényleg véletlenszerű legyen, és ne a beírás sorrendjétől függjön!
    random.shuffle(teams)
    
    if len(teams) % 2 != 0:
        teams.append('Pihenő')
    
    n = len(teams)
    schedule = []
    
    for round_idx in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            t1, t2 = teams[i], teams[n - 1 - i]
            if t1 != 'Pihenő' and t2 != 'Pihenő':
                round_matches.append({
                    "Hazai Csapat": t1, "Vendég Csapat": t2,
                    "🔴 Piros H": 0, "🔴 Piros V": 0,
                    "⚪ Szürke H": 0, "⚪ Szürke V": 0,
                    "🟢 Zöld H": 0, "🟢 Zöld V": 0,
                    "Befejezve": False
                })
        
        # 2. Megkeverjük a meccseket egy fordulón belül is
        random.shuffle(round_matches)
        
        # Hozzáadjuk a megkevert meccseket a fő listához
        schedule.extend(round_matches)
        
        # Csapatok forgatása a következő körhöz (Circle method)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
        
    return pd.DataFrame(schedule)

# --- 2. LOGIKA ÉS FUNKCIÓK ---
def calculate_standings(df, teams, scoring_type):
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
                h_score = row[h_col] if pd.notna(row[h_col]) else 0
                v_score = row[v_col] if pd.notna(row[v_col]) else 0
                
                if scoring_type == "Asztali győzelem (1 pont a nyertesnek)":
                    if h_score > v_score: points[h_team] += 1
                    elif v_score > h_score: points[v_team] += 1
                else:
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
                    "🟢 Zöld H": 0, "🟢 Zöld V": 0,
                    "Befejezve": False # <-- ÚJ: pipa oszlop hozzáadása
                })
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    return pd.DataFrame(schedule)

# <-- ÚJ: Sorok színezése funkció -->
#def highlight_finished_rows(row):
    # Ha a 'Befejezve' oszlop be van pipálva, az egész sor halványszürke lesz
#    if row['Befejezve']:
#        return ['background-color: rgba(128, 128, 128, 0.15); color: rgba(128, 128, 128, 0.6)'] * len(row)
#    return [''] * len(row)

# --- 3. FELÜLET ---
st.title("🏓 Csapatbajnokság 🏓")

if not st.session_state.tournament_started:
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
        
        scoring_choice = st.radio(
            "Válaszd ki a pontozási rendszert:",
            ["Asztali győzelem (1 pont a nyertesnek)", "Szett alapú (minden nyert szett 1 pont)"],
            help="Példa: 2-0 \n - asztali győzelem: a győztes 1 pontot kap, a vesztes 0-t \n - szett alapú: a győztes 2 pontot kap, a vesztes 0-t \n
            Példa: 2-1 \n -asztali győzelem: a győztes 1 pontot kap, a vesztes 0-t \n - szett alapú: a győztes 2 pontot kap, a vesztes 1-t"
        )
        
        if st.button("Verseny Indítása 🚀", type="primary"):
            st.session_state.scoring_type = scoring_choice
            st.session_state.schedule_df = generate_optimized_schedule(st.session_state.teams)
            st.session_state.tournament_started = True
            st.rerun()

else:
    st.info(f"Aktív pontozás: **{st.session_state.scoring_type}**")
    
    col_left, col_right = st.columns([3, 1.2])
    
    with col_left:
        st.subheader("📝 Eredmények rögzítése")
        
        max_val = 2 if "Szett" in st.session_state.scoring_type else 3
        
        # Oszlopok közös konfigurációja
        score_config = st.column_config.NumberColumn(min_value=0, max_value=max_val, step=1)
        
        # A st.data_editor most már egy formázott (Styled) DataFrame-et kap
        #styled_df = st.session_state.schedule_df.style.apply(highlight_finished_rows, axis=1)
        
        edited_df = st.data_editor(
            #styled_df,
            st.session_state.schedule_df,
            use_container_width=True,
            hide_index=True,
            key="eredmeny_editor",  # Fontos a villanás és adatvesztés elkerülésére!
            column_config={
                "Hazai Csapat": st.column_config.TextColumn(disabled=True),
                "Vendég Csapat": st.column_config.TextColumn(disabled=True),
                "🔴 Piros H": score_config,
                "🔴 Piros V": score_config,
                "⚪ Szürke H": score_config,
                "⚪ Szürke V": score_config,
                "🟢 Zöld H": score_config,
                "🟢 Zöld V": score_config,
                "Befejezve": st.column_config.CheckboxColumn("Befejezve ✅", default=False)
            }
        )
        # Az editált adatokat visszamentjük az eredeti változóba
       # st.session_state.schedule_df = edited_df

    with col_right:
        st.subheader("🏆 Élő ranglista")
        tabella_df = calculate_standings(edited_df, st.session_state.teams, st.session_state.scoring_type)
        st.dataframe(tabella_df, hide_index=True, use_container_width=True)
        
        if st.button("Vissza a nevezéshez (Reset)"):
            if st.checkbox("Biztosan törlöd az aktuális versenyt?"):
                st.session_state.clear()
                st.rerun()
