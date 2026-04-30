import streamlit as st
import pandas as pd
import random
from itertools import combinations

# Oldal beállításai
st.set_page_config(page_title="🏓 Egyéni férfi bajnokság", layout="wide")

# Állapotváltozók (Session State) inicializálása
if 'phase' not in st.session_state:
    st.session_state.phase = 'registration'
if 'players' not in st.session_state:
    st.session_state.players = []
if 'groups' not in st.session_state:
    st.session_state.groups = []
if 'matches' not in st.session_state:
    st.session_state.matches = {}
if 'ko_matches' not in st.session_state:
    st.session_state.ko_matches = {}

# Csoportméretek kiszámolása a szabályok alapján
def calculate_group_sizes(n):
    if n < 3: return []
    if n == 3: return [3]
    if n == 5: return [5]
    if n == 6: return [3, 3]
    
    q, r = divmod(n, 4)
    if r == 0: return [4] * q
    if r == 1: return [4] * (q - 1) + [5]
    if r == 2: return [4] * (q - 2) + [5, 5] if q >= 2 else [3, 3]
    if r == 3: return [4] * q + [3]
    return []

def generate_groups(player_list):
    random.shuffle(player_list)
    sizes = calculate_group_sizes(len(player_list))
    groups = []
    idx = 0
    for size in sizes:
        groups.append(player_list[idx:idx+size])
        idx += size
    return groups

# Statisztika számoló egy adott csoportra
def get_standings(player_list, matches_dict, group_id=None):
    stats = {p: {'Név': p, 'Mérkőzés': 0, 'Pont': 0, 'Győzelem': 0, 'Vereség': 0, 'Szett +': 0, 'Szett -': 0} for p in player_list}
    for m_data in matches_dict.values():
        if group_id is not None and m_data.get('group_id') != group_id:
            continue
            
        res = m_data['result']
        if res == "Nem játszott": continue
            
        p1, p2 = m_data['p1'], m_data['p2']
        if p1 not in stats or p2 not in stats: continue
            
        stats[p1]['Mérkőzés'] += 1
        stats[p2]['Mérkőzés'] += 1
        
        if res == "2 - 0":
            stats[p1]['Győzelem'] += 1; stats[p1]['Pont'] += 1; stats[p2]['Vereség'] += 1
            stats[p1]['Szett +'] += 2; stats[p2]['Szett -'] += 2
        elif res == "2 - 1":
            stats[p1]['Győzelem'] += 1; stats[p1]['Pont'] += 1; stats[p2]['Vereség'] += 1
            stats[p1]['Szett +'] += 2; stats[p1]['Szett -'] += 1; stats[p2]['Szett +'] += 1; stats[p2]['Szett -'] += 2
        elif res == "1 - 2":
            stats[p2]['Győzelem'] += 1; stats[p2]['Pont'] += 1; stats[p1]['Vereség'] += 1
            stats[p2]['Szett +'] += 2; stats[p2]['Szett -'] += 1; stats[p1]['Szett +'] += 1; stats[p1]['Szett -'] += 2
        elif res == "0 - 2":
            stats[p2]['Győzelem'] += 1; stats[p2]['Pont'] += 1; stats[p1]['Vereség'] += 1
            stats[p2]['Szett +'] += 2; stats[p1]['Szett -'] += 2

    df = pd.DataFrame(list(stats.values()))
    if not df.empty:
        df['Szett Arány'] = df['Szett +'] - df['Szett -']
        df = df.sort_values(by=['Pont', 'Szett Arány', 'Győzelem'], ascending=[False, False, False]).reset_index(drop=True)
        df.index += 1
    return df

# Kieséses fa dinamikus frissítése
def update_knockout_tree():
    ko = st.session_state.ko_matches
    for k, m in ko.items():
        if m['res'] in ['2 - 0', '2 - 1']: winner = m['p1']
        elif m['res'] in ['1 - 2', '0 - 2']: winner = m['p2']
        else: winner = '?'
        
        if m['next']:
            next_match, slot = m['next']
            ko[next_match][slot] = winner
            if winner == '?':
                ko[next_match]['res'] = 'Nem játszott'

