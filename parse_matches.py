import constants
import json
import numpy as np
import os
import pandas as pd
import requests
import sys

# Fetch the mapping for hero IDs and names.
r = requests.get("https://api.opendota.com/api/constants/heroes")
if r.status_code != 200:
    print(
        f"Could not fetch hero data due to unknown error {r.status_code}."
        "Try running this script again."
    )
    sys.exit(1)
hero_constants = r.json()

# This has the names for all of the downloaded match replay files.
match_files = os.listdir(constants.MATCH_DIRECTORY)

# Represented by integer bitmasks, keep count by splitting binary representation to digits.
# Even though they are represented by 8-bit and 16-bit binaries, respectively only 6 and 11 of
# those digits are used and thus meaningful. See below for more explanation.
barracks_dire_counter = [0] * 6
barracks_radiant_counter = [0] * 6

towers_dire_counter = [0] * 11
towers_radiant_counter = [0] * 11

# These are used to construct the DataFrames later on
dataframe_rows = []
picks_and_bans_dict = {}

for file in match_files:
    with open(f"{constants.MATCH_DIRECTORY}/{file}", "r") as f:
        match_json = json.load(f)

    # Keep count of the destroyed buildings. 1 means building stands, 0 means building has fallen.
    # Convert integer bitmask to binary, and split the digits into list elements, and then sum them
    # together element-wise. This allows us to count which buildings are the most destroyed ones,
    # since a certain list element corresponds to a certain building.

    # Barracks order: (2x NOT USED,) BOT RANGED, BOT MELEE, MID RANGED, MID MELEE, TOP RANGED, TOP MELEE
    barracks_dire = [int(x) for x in format(match_json["barracks_status_dire"], "06b")]
    barracks_radiant = [
        int(x) for x in format(match_json["barracks_status_radiant"], "06b")
    ]

    barracks_dire_counter = [sum(x) for x in zip(barracks_dire_counter, barracks_dire)]
    barracks_radiant_counter = [
        sum(x) for x in zip(barracks_radiant_counter, barracks_radiant)
    ]

    # Towers order: (5x NOT USED,) BOT TIER 4, TOP TIER 4, BOT TIER 3, BOT TIER 2, BOT TIER 1,
    #               MID TIER 3, MID TIER 2, MID TIER 1, TOP TIER 3, TOP TIER 2, TOP TIER 1
    towers_dire = [int(x) for x in format(match_json["tower_status_dire"], "011b")]
    towers_radiant = [
        int(x) for x in format(match_json["tower_status_radiant"], "011b")
    ]

    towers_dire_counter = [sum(x) for x in zip(towers_dire_counter, towers_dire)]
    towers_radiant_counter = [
        sum(x) for x in zip(towers_radiant_counter, towers_radiant)
    ]

    #############################
    # GO THROUGH PICKS AND BANS
    # Picks and their winrates could be deduced from the other DataFrame,
    # but this allows for more flexibility with bans and possibly pick orders as well.
    #############################
    for pickban in match_json["picks_bans"]:
        hero_id = str(pickban["hero_id"])

        # Initialize hero if not in dict already
        if hero_id not in picks_and_bans_dict:
            picks_and_bans_dict[hero_id] = {
                "hero_id": hero_id,
                "hero_name": hero_constants[hero_id]["localized_name"],
                "picked_games": 0,
                "picked_wins": 0,
                "banned_games": 0,
                "banned_wins": 0,
            }

        # If the hero was picked, add to pick statistics. Check if the picking team won.
        # Team 0 = radiant, 1 = dire
        if pickban["is_pick"]:
            picks_and_bans_dict[hero_id]["picked_games"] += 1

            if (match_json["radiant_win"] and pickban["team"] == 0) or (
                not match_json["radiant_win"] and pickban["team"] == 1
            ):
                picks_and_bans_dict[hero_id]["picked_wins"] += 1

        # If the hero was banned instead, add to ban statistics. Check if the banning team won.
        elif not pickban["is_pick"]:
            picks_and_bans_dict[hero_id]["banned_games"] += 1

            if (match_json["radiant_win"] and pickban["team"] == 0) or (
                not match_json["radiant_win"] and pickban["team"] == 1
            ):
                picks_and_bans_dict[hero_id]["banned_wins"] += 1

    # Go through players
    for player in match_json["players"]:
        # Define keys which to keep from this huge object, import them from another file due to size.
        # Add hero name manually.
        player_keys = constants.PLAYER_KEYS
        player_dict = {k: v for k, v in player.items() if k in player_keys}
        player_dict["hero_name"] = hero_constants[str(player["hero_id"])][
            "localized_name"
        ]
        dataframe_rows.append(player_dict)


