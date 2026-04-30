import streamlit as st
import pandas as pd
import random
from itertools import combinations

# Oldal beállításai
st.set_page_config(page_title="🏓 Pingpong Bajnokság", layout="wide")

# Állapotváltozók (Session State) inicializálása
if 'phase' not in st.session_state:
    st.session_state.phase = 'registration'
if 'players' not in st.session_state:
    st.session_state.players = []
if 'groups' not in st.session_state:
    st.session_state.groups = []
if 'matches' not in st.session_state:
    st.session_state.matches = {}

# Csoportméretek kiszámolása a szabályok alapján
def calculate_group_sizes(n):
    if n < 3: return []
    if n == 3: return [3]
    if n == 5: return [5]
    if n == 6: return [3, 3]
    
    q, r = divmod(n, 4)
    if r == 0: 
        return [4] * q
    if r == 1: 
        return [4] * (q - 1) + [5]
    if r == 2: 
        return [4] * (q - 2) + [5, 5] if q >= 2 else [3, 3]
    if r == 3: 
        return [4] * q + [3]
    return []

# Játékosok beosztása a kiszámolt méretek alapján
def generate_groups(player_list):
    random.shuffle(player_list) # Játékosok összekeverése a véletlenszerű sorsoláshoz
    sizes = calculate_group_sizes(len(player_list))
    groups = []
    idx = 0
    for size in sizes:
        groups.append(player_list[idx:idx+size])
        idx += size
    return groups

# --- 1. FÁZIS: JELENTKEZÉS ÉS SORSOLÁS ---
if st.session_state.phase == 'registration':
    st.title("🏓 Pingpong Bajnokság Szervező")
    st.markdown("### 1. Lépés: Jelentkezők megadása")
    st.write("Írd be a jelentkezők neveit, minden sort egy új névnek fenntartva!")
    
    players_input = st.text_area("Jelentkezők listája:", height=300, placeholder="Kovács János\nNagy Péter\nSzabó Anna...")

    if st.button("Csoportok sorsolása", type="primary"):
        players = [p.strip() for p in players_input.split('\n') if p.strip()]
        if len(players) < 3:
            st.error("A verseny indításához legalább 3 jelentkezőre van szükség!")
        else:
            st.session_state.players = players
            groups = generate_groups(players)
            st.session_state.groups = groups
            
            # Körmérkőzések legenerálása minden csoporthoz
            matches = {}
            match_id = 0
            for g_id, group in enumerate(groups):
                for p1, p2 in combinations(group, 2):
                    matches[match_id] = {
                        'group_id': g_id,
                        'p1': p1,
                        'p2': p2,
                        'result': 'Nem játszott'
                    }
                    match_id += 1
            st.session_state.matches = matches
            st.session_state.phase = 'groups'
            st.rerun()

# --- 2. FÁZIS: MÉRKŐZÉSEK ÉS ÉLŐ TABELLA ---
elif st.session_state.phase == 'groups':
    st.title("🏓 Csoportmérkőzések és Élő Tabella")
    
    if st.button("⬅️ Új verseny indítása (Vissza a regisztrációhoz)"):
        st.session_state.phase = 'registration'
        st.rerun()

    st.markdown("---")

    # Csoportok iterálása és megjelenítése
    for g_id, group in enumerate(st.session_state.groups):
        st.markdown(f"## {g_id + 1}. Csoport ({len(group)} fős)")
        
        # Két oszlop létrehozása: bal oldalon a meccsek, jobb oldalon a tabella
        col1, col2 = st.columns([1, 1.2], gap="large")
        
        # Csak az aktuális csoport meccseinek kiválogatása
        group_matches = {k: v for k, v in st.session_state.matches.items() if v['group_id'] == g_id}
        
        with col1:
            st.markdown("#### 📝 Eredmények rögzítése")
            for m_id, m_data in group_matches.items():
                options = ["Nem játszott", "2 - 0", "2 - 1", "1 - 2", "0 - 2"]
                current_val = m_data['result']
                idx = options.index(current_val)
                
                # Legördülő menü a pontos szetteredmény kiválasztásához
                new_val = st.selectbox(
                    f"{m_data['p1']} vs {m_data['p2']}", 
                    options, 
                    index=idx, 
                    key=f"match_{m_id}"
                )
                
                # Ha változik az eredmény, frissítjük az állapotot és újratöltjük az oldalt a tabellához
                if new_val != current_val:
                    st.session_state.matches[m_id]['result'] = new_val
                    st.rerun()
        
        with col2:
            st.markdown("#### 📊 Élő Tabella")
            
            # Tabella statisztikák inicializálása a csoport tagjainak
            stats = {p: {'Név': p, 'Mérkőzés': 0, 'Pont': 0, 'Győzelem': 0, 'Vereség': 0, 'Szett +': 0, 'Szett -': 0} for p in group}
            
            # Eredmények feldolgozása a tabellához
            for m_id, m_data in group_matches.items():
                res = m_data['result']
                p1, p2 = m_data['p1'], m_data['p2']
                
                if res != "Nem játszott":
                    stats[p1]['Mérkőzés'] += 1
                    stats[p2]['Mérkőzés'] += 1
                    
                    if res == "2 - 0":
                        stats[p1]['Győzelem'] += 1
                        stats[p1]['Pont'] += 1
                        stats[p2]['Vereség'] += 1
                        stats[p1]['Szett +'] += 2
                        stats[p2]['Szett -'] += 2
                    elif res == "2 - 1":
                        stats[p1]['Győzelem'] += 1
                        stats[p1]['Pont'] += 1
                        stats[p2]['Vereség'] += 1
                        stats[p1]['Szett +'] += 2
                        stats[p1]['Szett -'] += 1
                        stats[p2]['Szett +'] += 1
                        stats[p2]['Szett -'] += 2
                    elif res == "1 - 2":
                        stats[p2]['Győzelem'] += 1
                        stats[p2]['Pont'] += 1
                        stats[p1]['Vereség'] += 1
                        stats[p2]['Szett +'] += 2
                        stats[p2]['Szett -'] += 1
                        stats[p1]['Szett +'] += 1
                        stats[p1]['Szett -'] += 2
                    elif res == "0 - 2":
                        stats[p2]['Győzelem'] += 1
                        stats[p2]['Pont'] += 1
                        stats[p1]['Vereség'] += 1
                        stats[p2]['Szett +'] += 2
                        stats[p1]['Szett -'] += 2

            # Pandas DataFrame generálása a rendezéshez
            df = pd.DataFrame(list(stats.values()))
            df['Szett Arány'] = df['Szett +'] - df['Szett -']
            
            # Rendezés: 1. Pontszám, 2. Szett arány, 3. Győzelmek száma
            df = df.sort_values(by=['Pont', 'Szett Arány', 'Győzelem'], ascending=[False, False, False]).reset_index(drop=True)
            df.index += 1 # Hogy 1-től kezdődjön a sorszámozás
            
            st.dataframe(
                df[['Név', 'Mérkőzés', 'Pont', 'Szett +', 'Szett -', 'Szett Arány']], 
                use_container_width=True
            )
        
        st.divider()


