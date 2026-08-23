import requests
import time
import os
from datetime import datetime

# ============================================================
# POSTAVKE
# ============================================================

BASE_URL = "https://fantasy.premierleague.com/api/"

REFRESH_SECONDS = 300

OUTPUT_FOLDER = "FPL_STATS"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ============================================================
# API
# ============================================================

def get_data(endpoint):

    response = requests.get(
        BASE_URL + endpoint,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# POMOĆNE FUNKCIJE
# ============================================================

def safe_number(value):

    try:
        return float(value)

    except (ValueError, TypeError):
        return 0.0


def format_number(value, decimals=2):

    try:
        return f"{float(value):.{decimals}f}"

    except (ValueError, TypeError):
        return "N/A"


def format_price(value):

    try:
        return f"£{float(value) / 10:.1f}"

    except (ValueError, TypeError):
        return "N/A"


def position_name(element_type):

    positions = {
        1: "GK",
        2: "DEF",
        3: "MID",
        4: "FWD"
    }

    return positions.get(
        element_type,
        "N/A"
    )


def section_name(element_type):

    sections = {
        1: "GOALKEEPERS",
        2: "DEFENDERS",
        3: "MIDFIELDERS",
        4: "ATTACKERS"
    }

    return sections.get(
        element_type,
        "OTHER"
    )


# ============================================================
# UKUPNA STATISTIKA IGRAČA
# ============================================================

def get_season_statistics(player_id):

    try:

        data = get_data(
            f"element-summary/{player_id}/"
        )

        history = data.get(
            "history",
            []
        )

        if not history:

            return {
                "minutes": 0,
                "goals": 0,
                "assists": 0,
                "points": 0,
                "bonus": 0,
                "bps": 0,
                "xg": 0,
                "xa": 0,
                "xgi": 0,
                "dc": 0
            }

        # ----------------------------------------------------
        # ZBRAJANJE SVIH GAMEWEEKOVA
        # ----------------------------------------------------

        minutes = 0
        goals = 0
        assists = 0
        points = 0
        bonus = 0
        bps = 0
        xg = 0
        xa = 0
        dc = 0

        for gw in history:

            minutes += safe_number(
                gw.get(
                    "minutes",
                    0
                )
            )

            goals += safe_number(
                gw.get(
                    "goals_scored",
                    0
                )
            )

            assists += safe_number(
                gw.get(
                    "assists",
                    0
                )
            )

            points += safe_number(
                gw.get(
                    "total_points",
                    0
                )
            )

            bonus += safe_number(
                gw.get(
                    "bonus",
                    0
                )
            )

            bps += safe_number(
                gw.get(
                    "bps",
                    0
                )
            )

            xg += safe_number(
                gw.get(
                    "expected_goals",
                    0
                )
            )

            xa += safe_number(
                gw.get(
                    "expected_assists",
                    0
                )
            )

            dc_value = gw.get(
                "defensive_contribution"
            )

            if dc_value is not None:

                dc += safe_number(
                    dc_value
                )

        xgi = xg + xa

        return {

            "minutes": minutes,
            "goals": goals,
            "assists": assists,
            "points": points,
            "bonus": bonus,
            "bps": bps,
            "xg": xg,
            "xa": xa,
            "xgi": xgi,
            "dc": dc
        }

    except Exception as error:

        print(
            f"Greška kod player ID {player_id}: {error}"
        )

        return {

            "minutes": 0,
            "goals": 0,
            "assists": 0,
            "points": 0,
            "bonus": 0,
            "bps": 0,
            "xg": 0,
            "xa": 0,
            "xgi": 0,
            "dc": 0
        }


# ============================================================
# IGRAČ
# ============================================================

def create_player_row(
    player,
    stats
):

    return {

        "PLAYER": player.get(
            "web_name",
            "N/A"
        ),

        "POS": position_name(
            player.get(
                "element_type"
            )
        ),

        "PRICE": format_price(
            player.get(
                "now_cost"
            )
        ),

        "PTS": int(
            stats["points"]
        ),

        "BONUS": int(
            stats["bonus"]
        ),

        "BPS": int(
            stats["bps"]
        ),

        "DC": format_number(
            stats["dc"]
        ),

        "DC PTS": "N/A",

        "xG": format_number(
            stats["xg"]
        ),

        "xA": format_number(
            stats["xa"]
        ),

        "xGI": format_number(
            stats["xgi"]
        ),

        "G": int(
            stats["goals"]
        ),

        "A": int(
            stats["assists"]
        ),

        "MIN": int(
            stats["minutes"]
        ),

        "OWN": f"{player.get(
            'selected_by_percent',
            'N/A'
        )}%"
    }


# ============================================================
# TABLICA
# ============================================================