#############################
# QUERYING THE INFORMATION
# This DataFrame holds all player performances: a single row is a single player performance in a match.
# 10 players in a match -> amount of rows = 10 * matches
# Printing into console works fine for the purposes of this script;
# this could be aggregated into some file as well.
#############################
player_df = pd.DataFrame(dataframe_rows)

# Print total sums of different stats
for c in constants.TOTAL_STATS:
    print(f"Total {c}: {player_df[c].sum()}")

# Print 3 longest and shortest matches (in seconds) and their IDs
print(
    "Longest matches:\n",
    player_df[["duration", "match_id"]]
    .drop_duplicates()
    .sort_values(by="duration", ascending=False)
    .head(3),
)

print(
    "Shortest matches:\n",
    player_df[["duration", "match_id"]]
    .drop_duplicates()
    .sort_values(by="duration", ascending=True)
    .head(3),
)

# Can't ensure all players have the same or recognizable profile name through all the games,
# so just check the profiles manually for the most known nickname with the given ID.
print("Players with most games:")
print(player_df["account_id"].value_counts().head(3))

# Radiant/dire winrate
print(
    player_df[["match_id", "radiant_win"]]
    .drop_duplicates()["radiant_win"]
    .value_counts()
)

# Print the records and the players who got them for each stat with some extra info
for c in constants.HIGHEST_STATS:
    print(
        f"Most {c}:\n",
        player_df.sort_values(by=c, ascending=False).head(3)[
            [c, "hero_id", "hero_name", "account_id", "personaname", "match_id"]
        ],
    )


#############################
# Pick and ban stats of different characters
# Prepare dictionary into dataframe and add columns for winrates
#############################
pb_df = pd.DataFrame(list(picks_and_bans_dict.values()))

# Not everyone might be picked/banned; avoid dividing by zero
pb_df["picked_winrate"] = np.where(
    pb_df["picked_games"] == 0,
    0.0,
    round(pb_df["picked_wins"] / pb_df["picked_games"], 2),
)
pb_df["banned_winrate"] = np.where(
    pb_df["banned_games"] == 0,
    0.0,
    round(pb_df["banned_wins"] / pb_df["banned_games"], 2),
)

# This is a rather large print so save the pick/ban DF to a different file for easier distribution
pb_output = pb_df.drop(columns=["hero_id"]).sort_values(by="hero_name").to_string(index=False)

with open(f"{constants.LOG_DIRECTORY}/picks_and_bans.txt", "w") as f:
    f.write(pb_output)

# Print the characters with highest & lowest amount of games & winrate
# To avoid unnecessary copy/paste change column names when dealing with bans instead of picks
columns = ["picked_games", "picked_winrate", "banned_games", "banned_winrate"]
for col in columns:
    column_names = (
        ["picked_games", "picked_winrate"]
        if "picked" in col
        else ["banned_games", "banned_winrate"]
    )
    print(
        f"Highest {col}:\n",
        pb_df.sort_values(by=col, ascending=False).head(5)[
            ["hero_id", "hero_name", column_names[0], column_names[1]]
        ],
    )
    print(
        f"Lowest {col}:\n",
        pb_df.sort_values(by=col, ascending=True).head(5)[
            ["hero_id", "hero_name", column_names[0], column_names[1]]
        ],
    )

print("Barracks dire: ", barracks_dire_counter)
print("Barracks radiant: ", barracks_radiant_counter)
print("Towers dire: ", towers_dire_counter)
print("Towers radiant: ", towers_radiant_counter)

print("Program ran successfully.")
