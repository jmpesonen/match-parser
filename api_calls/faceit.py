import constants
import os
import requests
import sys
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def write_to_files(list_of_ids, list_of_outliers, filename):
    ids = [x + "\n" for x in list_of_ids]
    with open(f"{constants.LOG_DIRECTORY}/{filename}.txt", "w") as f:
        f.writelines(ids)

    outs = [x + "\n" for x in list_of_outliers]
    with open(f"{constants.LOG_DIRECTORY}/{filename}_outliers.txt", "w") as f:
        f.writelines(outs)


#############################
# Gets all the matches in a given FACEIT hub.
#############################
def get_faceit_matches(cutoff):
    if not os.path.isdir(constants.LOG_DIRECTORY):
        os.makedirs(constants.LOG_DIRECTORY)

    # Prepare variables for the paginated API
    offset = 0
    limit = 50
    faceit_match_ids = []
    outliers = []
    all_fetched = False

    # The API might randomly give some temporary error; utilize Retry to solve it.
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 503],
    )
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=retry_strategy))

    while not all_fetched:
        print(offset)

        payload = {
            "offset": offset,
            "limit": limit,
        }
        r = s.request(
            method="GET",
            url=f"https://open.faceit.com/data/v4/hubs/{constants.HUB_ID}/matches",
            params=payload,
            headers={"Authorization": f"Bearer {constants.APP_API_KEY}"},
        )

        # If the API still returned an error even after the retries (not supposed to happen),
        # write found IDs to a file and exit the program
        if r.status_code != 200:
            print(
                f"The API returned an unexpected error code: {r.status_code} at offset {offset}."
                f"The latest match ID was {faceit_match_ids[-1] if len(faceit_match_ids) > 0 else 'not found'}."
                f"Writing the collected match IDs to a file and exiting the program."
            )
            write_to_files(faceit_match_ids, outliers, "faceit_match_ids")
            s.close()
            sys.exit(1)

        data = r.json()
        for match in data["items"]:
            # All matches SHOULD be either finished or cancelled, check out for weird outliers
            if (
                match["status"].lower() != "finished"
                and match["status"].lower() != "cancelled"
            ):
                outliers.append(f"{match['match_id']} {match['status']}")

            elif "started_at" in match and match["status"].lower() == "finished":
                if cutoff is None or match["started_at"] > cutoff:
                    faceit_match_ids.append(str(match["match_id"]))
                else:
                    all_fetched = True
                    break  # stop the unnecessary looping of the returned data

        offset = data["end"]
        if len(data["items"]) < limit:
            all_fetched = True
        time.sleep(1.0)  # abide by rate limits
    s.close()
    write_to_files(faceit_match_ids, outliers, "faceit_match_ids")

    print("get_faceit_matches ran successfully.")
    return faceit_match_ids


#############################
# Turns FACEIT match IDs into Dota in-game match IDs by querying a different API.
#############################
def get_ingame_ids(faceit_match_ids):
    # All these steps in get_matches can be ran one at a time, but if done so,
    # get the match IDs from a file instead (as they can't then be provided as parameters).
    if faceit_match_ids is None or len(faceit_match_ids) == 0:
        with open(f"{constants.LOG_DIRECTORY}/faceit_match_ids.txt", "r") as file:
            faceit_match_ids = [line.rstrip() for line in file]

    # The API might randomly give some temporary error; utilize Retry to solve it.
    # Queried info is not available in the external API. This part of the API is internal,
    # not documented, and subject to change; thus, retry with any status code that is at least 400.
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[x for x in requests.status_codes._codes if x >= 400],
    )
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=retry_strategy))

    dota_match_ids = []
    outliers = []
    for i, match in enumerate(faceit_match_ids):
        if i % 10 == 0:
            print(i)  # lazy progress bar

        r = s.request(
            method="GET",
            url=f"https://api.faceit.com/match/v2/match/{match}",
            headers={"Authorization": f"Bearer {constants.PERSONAL_API_KEY}"},
        )

        # If the API still returned an error even after the retries (not supposed to happen),
        # write found IDs to a file and exit the program
        if r.status_code != 200:
            print(
                f"The API returned an unexpected error code: {r.status_code}."
                f"The latest queried match ID was {match}."
                f"Writing the collected Dota match IDs to a file and exiting the program."
            )
            write_to_files(faceit_match_ids, outliers, "dota_match_ids")
            s.close()
            sys.exit(1)

        data = r.json()
        data = data["payload"]
        if "clientCustom" in data and "dota_match_id" in data["clientCustom"]:
            dota_match_ids.append(str(data["clientCustom"]["dota_match_id"]))
        else:
            # Check out for outliers (should be empty)
            outliers.append(match)

        time.sleep(3.0)  # abide by strict rate limits to this internal API
    s.close()
    write_to_files(faceit_match_ids, outliers, "dota_match_ids")

    print("get_ingame_ids ran successfully.")
    return dota_match_ids
