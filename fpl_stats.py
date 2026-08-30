import requests
import os
from datetime import datetime, timezone


BASE_URL = "https://fantasy.premierleague.com/api"

OUTPUT_DIR = "FPL_STATS"


# =========================================================
# PREMIER LEAGUE TEAMS 2026/27
# =========================================================

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
    20: "Coventry_City",
    21: "Hull_City",
    22: "Ipswich_Town",
}


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
# REQUEST SESSION
# =========================================================

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
})


# =========================================================
# GET JSON
# =========================================================

def get_json(url):

    response = session.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# GET BOOTSTRAP
# =========================================================

def get_bootstrap():

    url = f"{BASE_URL}/bootstrap-static/"

    return get_json(url)


# =========================================================
# CURRENT GAMEWEEK
# =========================================================

def get_current_gameweek(data):

    events = data.get(
        "events",
        []
    )

    # Official current GW
    for event in events:

        if event.get("is_current"):

            return event.get("id")


    # Fallback
    now = datetime.now(
        timezone.utc
    )

    for event in events:

        deadline = event.get(
            "deadline_time"
        )

        if not deadline:
            continue

        try:

            deadline_dt = datetime.fromisoformat(
                deadline.replace(
                    "Z",
                    "+00:00"
                )
            )

            if (
                deadline_dt <= now
                and not event.get("finished")
            ):

                return event.get("id")

        except Exception:
            pass


    # Last fallback
    for event in events:

        if not event.get("finished"):

            return event.get("id")


    return None


# =========================================================
# LIVE GAMEWEEK
# =========================================================

def get_live_data(gameweek):

    if not gameweek:

        return {}


    url = (
        f"{BASE_URL}/event/"
        f"{gameweek}/live/"
    )


    try:

        data = get_json(url)

        return {

            item.get("id"):
            item.get("stats", {})

            for item in data.get(
                "elements",
                []
            )

        }

    except Exception as error:

        print(
            "WARNING: Could not load "
            f"live GW data: {error}"
        )

        return {}


# =========================================================
# SAFE NUMBER
# =========================================================

def safe_number(
    value,
    default=0
):

    try:

        if value is None:

            return default


        number = float(value)


        if number != number:

            return default


        if number.is_integer():

            return int(number)


        return number


    except (
        ValueError,
        TypeError
    ):

        return default


# =========================================================
# FORMAT NUMBER
# =========================================================

def format_number(value):

    value = safe_number(value)


    if isinstance(
        value,
        float
    ):

        return (
            f"{value:.2f}"
            .rstrip("0")
            .rstrip(".")
        )


    return str(value)


# =========================================================
# FORMAT PRICE
# =========================================================

def format_price(value):

    try:

        price = int(value) / 10

        return f"£{price:.1f}m"


    except (
        ValueError,
        TypeError
    ):

        return "£0.0m"


# =========================================================
# FORMAT OWNERSHIP
# =========================================================

def format_ownership(value):

    try:

        return f"{float(value):.1f}%"


    except (
        ValueError,
        TypeError
    ):

        return "0.0%"


# =========================================================
# DEFENSIVE CONTRIBUTION POINTS
# =========================================================

