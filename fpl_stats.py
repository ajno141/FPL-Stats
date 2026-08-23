import requests
import os
from datetime import datetime


# ============================================================
# SETTINGS
# ============================================================

OUTPUT_DIR = "FPL_STATS"

API_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"


# ============================================================
# CREATE OUTPUT FOLDER
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# DOWNLOAD FPL DATA
# ============================================================

print("Downloading FPL data...")

response = requests.get(
    API_URL,
    timeout=30
)

response.raise_for_status()

data = response.json()

print("FPL data downloaded successfully.")


# ============================================================
# BASIC DATA
# ============================================================

players = data["elements"]
teams = data["teams"]
positions = data["element_types"]


# ============================================================
# TEAM NAMES
# ============================================================

team_names = {}

for team in teams:
    team_names[team["id"]] = team["name"]


# ============================================================
# POSITION NAMES
# ============================================================

position_names = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD"
}


# ============================================================
# TEAM ORDER
# ============================================================

team_order = [
    team["id"]
    for team in teams
]


# ============================================================
# FORMAT HELPERS
# ============================================================

def safe_number(value, default=0):

    if value is None:
        return default

    try:
        return float(value)
    except:
        return default


def format_number(value):

    value = safe_number(value)

    if value.is_integer():
        return str(int(value))

    return f"{value:.2f}"


def format_price(value):

    value = safe_number(value)

    return f"£{value:.1f}m"


def format_ownership(value):

    value = safe_number(value)

    return f"{value:.1f}%"


# ============================================================
# PLAYER DATA
# ============================================================

processed_players = []


for player in players:

    player_id = player["id"]

    first_name = player.get(
        "first_name",
        ""
    ).strip()

    second_name = player.get(
        "second_name",
        ""
    ).strip()

    # IMPORTANT:
    # Keep the complete player name.
    # This fixes names such as:
    # De Kuyper
    # Van de Ven
    # etc.

    full_name = (
        first_name + " " + second_name
    ).strip()


    team_id = player.get(
        "team"
    )

    position_id = player.get(
        "element_type"
    )


    team_name = team_names.get(
        team_id,
        "Unknown"
    )


    position = position_names.get(
        position_id,
        "UNK"
    )


    # ========================================================
    # STATISTICS
    # ========================================================

    stats = {

        "id":
        player_id,

        "name":
        full_name,

        "first_name":
        first_name,

        "second_name":
        second_name,

        "team_id":
        team_id,

        "team":
        team_name,

        "position":
        position,

        "price":
        safe_number(
            player.get(
                "now_cost"
            )
        ) / 10,

        "points":
        safe_number(
            player.get(
                "total_points"
            )
        ),

        "bonus":
        safe_number(
            player.get(
                "bonus"
            )
        ),

        "bps":
        safe_number(
            player.get(
                "bps"
            )
        ),

        "defensive_contribution":
        safe_number(
            player.get(
                "defensive_contribution"
            )
        ),

        "xg":
        safe_number(
            player.get(
                "expected_goals"
            )
        ),

        "xa":
        safe_number(
            player.get(
                "expected_assists"
            )
        ),

        "xgi":
        safe_number(
            player.get(
                "expected_goal_involvements"
            )
        ),

        "goals":
        safe_number(
            player.get(
                "goals_scored"
            )
        ),

        "assists":
        safe_number(
            player.get(
                "assists"
            )
        ),

        "minutes":
        safe_number(
            player.get(
                "minutes"
            )
        ),

        "clean_sheets":
        safe_number(
            player.get(
                "clean_sheets"
            )
        ),

        "saves":
        safe_number(
            player.get(
                "saves"
            )
        ),

        "yellow_cards":
        safe_number(
            player.get(
                "yellow_cards"
            )
        ),

        "red_cards":
        safe_number(
            player.get(
                "red_cards"
            )
        ),

        "ownership":
        safe_number(
            player.get(
                "selected_by_percent"
            )
        ),

        "transfers_in":
        safe_number(
            player.get(
                "transfers_in"
            )
        ),

        "transfers_out":
        safe_number(
            player.get(
                "transfers_out"
            )
        ),

        "form":
        safe_number(
            player.get(
                "form"
            )
        ),

        "points_per_game":
        safe_number(
            player.get(
                "points_per_game"
            )
        )

    }


    processed_players.append(
        stats
    )


# ============================================================
# GROUP PLAYERS BY TEAM
# ============================================================

players_by_team = {}


for player in processed_players:

    team_id = player["team_id"]

    if team_id not in players_by_team:
        players_by_team[team_id] = []

    players_by_team[
        team_id
    ].append(player)


# ============================================================
# POSITION ORDER
# ============================================================

position_order = {
    "GK": 1,
    "DEF": 2,
    "MID": 3,
    "FWD": 4
}


# ============================================================
# GENERATE TEAM FILES
# ============================================================

updated_time = datetime.now().strftime(
    "%Y-%m-%d %H:%M:%S"
)


