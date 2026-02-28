import pandas as pd
import pybaseball as pb
import numpy as np
from datetime import datetime
import time

pb.cache.enable()

print("="*60)
print("Missing Data Fill Script")
print("="*60)

# Load the processed data
df = pd.read_csv('processed_baseball_injuries.csv')
print(f"\nLoaded {len(df)} players from processed_baseball_injuries.csv")

# Create a copy to work with
df_filled = df.copy()

# Track statistics
stats = {
    'total_missing_before': 0,
    'total_missing_after': 0,
    'fields_filled': {},
    'players_updated': set()
}

# Count initial missing values
for col in df.columns:
    if col not in ['Name', 'Injury / Surgery', 'Pos', 'Injury / Surgery Date', 'Injury_Year']:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            stats['total_missing_before'] += missing_count
            stats['fields_filled'][col] = 0

print(f"\nTotal missing values before: {stats['total_missing_before']}")
print(f"Number of fields with missing data: {len(stats['fields_filled'])}")

# Helper functions to retry data retrieval
def get_statcast_data_robust(player_id, year):
    """
    Robustly retrieve Statcast data with multiple retry strategies.
    """
    if pd.isna(player_id) or year < 2015:
        return None
    
    try:
        # Try standard date range
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
        data = pb.statcast_pitcher(start_date, end_date, int(player_id))
        
        if data is not None and not data.empty:
            return data
        
        # Try narrower date range (regular season)
        start_date = f'{year}-03-01'
        end_date = f'{year}-11-01'
        data = pb.statcast_pitcher(start_date, end_date, int(player_id))
        
        if data is not None and not data.empty:
            return data
            
    except Exception as e:
        pass
    
    return None


def fill_spin_rate(df_filled, idx, player_id, year, col_name):
    """Fill missing spin rate data."""
    if pd.notna(df_filled.at[idx, col_name]):
        return False
    
    data = get_statcast_data_robust(player_id, year)
    if data is None:
        return False
    
    regular_season = data[data['game_type'] == 'R']
    if regular_season.empty or 'release_spin_rate' not in regular_season.columns:
        return False
    
    avg_spin = regular_season['release_spin_rate'].mean()
    if pd.notna(avg_spin):
        df_filled.at[idx, col_name] = avg_spin
        return True
    
    return False


def fill_velocity(df_filled, idx, player_id, year, col_name, playoff=False):
    """Fill missing velocity data."""
    if pd.notna(df_filled.at[idx, col_name]):
        return False
    
    data = get_statcast_data_robust(player_id, year)
    if data is None:
        return False
    
    if playoff:
        filtered = data[data['game_type'].isin(['D', 'F', 'L', 'W'])]
    else:
        filtered = data[data['game_type'] == 'R']
    
    if filtered.empty or 'release_speed' not in filtered.columns:
        return False
    
    avg_velocity = filtered['release_speed'].mean()
    if pd.notna(avg_velocity):
        df_filled.at[idx, col_name] = avg_velocity
        return True
    
    return False


def fill_pitch_mix(df_filled, idx, player_id, year, pitch_type, period):
    """Fill missing pitch mix data."""
    col_name = f'{pitch_type.lower()}_pct_{period}'
    
    if pd.notna(df_filled.at[idx, col_name]):
        return False
    
    data = get_statcast_data_robust(player_id, year)
    if data is None:
        return False
    
    regular_season = data[data['game_type'] == 'R']
    if regular_season.empty or 'pitch_type' not in regular_season.columns:
        return False
    
    pitch_counts = regular_season['pitch_type'].value_counts()
    total_pitches = len(regular_season)
    
    if total_pitches == 0:
        return False
    
    if pitch_type in pitch_counts.index:
        percentage = (pitch_counts[pitch_type] / total_pitches) * 100
        df_filled.at[idx, col_name] = round(percentage, 2)
    else:
        df_filled.at[idx, col_name] = 0.0
    
    return True


def fill_lahman_stats(df_filled, idx, lahman_id, year, stat_type, col_name):
    """Fill missing Lahman-based stats (GS, SV, Relief App)."""
    if pd.notna(df_filled.at[idx, col_name]) or pd.isna(lahman_id):
        return False
    
    try:
        pitching_data = pb.pitching_stats(year, year)
        if pitching_data is None or pitching_data.empty:
            return False
        
        player_data = pitching_data[pitching_data['IDfg'] == int(lahman_id)]
        if player_data.empty:
            return False
        
        if stat_type == 'GS' and 'GS' in player_data.columns:
            value = player_data['GS'].sum()
            df_filled.at[idx, col_name] = int(value) if value > 0 else 0
            return True
        elif stat_type == 'SV' and 'SV' in player_data.columns:
            value = player_data['SV'].sum()
            df_filled.at[idx, col_name] = int(value) if value > 0 else 0
            return True
        elif stat_type == 'Relief':
            if 'G' in player_data.columns and 'GS' in player_data.columns:
                g = player_data['G'].sum()
                gs = player_data['GS'].sum()
                relief = g - gs
                df_filled.at[idx, col_name] = int(relief) if relief > 0 else 0
                return True
    except Exception as e:
        pass
    
    return False


