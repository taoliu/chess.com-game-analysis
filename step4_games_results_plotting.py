#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
import sys

def categorize_position(score):
    if score.startswith('#+'):
        return 'winning'
    elif score.startswith('#-'):
        return 'losing'
    elif score.startswith('#'):
        return 'neutral'
    else:
        score_value = float(score)
        if score_value > 300:
            return 'winning'
        elif score_value < -300:
            return 'losing'
        else:
            return 'neutral'

def extract_month(date_str):
    return datetime.strptime(date_str.split(' ')[0], '%Y/%m/%d').strftime('%Y-%m')

def plot_figures( df, prefix ):
    if prefix == "win":
        story = "Winning"
    elif prefix == "lose":
        story = "Losing"
    else:
        raise Exception(f"unknown {prefix}")
    fig, ax = plt.subplots()
    for time_class in ['bullet', 'blitz', 'rapid']:
        subset_df = df[df['time_class'] == time_class]
        position_counts = Counter(subset_df['position_category'])
        total_games = len(subset_df)
        winning_ratio = position_counts.get('winning', 0) / total_games
        losing_ratio = position_counts.get('losing', 0) / total_games
        neutral_ratio = position_counts.get('neutral', 0) / total_games
        ax.bar(time_class, winning_ratio, color='g')
        ax.bar(time_class, losing_ratio, color='r', bottom=winning_ratio)
        ax.bar(time_class, neutral_ratio, color='b', bottom=[winning_ratio + losing_ratio])
    ax.set_xlabel('Time Class')
    ax.set_ylabel('Ratio')
    ax.legend(['Winning', 'Losing', 'Neutral'])
    plt.title(f'Overall Position Statistics by Time Class While {story}')
    plt.savefig(f'{prefix}_overall_position_statistics.png')

    for time_class in ['bullet', 'blitz', 'rapid']:
        subset_df = df[df['time_class'] == time_class]
        monthly_stats = subset_df.groupby('month')['position_category'].value_counts(normalize=True).unstack().fillna(0)
    
        plt.figure()
        for category, color in zip(['winning', 'losing', 'neutral'], ['g', 'r', 'b']):
            if category in monthly_stats.columns:
                plt.plot(monthly_stats.index, monthly_stats[category], color=color, label=category.capitalize())
        plt.xlabel('Month')
        plt.ylabel('Ratio')
        plt.title(f'Trend of Position Ratios Over Time for {time_class.title()} Games While {story}')
        plt.legend()
        plt.savefig(f'{prefix}_trend_{time_class}.png')


if len(sys.argv) < 2:
    print("Usage: python script.py <csv_file_path>")
    sys.exit(1)

csv_file_path = sys.argv[1]
df = pd.read_csv(csv_file_path)

df_filtered = df[df['time_class'].isin(['bullet', 'blitz', 'rapid'])]
df_filtered['position_category'] = df_filtered['end_position_score'].apply(categorize_position)
df_filtered['month'] = df_filtered['date_time'].apply(extract_month)

df_filtered_win = df_filtered[df_filtered['result'].eq('win')]
df_filtered_lose = df_filtered[df_filtered['result'].eq('lose')]

plot_figures( df_filtered_win, "win" )
plot_figures( df_filtered_lose, "lose" )

