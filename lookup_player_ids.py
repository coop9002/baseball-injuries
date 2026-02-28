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
        original_name = name  # Save original for manual lookup
        
        # Name corrections for accented or special characters
        name_corrections = {
            "Adrian Morejon": "Adrián Morejón",
            "A.J. Puk": "A. J. Puk",
            "Angel Perdomo": "Ángel Perdomo",
            "Barret Loux": "Barrett Loux",
            "Chi Chi Gonzalez": "Chi-Chi González",
            "Darien Núñez": "Darién Núñez",
            "Hyun-jin Ryu": "Hyun Jin Ryu",
            "Jose Alvarez": "José Alvarez",
            "Michel Baez": "Michel Báez",
            "Sandy Alcantara": "Sandy Alcántara",
            "Vladimir Gutierrez": "Vladimir Gutiérrez"
        }
        if name in name_corrections:
            name = name_corrections[name]
        
        # Split name: first is all but last word, last is last word
        name_parts = name.split()
        if len(name_parts) < 2:
            return None
        first = ' '.join(name_parts[:-1])
        last = name_parts[-1]
        
        # Lookup
        lookup = pb.playerid_lookup(last, first)
        if lookup.empty:
            # Try without periods in first name
            first_no_dot = first.replace('.', '')
            lookup = pb.playerid_lookup(last, first_no_dot)
            if lookup.empty:
                # Try with space for initials
                first_spaced = first.replace('.', '. ')
                lookup = pb.playerid_lookup(last, first_spaced)
            if lookup.empty:
                # Manual overrides for players not in lookup
                manual_ids = {
                    "Barret Loux": 621344,
                    "Brady Aiken": 592094,
                    "Bryce Montes de Oca": 650489,
                    "Chi Chi Gonzalez": 592346,
                    "Jae Seo": 400134,
                    "Jay Groome": 668941,
                    "Jorge de la Rosa": 407822,
                    "Jose Alvarez": 501625,
                    "José De León": 605894,
                    "Lance McCullers Jr.": 621121,
                    "Luis F. Ortiz": 642528,
                    "Matt Bowman": 621199,
                    "Matthew Boyd": 571510,
                    "Nate Adcock": 502264,
                    "Pedro Borbón Jr.": 150337,
                    "Rubby De La Rosa": 523989,
                    "Sam Carlson": 676664,
                    "Ty Hensley": 669211,
                    "Tyler Kolek": 681217
                }
                if original_name in manual_ids:
                    return manual_ids[original_name]
            return None
        return lookup.iloc[0]['key_mlbam']
    except Exception as e:
        print(f"Error looking up ID for {name}: {e}")
        return None

def main():
    excel_path = 'Baseball Injury Report.xlsx'
    
    # Load and clean data
    data = load_and_clean_injury_data(excel_path)
    if data is None:
        print("Failed to load data")
        return
    
    # Get all player names
    all_names = data['Name'].tolist()
    
    print("Looking up MLB player IDs for all players:")
    print("-" * 50)
    
    failed = []
    
    for name in all_names:
        player_id = get_player_id(name)
        if player_id is not None:
            print(f"{name}: {player_id}")
        else:
            failed.append(name)
    
    if failed:
        print("\nPlayers with failed ID lookup:")
        for f in failed:
            print(f)
        print(f"\nTotal failed: {len(failed)}")
    else:
        print("\nAll players had successful ID lookup.")

if __name__ == "__main__":
    main()
