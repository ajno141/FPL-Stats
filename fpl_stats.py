import requests
import os
from datetime import datetime, timezone


BASE_URL = "https://fantasy.premierleague.com/api"
OUTPUT_DIR = "FPL_STATS"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


# =========================================================
# POSITION NAMES
# =========================================================

POSITION_NAMES = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}


# =========================================================
# API REQUEST
# =========================================================

def get_json(endpoint):

    url = f"{BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# NUMBER HELPERS
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


def format_price(value):

    try:

        return f"£{int(value) / 10:.1f}m"

    except (ValueError, TypeError):

        return "£0.0m"


def format_ownership(value):

    try:

        return f"{float(value):.1f}%"

    except (ValueError, TypeError):

        return "0.0%"


# =========================================================
# SAFE FILE NAME
# =========================================================

def safe_filename(name):

    invalid = '<>:"/\\|?*'

    for character in invalid:

        name = name.replace(
            character,
            "_"
        )

    return name.replace(
        " ",
        "_"
    )


# =========================================================
# GET BOOTSTRAP
# =========================================================

def get_bootstrap():

    print(
        "Downloading latest FPL data..."
    )

    return get_json(
        "bootstrap-static/"
    )


# =========================================================
# CURRENT GAMEWEEK
# =========================================================

def get_current_gameweek(data):

    events = data.get(
        "events",
        []
    )

    # Prvo tražimo trenutno aktivni GW.
    for event in events:

        if event.get("is_current"):

            return event.get("id")

    # Ako nema current, tražimo zadnji završeni.
    finished_events = [
        event
        for event in events
        if event.get("finished")
    ]

    if finished_events:

        return finished_events[-1].get(
            "id"
        )

    # Ako sezona još nije počela,
    # uzimamo prvi GW.
    if events:

        return events[0].get(
            "id"
        )

    return 1


# =========================================================
# LIVE GAMEWEEK DATA
# =========================================================

def get_live_gameweek(gameweek):

    print(
        f"Downloading live data for GW{gameweek}..."
    )

    try:

        return get_json(
            f"event/{gameweek}/live/"
        )

    except Exception as error:

        print(
            f"WARNING: Live GW data unavailable: {error}"
        )

        return {
            "elements": []
        }


# =========================================================
# BUILD LIVE MAP
# =========================================================

def build_live_map(live_data):

    live_map = {}

    for element in live_data.get(
        "elements",
        []
    ):

        player_id = element.get(
            "id"
        )

        if player_id is None:
            continue

        live_map[player_id] = element.get(
            "stats",
            {}
        )

    return live_map


# =========================================================
# BUILD TEAM MAP
# =========================================================

def build_team_map(data):

    team_map = {}

    for team in data.get(
        "teams",
        []
    ):

        team_id = team.get(
            "id"
        )

        if team_id is None:
            continue

        team_name = team.get(
            "name",
            "Unknown"
        )

        short_name = team.get(
            "short_name",
            ""
        )

        team_map[team_id] = {
            "name": team_name,
            "short_name": short_name
        }

    return team_map


# =========================================================
# PLAYER LINE
# =========================================================

def player_line(
    player,
    live_stats
):

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
        player.get("element_type"),
        "UNK"
    )

    price = format_price(
        player.get(
            "now_cost",
            0
        )
    )

    # =====================================================
    # TOTAL / SEASON DATA
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
    # CURRENT GAMEWEEK DATA
    # =====================================================

    gw_points = safe_number(
        live_stats.get(
            "total_points",
            0
        )
    )

    gw_bonus = safe_number(
        live_stats.get(
            "bonus",
            0
        )
    )

    gw_bps = safe_number(
        live_stats.get(
            "bps",
            0
        )
    )

    gw_dc = safe_number(
        live_stats.get(
            "defensive_contribution",
            0
        )
    )

    gw_goals = safe_number(
        live_stats.get(
            "goals_scored",
            0
        )
    )

    gw_assists = safe_number(
        live_stats.get(
            "assists",
            0
        )
    )

    gw_minutes = safe_number(
        live_stats.get(
            "minutes",
            0
        )
    )

    # =====================================================
    # OUTPUT
    # =====================================================

    return (
        f"{name:<28}"
        f"{position:<6}"
        f"{price:<9}"

        f"{gw_points:<9}"
        f"{total_points:<10}"

        f"{gw_bonus:<9}"
        f"{total_bonus:<10}"

        f"{gw_bps:<8}"
        f"{total_bps:<9}"

        f"{gw_dc:<9}"
        f"{total_dc:<10}"

        f"{format_number(total_xg):<9}"
        f"{format_number(total_xa):<9}"
        f"{format_number(total_xgi):<9}"

        f"{gw_goals:<8}"
        f"{total_goals:<8}"

        f"{gw_assists:<9}"
        f"{total_assists:<9}"

        f"{gw_minutes:<9}"
        f"{total_minutes:<9}"

        f"{ownership:<9}"
        f"{format_number(form):<8}"
        f"{format_number(ppg):<8}"
    )


# =========================================================
# WRITE CLUB FILE
# =========================================================

