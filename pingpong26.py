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
if 'tournament_ended' not in st.session_state:
    st.session_state.tournament_ended = False

# --- 2. LOGIKA ÉS FUNKCIÓK ---

def generate_optimized_schedule(teams_list):
    teams = teams_list.copy()
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
        
        random.shuffle(round_matches)
        schedule.extend(round_matches)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
        
    return pd.DataFrame(schedule)

def calculate_standings(df, teams, scoring_type):
    """ÚJ: Kiszámolja a pontokat ÉS a szett-differenciát is!"""
    stats = {t: {"Pontszám": 0, "Szerzett Szett": 0, "Kapott Szett": 0} for t in teams if t != 'Pihenő'}
    
    tables = [
        ("🔴 Piros H", "🔴 Piros V"),
        ("⚪ Szürke H", "⚪ Szürke V"),
        ("🟢 Zöld H", "🟢 Zöld V")
    ]
    
    for _, row in df.iterrows():
        h_team = row["Hazai Csapat"]
        v_team = row["Vendég Csapat"]
        
        if h_team in stats and v_team in stats:
            for h_col, v_col in tables:
                h_score = row[h_col] if pd.notna(row[h_col]) else 0
                v_score = row[v_col] if pd.notna(row[v_col]) else 0
                
                # Szettek gyűjtése a differenciához
                stats[h_team]["Szerzett Szett"] += h_score
                stats[h_team]["Kapott Szett"] += v_score
                stats[v_team]["Szerzett Szett"] += v_score
                stats[v_team]["Kapott Szett"] += h_score
                
                # Pontok számolása a szabály alapján
                if scoring_type == "Asztali győzelem (1 pont a nyertesnek)":
                    if h_score > v_score: stats[h_team]["Pontszám"] += 1
                    elif v_score > h_score: stats[v_team]["Pontszám"] += 1
                else:
                    stats[h_team]["Pontszám"] += h_score
                    stats[v_team]["Pontszám"] += v_score
                
    # Táblázat összeállítása
    tabella_data = []
    for team, data in stats.items():
        szett_diff = data["Szerzett Szett"] - data["Kapott Szett"]
        tabella_data.append({
            "Csapat": team,
            "Pontszám": data["Pontszám"],
            "Szett-differencia": szett_diff
        })
        
    tabella = pd.DataFrame(tabella_data)
    
    # Sorrend felállítása: 1. Pontszám, 2. Szett-differencia alapján
    tabella = tabella.sort_values(by=['Pontszám', 'Szett-differencia'], ascending=[False, False]).reset_index(drop=True)
    
    # Helyezés (sorszám) oszlop hozzáadása
    tabella.index = tabella.index + 1
    tabella.reset_index(inplace=True)
    tabella.rename(columns={'index': 'Helyezés'}, inplace=True)
    
    return tabella

def calculate_subteam_stats(df, teams):
    tables = [
        ("🔴 Piros", "🔴 Piros H", "🔴 Piros V"),
        ("⚪ Szürke", "⚪ Szürke H", "⚪ Szürke V"),
        ("🟢 Zöld", "🟢 Zöld H", "🟢 Zöld V")
    ]
    
    # Adatszerkezet inicializálása
    team_stats = {t: {asztal: {"GY": 0, "V": 0, "Szerzett": 0, "Kapott": 0} for asztal, _, _ in tables} for t in teams if t != 'Pihenő'}
    
    for _, row in df.iterrows():
        h_team, v_team = row["Hazai Csapat"], row["Vendég Csapat"]
        
        # Csak a befejezett (kipipált) meccseket számoljuk!
        if (h_team in team_stats and v_team in team_stats) and row.get("Befejezve", False):
            for asztal_nev, h_col, v_col in tables:
                h_score = row[h_col] if pd.notna(row[h_col]) else 0
                v_score = row[v_col] if pd.notna(row[v_col]) else 0
                
                # Hazai csapat statjai
                team_stats[h_team][asztal_nev]["Szerzett"] += h_score
                team_stats[h_team][asztal_nev]["Kapott"] += v_score
                
                # Vendég csapat statjai
                team_stats[v_team][asztal_nev]["Szerzett"] += v_score
                team_stats[v_team][asztal_nev]["Kapott"] += h_score
                
                # Győzelem / Vereség eldöntése
                if h_score > v_score:
                    team_stats[h_team][asztal_nev]["GY"] += 1
                    team_stats[v_team][asztal_nev]["V"] += 1
                elif v_score > h_score:
                    team_stats[v_team][asztal_nev]["GY"] += 1
                    team_stats[h_team][asztal_nev]["V"] += 1

    # Formázás DataFrame-be (a kép alapján)
    flattened_data = []
    for t in sorted(teams):
        if t == 'Pihenő': continue
        for asztal_nev, _, _ in tables:
            s = team_stats[t][asztal_nev]
            flattened_data.append({
                "Csapatok": t,
                "Asztal": asztal_nev,
                "GY": s["GY"],
                "V": s["V"],
                "Szerzett Sz.": s["Szerzett"],
                "Kapott Sz.": s["Kapott"]
            })
            
    return pd.DataFrame(flattened_data)

