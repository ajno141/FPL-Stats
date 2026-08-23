import requests
import os
from datetime import datetime, timezone

BASE_URL = "https://fantasy.premierleague.com/api/"
OUTPUT_FOLDER = "FPL_STATS"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TIMEOUT = 30


# ============================================================
# API
# ============================================================

def get_data(endpoint):

    url = BASE_URL + endpoint

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# POMOĆNE FUNKCIJE
# ============================================================

def num(value):

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
# BOOTSTRAP
# ============================================================

print("Dohvaćam FPL podatke...")

bootstrap = get_data("bootstrap-static/")

players = bootstrap["elements"]
teams = bootstrap["teams"]
events = bootstrap["events"]


# ============================================================
# KLUBOVI
# ============================================================

team_names = {
    team["id"]: team["name"]
    for team in teams
}


# ============================================================
# ZAVRŠENA KOLA
# ============================================================

finished_gameweeks = [
    event["id"]
    for event in events
    if event.get("finished")
]

finished_gameweeks.sort()

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
    f"Završeni GW-ovi: {len(finished_gameweeks)}"
)

print(
    f"Zadnji završeni GW: {last_finished}"
)


# ============================================================
# PRIPREMA STATISTIKA
# ============================================================

season_stats = {}

for player in players:

    season_stats[player["id"]] = {

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


# ============================================================
# DOHVAĆANJE SVAKOG ZAVRŠENOG GW-a
#
# Ovo je puno brže nego jedan API zahtjev po igraču.
# Jedan GW = jedan zahtjev.
# ============================================================

for gw in finished_gameweeks:

    print(
        f"Dohvaćam GW {gw}..."
    )

    try:

        data = get_data(
            f"event/{gw}/live/"
        )

    except Exception as error:

        print(
            f"Greška kod GW {gw}: {error}"
        )

        continue


    for element in data.get(
        "elements",
        []
    ):

        player_id = element.get(
            "id"
        )

        stats = element.get(
            "stats",
            {}
        )

        if player_id not in season_stats:
            continue


        season_stats[player_id][
            "minutes"
        ] += num(
            stats.get(
                "minutes",
                0
            )
        )


        season_stats[player_id][
            "goals"
        ] += num(
            stats.get(
                "goals_scored",
                0
            )
        )


        season_stats[player_id][
            "assists"
        ] += num(
            stats.get(
                "assists",
                0
            )
        )


        season_stats[player_id][
            "points"
        ] += num(
            stats.get(
                "total_points",
                0
            )
        )


        season_stats[player_id][
            "bonus"
        ] += num(
            stats.get(
                "bonus",
                0
            )
        )


        season_stats[player_id][
            "bps"
        ] += num(
            stats.get(
                "bps",
                0
            )
        )


        season_stats[player_id][
            "xg"
        ] += num(
            stats.get(
                "expected_goals",
                0
            )
        )


        season_stats[player_id][
            "xa"
        ] += num(
            stats.get(
                "expected_assists",
                0
            )
        )


        season_stats[player_id][
            "dc"
        ] += num(
            stats.get(
                "defensive_contribution",
                0
            )
        )


# ============================================================
# FOLDER
# ============================================================

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# GRUPIRANJE PO KLUBOVIMA
# ============================================================

clubs = {}

for player in players:

    team_id = player["team"]

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

    separator = "-" * len(header)

    output = [
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

        output.append(line)

    return "\n".join(output)


# ============================================================
# PRAVLJENJE FILEOVA
# ============================================================

for club in sorted(clubs):

    print(
        f"Pravim {club}.txt..."
    )

    by_position = {
        1: [],
        2: [],
        3: [],
        4: []
    }


    for player in clubs[club]:

        player_id = player["id"]

        stats = season_stats[player_id]

        xgi = (
            stats["xg"] +
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
                ) + "%"
            )
        }


        position = player.get(
            "element_type"
        )

        if position in by_position:

            by_position[position].append(
                row
            )


    # --------------------------------------------------------
    # SORTIRANJE
    # --------------------------------------------------------

    for position in by_position:

        by_position[position].sort(
            key=lambda x: x["PLAYER"].lower()
        )


    # --------------------------------------------------------
    # SADRŽAJ FILEA
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
        f"Updated: "
        f"{datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S UTC')}"
    )

    lines.append(
        f"Current GW: {current_gameweek}"
    )

    lines.append(
        f"Statistics through GW: {last_finished}"
    )

    lines.append("")

    lines.append(
        "PTS=FPL Points | "
        "BONUS=Bonus Points | "
        "BPS=Bonus Points System | "
        "DC=Defensive Contribution | "
        "xG=Expected Goals | "
        "xA=Expected Assists | "
        "xGI=xG+xA"
    )


    # --------------------------------------------------------
    # SEKCIJE
    # --------------------------------------------------------

    for position in [1, 2, 3, 4]:

        rows = by_position[position]

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
        .replace(" ", "_")
        .replace("/", "_")
        + ".txt"
    )

    filepath = os.path.join(
        OUTPUT_FOLDER,
        filename
    )


    # --------------------------------------------------------
    # SPREMANJE
    # --------------------------------------------------------

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(lines)
        )


print("")
print("=" * 60)
print("USPJEŠNO ZAVRŠENO!")
print("=" * 60)
print(
    f"Klubovi spremljeni u: {OUTPUT_FOLDER}/"
)
print(
    f"Statistika zaključno s GW {last_finished}"
)
print("=" * 60)
