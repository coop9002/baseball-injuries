import pandas as pd
import pybaseball as pb
import time

# Load the processed injury data
df = pd.read_csv('processed_baseball_injuries.csv')

print(f"Loaded {len(df)} players from processed_baseball_injuries.csv")

def get_avg_spin(player_id, year):
    """
    Get average spin rate for a player in a given year.
    """
    if pd.isna(player_id) or year < 2015:  # Statcast starts in 2015
        return None
    
    start_dt = f'{year}-03-01'
    end_dt = f'{year}-11-01'
    
    try:
        pitches_df = pb.statcast_pitcher(start_dt, end_dt, player_id)
        if not pitches_df.empty and 'release_spin_rate' in pitches_df.columns:
            avg_spin = pitches_df['release_spin_rate'].mean()
            return avg_spin
        else:
            return None
    except Exception as e:
        print(f"Error getting spin for player {player_id} in {year}: {e}")
        return None

# Initialize counters
count_before = 0
count_after = 0
count_both = 0

# Process each player
for idx, row in df.iterrows():
    player_id = row['player_id']
    injury_year = row['Injury_Year']
    
    if pd.isna(injury_year):
        continue
    
    year_before = int(injury_year) - 1
    year_after = int(injury_year) + 1
    
    avg_spin_before = get_avg_spin(player_id, year_before)
    avg_spin_after = get_avg_spin(player_id, year_after)
    
    if avg_spin_before is not None:
        count_before += 1
    if avg_spin_after is not None:
        count_after += 1
    if avg_spin_before is not None and avg_spin_after is not None:
        count_both += 1
    
    # Print progress every 10 players
    if (idx + 1) % 10 == 0:
        print(f"Processed {idx + 1} players...")

print("\nResults:")
print(f"Players with average spin rate in year before surgery: {count_before}")
print(f"Players with average spin rate in year after surgery: {count_after}")
print(f"Players with average spin rate in both years: {count_both}")
print(f"Total players processed: {len(df)}")
