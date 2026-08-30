import requests
import os
from datetime import datetime, timezone


# =========================================================
# CONFIG
# =========================================================

BASE_URL = "https://fantasy.premierleague.com/api"
OUTPUT_DIR = "FPL_STATS"

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
# POSITION
# =========================================================

POSITION_NAMES = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}


# =========================================================
# SAFE CLUB FILE NAME
# =========================================================

def make_filename(name):

    replacements = {
        " ": "_",
        "/": "_",
        "\\": "_",
        ":": "_",
        "*": "_",
        "?": "_",
        '"': "_",
        "<": "_",
        ">": "_",
        "|": "_",
    }

    result = name.strip()

    for old, new in replacements.items():

        result = result.replace(
            old,
            new
        )

    return result


# =========================================================
# CURRENT GAMEWEEK
# =========================================================

def find_current_gameweek(events):

    # 1. Trenutno kolo
    for event in events:

        if event.get("is_current"):

            return event["id"]


    # 2. Sljedeće kolo
    for event in events:

        if event.get("is_next"):

            return event["id"]


    # 3. Prvo nezavršeno kolo
    for event in events:

        if not event.get("finished"):

            return event["id"]


    # 4. Zadnje kolo
    if events:

        return events[-1]["id"]


    return None


# =========================================================
# LIVE DATA
# =========================================================

