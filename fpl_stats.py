import requests
import os
from datetime import datetime, timezone

BASE_URL = "https://fantasy.premierleague.com/api"

OUTPUT_DIR = "FPL_STATS"

TEAM_NAMES = {
    1: "Arsenal",
    2: "Aston_Villa",
    3: "Bournemouth",
    4: "Brentford",
    5: "Brighton",
    6: "Burnley",
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
    19: "West_Ham",
    20: "Wolverhampton_Wanderers",
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
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


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
        return f"{value:.2f}".rstrip("0").rstrip(".")

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


def player_line(player):
    first_name = player.get("first_name", "")
    second_name = player.get("second_name", "")

    name = f"{first_name} {second_name}".strip()

    position = POSITION_NAMES.get(
        player.get("element_type"),
        "UNK"
    )

    price = format_price(
        player.get("now_cost", 0)
    )

    pts = safe_number(
        player.get("event_points", 0)
    )

    bonus = safe_number(
        player.get("bonus", 0)
    )

    bps = safe_number(
        player.get("bps", 0)
    )

    defensive_contribution = safe_number(
        player.get("defensive_contribution", 0)
    )

    xg = safe_number(
        player.get("expected_goals", 0)
    )

    xa = safe_number(
        player.get("expected_assists", 0)
    )

    xgi = safe_number(
        player.get("expected_goal_involvements", 0)
    )

    goals = safe_number(
        player.get("goals_scored", 0)
    )

    assists = safe_number(
        player.get("assists", 0)
    )

    minutes = safe_number(
        player.get("minutes", 0)
    )

    ownership = format_ownership(
        player.get("selected_by_percent", 0)
    )

    form = safe_number(
        player.get("form", 0)
    )

    ppg = safe_number(
        player.get("points_per_game", 0)
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


def write_team_file(team_id, team_name, players):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

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
            p.get("element_type", 0),
            p.get("second_name", "")
        )
    )

    now = datetime.now(
        timezone.utc
    ).astimezone()

    lines = []

    lines.append(
        team_name.replace("_", " ").upper()
    )

    lines.append(
        "=" * 145
    )

    lines.append(
        f"Updated: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    lines.append(
        f"Players: {len(team_players)}"
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
            player_line(player)
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


def main():
    print("Downloading latest FPL data...")

    data = get_data()

    players = data.get(
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

    for team_id, team_name in TEAM_NAMES.items():
        write_team_file(
            team_id,
            team_name,
            players
        )

    print("")
    print("FPL update completed successfully.")


if __name__ == "__main__":
    main()
