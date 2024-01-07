import argparse
import sys
from datetime import datetime
from api_calls import faceit
from api_calls import opendota


def main():
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
        print(
            "The given date is in invalid format; please submit it in YYYY/MM/DD format."
        )
        sys.exit(1)

    # Since the runtime is an hour or two, these can be run one at a time by commenting out the rest,
    # but they MUST be run in order.
    faceit_match_ids = faceit.get_faceit_matches(cutoff)
    dota_match_ids = faceit.get_ingame_ids(faceit_match_ids)
    opendota.get_matches_from_opendota(dota_match_ids)
    print("get_matches ran successfully.")


if __name__ == "__main__":
    main()