def get_live_data(gameweek):

    print(
        f"Downloading LIVE data for GW{gameweek}..."
    )

    data = api_get(
        f"event/{gameweek}/live/"
    )

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


            # CURRENT GW POINTS

            if "total_points" in stats:

                player["event_points"] = safe_number(
                    stats["total_points"]
                )


            # CURRENT GW BONUS

            if "bonus" in stats:

                player["event_bonus"] = safe_number(
                    stats["bonus"]
                )


            # CURRENT GW BPS

            if "bps" in stats:

                player["event_bps"] = safe_number(
                    stats["bps"]
                )


            # CURRENT GW DEFENSIVE CONTRIBUTION

            if "defensive_contribution" in stats:

                player["event_defensive_contribution"] = safe_number(
                    stats["defensive_contribution"]
                )


            # CURRENT GW GOALS

            if "goals_scored" in stats:

                player["event_goals"] = safe_number(
                    stats["goals_scored"]
                )


            # CURRENT GW ASSISTS

            if "assists" in stats:

                player["event_assists"] = safe_number(
                    stats["assists"]
                )


            # CURRENT GW MINUTES

            if "minutes" in stats:

                player["event_minutes"] = safe_number(
                    stats["minutes"]
                )


            # CURRENT GW XG

            if "expected_goals" in stats:

                player["event_xg"] = safe_number(
                    stats["expected_goals"]
                )


            # CURRENT GW XA

            if "expected_assists" in stats:

                player["event_xa"] = safe_number(
                    stats["expected_assists"]
                )


            # CURRENT GW XGI

            if "expected_goal_involvements" in stats:

                player["event_xgi"] = safe_number(
                    stats["expected_goal_involvements"]
                )


        else:

            # Ako nema live podataka,
            # postavi trenutni GW na 0.

            player["event_points"] = 0
            player["event_bonus"] = 0
            player["event_bps"] = 0
            player["event_defensive_contribution"] = 0
            player["event_goals"] = 0
            player["event_assists"] = 0
            player["event_minutes"] = 0
            player["event_xg"] = 0
            player["event_xa"] = 0
            player["event_xgi"] = 0


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


    # =====================================================
    # CURRENT GAMEWEEK
    # =====================================================

    gw_points = safe_number(
        player.get(
            "event_points",
            0
        )
    )

    gw_bonus = safe_number(
        player.get(
            "event_bonus",
            0
        )
    )

    gw_bps = safe_number(
        player.get(
            "event_bps",
            0
        )
    )

    gw_dc = safe_number(
        player.get(
            "event_defensive_contribution",
            0
        )
    )

    gw_goals = safe_number(
        player.get(
            "event_goals",
            0
        )
    )

    gw_assists = safe_number(
        player.get(
            "event_assists",
            0
        )
    )

    gw_minutes = safe_number(
        player.get(
            "event_minutes",
            0
        )
    )

    gw_xg = safe_number(
        player.get(
            "event_xg",
            0
        )
    )

    gw_xa = safe_number(
        player.get(
            "event_xa",
            0
        )
    )

    gw_xgi = safe_number(
        player.get(
            "event_xgi",
            0
        )
    )


    # =====================================================
    # SEASON TOTALS
    # =====================================================

    total_points = safe_number(
        player.get(
            "total_points",
            0
        )
    )

    total_bonus = safe_number(
        player.get(
            "bonus",
            0
        )
    )

    total_bps = safe_number(
        player.get(
            "bps",
            0
        )
    )

    total_dc = safe_number(
        player.get(
            "defensive_contribution",
            0
        )
    )

    total_goals = safe_number(
        player.get(
            "goals_scored",
            0
        )
    )

    total_assists = safe_number(
        player.get(
            "assists",
            0
        )
    )

    total_minutes = safe_number(
        player.get(
            "minutes",
            0
        )
    )

    total_xg = safe_number(
        player.get(
            "expected_goals",
            0
        )
    )

    total_xa = safe_number(
        player.get(
            "expected_assists",
            0
        )
    )

    total_xgi = safe_number(
        player.get(
            "expected_goal_involvements",
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


    # =====================================================
    # OUTPUT
    # =====================================================

    lines = []


    lines.append(
        f"{name:<28}"
        f"{position:<6}"
        f"{price:<9}"
        f"{gw_points:<7}"
        f"{total_points:<8}"
        f"{gw_bonus:<8}"
        f"{total_bonus:<9}"
        f"{gw_bps:<7}"
        f"{total_bps:<8}"
        f"{gw_dc:<7}"
        f"{total_dc:<8}"
        f"{format_number(gw_xg):<8}"
        f"{format_number(total_xg):<8}"
        f"{format_number(gw_xa):<8}"
        f"{format_number(total_xa):<8}"
        f"{format_number(gw_xgi):<8}"
        f"{format_number(total_xgi):<8}"
        f"{gw_goals:<6}"
        f"{total_goals:<7}"
        f"{gw_assists:<6}"
        f"{total_assists:<7}"
        f"{gw_minutes:<7}"
        f"{total_minutes:<8}"
        f"{ownership:<9}"
        f"{format_number(form):<8}"
        f"{format_number(ppg):<8}"
    )


    return lines[0]


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


    filename = make_filename(
        team_name
    )


    path = os.path.join(
        OUTPUT_DIR,
        f"{filename}.txt"
    )


    # =====================================================
    # CRITICAL:
    # PLAYER CLUB IS DETERMINED ONLY BY TEAM ID
    # FROM THE CURRENT FPL API
    # =====================================================

    team_players = [

        player

        for player in players

        if int(
            player.get("team", -1)
        ) == int(team_id)

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
            ).lower()

        )

    )


    now = datetime.now(
        timezone.utc
    ).astimezone()


    lines = []


    lines.append(
        team_name.upper()
    )


    lines.append(
        "=" * 260
    )


    lines.append(
        f"Updated: "
        f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
    )


    lines.append(
        f"Gameweek: GW{gameweek}"
    )


    lines.append(
        f"Players: {len(team_players)}"
    )


    lines.append("")


    # =====================================================
    # HEADER
    # =====================================================

    lines.append(

        f"{'PLAYER':<28}"

        f"{'POS':<6}"

        f"{'PRICE':<9}"

        f"{'GW PTS':<7}"

        f"{'TOTAL PTS':<8}"

        f"{'GW BONUS':<8}"

        f"{'TOTAL BONUS':<9}"

        f"{'GW BPS':<7}"

        f"{'TOTAL BPS':<8}"

        f"{'GW DC':<7}"

        f"{'TOTAL DC':<8}"

        f"{'GW xG':<8}"

        f"{'TOTAL xG':<8}"

        f"{'GW xA':<8}"

        f"{'TOTAL xA':<8}"

        f"{'GW xGI':<8}"

        f"{'TOTAL xGI':<8}"

        f"{'GW G':<6}"

        f"{'TOTAL G':<7}"

        f"{'GW A':<6}"

        f"{'TOTAL A':<7}"

        f"{'GW MIN':<7}"

        f"{'TOTAL MIN':<8}"

        f"{'OWN':<9}"

        f"{'FORM':<8}"

        f"{'PPG':<8}"

    )


    lines.append(
        "-" * 260
    )


    # =====================================================
    # PLAYERS
    # =====================================================

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
    print("=" * 70)
    print("FPL LIVE STATISTICS UPDATE")
    print("=" * 70)
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


    teams = bootstrap.get(
        "teams",
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


    if not teams:

        raise RuntimeError(
            "FPL API returned no teams."
        )


    print(
        f"Received {len(players)} players."
    )


    print(
        f"Received {len(teams)} clubs."
    )


    # =====================================================
    # BUILD TEAM MAP DIRECTLY FROM FPL API
    # =====================================================

    team_map = {}


    for team in teams:

        team_id = team.get(
            "id"
        )

        team_name = team.get(
            "name"
        )


        if team_id is None:
            continue


        if not team_name:
            continue


        team_map[
            team_id
        ] = team_name


    print("")
    print("CURRENT FPL CLUBS:")
    print("")


    for team_id, team_name in sorted(
        team_map.items()
    ):

        print(
            f"{team_id:>3} -> {team_name}"
        )


    print("")


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
    # WRITE ALL CURRENT CLUBS
    # =====================================================

    for team_id, team_name in team_map.items():

        write_team_file(
            team_id,
            team_name,
            players,
            gameweek
        )


    # =====================================================
    # FINISH
    # =====================================================

    print("")
    print("=" * 70)
    print(
        f"FPL LIVE UPDATE COMPLETED - GW{gameweek}"
    )
    print("=" * 70)
    print("")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