# --- 1. FÁZIS: JELENTKEZÉS ---
if st.session_state.phase == 'registration':
    st.title("🏓 Egynéni férfi bajnokság")
    st.markdown("### 1. Lépés: Jelentkezők megadása")
    players_input = st.text_area("Jelentkezők listája (minden név új sorban):", height=200)

    if st.button("Csoportok sorsolása", type="primary"):
        players = [p.strip() for p in players_input.split('\n') if p.strip()]
        if len(players) < 4:
            st.error("A verseny indításához legalább 4 jelentkezőre van szükség!")
        else:
            st.session_state.players = players
            st.session_state.groups = generate_groups(players)
            
            matches = {}
            match_id = 0
            for g_id, group in enumerate(st.session_state.groups):
                for p1, p2 in combinations(group, 2):
                    matches[match_id] = {'group_id': g_id, 'p1': p1, 'p2': p2, 'result': 'Nem játszott'}
                    match_id += 1
            st.session_state.matches = matches
            st.session_state.phase = 'groups'
            st.rerun()

# --- 2. FÁZIS: CSOPORTMÉRKŐZÉSEK ---
elif st.session_state.phase == 'groups':
    st.title("🏓 Csoportmérkőzések és Élő Tabella")
    if st.button("⬅️ Új verseny indítása"):
        st.session_state.phase = 'registration'
        st.rerun()

    for g_id, group in enumerate(st.session_state.groups):
        st.markdown(f"## {g_id + 1}. Csoport ({len(group)} fős)")
        col1, col2 = st.columns([1, 1.2], gap="large")
        group_matches = {k: v for k, v in st.session_state.matches.items() if v['group_id'] == g_id}
        
        with col1:
            for m_id, m_data in group_matches.items():
                options = ["Nem játszott", "2 - 0", "2 - 1", "1 - 2", "0 - 2"]
                current_val = m_data['result']
                new_val = st.selectbox(f"{m_data['p1']} vs {m_data['p2']}", options, index=options.index(current_val), key=f"match_{m_id}")
                if new_val != current_val:
                    st.session_state.matches[m_id]['result'] = new_val
                    st.rerun()
        
        with col2:
            df = get_standings(group, st.session_state.matches, g_id)
            st.dataframe(df[['Név', 'Mérkőzés', 'Pont', 'Szett +', 'Szett -', 'Szett Arány']], use_container_width=True)
        st.divider()

    st.markdown("### 🏁 Csoportkör lezárása")
    if st.button("Tovább a Rájátszás beállításaihoz ➡️", type="primary"):
        st.session_state.phase = 'knockout_setup'
        st.rerun()

