import requests
import os
from datetime import datetime, timezone


# =========================================================
# CONFIG
# =========================================================

BASE_URL = "https://fantasy.premierleague.com/api"

OUTPUT_DIR = "FPL_STATS"

TEAM_NAMES = {
    1: "Arsenal",
    2: "Aston_Villa",
    3: "Bournemouth",
    4: "Brentford",
    5: "Brighton",
    7: "Chelsea",
    8: "Crystal_Palace",
    9: "Everton",
    10: "Fulham",
    11: "Leeds",
    12: "Liverpool",
    13: "Manchester_City",
    14: "Manchester_United",
    15: "Newcastle_United",
    16: "Nottingham_Forest",
    17: "Sunderland",
    18: "Tottenham_Hotspur",
    20: "Wolverhampton_Wanderers",
}


POSITION_NAMES = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}


HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


# =========================================================
# REQUEST
# =========================================================

def api_get(endpoint):

    url = f"{BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# SAFE NUMBERS
# =========================================================

def safe_number(value, default=0):

    try:

        if value is None:
            return default

        number = float(value)

        if number != number:
            return default

        if number.is_integer():
            return int(number)

        return number

    except (ValueError, TypeError):

        return default


def format_number(value):

    value = safe_number(value)

    if isinstance(value, float):

        return (
            f"{value:.2f}"
            .rstrip("0")
            .rstrip(".")
        )

    return str(value)


# =========================================================
# PRICE
# =========================================================

def format_price(value):

    try:

        price = int(value) / 10

        return f"£{price:.1f}m"

    except (ValueError, TypeError):

        return "£0.0m"


# =========================================================
# OWNERSHIP
# =========================================================

def format_ownership(value):

    try:

        return f"{float(value):.1f}%"

    except (ValueError, TypeError):

        return "0.0%"


# =========================================================
# FIND CURRENT GAMEWEEK
# =========================================================

def find_current_gameweek(events):

    for event in events:

        if event.get("is_current"):

            return event["id"]


    for event in events:

        if event.get("is_next"):

            return event["id"]


    for event in events:

        if not event.get("finished"):

            return event["id"]


    return None


# =========================================================
# LIVE DATA
# =========================================================

def get_live_data(gameweek):

    print(
        f"Downloading LIVE data for GW{gameweek}..."
    )

    endpoint = f"event/{gameweek}/live/"

    data = api_get(endpoint)

    elements = data.get(
        "elements",
        []
    )

    if not elements:

        raise RuntimeError(
            f"FPL live endpoint returned no "
            f"player data for GW{gameweek}."
        )

    print(
        f"Received live data for "
        f"{len(elements)} players."
    )

    return elements


# =========================================================
# MERGE LIVE DATA
# =========================================================

