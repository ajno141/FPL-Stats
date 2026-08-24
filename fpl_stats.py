import requests
import os
from datetime import datetime, timezone

BASE_URL = "https://fantasy.premierleague.com/api"

OUTPUT_DIR = "FPL_STATS"

TEAM_NAMES = {
    "Arsenal": "Arsenal",
    "Aston_Villa": "Aston Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton",
    "Coventry_City": "Coventry City",
    "Chelsea": "Chelsea",
    "Crystal_Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Hull_City": "Hull City",
    "Ipswich_Town": "Ipswich Town",
    "Leeds": "Leeds",
    "Liverpool": "Liverpool",
    "Manchester_City": "Manchester City",
    "Manchester_United": "Manchester United",
    "Newcastle_United": "Newcastle United",
    "Nottingham_Forest": "Nottingham Forest",
    "Sunderland": "Sunderland",
    "Tottenham_Hotspur": "Tottenham Hotspur",
}

POSITION_NAMES = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}


def get_data():

    url = f"{BASE_URL}/bootstrap-static/"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def get_live_data(gameweek):

    url = (
        f"{BASE_URL}/event/"
        f"{gameweek}/live/"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    live_players = {}

    for player in data.get(
        "elements",
        []
    ):

        player_id = player.get("id")

        if player_id is not None:

            live_players[player_id] = (
                player.get(
                    "stats",
                    {}
                )
            )

    return live_players


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


def live_value(
    player,
    live_players,
    stat_name
):

    player_id = player.get("id")

    live_stats = live_players.get(
        player_id,
        {}
    )

    if stat_name in live_stats:

        return safe_number(
            live_stats.get(
                stat_name
            )
        )

    return safe_number(
        player.get(
            stat_name,
            0
        )
    )


def player_line(
    player,
    live_players
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
        f"{first_name} "
        f"{second_name}"
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

    # ==========================
    # LIVE STATISTIKA
    # ==========================

    pts = live_value(
        player,
        live_players,
        "total_points"
    )

    bonus = live_value(
        player,
        live_players,
        "bonus"
    )

    bps = live_value(
        player,
        live_players,
        "bps"
    )

    defensive_contribution = live_value(
        player,
        live_players,
        "defensive_contribution"
    )

    goals = live_value(
        player,
        live_players,
        "goals_scored"
    )

    assists = live_value(
        player,
        live_players,
        "assists"
    )

    minutes = live_value(
        player,
        live_players,
        "minutes"
    )

    # ==========================
    # OSTALE STATISTIKE
    # ==========================

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
        f"{pts:<7}"
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


def write_team_file(
    team_id,
    team_name,
    display_name,
    players,
    live_players,
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

    lines.append(
        display_name.upper()
    )

    lines.append(
        "=" * 145
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
        f"{'PTS':<7}"
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
        "-" * 145
    )

    for player in team_players:

        lines.append(
            player_line(
                player,
                live_players
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
        f"Updated {display_name}: "
        f"{len(team_players)} players"
    )


def main():

    print("=" * 70)
    print("FPL LIVE STATISTICS UPDATE")
    print("=" * 70)

    print(
        "Downloading latest FPL data..."
    )

    data = get_data()

    players = data.get(
        "elements",
        []
    )

    teams = data.get(
        "teams",
        []
    )

    events = data.get(
        "events",
        []
    )

    if not players:

        raise RuntimeError(
            "FPL API returned no players."
        )

    print(
        f"Received {len(players)} players"
    )

    # ==========================
    # PRONAĐI ID KLUBOVA
    # ==========================

    team_ids = {}

    for api_team in teams:

        api_name = api_team.get(
            "name",
            ""
        )

        api_id = api_team.get(
            "id"
        )

        for file_name, display_name in TEAM_NAMES.items():

            if (
                api_name.lower()
                == display_name.lower()
            ):

                team_ids[file_name] = api_id

    # ==========================
    # PRONAĐI AKTUELNI GW
    # ==========================

    current_gameweek = None

    for event in events:

        if event.get(
            "is_current"
        ):

            current_gameweek = event.get(
                "id"
            )

            break

    if current_gameweek is None:

        for event in events:

            if event.get(
                "is_next"
            ):

                current_gameweek = event.get(
                    "id"
                )

                break

    if current_gameweek is None:

        started = [
            event
            for event in events
            if event.get(
                "is_started"
            )
        ]

        if started:

            current_gameweek = max(
                event.get("id")
                for event in started
            )

    if current_gameweek is None:

        raise RuntimeError(
            "Could not determine "
            "current gameweek."
        )

    print(
        f"Current gameweek: "
        f"GW{current_gameweek}"
    )

    # ==========================
    # LIVE PODACI
    # ==========================

    print(
        "Downloading LIVE statistics..."
    )

    try:

        live_players = get_live_data(
            current_gameweek
        )

        print(
            f"Live data received for "
            f"{len(live_players)} players."
        )

    except Exception as error:

        print(
            "WARNING: Live data could "
            "not be loaded."
        )

        print(error)

        live_players = {}

    # ==========================
    # UPIS SVIH KLUBOVA
    # ==========================

    for file_name, display_name in TEAM_NAMES.items():

        team_id = team_ids.get(
            file_name
        )

        if team_id is None:

            print(
                f"WARNING: {display_name} "
                f"does not exist in the "
                f"current FPL API."
            )

            continue

        write_team_file(
            team_id,
            file_name,
            display_name,
            players,
            live_players,
            current_gameweek
        )

    print("")
    print(
        "FPL update completed successfully."
    )


if __name__ == "__main__":
    main()
