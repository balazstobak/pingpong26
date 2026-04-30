import streamlit as st
import pandas as pd
import itertools

# --- STÍLUS ÉS OLDAL BEÁLLÍTÁS ---
st.set_page_config(page_title="Egyéni női bajnokság", page_icon="🏓", layout="wide")

# --- SESSION STATE INICIALIZÁLÁSA ---
if 'players' not in st.session_state:
    st.session_state.players = []
if 'started' not in st.session_state:
    st.session_state.started = False
if 'matches' not in st.session_state:
    st.session_state.matches = []
if 'finished' not in st.session_state:
    st.session_state.finished = False

# --- FÜGGVÉNYEK ---
def generate_optimal_schedule(players):
    """
    Legenerálja az összes körmérkőzést, majd sorba rendezi őket úgy, 
    hogy a játékosok a lehető legkevesebbszer játsszanak egymás után.
    """
    all_matches = list(itertools.combinations(players, 2))
    scheduled = []
    
    while all_matches:
        if not scheduled:
            scheduled.append(all_matches.pop(0))
        else:
            last_match_players = set(scheduled[-1])
            best_match_idx = 0
            # Keresünk egy meccset, amiben nem játszik az előző meccs egyik résztvevője sem
            for i, match in enumerate(all_matches):
                if not set(match).intersection(last_match_players):
                    best_match_idx = i
                    break
            scheduled.append(all_matches.pop(best_match_idx))
            
    return scheduled

def end_tournament():
    st.session_state.finished = True

# --- 1. FÁZIS: JELENTKEZÉS ---
if not st.session_state.started:
    st.title("🏓 Egyéni női bajnokság")
    st.write("Add meg a versenyzők neveit a bajnokság megkezdéséhez!")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.form("add_player_form", clear_on_submit=True):
            new_player = st.text_input("Versenyző neve:")
            submitted = st.form_submit_button("Hozzáadás")
            if submitted and new_player:
                if new_player not in st.session_state.players:
                    st.session_state.players.append(new_player)
                    st.rerun()
                else:
                    st.warning("Ez a versenyző már szerepel a listán!")
                    
    with col2:
        st.subheader("Jelentkezők listája:")
        if st.session_state.players:
            for i, player in enumerate(st.session_state.players, 1):
                st.write(f"{i}. {player}")
        else:
            st.info("Még nincs jelentkező.")
            
        if len(st.session_state.players) >= 2:
            if st.button("🚀 Verseny indítása (Sorsolás)"):
                st.session_state.matches = generate_optimal_schedule(st.session_state.players)
                st.session_state.started = True
                st.rerun()
        else:
            st.write("*A verseny indításához legalább 2 játékos szükséges.*")

