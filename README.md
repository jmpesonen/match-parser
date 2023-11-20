# match-parser

A collection of scripts to gather and analyse Dota 2 match data from matches played in a given FACEIT hub. **Implemented with Python and pandas**. The API keys and directories in `constants.py` need to be provided by the user.

It is important to note that these scripts could be tied together and ran with one command instead of running the necessary scripts separately; however, they are split since it makes them easier to run in small chunks, as the runtime can be rather long due to API rate limits, and in the future, the first two scripts might not be needed. Personal ease of use was preferred, as these scripts are not going to receive wide-spread usage and these are just here to demonstrate my Python and pandas skills.

## Instructions
1. Fill in the API keys, hub ID, match download directory, and logging directory in `constants.py`.
2. Run `hubmatches.py`. It accepts an YYYY/MM/DD format cutoff date as a positional command-line argument (normal use case) to retrieve IDs of matches that were played after the given date, or it can be omitted to retrieve all the IDs of the matches in a given hub (rare use case).
3. Run `get_ingame_ids.py` to ask a different API for the Dota 2 in-game match IDs with the FACEIT match IDs. This has strict API rate limits, so kept separately from the others for this use case due to long run time.
4. Run `opendota.py` to ask OpenDota API for match data with Dota 2 in-game match IDs and download what's available as JSONs.
5. Run `parse_matches.py` to analyze the JSON match data with pandas. Since this script is basically for personal use only, it prints most of the stuff into terminal, which is fine for personal use here.