def create_table(players):

    columns = [

        "PLAYER",
        "POS",
        "PRICE",
        "PTS",
        "BONUS",
        "BPS",
        "DC",
        "DC PTS",
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
        "DC PTS": 9,
        "xG": 8,
        "xA": 8,
        "xGI": 8,
        "G": 5,
        "A": 5,
        "MIN": 7,
        "OWN": 9
    }

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

    for player in players:

        line = " ".join(

            str(
                player.get(
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
# GLAVNI REPORT
# ============================================================

def create_reports():

    print("")
    print(
        "Dohvaćam FPL podatke..."
    )

    bootstrap = get_data(
        "bootstrap-static/"
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

    # --------------------------------------------------------
    # KLUBOVI
    # --------------------------------------------------------

    team_names = {

        team["id"]:
        team["name"]

        for team in teams
    }

    # --------------------------------------------------------
    # GAMEWEEK
    # --------------------------------------------------------

    current_gw = None
    last_finished_gw = None

    for event in events:

        if event.get(
            "is_current"
        ):

            current_gw = event[
                "id"
            ]

        if event.get(
            "finished"
        ):

            last_finished_gw = event[
                "id"
            ]

    print(
        f"Trenutni GW: {current_gw}"
    )

    print(
        f"Zadnji završeni GW: {last_finished_gw}"
    )

    # --------------------------------------------------------
    # GRUPIRANJE
    # --------------------------------------------------------

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

    clubs = dict(
        sorted(
            clubs.items()
        )
    )

    # --------------------------------------------------------
    # FOLDER
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    # --------------------------------------------------------
    # OBRADA KLUBOVA
    # --------------------------------------------------------

    for club, club_players in clubs.items():

        print(
            f"Obrađujem {club}..."
        )

        players_by_section = {

            1: [],
            2: [],
            3: [],
            4: []
        }

        # ----------------------------------------------------
        # IGRAČI
        # ----------------------------------------------------

        for player in club_players:

            stats = get_season_statistics(
                player["id"]
            )

            row = create_player_row(
                player,
                stats
            )

            position = player.get(
                "element_type"
            )

            if position in players_by_section:

                players_by_section[
                    position
                ].append(
                    row
                )

            # Mala pauza
            time.sleep(
                0.05
            )

        # ----------------------------------------------------
        # FILE NAME
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SADRŽAJ
        # ----------------------------------------------------

        lines = []

        lines.append(
            "=" * 150
        )

        lines.append(
            club.upper()
        )

        lines.append(
            "=" * 150
        )

        lines.append("")

        lines.append(
            f"Last update: "
            f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )

        lines.append(
            f"Current GW: {current_gw}"
        )

        lines.append(
            f"Statistics calculated through GW: "
            f"{last_finished_gw}"
        )

        lines.append("")

        lines.append(
            "ALL STATISTICS BELOW ARE SEASON TOTALS"
        )

        lines.append("")

        lines.append(
            "PTS  = Total FPL Points"
        )

        lines.append(
            "BONUS = Total Bonus Points"
        )

        lines.append(
            "BPS  = Total Bonus Points System"
        )

        lines.append(
            "DC   = Total Defensive Contributions"
        )

        lines.append(
            "xG   = Expected Goals"
        )

        lines.append(
            "xA   = Expected Assists"
        )

        lines.append(
            "xGI  = Expected Goal Involvements"
        )

        lines.append("")

        # ----------------------------------------------------
        # SEKCIJE
        # ----------------------------------------------------

        for position_id in [
            1,
            2,
            3,
            4
        ]:

            section_players = players_by_section[
                position_id
            ]

            if not section_players:
                continue

            section_title = section_name(
                position_id
            )

            lines.append("")
            lines.append("")
            lines.append(
                "=" * 150
            )

            lines.append(
                section_title
            )

            lines.append(
                "=" * 150
            )

            # Sortiranje po imenu
            section_players.sort(
                key=lambda x:
                x["PLAYER"]
            )

            lines.append(
                create_table(
                    section_players
                )
            )

        # ----------------------------------------------------
        # SPREMI FILE
        # ----------------------------------------------------

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "\n".join(
                    lines
                )
            )

    print("")
    print(
        "=============================================="
    )

    print(
        "SVE DATOTEKE SU AŽURIRANE!"
    )

    print(
        f"Folder: {OUTPUT_FOLDER}"
    )

    print(
        "=============================================="
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=============================================="
    )

    print(
        "       FPL SEASON STATISTICS"
    )

    print(
        "=============================================="
    )

    print("")

    print(
        "20 klubova -> 20 zasebnih Notepad datoteka"
    )

    print(
        "Statistike -> ukupno kroz sva odigrana kola"
    )

    print(
        f"Osvježavanje -> svakih "
        f"{REFRESH_SECONDS // 60} minuta"
    )

    print("")

    while True:

        try:

            create_reports()

        except Exception as error:

            print("")
            print(
                "GREŠKA:"
            )

            print(
                error
            )

            print("")

        print("")
        print(
            f"Sljedeće osvježavanje za "
            f"{REFRESH_SECONDS // 60} minuta."
        )

        print("")

        time.sleep(
            REFRESH_SECONDS
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()