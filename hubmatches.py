import argparse
import constants
import os
import requests
import sys
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

#############################
# Script for getting all the matches in a FACEIT hub.
#############################

# Add positional command line argument for cutoff date (fetch only matches played after the given date).
# The normal usage is to run this script for a single season after it ends while there is a break between
# the seasons. Fetching all matches can be achieved by omitting the argument when running the script.
parser = argparse.ArgumentParser()
parser.add_argument("date", nargs="?")  # YYYY/MM/DD format
args = parser.parse_args()
try:
    cutoff = int(datetime.strptime(args.date, "%Y/%m/%d").timestamp())
    print(
        f"Cutoff date set as: "
        f"{datetime.strftime(datetime.strptime(args.date, '%Y/%m/%d'), '%Y/%m/%d')}"
    )
# Arg was omitted; fetch all matches
except TypeError:
    print("Argument for cutoff date was not given; fetching all matches.")
    cutoff = None
except ValueError:
    print("The given date is in invalid format; please submit it in YYYY/MM/DD format.")
    sys.exit(1)

if not os.path.isdir(constants.LOG_DIRECTORY):
    os.mkdir(constants.LOG_DIRECTORY)

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

        with open(f"{constants.LOG_DIRECTORY}/faceit_match_ids.txt", "w") as f:
            f.writelines(faceit_match_ids)
        with open(f"{constants.LOG_DIRECTORY}/faceit_match_ids_outliers.txt", "w") as f:
            f.writelines(outliers)
        s.close()
        sys.exit(1)

    data = r.json()
    for match in data["items"]:
        # All matches SHOULD be either finished or cancelled, check out for weird outliers
        if (
            match["status"].lower() != "finished"
            and match["status"].lower() != "cancelled"
        ):
            outliers.append((match["match_id"], match["status"]))

        elif "started_at" in match and match["status"].lower() == "finished":
            if cutoff is None or match["started_at"] > cutoff:
                faceit_match_ids.append(str(match["match_id"]) + "\n")
            else:
                all_fetched = True
                break  # stop the unnecessary looping of the returned data

    offset = data["end"]
    if len(data["items"]) < limit:
        all_fetched = True
    time.sleep(1.0)  # abide by rate limits
s.close()

with open(f"{constants.LOG_DIRECTORY}/faceit_match_ids.txt", "w") as f:
    f.writelines(faceit_match_ids)

with open(f"{constants.LOG_DIRECTORY}/faceit_match_ids_outliers.txt", "w") as f:
    f.writelines(outliers)

print("Program ran successfully.")
