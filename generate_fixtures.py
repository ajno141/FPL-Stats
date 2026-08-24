import requests
import json

BASE_URL = "https://fantasy.premierleague.com/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


def get_json(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def main():

    print("Downloading FPL teams...")

    bootstrap = get_json(
        f"{BASE_URL}/bootstrap-static/"
    )

    teams = {}

    for team in bootstrap.get("teams", []):

        teams[team["id"]] = team["name"]


    print(
        f"Found {len(teams)} teams."
    )


    print("Downloading fixtures...")

    fixtures = get_json(
        f"{BASE_URL}/fixtures/"
    )


    result = []


    for fixture in fixtures:

        gameweek = fixture.get("event")

        if gameweek is None:
            continue


        home_id = fixture.get("team_h")
        away_id = fixture.get("team_a")


        home = teams.get(
            home_id,
            "Unknown"
        )

        away = teams.get(
            away_id,
            "Unknown"
        )


        kickoff = fixture.get(
            "kickoff_time"
        )


        result.append({

            "gameweek": gameweek,

            "date": (
                kickoff[:10]
                if kickoff
                else None
            ),

            "time": (
                kickoff[11:16]
                if kickoff
                else None
            ),

            "kickoff_time": kickoff,

            "home": home,

            "away": away,

            "home_id": home_id,

            "away_id": away_id

        })


    result.sort(
        key=lambda x: (
            x["gameweek"],
            x["kickoff_time"] or ""
        )
    )


    with open(
        "fixtures.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False
        )


    print(
        f"Saved {len(result)} fixtures to fixtures.json"
    )


if __name__ == "__main__":
    main()