def merge_live_data(
    players,
    live_players
):

    live_by_id = {
        item.get("id"): item
        for item in live_players
    }

    merged = []


    for player in players:

        player = player.copy()

        player_id = player.get("id")

        live = live_by_id.get(
            player_id
        )


        if live:

            stats = live.get(
                "stats",
                {}
            )


            # =================================================
            # CURRENT GAMEWEEK POINTS
            # =================================================

            if "total_points" in stats:

                player["event_points"] = (
                    stats["total_points"]
                )


            # =================================================
            # BONUS
            # =================================================

            if "bonus" in stats:

                player["bonus"] = (
                    stats["bonus"]
                )


            # =================================================
            # BPS
            # =================================================

            if "bps" in stats:

                player["bps"] = (
                    stats["bps"]
                )


            # =================================================
            # GOALS
            # =================================================

            if "goals_scored" in stats:

                player["goals_scored"] = (
                    stats["goals_scored"]
                )


            # =================================================
            # ASSISTS
            # =================================================

            if "assists" in stats:

                player["assists"] = (
                    stats["assists"]
                )


            # =================================================
            # MINUTES
            # =================================================

            if "minutes" in stats:

                player["minutes"] = (
                    stats["minutes"]
                )


            # =================================================
            # CLEAN SHEETS
            # =================================================

            if "clean_sheets" in stats:

                player["clean_sheets"] = (
                    stats["clean_sheets"]
                )


            # =================================================
            # GOALS CONCEDED
            # =================================================

            if "goals_conceded" in stats:

                player["goals_conceded"] = (
                    stats["goals_conceded"]
                )


            # =================================================
            # OWN GOALS
            # =================================================

            if "own_goals" in stats:

                player["own_goals"] = (
                    stats["own_goals"]
                )


            # =================================================
            # PENALTIES SAVED
            # =================================================

            if "penalties_saved" in stats:

                player["penalties_saved"] = (
                    stats["penalties_saved"]
                )


            # =================================================
            # PENALTIES MISSED
            # =================================================

            if "penalties_missed" in stats:

                player["penalties_missed"] = (
                    stats["penalties_missed"]
                )


            # =================================================
            # YELLOW CARDS
            # =================================================

            if "yellow_cards" in stats:

                player["yellow_cards"] = (
                    stats["yellow_cards"]
                )


            # =================================================
            # RED CARDS
            # =================================================

            if "red_cards" in stats:

                player["red_cards"] = (
                    stats["red_cards"]
                )


            # =================================================
            # SAVES
            # =================================================

            if "saves" in stats:

                player["saves"] = (
                    stats["saves"]
                )


            # =================================================
            # DEFENSIVE CONTRIBUTION
            # =================================================

            if "defensive_contribution" in stats:

                player["defensive_contribution"] = (
                    stats["defensive_contribution"]
                )


            # =================================================
            # EXPECTED GOALS
            # =================================================

            if "expected_goals" in stats:

                player["expected_goals"] = (
                    stats["expected_goals"]
                )


            # =================================================
            # EXPECTED ASSISTS
            # =================================================

            if "expected_assists" in stats:

                player["expected_assists"] = (
                    stats["expected_assists"]
                )


            # =================================================
            # EXPECTED GOAL INVOLVEMENTS
            # =================================================

            if "expected_goal_involvements" in stats:

                player["expected_goal_involvements"] = (
                    stats["expected_goal_involvements"]
                )


        merged.append(player)


    return merged


# =========================================================
# PLAYER LINE
# =========================================================

def player_line(player):

    first_name = player.get(
        "first_name",
        ""
    )

    second_name = player.get(
        "second_name",
        ""
    )


    name = (
        f"{first_name} {second_name}"
        .strip()
    )


    position = POSITION_NAMES.get(
        player.get(
            "element_type"
        ),
        "UNK"
    )


    price = format_price(
        player.get(
            "now_cost",
            0
        )
    )


    # ---------------------------------------------------------
    # CURRENT GAMEWEEK POINTS
    # ---------------------------------------------------------

    gw_pts = safe_number(
        player.get(
            "event_points",
            0
        )
    )


    # ---------------------------------------------------------
    # TOTAL SEASON POINTS
    # ---------------------------------------------------------

    total_pts = safe_number(
        player.get(
            "total_points",
            0
        )
    )


    bonus = safe_number(
        player.get(
            "bonus",
            0
        )
    )


    bps = safe_number(
        player.get(
            "bps",
            0
        )
    )


    defensive_contribution = safe_number(
        player.get(
            "defensive_contribution",
            0
        )
    )


    xg = safe_number(
        player.get(
            "expected_goals",
            0
        )
    )


    xa = safe_number(
        player.get(
            "expected_assists",
            0
        )
    )


    xgi = safe_number(
        player.get(
            "expected_goal_involvements",
            0
        )
    )


    goals = safe_number(
        player.get(
            "goals_scored",
            0
        )
    )


    assists = safe_number(
        player.get(
            "assists",
            0
        )
    )


    minutes = safe_number(
        player.get(
            "minutes",
            0
        )
    )


    ownership = format_ownership(
        player.get(
            "selected_by_percent",
            0
        )
    )


    form = safe_number(
        player.get(
            "form",
            0
        )
    )


    ppg = safe_number(
        player.get(
            "points_per_game",
            0
        )
    )


    return (

        f"{name:<28}"

        f"{position:<6}"

        f"{price:<9}"

        f"{gw_pts:<9}"

        f"{total_pts:<11}"

        f"{bonus:<8}"

        f"{bps:<8}"

        f"{defensive_contribution:<8}"

        f"{format_number(xg):<9}"

        f"{format_number(xa):<9}"

        f"{format_number(xgi):<9}"

        f"{goals:<6}"

        f"{assists:<6}"

        f"{minutes:<8}"

        f"{ownership:<9}"

        f"{format_number(form):<8}"

        f"{format_number(ppg):<8}"

    )


