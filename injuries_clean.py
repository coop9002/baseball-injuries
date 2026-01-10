# -*- coding: utf-8 -*-
"""
Baseball Injury Data Analysis

This script processes baseball injury data from Excel files and adds player IDs.

Author: Generated from cleaned notebook
Date: 2026-01-02
"""

import pandas as pd
import os
from pathlib import Path
import pybaseball as pb
import concurrent.futures

# Global variable for Lahman pitching post data
pitching_post = None

# Global variable for Lahman regular pitching data
pitching_reg = None

# Configuration
EXCEL_FILE_PATH = 'Baseball Injury Report.xlsx'


def load_and_merge_injury_data(excel_path):
    """
    Load and merge baseball injury data from Excel file.
    
    Args:
        excel_path (str): Path to the Excel file containing injury data
        
    Returns:
        pd.DataFrame: Merged and cleaned injury data
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
        
        return merged_df
        
    except Exception as e:
        print(f"Error loading injury data: {e}")
        return None


def clean_injury_data(df):
    """
    Clean and standardize the injury data.
    
    Args:
        df (pd.DataFrame): Raw merged injury data
        
    Returns:
        pd.DataFrame: Cleaned injury data
    """
    if df is None:
        return None
    
    # Drop unnecessary columns
    columns_to_drop = [
        'Throws', 'Status', 'Latest Update', 'Eligible to Return', 
        'IL Retro Date', 'Return Date', 'Team', '_merge'
    ]
    
    for col in columns_to_drop:
        if col in df.columns:
            df = df.drop(columns=[col])
    
    # Merge duplicate position columns
    if 'Pos_x' in df.columns and 'Pos_y' in df.columns:
        df['Pos'] = df['Pos_x'].fillna(df['Pos_y'])
        df = df.drop(columns=['Pos_x', 'Pos_y'])
    
    # Merge duplicate date columns
    if 'Injury / Surgery Date_x' in df.columns and 'Injury / Surgery Date_y' in df.columns:
        df['Injury / Surgery Date'] = df['Injury / Surgery Date_x'].fillna(df['Injury / Surgery Date_y'])
        df = df.drop(columns=['Injury / Surgery Date_x', 'Injury / Surgery Date_y'])
    
    # Fill missing injury descriptions
    if 'Injury / Surgery' in df.columns:
        df['Injury / Surgery'] = df['Injury / Surgery'].fillna('Tommy John surgery')
    
    # Convert dates and extract year
    df['Injury / Surgery Date'] = pd.to_datetime(df['Injury / Surgery Date'], errors='coerce')
    df = df.dropna(subset=['Injury / Surgery Date'])
    df['Injury_Year'] = df['Injury / Surgery Date'].dt.year
    
    # Standardize positions
    pitcher_positions = ['RP', 'SP', 'SP/RP', 'Pitcher / Outfielder', 'Pitcher / Designated hitter']
    df['Pos'] = df['Pos'].replace(pitcher_positions, 'Pitcher')
    
    # Filter for pitchers only
    df = df[df['Pos'] == 'Pitcher']
    
    return df


def display_data_info(df, name="DataFrame"):
    """
    Display basic information about a DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame to analyze
        name (str): Name for display purposes
    """
    if df is None:
        print(f"{name} is None")
        return
    
    print(f"\n{name} Information:")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst 5 rows:")
    print(df.head())


def get_player_id(name):
    """
    Get player ID from name using pybaseball lookup
    """
    try:
        original_name = name
        
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
                    return manual_ids[original_name], None
            return None
        mlb_id = lookup.iloc[0]['key_mlbam']
        lahman_id = lookup.iloc[0]['key_bbref']
        return mlb_id, lahman_id
    except Exception as e:
        return None


def calculate_avg_pitches_playoff(player_id, lahman_id, season):
    """
    Calculate average pitches per playoff game for a player in a season.
    
    Args:
        player_id (str): MLB player ID
        lahman_id (str): Lahman player ID
        season (int): Season year
        
    Returns:
        float: Average pitches per playoff game or None if not available
    """
    if season < 2015:
        return None  # Statcast data starts from 2015
    
    try:
        start_date = f'{season}-01-01'
        end_date = f'{season}-12-31'
        data = pb.statcast_pitcher(start_date, end_date, player_id)
        
        if data is None or data.empty:
            return None
        
        # Filter for playoffs
        playoffs = data[data['game_type'].isin(['D', 'L', 'W'])]
        
        if playoffs.empty:
            return None
        
        # Group by game_pk, count pitches
        pitches_per_game = playoffs.groupby('game_pk').size()
        
        # Average
        return pitches_per_game.mean()
        
    except Exception as e:
        return None


def calculate_avg_pitches_regular(player_id, lahman_id, season):
    """
    Calculate average pitches per regular season game for a player in a season.
    
    Args:
        player_id (str): MLB player ID
        lahman_id (str): Lahman player ID
        season (int): Season year
        
    Returns:
        float: Average pitches per regular season game or None if not available
    """
    global pitching_reg

    if season < 2015 and pitching_reg is not None and lahman_id is not None:
        player_reg = pitching_reg[(pitching_reg['playerID'] == lahman_id) & (pitching_reg['yearID'] == season)]
        if not player_reg.empty:
            total_ipouts = player_reg['IPouts'].sum()
            total_bf = player_reg['BFP'].sum()
            total_games = player_reg['G'].sum()
            if total_games > 0:
                estimated_pitches = total_ipouts + total_bf
                return estimated_pitches / total_games
        return None
    elif season >= 2015:
        start_date = f'{season}-01-01'
        end_date = f'{season}-12-31'
        data = pb.statcast_pitcher(start_date, end_date, player_id)
        
        if data is None or data.empty:
            return None
        
        # Filter for regular season
        regular = data[data['game_type'] == 'R']
        
        if regular.empty:
            return None
        
        pitches_per_game = regular.groupby('game_pk').size()
        
        return pitches_per_game.mean()
    else:
        return None


def main():
    """
    Main function to run the baseball injury data analysis.
    """
    print("Baseball Injury Data Analysis")
    print("=" * 40)
    
    output_path = 'processed_baseball_injuries.csv'
    if os.path.exists(output_path):
        processed_data = pd.read_csv(output_path)
        new_columns_added = False
        avg_columns = ['avg_pitches_t_minus_4', 'avg_pitches_t_minus_3', 'avg_pitches_t_minus_2', 'avg_pitches_before', 'avg_pitches_after', 'avg_pitches_t_plus_2', 'avg_pitches_t_plus_3', 'avg_pitches_t_plus_4', 'avg_pitches_regular_t_minus_4', 'avg_pitches_regular_t_minus_3', 'avg_pitches_regular_t_minus_2', 'avg_pitches_regular_t_minus_1', 'avg_pitches_regular_t_plus_1', 'avg_pitches_regular_t_plus_2', 'avg_pitches_regular_t_plus_3', 'avg_pitches_regular_t_plus_4']
        for col in avg_columns:
            if col not in processed_data.columns:
                processed_data[col] = None
                new_columns_added = True
        display_data_info(processed_data, "Loaded Processed Injury Data")
        print(f"Loaded dataset contains {len(processed_data)} pitcher injuries")
        if not new_columns_added:
            return
        # Proceed to compute missing data
        cleaned_data = processed_data
        final_count = len(cleaned_data)
        
        # Load Lahman data
        pitching_post_path = 'lahman_1871-2025_csv/PitchingPost.csv'
        if os.path.exists(pitching_post_path):
            global pitching_post
            pitching_post = pd.read_csv(pitching_post_path)
            print("Loaded Lahman PitchingPost data.")
        else:
            print("Lahman PitchingPost.csv not found.")
        
        # Load Lahman regular data
        pitching_reg_path = 'lahman_1871-2025_csv/Pitching.csv'
        if os.path.exists(pitching_reg_path):
            global pitching_reg
            pitching_reg = pd.read_csv(pitching_reg_path)
            print("Loaded Lahman Pitching data.")
        else:
            print("Lahman Pitching.csv not found.")
        
        print("\n4. Computing average pitches per playoff game...")
        
        def compute_averages(idx, player_id, lahman_id, injury_year):
            t_minus_4_season = injury_year - 4
            t_minus_3_season = injury_year - 3
            t_minus_2_season = injury_year - 2
            t_minus_1_season = injury_year - 1
            t_plus_1_season = injury_year + 1
            t_plus_2_season = injury_year + 2
            t_plus_3_season = injury_year + 3
            t_plus_4_season = injury_year + 4
            
            if ('avg_pitches_t_minus_4' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_t_minus_4'] is not None and
                'avg_pitches_t_minus_3' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_t_minus_3'] is not None and
                'avg_pitches_t_minus_2' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_t_minus_2'] is not None and
                'avg_pitches_before' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_before'] is not None and
                'avg_pitches_after' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_after'] is not None and
                'avg_pitches_t_plus_2' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_t_plus_2'] is not None and
                'avg_pitches_t_plus_3' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_t_plus_3'] is not None and
                'avg_pitches_t_plus_4' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_t_plus_4'] is not None and
                'avg_pitches_regular_t_minus_4' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_regular_t_minus_4'] is not None and
                'avg_pitches_regular_t_minus_3' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_regular_t_minus_3'] is not None and
                'avg_pitches_regular_t_minus_2' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_regular_t_minus_2'] is not None and
                'avg_pitches_regular_t_minus_1' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_regular_t_minus_1'] is not None and
                'avg_pitches_regular_t_plus_1' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_regular_t_plus_1'] is not None and
                'avg_pitches_regular_t_plus_2' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_regular_t_plus_2'] is not None and
                'avg_pitches_regular_t_plus_3' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_regular_t_plus_3'] is not None and
                'avg_pitches_regular_t_plus_4' in cleaned_data.columns and cleaned_data.at[idx, 'avg_pitches_regular_t_plus_4'] is not None):
                avg_t_minus_4 = cleaned_data.at[idx, 'avg_pitches_t_minus_4']
                avg_t_minus_3 = cleaned_data.at[idx, 'avg_pitches_t_minus_3']
                avg_t_minus_2 = cleaned_data.at[idx, 'avg_pitches_t_minus_2']
                avg_before = cleaned_data.at[idx, 'avg_pitches_before']
                avg_after = cleaned_data.at[idx, 'avg_pitches_after']
                avg_t_plus_2 = cleaned_data.at[idx, 'avg_pitches_t_plus_2']
                avg_t_plus_3 = cleaned_data.at[idx, 'avg_pitches_t_plus_3']
                avg_t_plus_4 = cleaned_data.at[idx, 'avg_pitches_t_plus_4']
                avg_regular_t_minus_4 = cleaned_data.at[idx, 'avg_pitches_regular_t_minus_4']
                avg_regular_t_minus_3 = cleaned_data.at[idx, 'avg_pitches_regular_t_minus_3']
                avg_regular_t_minus_2 = cleaned_data.at[idx, 'avg_pitches_regular_t_minus_2']
                avg_regular_t_minus_1 = cleaned_data.at[idx, 'avg_pitches_regular_t_minus_1']
                avg_regular_t_plus_1 = cleaned_data.at[idx, 'avg_pitches_regular_t_plus_1']
                avg_regular_t_plus_2 = cleaned_data.at[idx, 'avg_pitches_regular_t_plus_2']
                avg_regular_t_plus_3 = cleaned_data.at[idx, 'avg_pitches_regular_t_plus_3']
                avg_regular_t_plus_4 = cleaned_data.at[idx, 'avg_pitches_regular_t_plus_4']
            else:
                avg_t_minus_4 = calculate_avg_pitches_playoff(player_id, lahman_id, t_minus_4_season)
                avg_t_minus_3 = calculate_avg_pitches_playoff(player_id, lahman_id, t_minus_3_season)
                avg_t_minus_2 = calculate_avg_pitches_playoff(player_id, lahman_id, t_minus_2_season)
                avg_before = calculate_avg_pitches_playoff(player_id, lahman_id, t_minus_1_season)
                avg_after = calculate_avg_pitches_playoff(player_id, lahman_id, t_plus_1_season)
                avg_t_plus_2 = calculate_avg_pitches_playoff(player_id, lahman_id, t_plus_2_season)
                avg_t_plus_3 = calculate_avg_pitches_playoff(player_id, lahman_id, t_plus_3_season)
                avg_t_plus_4 = calculate_avg_pitches_playoff(player_id, lahman_id, t_plus_4_season)
                avg_regular_t_minus_4 = calculate_avg_pitches_regular(player_id, lahman_id, t_minus_4_season)
                avg_regular_t_minus_3 = calculate_avg_pitches_regular(player_id, lahman_id, t_minus_3_season)
                avg_regular_t_minus_2 = calculate_avg_pitches_regular(player_id, lahman_id, t_minus_2_season)
                avg_regular_t_minus_1 = calculate_avg_pitches_regular(player_id, lahman_id, t_minus_1_season)
                avg_regular_t_plus_1 = calculate_avg_pitches_regular(player_id, lahman_id, t_plus_1_season)
                avg_regular_t_plus_2 = calculate_avg_pitches_regular(player_id, lahman_id, t_plus_2_season)
                avg_regular_t_plus_3 = calculate_avg_pitches_regular(player_id, lahman_id, t_plus_3_season)
                avg_regular_t_plus_4 = calculate_avg_pitches_regular(player_id, lahman_id, t_plus_4_season)
            return (idx, avg_t_minus_4, avg_t_minus_3, avg_t_minus_2, avg_before, avg_after, avg_t_plus_2, avg_t_plus_3, avg_t_plus_4,
                    avg_regular_t_minus_4, avg_regular_t_minus_3, avg_regular_t_minus_2, avg_regular_t_minus_1, avg_regular_t_plus_1, avg_regular_t_plus_2, avg_regular_t_plus_3, avg_regular_t_plus_4)
        
        players_no_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(compute_averages, idx, row['player_id'], row['lahman_id'], row['Injury_Year']) for idx, row in cleaned_data.iterrows()]
            for future in concurrent.futures.as_completed(futures):
                (idx, avg_t_minus_4, avg_t_minus_3, avg_t_minus_2, avg_before, avg_after, avg_t_plus_2, avg_t_plus_3, avg_t_plus_4,
                 avg_regular_t_minus_4, avg_regular_t_minus_3, avg_regular_t_minus_2, avg_regular_t_minus_1, avg_regular_t_plus_1, avg_regular_t_plus_2, avg_regular_t_plus_3, avg_regular_t_plus_4) = future.result()
                cleaned_data.at[idx, 'avg_pitches_t_minus_4'] = avg_t_minus_4
                cleaned_data.at[idx, 'avg_pitches_t_minus_3'] = avg_t_minus_3
                cleaned_data.at[idx, 'avg_pitches_t_minus_2'] = avg_t_minus_2
                cleaned_data.at[idx, 'avg_pitches_before'] = avg_before
                cleaned_data.at[idx, 'avg_pitches_after'] = avg_after
                cleaned_data.at[idx, 'avg_pitches_t_plus_2'] = avg_t_plus_2
                cleaned_data.at[idx, 'avg_pitches_t_plus_3'] = avg_t_plus_3
                cleaned_data.at[idx, 'avg_pitches_t_plus_4'] = avg_t_plus_4
                cleaned_data.at[idx, 'avg_pitches_regular_t_minus_4'] = avg_regular_t_minus_4
                cleaned_data.at[idx, 'avg_pitches_regular_t_minus_3'] = avg_regular_t_minus_3
                cleaned_data.at[idx, 'avg_pitches_regular_t_minus_2'] = avg_regular_t_minus_2
                cleaned_data.at[idx, 'avg_pitches_regular_t_minus_1'] = avg_regular_t_minus_1
                cleaned_data.at[idx, 'avg_pitches_regular_t_plus_1'] = avg_regular_t_plus_1
                cleaned_data.at[idx, 'avg_pitches_regular_t_plus_2'] = avg_regular_t_plus_2
                cleaned_data.at[idx, 'avg_pitches_regular_t_plus_3'] = avg_regular_t_plus_3
                cleaned_data.at[idx, 'avg_pitches_regular_t_plus_4'] = avg_regular_t_plus_4
                if (avg_t_minus_4 is None and avg_t_minus_3 is None and avg_t_minus_2 is None and avg_before is None and 
                    avg_after is None and avg_t_plus_2 is None and avg_t_plus_3 is None and avg_t_plus_4 is None):
                    players_no_data.append(cleaned_data.at[idx, 'Name'])
        
        if players_no_data:
            print("Players with no playoff pitch data for any of T-4 to T+4:")
            for p in players_no_data:
                print(p)
        
        print(f"Final dataset contains {final_count} pitcher injuries")
        
        # Save processed data
        cleaned_data.to_csv(output_path, index=False)
        print(f"Processed data saved to: {output_path}")
        return


if __name__ == "__main__":
    main()