def write_team_file(
    team_id,
    team,
    players,
    live_map,
    current_gw
):

    team_name = team["name"]

    filename = (
        safe_filename(
            team_name
        )
        + ".txt"
    )

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # PLAYER CLUB IS DETERMINED BY player["team"]
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    lines.append(
        team_name.upper()
    )

    lines.append(
        "=" * 280
    )

    lines.append(
        f"Updated: "
        f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    lines.append(
        f"Current Gameweek: GW{current_gw}"
    )

    lines.append(
        f"Players: {len(team_players)}"
    )

    lines.append("")

    # -----------------------------------------------------
    # COLUMN HEADER
    # -----------------------------------------------------

    lines.append(
        f"{'PLAYER':<28}"
        f"{'POS':<6}"
        f"{'PRICE':<9}"

        f"{'GW_PTS':<9}"
        f"{'TOTAL_PTS':<10}"

        f"{'GW_BONUS':<9}"
        f"{'TOTAL_BONUS':<10}"

        f"{'GW_BPS':<8}"
        f"{'TOTAL_BPS':<9}"

        f"{'GW_DC':<9}"
        f"{'TOTAL_DC':<10}"

        f"{'xG':<9}"
        f"{'xA':<9}"
        f"{'xGI':<9}"

        f"{'GW_G':<8}"
        f"{'GOALS':<8}"

        f"{'GW_A':<9}"
        f"{'ASSISTS':<9}"

        f"{'GW_MIN':<9}"
        f"{'MINUTES':<9}"

        f"{'OWN':<9}"
        f"{'FORM':<8}"
        f"{'PPG':<8}"
    )

    lines.append(
        "-" * 280
    )

    # -----------------------------------------------------
    # PLAYERS
    # -----------------------------------------------------

    for player in team_players:

        player_id = player.get(
            "id"
        )

        live_stats = live_map.get(
            player_id,
            {}
        )

        lines.append(
            player_line(
                player,
                live_stats
            )
        )

    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    lines.append("")

    lines.append(
        "=" * 280
    )

    lines.append(
        "GW_PTS = current Gameweek points"
    )

    lines.append(
        "TOTAL_PTS = total season FPL points"
    )

    lines.append(
        "GW_BONUS = current Gameweek bonus"
    )

    lines.append(
        "TOTAL_BONUS = total season bonus"
    )

    lines.append(
        "GW_BPS = current Gameweek BPS"
    )

    lines.append(
        "TOTAL_BPS = total season BPS"
    )

    lines.append(
        "GW_DC = current Gameweek defensive contribution"
    )

    lines.append(
        "TOTAL_DC = total season defensive contribution"
    )

    lines.append(
        "GW_G = goals scored in current Gameweek"
    )

    lines.append(
        "GW_A = assists in current Gameweek"
    )

    lines.append(
        "GW_MIN = minutes in current Gameweek"
    )

    # -----------------------------------------------------
    # WRITE FILE
    # -----------------------------------------------------

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
    print(
        "=============================================="
    )
    print(
        "          FPL LIVE STATS UPDATE"
    )
    print(
        "=============================================="
    )
    print("")

    # -----------------------------------------------------
    # GET FPL DATA
    # -----------------------------------------------------

    data = get_bootstrap()

    players = data.get(
        "elements",
        []
    )

    teams = data.get(
        "teams",
        []
    )

    if not players:

        raise RuntimeError(
            "FPL API returned no players."
        )

    if not teams:

        raise RuntimeError(
            "FPL API returned no teams."
        )

    print(
        f"Players received: {len(players)}"
    )

    print(
        f"Teams received: {len(teams)}"
    )

    # -----------------------------------------------------
    # BUILD TEAM MAP
    # -----------------------------------------------------

    team_map = build_team_map(
        data
    )

    print("")
    print(
        "Using clubs directly from FPL API:"
    )

    for team_id, team in sorted(
        team_map.items()
    ):

        print(
            f"  {team_id}: "
            f"{team['name']} "
            f"({team['short_name']})"
        )

    # -----------------------------------------------------
    # CURRENT GW
    # -----------------------------------------------------

    current_gw = get_current_gameweek(
        data
    )

    print("")
    print(
        f"Current Gameweek: GW{current_gw}"
    )

    # -----------------------------------------------------
    # LIVE DATA
    # -----------------------------------------------------

    live_data = get_live_gameweek(
        current_gw
    )

    live_map = build_live_map(
        live_data
    )

    print(
        f"Live players received: "
        f"{len(live_map)}"
    )

    # -----------------------------------------------------
    # OUTPUT DIRECTORY
    # -----------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    # -----------------------------------------------------
    # WRITE ONE FILE PER REAL FPL TEAM
    # -----------------------------------------------------

    for team_id, team in sorted(
        team_map.items()
    ):

        write_team_file(
            team_id,
            team,
            players,
            live_map,
            current_gw
        )

    print("")
    print(
        "=============================================="
    )
    print(
        "             UPDATE COMPLETE"
    )
    print(
        "=============================================="
    )
    print("")


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()
