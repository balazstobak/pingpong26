import streamlit as st
import random
import itertools
import pandas as pd

st.set_page_config(page_title="Pingpong verseny", layout="wide")

st.title("🏓 Pingpong verseny lebonyolító app")


# -----------------------------
# Segédfüggvények
# -----------------------------

def create_groups(players):
    """
    A játékosokat lehetőleg 4 fős csoportokba osztja.
    Ha nem osztható pontosan 4-gyel, akkor 3 vagy 5 fős csoportokat is használ.
    """

    n = len(players)

    if n < 3:
        return None

    group_sizes = None

    # Először próbáljuk csak 4-es csoportokkal
    if n % 4 == 0:
        group_sizes = [4] * (n // 4)

    else:
        # Megengedett csoportméretek: 3, 4, 5
        # Olyan beosztást keresünk, ahol a legtöbb csoport 4 fős
        best = None

        for num_groups in range(1, n + 1):
            for sizes in itertools.product([3, 4, 5], repeat=num_groups):
                if sum(sizes) == n:
                    score = sizes.count(4)
                    if best is None or score > best[0]:
                        best = (score, list(sizes))

        if best:
            group_sizes = best[1]

    if group_sizes is None:
        return None

    random.shuffle(players)

    groups = {}
    index = 0

    for i, size in enumerate(group_sizes, start=1):
        group_name = f"Csoport {i}"
        groups[group_name] = players[index:index + size]
        index += size

    return groups


def create_matches(players):
    """Körmérkőzések létrehozása egy csoporton belül."""
    return list(itertools.combinations(players, 2))


def calculate_table(players, results):
    table = {
        player: {
            "Játékos": player,
            "Meccs": 0,
            "Győzelem": 0,
            "Vereség": 0,
            "Pont": 0,
            "Nyert szett": 0,
            "Vesztett szett": 0,
            "Szettkülönbség": 0,
        }
        for player in players
    }

    for result in results:
        p1 = result["p1"]
        p2 = result["p2"]
        s1 = result["s1"]
        s2 = result["s2"]

        if s1 is None or s2 is None:
            continue

        # Csak érvényes pingpong eredmény: 2-0, 2-1, 1-2, 0-2
        valid_scores = [(2, 0), (2, 1), (1, 2), (0, 2)]

        if (s1, s2) not in valid_scores:
            continue

        table[p1]["Meccs"] += 1
        table[p2]["Meccs"] += 1

        table[p1]["Nyert szett"] += s1
        table[p1]["Vesztett szett"] += s2

        table[p2]["Nyert szett"] += s2
        table[p2]["Vesztett szett"] += s1

        if s1 > s2:
            winner = p1
            loser = p2
        else:
            winner = p2
            loser = p1

        table[winner]["Győzelem"] += 1
        table[winner]["Pont"] += 1
        table[loser]["Vereség"] += 1

    for player in players:
        table[player]["Szettkülönbség"] = (
            table[player]["Nyert szett"] - table[player]["Vesztett szett"]
        )

    df = pd.DataFrame(table.values())

    df = df.sort_values(
        by=["Pont", "Szettkülönbség", "Nyert szett"],
        ascending=False
    ).reset_index(drop=True)

    df.index = df.index + 1

    return df


# -----------------------------
# Session state inicializálás
# -----------------------------

if "groups" not in st.session_state:
    st.session_state.groups = None

if "results" not in st.session_state:
    st.session_state.results = {}


# -----------------------------
# Játékosok bevitele
# -----------------------------

st.header("1. Jelentkezők megadása")

names_text = st.text_area(
    "Írd be a játékosok neveit, soronként egyet:",
    height=250,
    placeholder="Példa:\nAnna\nBéla\nCsaba\nDóra"
)

col1, col2 = st.columns(2)

with col1:
    shuffle_players = st.checkbox("Játékosok véletlenszerű keverése", value=True)

with col2:
    create_button = st.button("Csoportok létrehozása")


if create_button:
    players = [
        name.strip()
        for name in names_text.split("\n")
        if name.strip()
    ]

    players = list(dict.fromkeys(players))

    if len(players) < 3:
        st.error("Legalább 3 játékos szükséges.")
    else:
        if shuffle_players:
            random.shuffle(players)

        groups = create_groups(players)

        if groups is None:
            st.error("Nem sikerült megfelelő csoportbeosztást készíteni.")
        else:
            st.session_state.groups = groups
            st.session_state.results = {}

            for group_name, group_players in groups.items():
                st.session_state.results[group_name] = []

                for p1, p2 in create_matches(group_players):
                    st.session_state.results[group_name].append({
                        "p1": p1,
                        "p2": p2,
                        "s1": None,
                        "s2": None,
                    })

            st.success("Csoportok sikeresen létrehozva!")


# -----------------------------
# Csoportok és eredmények
# -----------------------------

if st.session_state.groups:

    st.header("2. Csoportok és eredmények")

    for group_name, players in st.session_state.groups.items():

        st.subheader(group_name)

        st.write("**Játékosok:** " + ", ".join(players))

        left, right = st.columns([1.2, 1])

        with left:
            st.markdown("### Mérkőzések")

            for i, match in enumerate(st.session_state.results[group_name]):

                p1 = match["p1"]
                p2 = match["p2"]

                col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 2])

                with col_a:
                    st.write(p1)

                with col_b:
                    s1 = st.selectbox(
                        "Szett",
                        options=[None, 0, 1, 2],
                        key=f"{group_name}_{i}_s1",
                        label_visibility="collapsed"
                    )

                with col_c:
                    s2 = st.selectbox(
                        "Szett",
                        options=[None, 0, 1, 2],
                        key=f"{group_name}_{i}_s2",
                        label_visibility="collapsed"
                    )

                with col_d:
                    st.write(p2)

                st.session_state.results[group_name][i]["s1"] = s1
                st.session_state.results[group_name][i]["s2"] = s2

                if s1 is not None and s2 is not None:
                    if (s1, s2) not in [(2, 0), (2, 1), (1, 2), (0, 2)]:
                        st.warning(
                            f"Érvénytelen eredmény: {p1} {s1}-{s2} {p2}. "
                            "Csak 2-0, 2-1, 1-2 vagy 0-2 lehet."
                        )

        with right:
            st.markdown("### Élő tabella")

            table = calculate_table(
                players,
                st.session_state.results[group_name]
            )

            st.dataframe(table, use_container_width=True)

        st.divider()


# -----------------------------
# Újrakezdés
# -----------------------------

st.header("3. Verseny kezelése")

if st.button("Verseny törlése / újrakezdés"):
    st.session_state.groups = None
    st.session_state.results = {}
    st.rerun()

    if st.button("Vissza a regisztrációhoz (Törlés)"):
        st.session_state.clear()
        st.rerun()


