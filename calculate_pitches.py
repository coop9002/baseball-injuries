import pybaseball
import pandas as pd

# Player: Clayton Kershaw, ID 477132
player_id = 477132

# Fetch all pitches in 2017
data = pybaseball.statcast_pitcher('2017-01-01', '2017-12-31', player_id)

# Filter for playoffs: game_type D, L, W
playoffs = data[data['game_type'].isin(['D', 'L', 'W'])]

# Group by game_pk, count pitches
pitches_per_game = playoffs.groupby('game_pk').size()

# Average
avg_pitches = pitches_per_game.mean()

print(f"Average pitches per playoff game for Clayton Kershaw in 2017: {avg_pitches}")
