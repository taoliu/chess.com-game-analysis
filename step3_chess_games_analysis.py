#!/usr/bin/env python3
import json
import csv
import re
import argparse

import chess
import chess.engine

def analyze_fen(fen, engine,side):
    board = chess.Board(fen)
    info = engine.analyse(board, chess.engine.Limit(depth=20))
    if side == "white":
        score = info["score"].white()
    else:
        score = info["score"].black()
    return str(score)

def find_uoi(games):
    username_counts = {}
    for game in games:
        white_username = game["white"]["username"].lower()
        black_username = game["black"]["username"].lower()
        
        username_counts[white_username] = username_counts.get(white_username, 0) + 1
        username_counts[black_username] = username_counts.get(black_username, 0) + 1
    
    uoi = max(username_counts, key=username_counts.get)
    return uoi

def extract_from_pgn(pgn, field):
    pattern = rf'\[{field} "([^"]+)"\]'
    match = re.search(pattern, pgn)
    return match.group(1) if match else None

def process_game(game, uoi, engine):
    pgn = game["pgn"]
    game_info = {}
    
    date = extract_from_pgn(pgn, "UTCDate").replace('.', '/')
    time = extract_from_pgn(pgn, "UTCTime")
    game_info["date_time"] = f'"{date} {time}"'
    
    white_username = game["white"]["username"].lower()
    black_username = game["black"]["username"].lower()
    side = "white" if white_username == uoi else "black"
    game_info["side"] = f'"{side}"'
    
    game_info["uoi_elo"] = game[side]["rating"]
    
    opponent_side = "black" if side == "white" else "white"
    game_info["opponent"] = f'"{game[opponent_side]["username"].lower()}"'
    
    game_info["opponent_elo"] = game[opponent_side]["rating"]
    
    game_info["time_class"] = f'"{game["time_class"]}"'
    
    game_info["time_control"] = f'"{game["time_control"]}"'
    
    result = extract_from_pgn(pgn, "Result")
    if result == "1-0":
        game_info["result"] = "win" if side == "white" else "lose"
        lose_side = "black"
    elif result == "0-1":
        game_info["result"] = "win" if side == "black" else "lose"
        lose_side = "white"
    else:
        game_info["result"] = "draw"
        lose_side = "white"
    game_info["result"] = f'"{game_info["result"]}"'
    
    game_info["end_reason"] = f'"{game[lose_side if game_info["result"] != "draw" else side]["result"]}"'
    
    game_info["fen"] = f'"{game["fen"]}"'

    game_info["end_position_score"] = analyze_fen(game["fen"], engine, side)
    print(f'analyzed a position, score is {game_info["end_position_score"]}')
    
    return game_info

def main(input_file, output_file):
    stockfish_path = "stockfish16"  # Replace with the actual path to your Stockfish engine
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    
    with open(input_file, "r") as f:
        games = json.load(f)
    
    uoi = find_uoi(games)
    print(f"User-of-Interest (UOI) discovered: {uoi}")
    
    headers = ["date_time", "side", "uoi_elo", "opponent", "opponent_elo", "time_class", "time_control", "result", "end_reason", "fen", "end_position_score"]
    with open(output_file, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers, quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
    
        for game in games:
            game_info = process_game(game, uoi, engine)
            writer.writerow(game_info)
    
    engine.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze chess games from a JSON file.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input JSON file containing chess games.")
    parser.add_argument("-o", "--output", required=True, help="Path to the output CSV file.")
    
    args = parser.parse_args()
    
    main(args.input, args.output)
