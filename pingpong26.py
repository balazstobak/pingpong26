import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Csapatos Pingpong Kupa", layout="wide")

# --- 1. ADATOK INICIALIZÁLÁSA ---
if 'teams' not in st.session_state:
    st.session_state.teams = []
if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = None
if 'tournament_started' not in st.session_state:
    st.session_state.tournament_started = False

# --- 2. OPTIMALIZÁLT SORSOLÁS (Circle Method) ---
def generate_optimized_schedule(teams_list):
    teams = teams_list.copy()
    if len(teams) % 2 != 0:
        teams.append('Pihenő') # Ha páratlan, kell egy fantom csapat
    
    n = len(teams)
    schedule = []
    
    # Körforgó módszer generálása (alapból kerüli az egymás utáni meccseket)
    for round_idx in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            t1 = teams[i]
            t2 = teams[n - 1 - i]
            if t1 != 'Pihenő' and t2 != 'Pihenő':
                round_matches.append((t1, t2))
        
        # Rotáció (az első fix marad, a többi forog)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
        
        # Hogy egy körön belül is keverve legyenek az asztalhoz állások
        random.shuffle(round_matches) 
        
        for m in round_matches:
            schedule.append({
                "Hazai Csapat": m[0],
                "Vendég Csapat": m[1],
                "🔴 Piros H": 0, "🔴 Piros V": 0,
                "⚪ Szürke H": 0, "⚪ Szürke V": 0,
                "🟢 Zöld H": 0, "🟢 Zöld V": 0,
                "Befejezve": False
            })
            
    return pd.DataFrame(schedule)

# --- 3. FELÜLET: NEVEZÉS ---
st.title("🏓 3-Asztalos Csapatverseny")

if not st.session_state.tournament_started:
    st.header("1. Lépés: Csapatok megadása")
    st.info("Add meg a 3 fős csapatok neveit. A sorsolás optimalizálva lesz az asztalokhoz és a pihenőidőkhöz.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        new_team = st.text_input("Csapat neve (pl. A csapat):", key="team_input")
        if st.button("Hozzáadás"):
            if new_team and new_team not in st.session_state.teams:
                st.session_state.teams.append(new_team)
                st.rerun()
                
    with col2:
        st.write(f"**Regisztrált csapatok ({len(st.session_state.teams)}):**")
        st.write(", ".join(st.session_state.teams))
        
    if len(st.session_state.teams) >= 2:
        st.divider()
        if st.button("🚀 Sorsolás és Verseny Indítása", type="primary"):
            st.session_state.schedule_df = generate_optimized_schedule(st.session_state.teams)
            st.session_state.tournament_started = True
            st.rerun()

# --- 4. FELÜLET: ÉLŐ TÁBLÁZAT ---
else:
    st.header("2. Lépés: Eredmények folyamatos vezetése")
    st.write("A táblázat celláira duplán kattintva tudod beírni a pontokat. Az asztalok (Piros, Szürke, Zöld) függetlenül, aszinkron módon szerkeszthetők.")
    
    # Adatszerkesztő konfigurálása a színes asztalokhoz
    edited_df = st.data_editor(
        st.session_state.schedule_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Hazai Csapat": st.column_config.TextColumn(disabled=True),
            "Vendég Csapat": st.column_config.TextColumn(disabled=True),
            "🔴 Piros H": st.column_config.NumberColumn(min_value=0, step=1),
            "🔴 Piros V": st.column_config.NumberColumn(min_value=0, step=1),
            "⚪ Szürke H": st.column_config.NumberColumn(min_value=0, step=1),
            "⚪ Szürke V": st.column_config.NumberColumn(min_value=0, step=1),
            "🟢 Zöld H": st.column_config.NumberColumn(min_value=0, step=1),
            "🟢 Zöld V": st.column_config.NumberColumn(min_value=0, step=1),
            "Befejezve": st.column_config.CheckboxColumn("Befejezve ✅")
        }
    )
    
    # Változások mentése a memóriába
    st.session_state.schedule_df = edited_df

    st.divider()
    if st.button("Vissza a nevezéshez (Újraindítás)", type="secondary"):
        st.session_state.clear()
        st.rerun()
