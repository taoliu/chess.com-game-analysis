#!/usr/bin/env python3

import argparse
import chess.pgn
import chess.engine
import math
import statistics
from math import exp

def winning_chances(cp):
    MULTIPLIER = -0.00368208
    v = 2 / (1 + exp(MULTIPLIER * cp)) - 1
    return max(-1, min(1, v))

# Function to calculate average centipawn loss
def calculate_accuracy(game, stockfish_path):
    board = game.board() # assume standard game
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    # initial analysis of initial board
    info = engine.analyse(board, chess.engine.Limit(depth=20))

    accuracies = []
    wins = [0]
    turn = chess.WHITE

    white_cp_before = max(min(info["score"].white().score(mate_score=10000),1500),-1500)
    white_cp_after = None

    white_win_before = 50 + 50 * winning_chances(white_cp_before)
    white_win_after = None

    print(f"  move white    black      eval (accuracy%)")

    for move in game.mainline_moves():
        # now move
        n = board.fullmove_number
        san = board.san(move)
        board.push(move)
        info = engine.analyse(board, chess.engine.Limit(depth=20))
        white_cp_after = max(min(info["score"].white().score(mate_score=10000),1500),-1500)
        white_win_after = 50 + 50 * winning_chances(white_cp_after)
        wins.append(white_win_after)
        clk = game.comment

        # calculate after
        if turn == chess.WHITE:
            accuracy = 103.1668100711649 * exp(-0.04354415386753951 * ( white_win_before - white_win_after )) - 3.166924740191411 + 1
            accuracy = min(100, max( 0, accuracy))
            accuracies.append( accuracy )
            print(f"  {n:4d} {san:8s}          {white_cp_after/100.0:6.2f} ({accuracy:.2f}) {clk}")
        else:
            accuracy = 103.1668100711649 * exp(-0.04354415386753951 * ( white_win_after - white_win_before )) - 3.166924740191411 + 1
            accuracy = min(100, max( 0, accuracy))
            accuracies.append( accuracy )
            print(f"  {n:4d} ..       {san:8s} {white_cp_after/100.0:6.2f} ({accuracy:.2f}) {clk}")
        turn = not turn
        white_cp_before = white_cp_after
        white_win_before = white_win_after

    engine.quit()

    return accuracies, wins

def game_accuracy( wins, accuracies ):
    # Calculate weighted mean
    window_size = max(2, min(8, len(accuracies) // 10))
    windows = [wins[:window_size]] + [wins[i:i + window_size] for i in range(1, len(wins) - window_size + 1)]
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

    i = 0
    with open(pgn_path, 'r') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        while game != None:
            i += 1
            print(f"Analysis of Game #{i}:")
            accuracies, wins = calculate_accuracy(game, stockfish_path)
            accuracy_white, accuracy_black = game_accuracy( wins, accuracies)
    
            print(f' Accuracy for White ({game.headers["White"]}): {accuracy_white:.2f}%')
            print(f' Accuracy for Black ({game.headers["Black"]}): {accuracy_black:.2f}%')
            game = chess.pgn.read_game(pgn_file)
    