# --- 3. FÁZIS: RÁJÁTSZÁS BEÁLLÍTÁSA ---
elif st.session_state.phase == 'knockout_setup':
    st.title("🏆 Rájátszás beállítása (Kieséses szakasz)")
    
    st.markdown("### 🌍 Továbbjutási Ranglista")
    st.info("A rangsorolás elve: 1. A játékos helyezése a saját csoportjában, 2. Pontszám, 3. Szettarány, 4. Győzelmek száma. (Tehát minden csoportelső megelőzi a csoportmásodikakat, függetlenül a pontszámtól).")
    
    # Kinyerjük és egyesítjük az összes csoporteredményt
    all_players_stats = []
    for g_id, group in enumerate(st.session_state.groups):
        df = get_standings(group, st.session_state.matches, g_id)
        for idx, row in df.iterrows():
            all_players_stats.append({
                'Név': row['Név'],
                'Csoport': f"{g_id + 1}.",
                'Csoport Helyezés': idx, # Ez mutatja, hogy 1., 2. vagy 3. lett a csoportjában
                'Pont': row['Pont'],
                'Szett Arány': row['Szett Arány'],
                'Győzelem': row['Győzelem']
            })
            
    # Sorba rendezés a szabályok alapján
    qual_df = pd.DataFrame(all_players_stats)
    qual_df = qual_df.sort_values(
        by=['Csoport Helyezés', 'Pont', 'Szett Arány', 'Győzelem'], 
        ascending=[True, False, False, False]
    ).reset_index(drop=True)
    
    # Hányan jutnak tovább?
    num_groups = len(st.session_state.groups)
    if num_groups > 4:
        st.warning(f"Mivel {num_groups} csoport van, a rendszer a szabályzat alapján automatikusan a **legjobb 8 játékost** juttatja tovább (Negyeddöntők).")
        ko_size = 8
    else:
        options = [4]
        if len(st.session_state.players) >= 8:
            options.append(8)
        ko_size = st.radio("Mivel 4 vagy annál kevesebb csoport van, válaszd ki a rájátszás méretét:", options, format_func=lambda x: f"Legjobb {x} játékos továbbjutása")

    # Továbbjutók vizuális jelölése a táblázatban
    qual_df.insert(0, 'Továbbjut', ['✅ IGEN' if i < ko_size else '❌ NEM' for i in range(len(qual_df))])
    qual_df.index += 1
    
    st.dataframe(qual_df[['Továbbjut', 'Név', 'Csoport', 'Csoport Helyezés', 'Pont', 'Szett Arány']], use_container_width=True)

    st.markdown("### 🎲 Sorsolás")
    if st.button("Továbbjutók sorsolása és Rájátszás indítása 🚀", type="primary"):
        # Kiválasztjuk a top K játékost a sorba rendezett listából
        top_players = qual_df['Név'].head(ko_size).tolist()
        random.shuffle(top_players) # Megkeverjük a sorsoláshoz
        
        ko = {}
        if ko_size == 8:
            ko['QF1'] = {'p1': top_players[0], 'p2': top_players[1], 'res': 'Nem játszott', 'next': ('SF1', 'p1'), 'label': '1. Negyeddöntő'}
            ko['QF2'] = {'p1': top_players[2], 'p2': top_players[3], 'res': 'Nem játszott', 'next': ('SF1', 'p2'), 'label': '2. Negyeddöntő'}
            ko['QF3'] = {'p1': top_players[4], 'p2': top_players[5], 'res': 'Nem játszott', 'next': ('SF2', 'p1'), 'label': '3. Negyeddöntő'}
            ko['QF4'] = {'p1': top_players[6], 'p2': top_players[7], 'res': 'Nem játszott', 'next': ('SF2', 'p2'), 'label': '4. Negyeddöntő'}
            ko['SF1'] = {'p1': '?', 'p2': '?', 'res': 'Nem játszott', 'next': ('F1', 'p1'), 'label': '1. Elődöntő'}
            ko['SF2'] = {'p1': '?', 'p2': '?', 'res': 'Nem játszott', 'next': ('F1', 'p2'), 'label': '2. Elődöntő'}
            ko['F1'] = {'p1': '?', 'p2': '?', 'res': 'Nem játszott', 'next': None, 'label': '🏆 DÖNTŐ'}
        else:
            ko['SF1'] = {'p1': top_players[0], 'p2': top_players[1], 'res': 'Nem játszott', 'next': ('F1', 'p1'), 'label': '1. Elődöntő'}
            ko['SF2'] = {'p1': top_players[2], 'p2': top_players[3], 'res': 'Nem játszott', 'next': ('F1', 'p2'), 'label': '2. Elődöntő'}
            ko['F1'] = {'p1': '?', 'p2': '?', 'res': 'Nem játszott', 'next': None, 'label': '🏆 DÖNTŐ'}
            
        st.session_state.ko_matches = ko
        st.session_state.phase = 'knockout'
        st.rerun()

# --- 4. FÁZIS: KIESÉSES SZAKASZ (MÉRKŐZÉSEK) ---
elif st.session_state.phase == 'knockout':
    st.title("🏆 Egyenes Kieséses Szakasz")
    
    ko = st.session_state.ko_matches
    
    def render_ko_match(m_key):
        m = ko[m_key]
        options = ["Nem játszott", "2 - 0", "2 - 1", "1 - 2", "0 - 2"]
        is_disabled = (m['p1'] == '?' or m['p2'] == '?')
        
        st.markdown(f"**{m['label']}**")
        if is_disabled:
            st.info(f"Várakozás a továbbjutóra...")
        else:
            current_val = m['res']
            new_val = st.selectbox(f"{m['p1']} vs {m['p2']}", options, index=options.index(current_val), key=f"ko_{m_key}")
            if new_val != current_val:
                ko[m_key]['res'] = new_val
                update_knockout_tree()
                st.rerun()
        st.write("---")

    col1, col2, col3 = st.columns(3)
    
    if 'QF1' in ko:
        with col1:
            st.header("Negyeddöntők")
            render_ko_match('QF1')
            render_ko_match('QF2')
            render_ko_match('QF3')
            render_ko_match('QF4')
        with col2:
            st.header("Elődöntők")
            render_ko_match('SF1')
            render_ko_match('SF2')
        with col3:
            st.header("Döntő")
            render_ko_match('F1')
    else:
        with col1:
            st.header("Elődöntők")
            render_ko_match('SF1')
            render_ko_match('SF2')
        with col2:
            st.header("Döntő")
            render_ko_match('F1')
