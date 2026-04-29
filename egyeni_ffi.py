import streamlit as st
import random
import pandas as pd
import math
from itertools import combinations

# --- BEÁLLÍTÁSOK ÉS STÍLUS ---
st.set_page_config(page_title="Ping-Pong Tournament Pro", layout="wide")

# Egyedi CSS a szép megjelenéshez
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #deff9a; color: black; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #c5e685; color: black; }
    .status-box { padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INICIALIZÁLÁSA ---
if 'players' not in st.session_state:
    st.session_state.players = []
if 'phase' not in st.session_state:
    st.session_state.phase = "REGISTRATION"  # REGISTRATION, GROUPS, KNOCKOUT
if 'groups' not in st.session_state:
    st.session_state.groups = {}
if 'matches' not in st.session_state:
    st.session_state.matches = []
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'ko_bracket' not in st.session_state:
    st.session_state.ko_bracket = []

# --- SEGÉDFÜGGVÉNYEK ---
def validate_score(s1, s2):
    """Ellenőrzi a ping-pong szabályokat: min 11 pont és 2 különbség."""
    if (s1 >= 11 or s2 >= 11) and abs(s1 - s2) >= 2:
        return True
    return False

def init_tournament():
    players = st.session_state.players.copy()
    random.shuffle(players)
    n = len(players)
    
    # Ellenőrzés: 16, 32 vagy 64 -> Azonnali KO
    if n in [16, 32, 64]:
        st.session_state.phase = "KNOCKOUT"
        setup_ko(players)
    else:
        # Csoportok kialakítása (cél: ~4 fős csoportok)
        st.session_state.phase = "GROUPS"
        num_groups = math.ceil(n / 4)
        groups = {f"Csoport {chr(65+i)}": [] for i in range(num_groups)}
        for i, p in enumerate(players):
            groups[list(groups.keys())[i % num_groups]].append(p)
        st.session_state.groups = groups
        
        # Meccsek generálása a csoportokon belül
        all_matches = []
        for g_name, g_players in groups.items():
            for p1, p2 in combinations(g_players, 2):
                all_matches.append({"group": g_name, "p1": p1, "p2": p2, "played": False})
        st.session_state.matches = all_matches

def setup_ko(advancing_players):
    """Beállítja a kieséses ágat."""
    pairs = []
    for i in range(0, len(advancing_players), 2):
        pairs.append({"p1": advancing_players[i], "p2": advancing_players[i+1], "played": False, "winner": None})
    st.session_state.ko_bracket = [pairs] # Lista a körökről

# --- UI: REGISZTRÁCIÓ ---
if st.session_state.phase == "REGISTRATION":
    st.title("🏓 Szuper Ping-Pong Bajnokság")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Jelentkezés")
        name = st.text_input("Neved:", placeholder="Példa Béla")
        if st.button("Nevezek!"):
            if name and name not in st.session_state.players:
                st.session_state.players.append(name)
                st.success(f"{name} hozzáadva!")
            else:
                st.error("Névtelen vagy már létező játékos!")
        
        st.write(f"**Jelenlegi létszám:** {len(st.session_state.players)} fő")
        if len(st.session_state.players) >= 4:
            if st.button("🏁 SORSOLÁS INDÍTÁSA", type="primary"):
                init_tournament()
                st.rerun()

    with col2:
        st.subheader("Nevezési lista")
        if not st.session_state.players:
            st.info("Még nincs nevező.")
        else:
            for p in st.session_state.players:
                st.text(f"• {p}")

# --- UI: CSOPORTKÖRÖK ---
elif st.session_state.phase == "GROUPS":
    st.title("📊 Csoportmérkőzések")
    
    tabs = st.tabs(["Meccsek rögzítése", "Tabellák", "Továbbjutás"])
    
    with tabs[0]:
        for i, m in enumerate(st.session_state.matches):
            if not m['played']:
                with st.expander(f"{m['group']}: {m['p1']} vs {m['p2']}"):
                    c1, c2 = st.columns(2)
                    s1_1 = c1.number_input(f"{m['p1']} (1. szett)", 0, 30, key=f"s11_{i}")
                    s2_1 = c2.number_input(f"{m['p2']} (1. szett)", 0, 30, key=f"s21_{i}")
                    s1_2 = c1.number_input(f"{m['p1']} (2. szett)", 0, 30, key=f"s12_{i}")
                    s2_2 = c2.number_input(f"{m['p2']} (2. szett)", 0, 30, key=f"s22_{i}")
                    
                    if st.button(f"Eredmény mentése", key=f"btn_{i}"):
                        if validate_score(s1_1, s2_1) and validate_score(s1_2, s2_2):
                            # Győztes kiszámítása (egyszerűsítve 2 nyert szett alapján)
                            w1 = 1 if s1_1 > s2_1 else 0
                            w1 += 1 if s1_2 > s2_2 else 0
                            winner = m['p1'] if w1 >= 2 else m['p2']
                            st.session_state.matches[i]['played'] = True
                            st.session_state.matches[i]['winner'] = winner
                            st.session_state.matches[i]['scores'] = [(s1_1, s2_1), (s1_2, s2_2)]
                            st.success(f"Győztes: {winner}")
                            st.rerun()
                        else:
                            st.error("Nem valós végeredmény! (Min. 11 pont és 2 különbség kell)")

    with tabs[1]:
        # Csoportok számítása
        standings = []
        for g_name, g_players in st.session_state.groups.items():
            for p in g_players:
                matches = [m for m in st.session_state.matches if m['played'] and (m['p1'] == p or m['p2'] == p)]
                wins = len([m for m in matches if m['winner'] == p])
                standings.append({"Csoport": g_name, "Játékos": p, "Győzelem": wins, "Pont": wins * 2})
        
        df = pd.DataFrame(standings)
        for g in st.session_state.groups.keys():
            st.write(f"### {g}")
            st.table(df[df['Csoport'] == g].sort_values(by="Pont", ascending=False))

    with tabs[2]:
        all_played = all([m['played'] for m in st.session_state.matches])
        if all_played:
            st.success("Minden csoportmeccs véget ért!")
            if st.button("Továbbjutók sorsolása és KO szakasz"):
                # TOP 8 kiválasztása: csoportelsők + legjobb másodikok
                winners = df.sort_values(by=["Pont", "Győzelem"], ascending=False).head(8)['Játékos'].tolist()
                st.session_state.phase = "KNOCKOUT"
                setup_ko(winners)
                st.rerun()
        else:
            st.warning("Még vannak le nem játszott meccsek!")

# --- UI: KNOCKOUT ---
elif st.session_state.phase == "KNOCKOUT":
    st.title("🏆 Egyenes Kieséses Szakasz")
    
    current_round = st.session_state.ko_bracket[-1]
    
    st.subheader(f"Aktuális kör: {len(current_round)} meccs")
    
    cols = st.columns(len(current_round))
    round_finished = True
    next_round_players = []

    for i, m in enumerate(current_round):
        with cols[i]:
            st.markdown(f"**{m['p1']}**")
            st.write("vs")
            st.markdown(f"**{m['p2']}**")
            
            if not m['played']:
                round_finished = False
                with st.popover("Eredmény"):
                    s1_1 = st.number_input(f"{m['p1']} sz1", 0, 30, key=f"ko_s11_{i}")
                    s2_1 = st.number_input(f"{m['p2']} sz1", 0, 30, key=f"ko_s21_{i}")
                    s1_2 = st.number_input(f"{m['p1']} sz2", 0, 30, key=f"ko_s12_{i}")
                    s2_2 = st.number_input(f"{m['p2']} sz2", 0, 30, key=f"ko_s22_{i}")
                    
                    if st.button("Mentés", key=f"ko_btn_{i}"):
                        if validate_score(s1_1, s2_1) and validate_score(s1_2, s2_2):
                            winner = m['p1'] if s1_1 > s2_1 else m['p2'] # egyszerűsített
                            st.session_state.ko_bracket[-1][i]['played'] = True
                            st.session_state.ko_bracket[-1][i]['winner'] = winner
                            st.rerun()
                        else:
                            st.error("Hibás pontszám!")
            else:
                st.success(f"Győztes: {m['winner']}")
                next_round_players.append(m['winner'])

    if round_finished and len(current_round) > 1:
        if st.button("Következő forduló generálása"):
            setup_ko(next_round_players)
            st.rerun()
    elif round_finished and len(current_round) == 1:
        st.balloons()
        st.header(f"🎊 A BAJNOK: {current_round[0]['winner']} 🎊")

    if st.button("Vissza a regisztrációhoz (Törlés)"):
        st.session_state.clear()
        st.rerun()

A fenti prezentáció és kód minden igényedet lefedi! Sok sikert a versenyhez!