# =========================================================
# WRITE TEAM FILE
# =========================================================

def write_team_file(
    team_id,
    team_name,
    players,
    gameweek
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


    path = os.path.join(
        OUTPUT_DIR,
        f"{team_name}.txt"
    )


    # =====================================================
    # IMPORTANT:
    # CLUB IS TAKEN DIRECTLY FROM FPL API TEAM ID
    # =====================================================

    team_players = [

        player

        for player in players

        if player.get("team") == team_id

    ]


    team_players.sort(

        key=lambda player: (

            player.get(
                "element_type",
                0
            ),

            player.get(
                "second_name",
                ""
            )

        )

    )


    now = datetime.now(
        timezone.utc
    ).astimezone()


    lines = []


    lines.append(
        team_name
        .replace(
            "_",
            " "
        )
        .upper()
    )


    lines.append(
        "=" * 160
    )


    lines.append(
        f"Updated: "
        f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
    )


    lines.append(
        f"Gameweek: GW{gameweek}"
    )


    lines.append(
        f"Players: "
        f"{len(team_players)}"
    )


    lines.append("")


    lines.append(

        f"{'PLAYER':<28}"

        f"{'POS':<6}"

        f"{'PRICE':<9}"

        f"{'GW_PTS':<9}"

        f"{'TOTAL_PTS':<11}"

        f"{'BONUS':<8}"

        f"{'BPS':<8}"

        f"{'DC':<8}"

        f"{'xG':<9}"

        f"{'xA':<9}"

        f"{'xGI':<9}"

        f"{'G':<6}"

        f"{'A':<6}"

        f"{'MIN':<8}"

        f"{'OWN':<9}"

        f"{'FORM':<8}"

        f"{'PPG':<8}"

    )


    lines.append(
        "-" * 160
    )


    for player in team_players:

        lines.append(
            player_line(
                player
            )
        )


    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(lines)
        )


    print(
        f"Updated {team_name}: "
        f"{len(team_players)} players"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("")
    print("=" * 60)
    print("FPL LIVE STATISTICS UPDATE")
    print("=" * 60)
    print("")


    # =====================================================
    # BOOTSTRAP
    # =====================================================

    print(
        "Downloading FPL bootstrap data..."
    )


    bootstrap = api_get(
        "bootstrap-static/"
    )


    players = bootstrap.get(
        "elements",
        []
    )


    events = bootstrap.get(
        "events",
        []
    )


    if not players:

        raise RuntimeError(
            "FPL API returned no players."
        )


    if not events:

        raise RuntimeError(
            "FPL API returned no gameweeks."
        )


    print(
        f"Received {len(players)} players."
    )


    # =====================================================
    # CURRENT GAMEWEEK
    # =====================================================

    gameweek = find_current_gameweek(
        events
    )


    if gameweek is None:

        raise RuntimeError(
            "Could not determine current gameweek."
        )


    print(
        f"Current gameweek: GW{gameweek}"
    )


    # =====================================================
    # LIVE DATA
    # =====================================================

    live_players = get_live_data(
        gameweek
    )


    # =====================================================
    # MERGE LIVE DATA
    # =====================================================

    players = merge_live_data(
        players,
        live_players
    )


    print(
        "Live statistics merged successfully."
    )


    # =====================================================
    # WRITE ALL CLUB FILES
    # =====================================================

    for team_id, team_name in TEAM_NAMES.items():

        write_team_file(
            team_id,
            team_name,
            players,
            gameweek
        )


    print("")
    print("=" * 60)
    print(
        f"FPL LIVE UPDATE COMPLETED - GW{gameweek}"
    )
    print("=" * 60)
    print("")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
