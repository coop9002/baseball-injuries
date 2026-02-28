import pandas as pd
import pybaseball as pb

def load_and_clean_injury_data(excel_path):
    """
    Load and clean injury data from Excel file, similar to injuries_clean.py
    """
    try:
        excel_file = pd.ExcelFile(excel_path)
        sheet_names = excel_file.sheet_names
        
        if len(sheet_names) < 2:
            raise ValueError("Excel file must have at least 2 sheets")
            
        # Load data from first two sheets
        df1 = pd.read_excel(excel_file, sheet_name=sheet_names[0])
        df2 = pd.read_excel(excel_file, sheet_name=sheet_names[1])
        
        # Standardize column names
        df2 = df2.rename(columns={
            'Position': 'Pos', 
            'Date of surgery': 'Injury / Surgery Date', 
            'Player': 'Name'
        })
        
        # Merge datasets
        merged_df = pd.merge(df1, df2, on='Name', how='outer', indicator=True)
        
        # Clean similar to injuries_clean.py
        columns_to_drop = [
            'Throws', 'Status', 'Latest Update', 'Eligible to Return', 
            'IL Retro Date', 'Return Date', 'Team', '_merge'
        ]
        
        for col in columns_to_drop:
            if col in merged_df.columns:
                merged_df = merged_df.drop(columns=[col])
        
        # Merge duplicate position columns
        if 'Pos_x' in merged_df.columns and 'Pos_y' in merged_df.columns:
            merged_df['Pos'] = merged_df['Pos_x'].fillna(merged_df['Pos_y'])
            merged_df = merged_df.drop(columns=['Pos_x', 'Pos_y'])
        
        # Merge duplicate date columns
        if 'Injury / Surgery Date_x' in merged_df.columns and 'Injury / Surgery Date_y' in merged_df.columns:
            merged_df['Injury / Surgery Date'] = merged_df['Injury / Surgery Date_x'].fillna(merged_df['Injury / Surgery Date_y'])
            merged_df = merged_df.drop(columns=['Injury / Surgery Date_x', 'Injury / Surgery Date_y'])
        
        # Fill missing injury descriptions
        if 'Injury / Surgery' in merged_df.columns:
            merged_df['Injury / Surgery'] = merged_df['Injury / Surgery'].fillna('Tommy John surgery')
        
        # Convert dates and extract year
        merged_df['Injury / Surgery Date'] = pd.to_datetime(merged_df['Injury / Surgery Date'], errors='coerce')
        merged_df = merged_df.dropna(subset=['Injury / Surgery Date'])
        merged_df['Injury_Year'] = merged_df['Injury / Surgery Date'].dt.year
        
        # Standardize positions
        pitcher_positions = ['RP', 'SP', 'SP/RP', 'Pitcher / Outfielder', 'Pitcher / Designated hitter']
        merged_df['Pos'] = merged_df['Pos'].replace(pitcher_positions, 'Pitcher')
        
        # Filter for pitchers only
        merged_df = merged_df[merged_df['Pos'] == 'Pitcher']
        
        return merged_df
        
    except Exception as e:
        print(f"Error loading injury data: {e}")
        return None

def get_player_id(name):
    """
    Get player ID from name using pybaseball lookup
    """
    try:
        # Split name
        name_parts = name.split(' ')
        if len(name_parts) < 2:
            return None
        first = name_parts[0]
        last = name_parts[-1]
        
        # Lookup
        lookup = pb.playerid_lookup(last, first)
        if lookup.empty:
            return None
        return lookup.iloc[0]['key_mlbam']
    except Exception as e:
        print(f"Error looking up ID for {name}: {e}")
        return None

def calculate_avg_pitches_playoff_2017(player_id):
    """
    Calculate average pitches per playoff game for player in 2017
    """
    try:
        # Fetch all pitches in 2017
        data = pb.statcast_pitcher('2017-01-01', '2017-12-31', player_id)
        if data.empty:
            return None
        
        # Filter for playoffs: game_type D, L, W
        playoffs = data[data['game_type'].isin(['D', 'L', 'W'])]
        if playoffs.empty:
            return None
        
        # Group by game_pk, count pitches
        pitches_per_game = playoffs.groupby('game_pk').size()
        
        # Average
        avg_pitches = pitches_per_game.mean()
        return avg_pitches
        
    except Exception as e:
        print(f"Error calculating for player ID {player_id}: {e}")
        return None

def main():
    excel_path = 'Baseball Injury Report.xlsx'
    
    # Load and clean data
    data = load_and_clean_injury_data(excel_path)
    if data is None:
        print("Failed to load data")
        return
    
    # Get first 10 player names
    first_10_names = data['Name'].head(10).tolist()
    
    print("Calculating average pitches per playoff game in 2017 for the first 10 players:")
    print("-" * 70)
    
    for name in first_10_names:
        player_id = get_player_id(name)
        if player_id is None:
            print(f"{name}: Player ID not found")
            continue
        
        avg_pitches = calculate_avg_pitches_playoff_2017(player_id)
        if avg_pitches is not None:
            print(f"{name}: {avg_pitches:.1f} pitches per game")
        else:
            print(f"{name}: No playoff data in 2017")

if __name__ == "__main__":
    main()