def calculate_dc_points(
    position,
    defensive_contribution
):

    dc = safe_number(
        defensive_contribution,
        0
    )


    # Defenders:
    # 10 DC = 2 points

    if position == "DEF":

        threshold = 10


    # Midfielders / Forwards:
    # 12 DC = 2 points

    elif position in (
        "MID",
        "FWD"
    ):

        threshold = 12


    # Goalkeepers don't get
    # defensive contribution points

    else:

        return 0


    return (
        int(dc // threshold)
        * 2
    )


# =========================================================
# BUILD PLAYER
# =========================================================

def build_player(
    player,
    live_stats
):

    player_id = player.get(
        "id"
    )


    first_name = player.get(
        "first_name",
        ""
    )


    second_name = player.get(
        "second_name",
        ""
    )


    name = (
        f"{first_name} "
        f"{second_name}"
    ).strip()


    position = POSITION_NAMES.get(
        player.get(
            "element_type"
        ),
        "UNK"
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


    # =====================================================
    # TOTAL DC POINTS
    # =====================================================

    total_dc_points = calculate_dc_points(
        position,
        total_dc
    )


    # =====================================================
    # CURRENT GAMEWEEK LIVE
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
    # CURRENT GW DC POINTS
    # =====================================================

    gw_dc_points = calculate_dc_points(
        position,
        gw_dc
    )


    # =====================================================
    # RETURN PLAYER
    # =====================================================

    return {

        "id":
            player_id,

        "name":
            name,

        "position":
            position,

        "price":
            format_price(
                player.get(
                    "now_cost",
                    0
                )
            ),


        # =================================================
        # SEASON TOTALS
        # =================================================

        "points":
            total_points,

        "bonus":
            total_bonus,

        "bps":
            total_bps,

        "dc":
            total_dc,

        "dc_points":
            total_dc_points,

        "goals":
            total_goals,

        "assists":
            total_assists,

        "minutes":
            total_minutes,

        "xg":
            xg,

        "xa":
            xa,

        "xgi":
            xgi,

        "ownership":
            format_ownership(
                player.get(
                    "selected_by_percent",
                    0
                )
            ),

        "form":
            safe_number(
                player.get(
                    "form",
                    0
                )
            ),

        "ppg":
            safe_number(
                player.get(
                    "points_per_game",
                    0
                )
            ),


        # =================================================
        # CURRENT GW
        # =================================================

        "gw_points":
            gw_points,

        "gw_bonus":
            gw_bonus,

        "gw_bps":
            gw_bps,

        "gw_dc":
            gw_dc,

        "gw_dc_points":
            gw_dc_points,

        "gw_goals":
            gw_goals,

        "gw_assists":
            gw_assists,

        "gw_minutes":
            gw_minutes,

    }


# =========================================================
# PLAYER LINE
# =========================================================

def player_line(player):

    return (

        f"{player['name']:<28}"

        f"{player['position']:<6}"

        f"{player['price']:<9}"


        # -----------------------------------------------
        # SEASON TOTALS
        # -----------------------------------------------

        f"{player['points']:<7}"

        f"{player['bonus']:<8}"

        f"{player['bps']:<8}"

        f"{player['dc']:<8}"

        f"{player['dc_points']:<9}"


        f"{format_number(player['xg']):<9}"

        f"{format_number(player['xa']):<9}"

        f"{format_number(player['xgi']):<9}"


        f"{player['goals']:<6}"

        f"{player['assists']:<6}"

        f"{player['minutes']:<8}"


        f"{player['ownership']:<9}"

        f"{format_number(player['form']):<8}"

        f"{format_number(player['ppg']):<8}"


        # -----------------------------------------------
        # CURRENT GAMEWEEK
        # -----------------------------------------------

        f"{player['gw_points']:<9}"

        f"{player['gw_bonus']:<10}"

        f"{player['gw_bps']:<9}"

        f"{player['gw_dc']:<9}"

        f"{player['gw_dc_points']:<12}"

        f"{player['gw_goals']:<8}"

        f"{player['gw_assists']:<8}"

        f"{player['gw_minutes']:<8}"

    )


# =========================================================
# WRITE TEAM FILE
# =========================================================

def write_team_file(
    team_id,
    team_name,
    players,
    current_gameweek
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


    path = os.path.join(
        OUTPUT_DIR,
        f"{team_name}.txt"
    )


    team_players = [

        p for p in players

        if p.get("team") == team_id

    ]


    team_players.sort(

        key=lambda p: (

            p.get(
                "element_type",
                0
            ),

            p.get(
                "second_name",
                ""
            )

        )

    )


    now = datetime.now(
        timezone.utc
    ).astimezone()


    lines = []


    # =====================================================
    # HEADER
    # =====================================================

    lines.append(
        team_name
        .replace(
            "_",
            " "
        )
        .upper()
    )


    lines.append(
        "=" * 250
    )


    lines.append(
        "Updated: "
        +
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


    lines.append(
        f"Current Gameweek: "
        f"{current_gameweek or 'N/A'}"
    )


    lines.append(
        f"Players: "
        f"{len(team_players)}"
    )


    lines.append("")


    # =====================================================
    # COLUMN HEADER
    # =====================================================

    lines.append(

        f"{'PLAYER':<28}"

        f"{'POS':<6}"

        f"{'PRICE':<9}"


        # TOTALS

        f"{'PTS':<7}"

        f"{'BONUS':<8}"

        f"{'BPS':<8}"

        f"{'DC':<8}"

        f"{'DC_PTS':<9}"

        f"{'xG':<9}"

        f"{'xA':<9}"

        f"{'xGI':<9}"

        f"{'G':<6}"

        f"{'A':<6}"

        f"{'MIN':<8}"

        f"{'OWN':<9}"

        f"{'FORM':<8}"

        f"{'PPG':<8}"


        # CURRENT GW

        f"{'GW_PTS':<9}"

        f"{'GW_BONUS':<10}"

        f"{'GW_BPS':<9}"

        f"{'GW_DC':<9}"

        f"{'GW_DC_PTS':<12}"

        f"{'GW_G':<8}"

        f"{'GW_A':<8}"

        f"{'GW_MIN':<8}"

    )


    lines.append(
        "-" * 250
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


    # =====================================================
    # TEAM TOTALS
    # =====================================================

    lines.append("")

    lines.append(
        "TEAM TOTALS"
    )

    lines.append(
        "-" * 50
    )


    total_points = sum(
        p["points"]
        for p in team_players
    )


    total_goals = sum(
        p["goals"]
        for p in team_players
    )


    total_assists = sum(
        p["assists"]
        for p in team_players
    )


    total_dc = sum(
        p["dc"]
        for p in team_players
    )


    total_dc_points = sum(
        p["dc_points"]
        for p in team_players
    )


    gw_points = sum(
        p["gw_points"]
        for p in team_players
    )


    gw_bonus = sum(
        p["gw_bonus"]
        for p in team_players
    )


    gw_bps = sum(
        p["gw_bps"]
        for p in team_players
    )


    gw_dc = sum(
        p["gw_dc"]
        for p in team_players
    )


    gw_dc_points = sum(
        p["gw_dc_points"]
        for p in team_players
    )


    gw_goals = sum(
        p["gw_goals"]
        for p in team_players
    )


    gw_assists = sum(
        p["gw_assists"]
        for p in team_players
    )


    gw_minutes = sum(
        p["gw_minutes"]
        for p in team_players
    )


    lines.append(
        f"TOTAL SEASON POINTS: "
        f"{total_points}"
    )


    lines.append(
        f"TOTAL SEASON GOALS: "
        f"{total_goals}"
    )


    lines.append(
        f"TOTAL SEASON ASSISTS: "
        f"{total_assists}"
    )


    lines.append(
        f"TOTAL SEASON DC: "
        f"{total_dc}"
    )


    lines.append(
        f"TOTAL SEASON DC POINTS: "
        f"{total_dc_points}"
    )


    lines.append("")


    lines.append(
        f"GW{current_gameweek} POINTS: "
        f"{gw_points}"
    )


    lines.append(
        f"GW{current_gameweek} BONUS: "
        f"{gw_bonus}"
    )


    lines.append(
        f"GW{current_gameweek} BPS: "
        f"{gw_bps}"
    )


    lines.append(
        f"GW{current_gameweek} DC: "
        f"{gw_dc}"
    )


    lines.append(
        f"GW{current_gameweek} DC POINTS: "
        f"{gw_dc_points}"
    )


    lines.append(
        f"GW{current_gameweek} GOALS: "
        f"{gw_goals}"
    )


    lines.append(
        f"GW{current_gameweek} ASSISTS: "
        f"{gw_assists}"
    )


    lines.append(
        f"GW{current_gameweek} MINUTES: "
        f"{gw_minutes}"
    )


    # =====================================================
    # WRITE FILE
    # =====================================================

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

    print(
        "=========================================="
    )

    print(
        "FPL LIVE STATISTICS UPDATE"
    )

    print(
        "=========================================="
    )


    # =====================================================
    # BOOTSTRAP
    # =====================================================

    print(
        "Downloading latest FPL data..."
    )


    bootstrap = get_bootstrap()


    players = bootstrap.get(
        "elements",
        []
    )


    print(
        f"Received {len(players)} players"
    )


    if not players:

        raise RuntimeError(
            "FPL API returned no players."
        )


    # =====================================================
    # CURRENT GAMEWEEK
    # =====================================================

    current_gameweek = (
        get_current_gameweek(
            bootstrap
        )
    )


    print(
        f"Current Gameweek: "
        f"{current_gameweek}"
    )


    # =====================================================
    # LIVE DATA
    # =====================================================

    live_data = {}


    if current_gameweek:

        print(
            f"Downloading LIVE data "
            f"for GW{current_gameweek}..."
        )


        live_data = get_live_data(
            current_gameweek
        )


        print(
            f"Received live data for "
            f"{len(live_data)} players"
        )


    else:

        print(
            "No current gameweek found."
        )


    # =====================================================
    # BUILD PLAYERS
    # =====================================================

    processed_players = []


    for player in players:

        player_id = player.get(
            "id"
        )


        live_stats = live_data.get(
            player_id,
            {}
        )


        processed = build_player(
            player,
            live_stats
        )


        processed["team"] = player.get(
            "team"
        )


        processed["element_type"] = player.get(
            "element_type"
        )


        processed["second_name"] = player.get(
            "second_name",
            ""
        )


        processed_players.append(
            processed
        )


    # =====================================================
    # WRITE ALL TEAMS
    # =====================================================

    for team_id, team_name in TEAM_NAMES.items():

        write_team_file(
            team_id,
            team_name,
            processed_players,
            current_gameweek
        )


    # =====================================================
    # DONE
    # =====================================================

    print("")

    print(
        "=========================================="
    )

    print(
        "FPL UPDATE COMPLETED SUCCESSFULLY"
    )

    print(
        "=========================================="
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
