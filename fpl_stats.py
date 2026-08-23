import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

BASE_URL = "https://fantasy.premierleague.com/api/"
OUTPUT_FOLDER = "FPL_STATS"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TIMEOUT = 30

# Broj istovremenih zahtjeva
MAX_WORKERS = 12


# ============================================================
# POMOĆNE FUNKCIJE
# ============================================================

def get_json(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    return response.json()


def number(value):

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def fmt(value):

    if abs(value - round(value)) < 0.0001:
        return str(int(round(value)))

    return f"{value:.2f}"


def price(value):

    try:
        return f"£{float(value) / 10:.1f}"
    except (TypeError, ValueError):
        return "N/A"


POSITIONS = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD"
}


SECTIONS = {
    1: "GOALKEEPERS",
    2: "DEFENDERS",
    3: "MIDFIELDERS",
    4: "ATTACKERS"
}


# ============================================================
# DOHVATI HISTORIJU JEDNOG IGRAČA
# ============================================================

def get_player_history(player_id):

    url = (
        BASE_URL
        + f"element-summary/{player_id}/"
    )

    try:

        data = get_json(url)

        return player_id, data.get(
            "history",
            []
        )

    except Exception as error:

        print(
            f"Greška za player {player_id}: {error}"
        )

        return player_id, []


# ============================================================
# POČETAK
# ============================================================

print("=" * 60)
print("FPL SEASON STATISTICS")
print("=" * 60)

print("")

print("Dohvaćam osnovne FPL podatke...")

bootstrap = get_json(
    BASE_URL + "bootstrap-static/"
)

players = bootstrap.get(
    "elements",
    []
)

teams = bootstrap.get(
    "teams",
    []
)

events = bootstrap.get(
    "events",
    []
)


# ============================================================
# GAMEWEEK
# ============================================================

finished_gameweeks = sorted(
    event["id"]
    for event in events
    if event.get("finished")
)

current_gameweek = next(
    (
        event["id"]
        for event in events
        if event.get("is_current")
    ),
    None
)

last_finished = (
    max(finished_gameweeks)
    if finished_gameweeks
    else 0
)


print(
    f"Trenutni GW: {current_gameweek}"
)

print(
    f"Zadnji završeni GW: {last_finished}"
)

print(
    f"Ukupno završenih GW-ova: "
    f"{len(finished_gameweeks)}"
)

print("")


# ============================================================
# KLUBOVI
# ============================================================

team_names = {

    team["id"]:
    team["name"]

    for team in teams
}


# ============================================================
# PRIPREMA
# ============================================================

season_stats = {

    player["id"]: {

        "minutes": 0,
        "goals": 0,
        "assists": 0,
        "points": 0,
        "bonus": 0,
        "bps": 0,
        "xg": 0,
        "xa": 0,
        "dc": 0

    }

    for player in players
}


# ============================================================
# DOHVAĆANJE SVIH IGRAČA
# ============================================================

print(
    f"Dohvaćam historiju za "
    f"{len(players)} igrača..."
)

print(
    "Ovo može trajati nekoliko minuta."
)

print("")


completed = 0


with ThreadPoolExecutor(
    max_workers=MAX_WORKERS
) as executor:

    futures = [

        executor.submit(
            get_player_history,
            player["id"]
        )

        for player in players
    ]


    for future in as_completed(futures):

        player_id, history = (
            future.result()
        )

        stats = season_stats[
            player_id
        ]


        # ----------------------------------------------------
        # ZBROJI SVA ODIGRANA KOLA
        # ----------------------------------------------------

        for gw in history:

            stats["minutes"] += number(
                gw.get(
                    "minutes",
                    0
                )
            )

            stats["goals"] += number(
                gw.get(
                    "goals_scored",
                    0
                )
            )

            stats["assists"] += number(
                gw.get(
                    "assists",
                    0
                )
            )

            stats["points"] += number(
                gw.get(
                    "total_points",
                    0
                )
            )

            stats["bonus"] += number(
                gw.get(
                    "bonus",
                    0
                )
            )

            stats["bps"] += number(
                gw.get(
                    "bps",
                    0
                )
            )

            stats["xg"] += number(
                gw.get(
                    "expected_goals",
                    0
                )
            )

            stats["xa"] += number(
                gw.get(
                    "expected_assists",
                    0
                )
            )

            stats["dc"] += number(
                gw.get(
                    "defensive_contribution",
                    0
                )
            )


        completed += 1


        if completed % 50 == 0:

            print(
                f"Obrađeno: "
                f"{completed}/{len(players)}"
            )


# ============================================================
# FOLDER
# ============================================================

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# GRUPIRANJE IGRAČA PO KLUBOVIMA
# ============================================================

clubs = {}


for player in players:

    team_id = player.get(
        "team"
    )

    club = team_names.get(
        team_id,
        "UNKNOWN"
    )

    if club not in clubs:

        clubs[club] = []

    clubs[club].append(
        player
    )


# ============================================================
# TABLICA
# ============================================================

columns = [

    "PLAYER",
    "POS",
    "PRICE",
    "PTS",
    "BONUS",
    "BPS",
    "DC",
    "xG",
    "xA",
    "xGI",
    "G",
    "A",
    "MIN",
    "OWN"
]


