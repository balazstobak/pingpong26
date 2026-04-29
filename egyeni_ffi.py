import streamlit as st
import random
import math

# Oldal beállítások
st.set_page_config(page_title="🏓 Ping-Pong Bajnokság", layout="wide")

# Állapottér (Session State) inicializálása, hogy a változók megmaradjanak újratöltéskor is
if 'players' not in st.session_state:
    st.session_state.players = []
if 'tournament_started' not in st.session_state:
    st.session_state.tournament_started = False
if 'matchups' not in st.session_state:
    st.session_state.matchups = None
if 'groups' not in st.session_state:
    st.session_state.groups = None

def is_power_of_two(n):
    """Ellenőrzi, hogy a szám kettő hatványa-e (2, 4, 8, 16, 32...)."""
    if n <= 1:
        return False
    return (n & (n - 1)) == 0

def start_tournament():
    players = st.session_state.players.copy()
    random.shuffle(players) # Véletlenszerű sorsolás
    n = len(players)
    
    if is_power_of_two(n):
        # EGYENES KIESÉS - Ha pontosan 2^x a létszám
        matchups = []
        for i in range(0, n, 2):
            matchups.append((players[i], players[i+1]))
        st.session_state.matchups = matchups
        st.session_state.groups = None
    else:
        # CSOPORTKÖRÖK - Ha nem lehet egyből egyenes kiesést játszani
        # Cél a maximum 4 fős csoportok kialakítása
        num_groups = math.ceil(n / 4)
        groups = {f"{i+1}. Csoport": [] for i in range(num_groups)}
        
        # "Kártyaosztás" módszer, hogy a lehető legkiegyensúlyozottabb legyen (pl. 4-4-4-3)
        for i, player in enumerate(players):
            groups[f"{(i % num_groups) + 1}. Csoport"].append(player)
        
        st.session_state.groups = groups
        st.session_state.matchups = None
        
    st.session_state.tournament_started = True

# --- FELHASZNÁLÓI FELÜLET (UI) ---

st.title("🏓 Élö Ping-Pong Bajnokság Nevezés")

# Oldalsáv (Sidebar) a nevezéshez
with st.sidebar:
    st.header("📝 Csatlakozz a játékhoz!")
    st.info("Írd be a neved, és nyomj a jelentkezésre.")
    
    new_player = st.text_input("Játékos neve:")
    if st.button("Jelentkezem!"):
        if new_player.strip() and new_player not in st.session_state.players:
            st.session_state.players.append(new_player.strip())
            st.success(f"Hajrá {new_player}! Sikeresen neveztél.")
        elif new_player in st.session_state.players:
            st.warning("Ez a név már regisztrált!")
        else:
            st.error("Kérlek, adj meg egy érvényes nevet!")
            
    st.write("---")
    st.subheader(f"Jelenlegi nevezők ({len(st.session_state.players)} fő):")
    for p in st.session_state.players:
        st.write(f"🏸 {p}")

# Fő panel: Bajnokság kezelése
if not st.session_state.tournament_started:
    st.info("👈 A jelentkezéshez használd a bal oldali panelt! (Telefonon a bal felső sarokban lévő > nyíllal nyithatod le)")
    
    # Szervezői gomb a sorsoláshoz
    st.write("---")
    st.subheader("Szervezői panel")
    if len(st.session_state.players) >= 3:
        if st.button("🎲 Sorsolás és Bajnokság Indítása", type="primary"):
            start_tournament()
            st.rerun()
    else:
        st.warning("Legalább 3 játékos szükséges a sorsoláshoz!")

else:
    # EREDMÉNYEK MEGJELENÍTÉSE
    st.header("🏆 A Sorsolás Eredménye")
    
    if st.session_state.matchups:
        st.success("Tökéletes létszám! Egyenes kieséses szakaszt játszunk (Kettő hatványa).")
        st.subheader("⚔️ 1. Forduló párosításai:")
        
        cols = st.columns(2)
        for i, match in enumerate(st.session_state.matchups):
            with cols[i % 2]:
                st.info(f"**{match[0]}** 🆚  **{match[1]}**")
                
    elif st.session_state.groups:
        st.warning("A nevezők száma miatt kiegyensúlyozott csoportköröket alakítottunk ki.")
        
        cols = st.columns(min(len(st.session_state.groups), 4)) # Formázás miatt max 4 oszlop
        for i, (group_name, members) in enumerate(st.session_state.groups.items()):
            with cols[i % len(cols)]:
                st.markdown(f"### {group_name}")
                for member in members:
                    st.success(member)

    st.write("---")
    if st.button("🔄 Bajnokság törlése és újrakezdése"):
        st.session_state.clear()
        st.rerun()
