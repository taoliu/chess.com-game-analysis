#!/usr/bin/env python3

import argparse
import chess.pgn
import chess.engine
import chess.svg
import math
import statistics
from math import exp
import re


class MoveEvaluation:
    def __init__(self):
        self.mn = None                    #move number
        self.san = None                   #move in SAN
        self.side = None                  #side of move, either white/True or black/False
        self.weval = None                 #eval in white
        self.eval = None                  #eval in POV
        self.delta = None                 #change in eval in POV
        self.wwp = None                   #white win percentage
        self.wp = None                    #win percentage in POV
        self.wp_delta = None              #win percentage change
        self.accuracy = None              #accuracy
        self.time = None                  #time spent on this move
        self.grade = None                 #best, good, inaccurate, mistake, blunder
        self.blunder = False
        self.fen = None                   #FEN at this move
        self.svg = None                   #SVG of the board when necessary

    def grade_move(self, board, move):
        #blunder is a move that make you lose or make you lose huge chance to win.
        # thus, we assume the delta should <= -5, and the final eval is <=5 and >=-10
        if self.accuracy < 20:
            self.blunder = True
            self.grade = "blunder"
        elif self.accuracy < 50:
            self.grade = "mistake"
        elif self.accuracy < 80:
            self.grade = "inaccurate"
        elif self.accuracy < 98:
            self.grade = "good"
        else:
            self.grade = "best"

        if self.blunder:
            self.fen = "\""+board.fen()+"\""
            self.svg = chess.svg.board( board, lastmove = move, size=350)
        return

    def __str__ (self):
        s = "%3d\t%7s\t%7s\t%6.1f\t%6.1f\t%4.1f\t%8.1f\t%d\t%10s\t%s" % (self.mn, self.san if self.side else "..", ".." if self.side else self.san, self.weval, self.delta, self.wwp, self.accuracy, self.time, self.grade, self.fen if self.fen!=None else "")
        return s
        

def extract_time_control(time_control_str):
    match = re.search(r"(\d+)\+(\d+)", time_control_str)
    if match:
        total = int(match.group(1))
        inc = int(match.group(2))
    else:
        match = re.search(r"(\d+)", time_control_str)
        if match:
            total = int(match.group(1))
            inc = 0
        else:
            raise Exception(f'unrecognized time control {time_control_str}')
    return total, inc

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
def calculate_accuracy(game, stockfish_path):
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

    board = game.board() # assume standard game

    total, inc = extract_time_control( game.headers["TimeControl"] )
    if inc == None:
        inc = 0

    # initial analysis of initial board
    info = engine.analyse(board, chess.engine.Limit(depth=20))

    move_evals = []
    accuracies = []
    wps = []
    
    turn = chess.WHITE

    white_cp_before = max(min(info["score"].white().score(mate_score=10000),1500),-1500)
    white_cp_after = None

    white_wp_before = 50 + 50 * winning_chances(white_cp_before)
    white_wp_after = None

    white_clk = total
    black_clk = total
    
    result = []
    
    for move in game.mainline_moves():
        move_eval = MoveEvaluation()
        # now move
        game = game.next()
        move_eval.mn = board.fullmove_number
        move_eval.san = board.san(move)
        move_eval.side = turn
        
        board.push(move)
        info = engine.analyse(board, chess.engine.Limit(depth=20))
        white_cp_after = max(min(info["score"].white().score(mate_score=10000),1500),-1500)
        move_eval.weval = white_cp_after/100.0
        white_wp_after = 50 + 50 * winning_chances(white_cp_after)
        move_eval.wwp = white_wp_after
        wps.append(white_wp_after)
        clk = game.clock()

        # calculate after
        if turn == chess.WHITE:
            move_eval.time = white_clk - clk + inc
            white_clk = clk
            move_eval.accuracy = wp_to_accuracy( white_wp_before - white_wp_after )
            accuracies.append( move_eval.accuracy )
            move_eval.eval = move_eval.weval
            move_eval.wp = move_eval.wwp
            move_eval.delta = (white_cp_after-white_cp_before)/100.0
            move_eval.wp_delta = white_wp_after - white_wp_before            
        else:
            move_eval.time = black_clk - clk + inc
            black_clk = clk
            move_eval.accuracy = wp_to_accuracy( white_wp_after - white_wp_before )
            accuracies.append( move_eval.accuracy )
            move_eval.eval = -1 * move_eval.weval
            move_eval.wp = 100 - move_eval.wwp
            move_eval.delta = (white_cp_before-white_cp_after)/100.0
            move_eval.wp_delta = white_wp_before - white_wp_after

        move_eval.grade_move( board, move )
        move_evals.append( move_eval )
        turn = not turn
        white_cp_before = white_cp_after
        white_wp_before = white_wp_after

    engine.quit()
    return move_evals, accuracies, wps

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

    i = 0
    svg_n = 0
    with open(pgn_path, 'r') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        while game != None:
            move_evals, accuracies, wps = calculate_accuracy(game, stockfish_path)
            if len(move_evals) < 10:      #skip short games
                continue
            i += 1
            print(f'Analysis of Game #{i}, {game.headers["White"]} vs {game.headers["Black"]}, {game.headers["Result"]}:')
            print(f' Time Control:{game.headers["TimeControl"]}')
            accuracy_white, accuracy_black = game_accuracy( wps, accuracies)
            print(f"  move\t  white\t  black\t  eval\t delta\twwp\taccuracy\ttime\tgrade     \tfen\tsvg#")
            for move_eval in move_evals:
                s = "  "+str(move_eval)
                if move_eval.svg != None:
                    svg_n += 1
                    s +=f"\t{svg_n}"
                    with open(f"svg_{svg_n}.svg","w") as f:
                        f.write(move_eval.svg)
                print( s )
            print(f' Accuracy for White ({game.headers["White"]}): {accuracy_white:.2f}%')
            print(f' Accuracy for Black ({game.headers["Black"]}): {accuracy_black:.2f}%')
            game = chess.pgn.read_game(pgn_file)
    

