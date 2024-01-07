import constants
import json
import os
import requests
import time
from requests.adapters import HTTPAdapter


#############################
# Downloads the available match infos as JSONs from OpenDota API.
#############################
def get_matches_from_opendota(dota_match_ids):
    # All these steps in get_matches can be ran one at a time, but if done so,
    # get the match IDs from a file instead (as they can't then be provided as parameters).
    if dota_match_ids is None or len(dota_match_ids) == 0:
        with open(f"{constants.LOG_DIRECTORY}/dota_match_ids.txt", "r") as file:
            dota_match_ids = [line.rstrip() for line in file]

    if not os.path.isdir(constants.MATCH_DIRECTORY):
        os.makedirs(constants.MATCH_DIRECTORY)

    outliers = []
    rejected = []
    s = requests.Session()
    s.mount("https://", HTTPAdapter())

    for i, match_id in enumerate(dota_match_ids):
        if i % 10 == 0:
            print(i)

        # Not all the matches are available, and the API returns 404 for unavailable ones.
        r = s.request(
            method="GET",
            url=f"https://api.opendota.com/api/matches/{match_id}",
        )
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

    print("get_matches_from_opendota ran successfully.")
