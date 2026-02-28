import pandas as pd
import pybaseball as pb
import time

pb.cache.enable()

df = pd.read_csv('processed_baseball_injuries.csv')

print(f"Loaded {len(df)} players from processed_baseball_injuries.csv")
print("\nTesting pitch mix retrieval using Statcast data...")

def get_pitch_mix(player_id, year):
    """
    Get pitch mix for a player in a given year using Statcast data.
    Returns a dictionary with pitch type percentages.
    """
    if pd.isna(player_id) or year < 2015:
        return None
    
    try:
        start_dt = f'{year}-03-01'
        end_dt = f'{year}-11-01'
        
        print(f"\nFetching data for player {player_id} in {year}...")
        data = pb.statcast_pitcher(start_dt, end_dt, player_id)
        
        if data is None or data.empty:
            print(f"  No data found")
            return None
        
        regular_season = data[data['game_type'] == 'R']
        
        if regular_season.empty:
            print(f"  No regular season data")
            return None
        
        if 'pitch_type' not in regular_season.columns:
            print(f"  No pitch_type column")
            return None
        
        pitch_counts = regular_season['pitch_type'].value_counts()
        total_pitches = len(regular_season)
        
        pitch_mix = {}
        for pitch_type, count in pitch_counts.items():
            if pd.notna(pitch_type):
                percentage = (count / total_pitches) * 100
                pitch_mix[pitch_type] = {
                    'count': int(count),
                    'percentage': round(percentage, 2)
                }
        
        print(f"  Total pitches: {total_pitches}")
        print(f"  Pitch types found: {list(pitch_mix.keys())}")
        
        return pitch_mix
        
    except Exception as e:
        print(f"  Error: {e}")
        return None


test_players = df[df['Injury_Year'] >= 2015].head(3)

for idx, row in test_players.iterrows():
    player_id = row['player_id']
    injury_year = row['Injury_Year']
    name = row['Name']
    
    print(f"\n{'='*60}")
    print(f"Player: {name}")
    print(f"Player ID: {player_id}")
    print(f"Injury Year: {injury_year}")
    
    year_before = injury_year - 1
    pitch_mix = get_pitch_mix(player_id, year_before)
    
    if pitch_mix:
        print(f"\nPitch Mix for {year_before} (year before injury):")
        for pitch_type, stats in sorted(pitch_mix.items(), key=lambda x: x[1]['percentage'], reverse=True):
            print(f"  {pitch_type}: {stats['percentage']}% ({stats['count']} pitches)")
    else:
        print(f"\nNo pitch mix data available for {year_before}")
    
    time.sleep(1)

print("\n" + "="*60)
print("\nPitch Type Codes (common ones):")
print("  FF - Four-seam Fastball")
print("  SI - Sinker")
print("  FC - Cutter")
print("  SL - Slider")
print("  CU - Curveball")
print("  CH - Changeup")
print("  FS - Splitter")
print("  KC - Knuckle Curve")
print("  KN - Knuckleball")
print("  EP - Eephus")
print("\nConclusion:")
print("Statcast provides detailed pitch_type data starting from 2015.")
print("We can calculate pitch mix percentages for each season.")
print("This can be added to the main injuries_clean.py script.")
