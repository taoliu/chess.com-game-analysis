#### Chess Analysis Tools

This repository contains three Python scripts designed to collect, convert, and analyze chess games from chess.com.

1. **step1_retrieve.py**: This script fetches chess games for a user-of-interest (UOI) within a specified date range and stores them in a JSON file.
    - **Input**: Username, starting date, ending date
    - **Output**: JSON file containing a list of all retrieved games
    
2. **step2_json_to_pgn_converter.py**: This script takes the JSON output from `step1_retrieve.py` and converts it into a PGN (Portable Game Notation) file for easier analysis.
    - **Input**: JSON file from `step1_retrieve.py`
    - **Output**: PGN file
    
3. **step3_chess_games_analysis.py**: This script performs a detailed analysis of the UOI's games stored in the JSON file. Metrics such as the playing side, game result, reason for win/loss, and ELO ratings are extracted. Additionally, it uses Stockfish16 to evaluate the final board position from the UOI's perspective.
    - **Input**: JSON file from `step1_retrieve.py`
    - **Output**: CSV file containing analyzed metrics and Stockfish16 evaluation scores

Disclaim: most of codes were written with the help from chatGPT-4, including this introduction.
