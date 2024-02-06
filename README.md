# match-parser

A collection of scripts to gather and analyse Dota 2 match data from matches played in a given FACEIT hub. **Implemented with Python and pandas**. The API keys and directories in `constants.py` need to be provided by the user.

## Instructions

**NOTE: This is uploaded here just for demonstrative purposes. I advise you not to waste time on finding/creating the API keys etc.; these instructions are here just to make the flow easier to follow. I can demo it if needed.**

1. Fill in the API keys, hub ID, match download directory, and logging directory in `constants.py`.
2. Run `get_matches.py`. It accepts an YYYY/MM/DD format cutoff date as a positional command-line argument (normal use case) to retrieve IDs of matches that were played after the given date, or it can be omitted to retrieve all the IDs of the matches in a given hub (rare use case).
3. Run `parse_matches.py` to analyze the JSON match data with pandas. Since this script is basically used only by me, it prints most of the stuff into terminal, which is fine for personal use here.
