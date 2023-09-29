#!/usr/bin/env python3

import argparse
import chess.pgn
import chess.engine
import math
import statistics
from math import exp

# Function to convert Centipawn to Winning chances (lichess algorithm)
def winning_chances(cp):
    MULTIPLIER = -0.00368208
    v = 2 / (1 + exp(MULTIPLIER * cp)) - 1
    return max(-1, min(1, v))

# Function to calculate accuracy from Winning Percentage difference (lichess algorithm)
def wp_to_accuracy( delta_wp ):
    accuracy = 103.1668100711649 * exp(-0.04354415386753951 * delta_wp) - 3.166924740191411 + 1 # bonus 1
    accuracy = min(100, max( 0, accuracy))
    return accuracy
    
# Function to calculate winning percentages (wps) and accuracies for each move of a game
# take game and engine, return wps, and accuracies
def calculate_accuracy(game, engine):
    board = game.board() # assume standard game
    # initial analysis of initial board
    info = engine.analyse(board, chess.engine.Limit(depth=20))

    accuracies = []
    wps = []
    
    turn = chess.WHITE

    white_cp_before = max(min(info["score"].white().score(mate_score=10000),1500),-1500)
    white_cp_after = None

    white_wp_before = 50 + 50 * winning_chances(white_cp_before)
    white_wp_after = None

    print(f"  move white    black      eval (accuracy%)")

    for move in game.mainline_moves():
        # now move
        n = board.fullmove_number
        san = board.san(move)
        board.push(move)
        info = engine.analyse(board, chess.engine.Limit(depth=20))
        white_cp_after = max(min(info["score"].white().score(mate_score=10000),1500),-1500)
        white_wp_after = 50 + 50 * winning_chances(white_cp_after)
        wps.append(white_wp_after)
        #clk = game.comment

        # calculate after
        if turn == chess.WHITE:
            accuracy = wp_to_accuracy( white_wp_before - white_wp_after )
            accuracies.append( accuracy )
            print(f"  {n:4d} {san:8s}          {white_cp_after/100.0:6.2f} ({accuracy:.2f})")
        else:
            accuracy = wp_to_accuracy( white_wp_after - white_wp_before )
            accuracies.append( accuracy )
            print(f"  {n:4d} ..       {san:8s} {white_cp_after/100.0:6.2f} ({accuracy:.2f})")
        turn = not turn
        white_cp_before = white_cp_after
        white_wp_before = white_wp_after


    return accuracies, wps

# Calculate overall accuracies for white and black of the whole game
def game_accuracy( wps, accuracies ):
    # Calculate weighted mean
    window_size = max(2, min(8, len(accuracies) // 10))
    windows = [wps[:window_size]] + [wps[i:i + window_size] for i in range(1, len(wps) - window_size + 1)]
    weights = [max(0.5, min(12, statistics.stdev(window))) for window in windows]

    weighted_accuracies = [(acc, weights[i // 2]) for i, acc in enumerate(accuracies)]

    white_acc = [wacc for i, (acc, w) in enumerate(weighted_accuracies) if i % 2 == 0 for wacc in [acc] * int(w)]
    black_acc = [bacc for i, (acc, w) in enumerate(weighted_accuracies) if i % 2 != 0 for bacc in [acc] * int(w)]

    white_accuracy = (statistics.mean(white_acc) + statistics.harmonic_mean(white_acc)) / 2
    black_accuracy = (statistics.mean(black_acc) + statistics.harmonic_mean(black_acc)) / 2

    return white_accuracy, black_accuracy

# Command-line interface
if __name__ == "__main__":
    stockfish_path = "stockfish16"
    parser = argparse.ArgumentParser(description="Analyze a PGN file using stockfish.")
    parser.add_argument('-i', '--input', required=True, help="Path to the input PGN file.")
    
    args = parser.parse_args()
    pgn_path = args.input

    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    i = 0
    with open(pgn_path, 'r') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        while game != None:
            i += 1
            print(f'Analysis of Game #{i}, {game.headers["White"]} vs {game.headers["Black"]}, {game.headers["Result"]}:')
            accuracies, wps = calculate_accuracy(game, engine)
            accuracy_white, accuracy_black = game_accuracy( wps, accuracies)
    
            print(f' Accuracy for White ({game.headers["White"]}): {accuracy_white:.2f}%')
            print(f' Accuracy for Black ({game.headers["Black"]}): {accuracy_black:.2f}%')
            game = chess.pgn.read_game(pgn_file)
    
    engine.quit()