widths = {

    "PLAYER": 22,
    "POS": 5,
    "PRICE": 8,
    "PTS": 7,
    "BONUS": 7,
    "BPS": 8,
    "DC": 8,
    "xG": 8,
    "xA": 8,
    "xGI": 8,
    "G": 5,
    "A": 5,
    "MIN": 7,
    "OWN": 9
}


def make_table(rows):

    header = " ".join(

        column.ljust(
            widths[column]
        )

        for column in columns
    )

    separator = "-" * len(
        header
    )

    lines = [

        header,
        separator
    ]


    for row in rows:

        line = " ".join(

            str(
                row.get(
                    column,
                    "N/A"
                )
            )[:widths[column]].ljust(
                widths[column]
            )

            for column in columns
        )

        lines.append(
            line
        )


    return "\n".join(
        lines
    )


# ============================================================
# PRAVLJENJE 20 FILEOVA
# ============================================================

print("")
print("Pravim klupske datoteke...")


for club in sorted(clubs):

    print(
        f"  → {club}"
    )


    by_position = {

        1: [],
        2: [],
        3: [],
        4: []

    }


    # --------------------------------------------------------
    # IGRAČI KLUBA
    # --------------------------------------------------------

    for player in clubs[club]:

        player_id = player["id"]

        stats = season_stats[
            player_id
        ]


        xgi = (
            stats["xg"]
            +
            stats["xa"]
        )


        row = {

            "PLAYER": player.get(
                "web_name",
                "N/A"
            ),

            "POS": POSITIONS.get(
                player.get(
                    "element_type"
                ),
                "N/A"
            ),

            "PRICE": price(
                player.get(
                    "now_cost"
                )
            ),

            "PTS": fmt(
                stats["points"]
            ),

            "BONUS": fmt(
                stats["bonus"]
            ),

            "BPS": fmt(
                stats["bps"]
            ),

            "DC": fmt(
                stats["dc"]
            ),

            "xG": fmt(
                stats["xg"]
            ),

            "xA": fmt(
                stats["xa"]
            ),

            "xGI": fmt(
                xgi
            ),

            "G": fmt(
                stats["goals"]
            ),

            "A": fmt(
                stats["assists"]
            ),

            "MIN": fmt(
                stats["minutes"]
            ),

            "OWN": (
                str(
                    player.get(
                        "selected_by_percent",
                        "N/A"
                    )
                )
                + "%"
            )
        }


        position = player.get(
            "element_type"
        )


        if position in by_position:

            by_position[
                position
            ].append(
                row
            )


    # --------------------------------------------------------
    # SORTIRANJE
    # --------------------------------------------------------

    for position in by_position:

        by_position[position].sort(

            key=lambda x:
            x["PLAYER"].lower()

        )


    # --------------------------------------------------------
    # FILE
    # --------------------------------------------------------

    lines = []


    lines.append(
        "=" * 145
    )

    lines.append(
        club.upper()
    )

    lines.append(
        "=" * 145
    )

    lines.append("")

    lines.append(
        "FPL SEASON STATISTICS"
    )

    lines.append(
        "Updated: "
        +
        datetime.now(
            timezone.utc
        ).strftime(
            "%d.%m.%Y %H:%M:%S UTC"
        )
    )

    lines.append(
        f"Current GW: {current_gameweek}"
    )

    lines.append(
        f"Statistics through GW: "
        f"{last_finished}"
    )

    lines.append("")

    lines.append(
        "ALL STATISTICS ARE SEASON TOTALS"
    )

    lines.append("")

    lines.append(
        "PTS = FPL Points"
    )

    lines.append(
        "BONUS = Bonus Points"
    )

    lines.append(
        "BPS = Bonus Points System"
    )

    lines.append(
        "DC = Defensive Contribution"
    )

    lines.append(
        "xG = Expected Goals"
    )

    lines.append(
        "xA = Expected Assists"
    )

    lines.append(
        "xGI = xG + xA"
    )


    # --------------------------------------------------------
    # SEKCIJE
    # --------------------------------------------------------

    for position in [1, 2, 3, 4]:

        rows = by_position[
            position
        ]


        if not rows:
            continue


        lines.append("")
        lines.append("")

        lines.append(
            "=" * 145
        )

        lines.append(
            SECTIONS[position]
        )

        lines.append(
            "=" * 145
        )

        lines.append(
            make_table(rows)
        )


    # --------------------------------------------------------
    # IME FILEA
    # --------------------------------------------------------

    filename = (

        club
        .replace(
            " ",
            "_"
        )
        .replace(
            "/",
            "_"
        )
        + ".txt"

    )


    filepath = os.path.join(
        OUTPUT_FOLDER,
        filename
    )


    # --------------------------------------------------------
    # SPREMI
    # --------------------------------------------------------

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(lines)
        )


# ============================================================
# GOTOVO
# ============================================================

print("")
print("=" * 60)
print("USPJEŠNO ZAVRŠENO!")
print("=" * 60)

print(
    f"Statistike do GW {last_finished}"
)

print(
    f"Datoteke: {OUTPUT_FOLDER}/"
)

print("=" * 60)
