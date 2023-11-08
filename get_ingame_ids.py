import constants
import requests
import sys
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

#############################
# Script for getting Dota in-game match IDs from the FACEIT match IDs.
# This could be integrated into hubmatches.py, but this has a rather long running time
# due to strict rate limits, so run this separately (makes the script easier to run in chunks).
#############################

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

        with open(f"{constants.LOG_DIRECTORY}/dota_match_ids.txt", "w") as f:
            f.writelines(dota_match_ids)
        with open(f"{constants.LOG_DIRECTORY}/dota_match_ids_outliers.txt", "w") as f:
            f.writelines(outliers)
        s.close()
        sys.exit(1)

    data = r.json()
    data = data["payload"]
    if "clientCustom" in data and "dota_match_id" in data["clientCustom"]:
        dota_match_ids.append(str(data["clientCustom"]["dota_match_id"]) + "\n")
    else:
        # Check out for outliers (should be empty)
        outliers.append(match)

    time.sleep(3.0)  # abide by strict rate limits to this internal API
s.close()

with open(f"{constants.LOG_DIRECTORY}/dota_match_ids.txt", "w") as f:
    f.writelines(dota_match_ids)

with open(f"{constants.LOG_DIRECTORY}/dota_match_ids_outliers.txt", "w") as f:
    f.writelines(outliers)

print("Program ran successfully.")