# --- 2. FÁZIS: VERSENY LEBONYOLÍTÁSA ---
if st.session_state.started:
    st.title("🏆 Éles Verseny")
    
    # Két oszlopos elrendezés: bal oldalt a meccsek bevitele, jobb oldalt az élő tabella
    col_matches, col_standings = st.columns([1, 1.5])
    
    # --- MÉRKŐZÉSEK ÉS EREDMÉNYEK BEVITELE ---
    with col_matches:
        st.subheader("Mérkőzések")
        st.write("Minden mérkőzés 2 nyert szettig tart.")
        
        options = ["Nincs lejátszva", "2 - 0", "2 - 1", "1 - 2", "0 - 2"]
        
        for i, match in enumerate(st.session_state.matches):
            p1, p2 = match
            st.selectbox(
                f"{i+1}. Meccs: {p1} vs {p2}", 
                options=options,
                key=f"match_{i}",
                disabled=st.session_state.finished
            )
            
    # --- ÉLŐ TABELLA SZÁMÍTÁSA ---
    # Alapadatok inicializálása minden játékosnak
    stats = {p: {"Meccs": 0, "Győzelem": 0, "Vereség": 0, "Szett_N": 0, "Szett_V": 0, "Pont": 0} 
             for p in st.session_state.players}
    
    all_matches_played = True # Figyeljük, hogy minden meccset lejátszottak-e

    for i, match in enumerate(st.session_state.matches):
        res = st.session_state.get(f"match_{i}", "Nincs lejátszva")
        if res != "Nincs lejátszva":
            p1, p2 = match
            s1 = int(res[0]) # pl. "2 - 1" -> s1 = 2
            s2 = int(res[4]) # pl. "2 - 1" -> s2 = 1
            
            # Statisztikák frissítése
            stats[p1]["Meccs"] += 1
            stats[p2]["Meccs"] += 1
            stats[p1]["Szett_N"] += s1
            stats[p1]["Szett_V"] += s2
            stats[p2]["Szett_N"] += s2
            stats[p2]["Szett_V"] += s1
            
            if s1 > s2:
                stats[p1]["Győzelem"] += 1
                stats[p2]["Vereség"] += 1
                stats[p1]["Pont"] += 1 # 1 pont a győzelemért
            else:
                stats[p2]["Győzelem"] += 1
                stats[p1]["Vereség"] += 1
                stats[p2]["Pont"] += 1
        else:
            all_matches_played = False

    # Pandas DataFrame készítése a rendezéshez és megjelenítéshez
    df_data = []
    for p, s in stats.items():
        szett_kulonbseg = s["Szett_N"] - s["Szett_V"]
        df_data.append({
            "Játékos": p,
            "Meccs": s["Meccs"],
            "Győzelem": s["Győzelem"],
            "Vereség": s["Vereség"],
            "Szettarány": f"{s['Szett_N']}:{s['Szett_V']}",
            "Szett Kül.": szett_kulonbseg,
            "Pont": s["Pont"]
        })
        
    df = pd.DataFrame(df_data)
    # Rendezés: Pontszám szerint, majd Szett Különbség alapján csökkenőbe
    df = df.sort_values(by=["Pont", "Szett Kül."], ascending=[False, False]).reset_index(drop=True)
    df.index = df.index + 1 # Az index 1-től induljon (Helyezés)

    with col_standings:
        st.subheader("📊 Élő Tabella")
        # Stílusozott DataFrame megjelenítése
        st.dataframe(df.style.highlight_max(subset=['Pont', 'Győzelem'], color='lightgreen'), use_container_width=True)
        
        st.markdown("---")
        # --- VERSENY LEZÁRÁSA GOMB ---
        if not st.session_state.finished:
            if all_matches_played:
                st.success("Minden mérkőzést lejátszottak! Lezárhatod a versenyt.")
            st.button("🏁 Verseny befejezése és Eredményhirdetés", on_click=end_tournament, type="primary")

# --- 3. FÁZIS: EREDMÉNYHIRDETÉS ---
if st.session_state.finished:
    st.balloons() # Lufi animáció!
    st.markdown("---")
    st.title("🎉 VÉGEREDMÉNY ÉS EREDMÉNYHIRDETÉS 🎉")
    
    col_podium1, col_podium2, col_podium3 = st.columns(3)
    
    # Első 3 helyezett kiemelése, biztonságos ellenőrzéssel (ha pl. csak 2 játékos volt)
    with col_podium2:
        if len(df) >= 1:
            st.markdown(f"<h2 style='text-align: center;'>🥇 1. Helyezett<br><span style='color: gold;'>{df.iloc[0]['Játékos']}</span></h2>", unsafe_allow_html=True)
            
    with col_podium1:
        if len(df) >= 2:
            st.markdown(f"<h3 style='text-align: center; margin-top: 50px;'>🥈 2. Helyezett<br><span style='color: silver;'>{df.iloc[1]['Játékos']}</span></h3>", unsafe_allow_html=True)
            
    with col_podium3:
        if len(df) >= 3:
            st.markdown(f"<h4 style='text-align: center; margin-top: 70px;'>🥉 3. Helyezett<br><span style='color: #cd7f32;'>{df.iloc[2]['Játékos']}</span></h4>", unsafe_allow_html=True)
            
    st.write("Gratulálunk minden résztvevőnek a nagyszerű játékhoz! 👏")
    
    if st.button("🔄 Új bajnokság indítása"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
