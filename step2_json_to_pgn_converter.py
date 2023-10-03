#!/usr/bin/env python3

# Import required libraries
import json
import argparse

# Function to convert JSON to PGN
def json_to_pgn(input_file, output_file, exclude_types):
    try:
        i = 0
        # Read JSON file
        with open(input_file, 'r') as f:
            games = json.load(f)
        
        # Open output file for writing PGN data
        with open(output_file, 'w') as f:
            for game in games:
                if game["time_class"] not in exclude_types:
                    # Write the PGN data to the output file
                    f.write(game['pgn'])
                    f.write("\n\n")
                    i += 1
        
        print(f"Successfully converted {i} games to PGN format and saved to {output_file}.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Command-line interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a JSON file of chess games to PGN format.")
    parser.add_argument('-i', '--input', required=True, help="Path to the input JSON file.")
    parser.add_argument("-x", "--exclude", required=False, help="Exclude certain game types, choices are bullet, blitz, rapid, daily", choices=("bullet","blitz","rapid","daily"), nargs = "+")
    parser.add_argument('-o', '--output', required=True, help="Path to the output PGN file.")
    
    args = parser.parse_args()
    json_to_pgn(args.input, args.output, args.exclude)
