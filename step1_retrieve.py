#!/usr/bin/env python3

import requests
import json
import argparse
from datetime import datetime, timedelta

def fetch_games(username, year, month, contact_info):
    url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month:02}"
    headers = {'User-Agent': contact_info}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("games", [])
    else:
        print(f"Failed to retrieve data for {year}/{month:02}. Status code: {response.status_code}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Fetch and merge chess games from chess.com's API")
    parser.add_argument("-u", "--username", required=True, help="Chess.com username")
    parser.add_argument("-s", "--start", required=True, help="Start year/month in YYYY/MM format")
    parser.add_argument("-e", "--end", required=True, help="End year/month in YYYY/MM format")
    parser.add_argument("-c", "--contact", required=True, help="Contact information for API user-agent")
    parser.add_argument("-o", "--output", required=True, help="Output JSON file name")

    args = parser.parse_args()

    start_year, start_month = map(int, args.start.split('/'))
    end_year, end_month = map(int, args.end.split('/'))
    
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 1)
    
    merged_games = []
    
    while start_date <= end_date:
        year, month = start_date.year, start_date.month
        print(f"Fetching games for {year}/{month:02}...")
        games = fetch_games(args.username, year, month, args.contact)
        merged_games.extend(games)
        
        start_date += timedelta(days=32)
        start_date = start_date.replace(day=1)

    # Merging all games into a list of dictionaries
    final_output = [game for game in merged_games]
    
    with open(args.output, "w") as f:
        json.dump(final_output, f, indent=4)

if __name__ == "__main__":
    main()