for team_id in team_order:

    team_name = team_names.get(
        team_id,
        "Unknown"
    )


    team_players = players_by_team.get(
        team_id,
        []
    )


    # Sort:
    # GK
    # DEF
    # MID
    # FWD
    #
    # then alphabetically

    team_players.sort(
        key=lambda p: (
            position_order.get(
                p["position"],
                99
            ),
            p["name"].lower()
        )
    )


    filename = (
        team_name
        .replace(" ", "_")
        .replace("/", "_")
        + ".txt"
    )


    filepath = os.path.join(
        OUTPUT_DIR,
        filename
    )


    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:


        # ====================================================
        # HEADER
        # ====================================================

        file.write(
            f"{team_name.upper()}\n"
        )

        file.write(
            "=" * 145
            + "\n"
        )

        file.write(
            f"Updated: {updated_time}\n"
        )

        file.write(
            f"Players: {len(team_players)}\n\n"
        )


        # ====================================================
        # TABLE HEADER
        # ====================================================

        header = (

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


        file.write(
            header + "\n"
        )

        file.write(
            "-" * 145
            + "\n"
        )


        # ====================================================
        # PLAYERS
        # ====================================================

        for p in team_players:

            # ------------------------------------------------
            # IMPORTANT:
            #
            # PLAYER name is allowed to contain spaces.
            #
            # Example:
            #
            # De Kuyper
            # Van de Ven
            # Morgan Rogers
            #
            # Nothing gets split here.
            # ------------------------------------------------

            row = (

                f"{p['name']:<28}"
                f"{p['position']:<6}"
                f"{format_price(p['price']):<9}"
                f"{format_number(p['points']):<7}"
                f"{format_number(p['bonus']):<8}"
                f"{format_number(p['bps']):<8}"
                f"{format_number(p['defensive_contribution']):<8}"
                f"{format_number(p['xg']):<9}"
                f"{format_number(p['xa']):<9}"
                f"{format_number(p['xgi']):<9}"
                f"{format_number(p['goals']):<6}"
                f"{format_number(p['assists']):<6}"
                f"{format_number(p['minutes']):<8}"
                f"{format_ownership(p['ownership']):<9}"
                f"{format_number(p['form']):<8}"
                f"{format_number(p['points_per_game']):<8}"
            )


            file.write(
                row + "\n"
            )


        # ====================================================
        # LEGEND
        # ====================================================

        file.write("\n")

        file.write(
            "=" * 145
            + "\n"
        )

        file.write(
            "STATISTICS LEGEND\n"
        )

        file.write(
            "PTS = FPL Points | "
            "BONUS = Bonus Points | "
            "BPS = Bonus Point System | "
            "DC = Defensive Contribution | "
            "xG = Expected Goals | "
            "xA = Expected Assists | "
            "xGI = Expected Goal Involvements\n"
        )


# ============================================================
# ALSO CREATE COMPLETE ALL PLAYERS FILE
# ============================================================

all_players_file = os.path.join(
    OUTPUT_DIR,
    "ALL_PLAYERS.txt"
)


all_players = sorted(
    processed_players,
    key=lambda p: (
        team_order.index(
            p["team_id"]
        )
        if p["team_id"] in team_order
        else 999,

        position_order.get(
            p["position"],
            99
        ),

        p["name"].lower()
    )
)


with open(
    all_players_file,
    "w",
    encoding="utf-8"
) as file:


    file.write(
        "FPL ALL PLAYERS\n"
    )

    file.write(
        "=" * 145
        + "\n"
    )

    file.write(
        f"Updated: {updated_time}\n"
    )

    file.write(
        f"Total players: {len(all_players)}\n\n"
    )


    header = (

        f"{'PLAYER':<28}"
        f"{'TEAM':<25}"
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
    )


    file.write(
        header + "\n"
    )

    file.write(
        "-" * 145
        + "\n"
    )


    for p in all_players:

        row = (

            f"{p['name']:<28}"
            f"{p['team']:<25}"
            f"{p['position']:<6}"
            f"{format_price(p['price']):<9}"
            f"{format_number(p['points']):<7}"
            f"{format_number(p['bonus']):<8}"
            f"{format_number(p['bps']):<8}"
            f"{format_number(p['defensive_contribution']):<8}"
            f"{format_number(p['xg']):<9}"
            f"{format_number(p['xa']):<9}"
            f"{format_number(p['xgi']):<9}"
            f"{format_number(p['goals']):<6}"
            f"{format_number(p['assists']):<6}"
            f"{format_number(p['minutes']):<8}"
            f"{format_ownership(p['ownership']):<9}"
        )


        file.write(
            row + "\n"
        )


print()
print("=" * 60)
print("FPL STATISTICS UPDATED SUCCESSFULLY")
print("=" * 60)
print(f"Players processed: {len(processed_players)}")
print(f"Files saved in: {OUTPUT_DIR}")
print(f"Updated: {updated_time}")
print("=" * 60)
