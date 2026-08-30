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
# API
# =========================================================

def get_json(endpoint):
    url = f"{BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def get_bootstrap():
    print("Downloading FPL bootstrap data...")

    return get_json(
        "bootstrap-static/"
    )


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

        price = int(value) / 10

        return f"£{price:.1f}m"

    except (ValueError, TypeError):

        return "£0.0m"


def format_ownership(value):

    try:

        return f"{float(value):.1f}%"

    except (ValueError, TypeError):

        return "0.0%"


# =========================================================
# POSITIONS
# =========================================================

POSITION_NAMES = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}


# =========================================================
# BUILD TEAM MAP FROM FPL API
# =========================================================

def build_team_map(data):

    team_map = {}

    for team in data.get("teams", []):

        team_id = team.get("id")

        team_name = team.get(
            "name",
            "Unknown"
        )

        short_name = team.get(
            "short_name",
            ""
        )

        if team_id is not None:

            team_map[team_id] = {
                "name": team_name,
                "short_name": short_name,
            }

    return team_map


# =========================================================
# SAFE FILE NAME
# =========================================================

def safe_filename(name):

    replacements = {
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

    for old, new in replacements.items():

        name = name.replace(
            old,
            new
        )

    return name.replace(
        " ",
        "_"
    )


# =========================================================
# GET CURRENT GAMEWEEK
# =========================================================

def get_current_gameweek(data):

    events = data.get(
        "events",
        []
    )

    # First try the event marked as current.
    for event in events:

        if event.get("is_current"):

            return event.get("id")

    # Otherwise find the latest finished/started event.
    for event in reversed(events):

        if event.get("finished"):

            return event.get("id")

    # Otherwise use first non-finished event.
    for event in events:

        if not event.get("finished"):

            return event.get("id")

    return 1


# =========================================================
# GET GAMEWEEK LIVE DATA
# =========================================================

def get_gameweek_live(gameweek):

    print(
        f"Downloading live data for GW{gameweek}..."
    )

    endpoint = (
        f"event/{gameweek}/live/"
    )

    try:

        return get_json(endpoint)

    except Exception as error:

        print(
            "WARNING: Could not load "
            f"GW{gameweek} live data: {error}"
        )

        return {
            "elements": []
        }


# =========================================================
# LIVE PLAYER MAP
# =========================================================

def build_live_map(live_data):

    live_map = {}

    for item in live_data.get(
        "elements",
        []
    ):

        player_id = item.get("id")

        if player_id is not None:

            live_map[player_id] = item.get(
                "stats",
                {}
            )

    return live_map


# =========================================================
# PLAYER LINE
# =========================================================

def player_line(
    player,
    live_stats,
    team_name,
    gw
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

    # -----------------------------------------------------
    # TOTAL SEASON STATS
    # -----------------------------------------------------

    total_points = safe_number(
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

    # -----------------------------------------------------
    # CURRENT GAMEWEEK STATS
    # -----------------------------------------------------

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

    gw_defensive_contribution = safe_number(
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

    # -----------------------------------------------------
    # LINE
    # -----------------------------------------------------

    return (
        f"{name:<28}"
        f"{position:<6}"
        f"{price:<9}"

        f"{gw_points:<8}"
        f"{total_points:<9}"

        f"{gw_bonus:<8}"
        f"{bonus:<8}"

        f"{gw_bps:<8}"
        f"{bps:<8}"

        f"{gw_defensive_contribution:<8}"
        f"{defensive_contribution:<8}"

        f"{format_number(xg):<9}"
        f"{format_number(xa):<9}"
        f"{format_number(xgi):<9}"

        f"{gw_goals:<7}"
        f"{goals:<7}"

        f"{gw_assists:<7}"
        f"{assists:<7}"

        f"{gw_minutes:<8}"
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
    team_info,
    players,
    live_map,
    current_gw
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    team_name = team_info["name"]

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
        "=" * 260
    )

    lines.append(
        f"Updated: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    lines.append(
        f"Current Gameweek: GW{current_gw}"
    )

    lines.append(
        f"Players: {len(team_players)}"
    )

    lines.append("")

    # -----------------------------------------------------
    # TABLE HEADER
    # -----------------------------------------------------

    lines.append(
        f"{'PLAYER':<28}"
        f"{'POS':<6}"
        f"{'PRICE':<9}"

        f"{'GW_PTS':<8}"
        f"{'TOTAL_PTS':<9}"

        f"{'GW_BONUS':<8}"
        f"{'BONUS':<8}"

        f"{'GW_BPS':<8}"
        f"{'BPS':<8}"

        f"{'GW_DC':<8}"
        f"{'TOTAL_DC':<8}"

        f"{'xG':<9}"
        f"{'xA':<9}"
        f"{'xGI':<9}"

        f"{'GW_G':<7}"
        f"{'GOALS':<7}"

        f"{'GW_A':<7}"
        f"{'ASSISTS':<7}"

        f"{'GW_MIN':<8}"
        f"{'MIN':<8}"

        f"{'OWN':<9}"
        f"{'FORM':<8}"
        f"{'PPG':<8}"
    )

    lines.append(
        "-" * 260
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
                live_stats,
                team_name,
                current_gw
            )
        )

    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    lines.append("")
    lines.append(
        "=" * 260
    )

    lines.append(
        "GW_PTS = points in current Gameweek"
    )

    lines.append(
        "TOTAL_PTS = total FPL points for season"
    )

    lines.append(
        "GW_DC = defensive contribution in current Gameweek"
    )

    lines.append(
        "TOTAL_DC = total defensive contribution"
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
    print(
        "=========================================="
    )
    print(
        "       FPL LIVE STATISTICS UPDATE"
    )
    print(
        "=========================================="
    )
    print("")

    # -----------------------------------------------------
    # BOOTSTRAP
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

    print(
        f"Received {len(players)} players"
    )

    print(
        f"Received {len(teams)} teams"
    )

    if not players:

        raise RuntimeError(
            "FPL API returned no players."
        )

    if not teams:

        raise RuntimeError(
            "FPL API returned no teams."
        )

    # -----------------------------------------------------
    # TEAM MAP
    # -----------------------------------------------------

    team_map = build_team_map(
        data
    )

    print("")
    print("Current FPL clubs:")

    for team_id, team_info in sorted(
        team_map.items()
    ):

        print(
            f"  {team_id}: "
            f"{team_info['name']}"
        )

    # -----------------------------------------------------
    # CURRENT GAMEWEEK
    # -----------------------------------------------------

    current_gw = get_current_gameweek(
        data
    )

    print("")
    print(
        f"Current Gameweek: GW{current_gw}"
    )

    # -----------------------------------------------------
    # LIVE GAMEWEEK DATA
    # -----------------------------------------------------

    live_data = get_gameweek_live(
        current_gw
    )

    live_map = build_live_map(
        live_data
    )

    print(
        f"Received live data for "
        f"{len(live_map)} players"
    )

    # -----------------------------------------------------
    # WRITE ALL CLUB FILES
    # -----------------------------------------------------

    print("")

    for team_id, team_info in sorted(
        team_map.items()
    ):

        write_team_file(
            team_id,
            team_info,
            players,
            live_map,
            current_gw
        )

    # -----------------------------------------------------
    # FINISHED
    # -----------------------------------------------------

    print("")
    print(
        "=========================================="
    )
    print(
        "       FPL UPDATE COMPLETED"
    )
    print(
        "=========================================="
    )
    print("")


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()