# --- 3. FELÜLET (UI) ---
st.title("🏓 3-Asztalos Csapatbajnokság")

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
            help="Szett alapú módban maximum 2 pont (szett) írható be egy asztalhoz."
        )
        
        if st.button("Verseny Indítása 🚀", type="primary"):
            st.session_state.scoring_type = scoring_choice
            st.session_state.schedule_df = generate_optimized_schedule(st.session_state.teams)
            st.session_state.tournament_started = True
            st.session_state.tournament_ended = False
            st.rerun()

else:
    # Ha a verseny már lezárult, nem engedjük szerkeszteni az eredményeket
    if st.session_state.tournament_ended:
        st.balloons()
        st.success("🎉 A verseny véget ért! Íme a hivatalos végeredmény:")
        
        # Végső tabella kiszámolása (az elmentett adatokból) és megjelenítése nagyban
        final_tabella = calculate_standings(st.session_state.schedule_df, st.session_state.teams, st.session_state.scoring_type)
        st.dataframe(final_tabella, hide_index=True, use_container_width=True)
        
        st.divider()
        if st.button("Új verseny indítása (Teljes Reset)"):
            st.session_state.clear()
            st.rerun()
            
    # Ha még tart a verseny, mutatjuk a szerkesztőt
    else:
        st.info(f"Aktív pontozás: **{st.session_state.scoring_type}**")
        
        col_left, col_right = st.columns([3, 1.2])
        
        with col_left:
            st.subheader("📝 Eredmények rögzítése")
            
            max_val = 2 if "Szett" in st.session_state.scoring_type else 30
            score_config = st.column_config.NumberColumn(min_value=0, max_value=max_val, step=1)
            
            edited_df = st.data_editor(
                st.session_state.schedule_df,
                use_container_width=True,
                hide_index=True,
                key="eredmeny_editor",
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

        with col_right:
            st.subheader("🏆 Aktuális Ranglista")
            tabella_df = calculate_standings(edited_df, st.session_state.teams, st.session_state.scoring_type)
            # A kis táblázatból eltüntetjük a Szett-differenciát, hogy jobban kiférjen (opcionális, de szebb így)
            st.dataframe(tabella_df[['Helyezés', 'Csapat', 'Pontszám']], hide_index=True, use_container_width=True)
            
            if st.button("Vissza a nevezéshez (Reset)"):
                if st.checkbox("Biztosan törlöd az aktuális versenyt?"):
                    st.session_state.clear()
                    st.rerun()
        
        # --- ÚJ: Verseny lezárása logika ---
        # Ha minden sor Befejezve oszlopa True (igaz), felajánljuk a lezárást
        if not edited_df.empty and edited_df['Befejezve'].all():
            st.divider()
            st.warning("Minden mérkőzés lezárult!")
            if st.button("🏁 Véget ért a verseny? (Eredményhirdetés mutatása)", type="primary"):
                # Mielőtt lezárjuk, gyorsan elmentjük a legutolsó szerkesztett állapotot!
                st.session_state.schedule_df = edited_df
                st.session_state.tournament_ended = True
                st.rerun()