# Process each player
print("\nAttempting to fill missing data...")
print("-" * 60)

time_periods = ['t_minus_4', 't_minus_3', 't_minus_2', 't_minus_1', 't_plus_1', 't_plus_2', 't_plus_3', 't_plus_4']
pitch_types = ['FF', 'SI', 'SL', 'CU', 'CH', 'FC']

for idx, row in df_filled.iterrows():
    player_id = row['player_id']
    lahman_id = row['lahman_id']
    injury_year = row['Injury_Year']
    name = row['Name']
    
    if pd.isna(player_id):
        continue
    
    player_updated = False
    
    # Try to fill data for each time period
    for i, period in enumerate(time_periods):
        if period.startswith('t_minus'):
            offset = -int(period.split('_')[-1])
        else:
            offset = int(period.split('_')[-1])
        
        year = injury_year + offset
        
        # Skip if year is too old for Statcast
        if year < 2015:
            continue
        
        # Fill spin rate
        col_name = f'avg_spin_rate_{period}'
        if col_name in df_filled.columns:
            if fill_spin_rate(df_filled, idx, player_id, year, col_name):
                stats['fields_filled'][col_name] = stats['fields_filled'].get(col_name, 0) + 1
                player_updated = True
        
        # Fill regular season velocity
        col_name = f'avg_velocity_{period}'
        if col_name in df_filled.columns:
            if fill_velocity(df_filled, idx, player_id, year, col_name, playoff=False):
                stats['fields_filled'][col_name] = stats['fields_filled'].get(col_name, 0) + 1
                player_updated = True
        
        # Fill playoff velocity
        col_name = f'avg_velocity_playoff_{period}'
        if col_name in df_filled.columns:
            if fill_velocity(df_filled, idx, player_id, year, col_name, playoff=True):
                stats['fields_filled'][col_name] = stats['fields_filled'].get(col_name, 0) + 1
                player_updated = True
        
        # Fill pitch mix
        for pitch_type in pitch_types:
            if fill_pitch_mix(df_filled, idx, player_id, year, pitch_type, period):
                col_name = f'{pitch_type.lower()}_pct_{period}'
                stats['fields_filled'][col_name] = stats['fields_filled'].get(col_name, 0) + 1
                player_updated = True
        
        # Fill Lahman stats (GS, SV, Relief App)
        col_name = f'gs_{period}'
        if col_name in df_filled.columns:
            if fill_lahman_stats(df_filled, idx, lahman_id, year, 'GS', col_name):
                stats['fields_filled'][col_name] = stats['fields_filled'].get(col_name, 0) + 1
                player_updated = True
        
        col_name = f'sv_{period}'
        if col_name in df_filled.columns:
            if fill_lahman_stats(df_filled, idx, lahman_id, year, 'SV', col_name):
                stats['fields_filled'][col_name] = stats['fields_filled'].get(col_name, 0) + 1
                player_updated = True
        
        col_name = f'relief_app_{period}'
        if col_name in df_filled.columns:
            if fill_lahman_stats(df_filled, idx, lahman_id, year, 'Relief', col_name):
                stats['fields_filled'][col_name] = stats['fields_filled'].get(col_name, 0) + 1
                player_updated = True
    
    if player_updated:
        stats['players_updated'].add(name)
        print(f"Updated data for: {name}")
    
    # Rate limiting
    if idx % 10 == 0:
        time.sleep(0.5)

# Count final missing values
for col in df_filled.columns:
    if col not in ['Name', 'Injury / Surgery', 'Pos', 'Injury / Surgery Date', 'Injury_Year']:
        missing_count = df_filled[col].isna().sum()
        stats['total_missing_after'] += missing_count

# Calculate total fields filled
total_filled = sum(stats['fields_filled'].values())

# Save the updated data
output_path = 'processed_baseball_injuries_filled.csv'
df_filled.to_csv(output_path, index=False)

# Print results
print("\n" + "="*60)
print("RESULTS")
print("="*60)
print(f"\nTotal missing values before: {stats['total_missing_before']}")
print(f"Total missing values after:  {stats['total_missing_after']}")
print(f"Total fields filled:         {total_filled}")
print(f"Reduction in missing data:   {stats['total_missing_before'] - stats['total_missing_after']}")
print(f"Players updated:             {len(stats['players_updated'])}")

if total_filled > 0:
    print(f"\nTop fields filled:")
    sorted_fields = sorted(stats['fields_filled'].items(), key=lambda x: x[1], reverse=True)
    for field, count in sorted_fields[:10]:
        if count > 0:
            print(f"  {field}: {count} values")

print(f"\nUpdated data saved to: {output_path}")
print("="*60)
