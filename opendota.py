import constants
import json
import os
import requests
import time

#############################
# Script for getting and downloading the match info from OpenDota API.
# This could also be integrated to the other scripts, but the intermediary
# get_ingame_ids.py is very slow due to rate limits, so keep this separate for this purpose.
#############################

with open(f"{constants.LOG_DIRECTORY}/dota_match_ids.txt", "r") as file:
    dota_match_ids = [line.rstrip() for line in file]

if not os.path.isdir(constants.MATCH_DIRECTORY):
    os.mkdir(constants.MATCH_DIRECTORY)

outliers = []
rejected = []
for i, match_id in enumerate(dota_match_ids):
    if i % 10 == 0:
        print(i)

    # Not all the matches are available, and the API returns 404 for unavailable ones.
    r = requests.get(f"https://api.opendota.com/api/matches/{match_id}")
    if r.status_code != 200:
        if r.status_code == 404:
            rejected.append(str(match_id) + "\n")
        # The API should only return 200 or 404
        else:
            print(
                f"The API returned an unexpected status code {r.status_code}"
                f"for match ID {match_id}."
            )
            outliers.append({match_id: r.status_code})
    else:
        # Save match data to json for parsing later on
        data = r.json()
        with open(f"{constants.MATCH_DIRECTORY}/{match_id}.json", "w") as f:
            json.dump(data, f, indent=4)
    time.sleep(1.0)  # abide by rate limits

# Save also matches that were not found and outliers (where API returned unexpected status code)
with open(f"{constants.LOG_DIRECTORY}/opendota_404.txt", "w") as f:
    f.writelines(rejected)
with open(f"{constants.LOG_DIRECTORY}/opendota_outliers.json", "w") as f:
    json.dump(outliers, f, indent=4)

print("Program ran successfully.")
