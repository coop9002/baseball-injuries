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


def calculate_avg_spin_rate(player_id, season):
    """
    Calculate average spin rate for a player in a season.
    
    Args:
        player_id (str): MLB player ID
        season (int): Season year
        
    Returns:
        float: Average spin rate or None if not available
    """
    if season < 2015:
        return None
    
    try:
        start_date = f'{season}-01-01'
        end_date = f'{season}-12-31'
        data = pb.statcast_pitcher(start_date, end_date, player_id)
        
        if data is None or data.empty:
            return None
        
        if 'release_spin_rate' not in data.columns:
            return None
        
        spin_data = data['release_spin_rate'].dropna()
        
        if spin_data.empty:
            return None
        
        return spin_data.mean()
        
    except Exception as e:
        return None


def calculate_avg_pitch_velocity(player_id, season):
    """
    Calculate average pitch velocity for a player in a season (excluding playoff games).
    
    Args:
        player_id (str): MLB player ID
        season (int): Season year
        
    Returns:
        float: Average pitch velocity or None if not available
    """
    if season < 2015:
        return None
    
    try:
        start_date = f'{season}-01-01'
        end_date = f'{season}-12-31'
        data = pb.statcast_pitcher(start_date, end_date, player_id)
        
        if data is None or data.empty:
            return None
        
        regular_season = data[data['game_type'] == 'R']
        
        if regular_season.empty:
            return None
        
        if 'release_speed' not in regular_season.columns:
            return None
        
        velocity_data = regular_season['release_speed'].dropna()
        
        if velocity_data.empty:
            return None
        
        return velocity_data.mean()
        
    except Exception as e:
        return None


def calculate_avg_velocity_playoff(player_id, season):
    """
    Calculate average pitch velocity per playoff game for a player in a season.
    
    Args:
        player_id (str): MLB player ID
        season (int): Season year
        
    Returns:
        float: Average pitch velocity per playoff game or None if not available
    """
    if season < 2015:
        return None
    
    try:
        start_date = f'{season}-01-01'
        end_date = f'{season}-12-31'
        data = pb.statcast_pitcher(start_date, end_date, player_id)
        
        if data is None or data.empty:
            return None
        
        playoffs = data[data['game_type'].isin(['D', 'L', 'W'])]
        
        if playoffs.empty:
            return None
        
        if 'release_speed' not in playoffs.columns:
            return None
        
        velocity_data = playoffs['release_speed'].dropna()
        
        if velocity_data.empty:
            return None
        
        return velocity_data.mean()
        
    except Exception as e:
        return None


def calculate_games_started(player_id, lahman_id, season):
    """
    Calculate games started for a player in a season.
    
    Args:
        player_id (str): MLB player ID
        lahman_id (str): Lahman player ID
        season (int): Season year
        
    Returns:
        int: Games started or None if not available
    """
    global pitching_reg
    
    if pitching_reg is not None and lahman_id is not None:
        player_reg = pitching_reg[(pitching_reg['playerID'] == lahman_id) & (pitching_reg['yearID'] == season)]
        if not player_reg.empty:
            gs = player_reg['GS'].sum()
            return int(gs) if gs > 0 else 0
    
    if season >= 2015:
        try:
            start_date = f'{season}-01-01'
            end_date = f'{season}-12-31'
            data = pb.statcast_pitcher(start_date, end_date, player_id)
            
            if data is None or data.empty:
                return None
            
            regular_season = data[data['game_type'] == 'R']
            
            if regular_season.empty:
                return None
            
            if 'game_pk' not in regular_season.columns or 'inning' not in regular_season.columns:
                return None
            
            games_started = 0
            for game_id in regular_season['game_pk'].unique():
                game_data = regular_season[regular_season['game_pk'] == game_id]
                if not game_data.empty and game_data['inning'].min() == 1:
                    games_started += 1
            
            return games_started if games_started > 0 else 0
            
        except Exception as e:
            return None
    
    return None


def calculate_saves(player_id, lahman_id, season):
    """
    Calculate saves for a player in a season.
    
    Args:
        player_id (str): MLB player ID
        lahman_id (str): Lahman player ID
        season (int): Season year
        
    Returns:
        int: Saves or None if not available
    """
    global pitching_reg
    
    if pitching_reg is not None and lahman_id is not None:
        player_reg = pitching_reg[(pitching_reg['playerID'] == lahman_id) & (pitching_reg['yearID'] == season)]
        if not player_reg.empty:
            sv = player_reg['SV'].sum()
            return int(sv) if sv > 0 else 0
    
    return None


def calculate_relief_appearances(player_id, lahman_id, season):
    """
    Calculate relief appearances (games without starts) for a player in a season.
    
    Args:
        player_id (str): MLB player ID
        lahman_id (str): Lahman player ID
        season (int): Season year
        
    Returns:
        int: Relief appearances or None if not available
    """
    global pitching_reg
    
    if pitching_reg is not None and lahman_id is not None:
        player_reg = pitching_reg[(pitching_reg['playerID'] == lahman_id) & (pitching_reg['yearID'] == season)]
        if not player_reg.empty:
            g = player_reg['G'].sum()
            gs = player_reg['GS'].sum()
            relief = g - gs
            return int(relief) if relief > 0 else 0
    
    if season >= 2015:
        try:
            start_date = f'{season}-01-01'
            end_date = f'{season}-12-31'
            data = pb.statcast_pitcher(start_date, end_date, player_id)
            
            if data is None or data.empty:
                return None
            
            regular_season = data[data['game_type'] == 'R']
            
            if regular_season.empty:
                return None
            
            if 'game_pk' not in regular_season.columns or 'inning' not in regular_season.columns:
                return None
            
            total_games = regular_season['game_pk'].nunique()
            games_started = 0
            for game_id in regular_season['game_pk'].unique():
                game_data = regular_season[regular_season['game_pk'] == game_id]
                if not game_data.empty and game_data['inning'].min() == 1:
                    games_started += 1
            
            relief = total_games - games_started
            return relief if relief > 0 else 0
            
        except Exception as e:
            return None
    
    return None


def calculate_pitch_mix(player_id, season):
    """
    Calculate pitch mix percentages for a player in a season.
    Returns percentages for major pitch types: FF, SI, SL, CU, CH, FC.
    
    Args:
        player_id (str): MLB player ID
        season (int): Season year
        
    Returns:
        dict: Dictionary with pitch type percentages (FF, SI, SL, CU, CH, FC) or None if not available
    """
    if season < 2015:
        return None
    
    try:
        start_date = f'{season}-01-01'
        end_date = f'{season}-12-31'
        data = pb.statcast_pitcher(start_date, end_date, player_id)
        
        if data is None or data.empty:
            return None
        
        regular_season = data[data['game_type'] == 'R']
        
        if regular_season.empty:
            return None
        
        if 'pitch_type' not in regular_season.columns:
            return None
        
        pitch_counts = regular_season['pitch_type'].value_counts()
        total_pitches = len(regular_season)
        
        if total_pitches == 0:
            return None
        
        pitch_types = ['FF', 'SI', 'SL', 'CU', 'CH', 'FC']
        pitch_mix = {}
        
        for pitch_type in pitch_types:
            if pitch_type in pitch_counts.index:
                percentage = (pitch_counts[pitch_type] / total_pitches) * 100
                pitch_mix[pitch_type] = round(percentage, 2)
            else:
                pitch_mix[pitch_type] = 0.0
        
        return pitch_mix
        
    except Exception as e:
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
        pitch_types = ['FF', 'SI', 'SL', 'CU', 'CH', 'FC']
        time_periods = ['t_minus_4', 't_minus_3', 't_minus_2', 't_minus_1', 't_plus_1', 't_plus_2', 't_plus_3', 't_plus_4']
        pitch_mix_columns = [f'{pitch_type.lower()}_pct_{period}' for pitch_type in pitch_types for period in time_periods]
        
        avg_columns = ['avg_pitches_t_minus_4', 'avg_pitches_t_minus_3', 'avg_pitches_t_minus_2', 'avg_pitches_before', 'avg_pitches_after', 'avg_pitches_t_plus_2', 'avg_pitches_t_plus_3', 'avg_pitches_t_plus_4', 'avg_pitches_regular_t_minus_4', 'avg_pitches_regular_t_minus_3', 'avg_pitches_regular_t_minus_2', 'avg_pitches_regular_t_minus_1', 'avg_pitches_regular_t_plus_1', 'avg_pitches_regular_t_plus_2', 'avg_pitches_regular_t_plus_3', 'avg_pitches_regular_t_plus_4', 'avg_spin_rate_t_minus_4', 'avg_spin_rate_t_minus_3', 'avg_spin_rate_t_minus_2', 'avg_spin_rate_t_minus_1', 'avg_spin_rate_t_plus_1', 'avg_spin_rate_t_plus_2', 'avg_spin_rate_t_plus_3', 'avg_spin_rate_t_plus_4', 'avg_velocity_t_minus_4', 'avg_velocity_t_minus_3', 'avg_velocity_t_minus_2', 'avg_velocity_t_minus_1', 'avg_velocity_t_plus_1', 'avg_velocity_t_plus_2', 'avg_velocity_t_plus_3', 'avg_velocity_t_plus_4', 'avg_velocity_playoff_t_minus_4', 'avg_velocity_playoff_t_minus_3', 'avg_velocity_playoff_t_minus_2', 'avg_velocity_playoff_t_minus_1', 'avg_velocity_playoff_t_plus_1', 'avg_velocity_playoff_t_plus_2', 'avg_velocity_playoff_t_plus_3', 'avg_velocity_playoff_t_plus_4', 'gs_t_minus_4', 'gs_t_minus_3', 'gs_t_minus_2', 'gs_t_minus_1', 'gs_t_plus_1', 'gs_t_plus_2', 'gs_t_plus_3', 'gs_t_plus_4', 'sv_t_minus_4', 'sv_t_minus_3', 'sv_t_minus_2', 'sv_t_minus_1', 'sv_t_plus_1', 'sv_t_plus_2', 'sv_t_plus_3', 'sv_t_plus_4', 'relief_app_t_minus_4', 'relief_app_t_minus_3', 'relief_app_t_minus_2', 'relief_app_t_minus_1', 'relief_app_t_plus_1', 'relief_app_t_plus_2', 'relief_app_t_plus_3', 'relief_app_t_plus_4'] + pitch_mix_columns
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
            
            def get_or_compute(col_name, compute_func, *args):
                if col_name in cleaned_data.columns and pd.notna(cleaned_data.at[idx, col_name]):
                    return cleaned_data.at[idx, col_name]
                return compute_func(*args)
            
            avg_t_minus_4 = get_or_compute('avg_pitches_t_minus_4', calculate_avg_pitches_playoff, player_id, lahman_id, t_minus_4_season)
            avg_t_minus_3 = get_or_compute('avg_pitches_t_minus_3', calculate_avg_pitches_playoff, player_id, lahman_id, t_minus_3_season)
            avg_t_minus_2 = get_or_compute('avg_pitches_t_minus_2', calculate_avg_pitches_playoff, player_id, lahman_id, t_minus_2_season)
            avg_before = get_or_compute('avg_pitches_before', calculate_avg_pitches_playoff, player_id, lahman_id, t_minus_1_season)
            avg_after = get_or_compute('avg_pitches_after', calculate_avg_pitches_playoff, player_id, lahman_id, t_plus_1_season)
            avg_t_plus_2 = get_or_compute('avg_pitches_t_plus_2', calculate_avg_pitches_playoff, player_id, lahman_id, t_plus_2_season)
            avg_t_plus_3 = get_or_compute('avg_pitches_t_plus_3', calculate_avg_pitches_playoff, player_id, lahman_id, t_plus_3_season)
            avg_t_plus_4 = get_or_compute('avg_pitches_t_plus_4', calculate_avg_pitches_playoff, player_id, lahman_id, t_plus_4_season)
            
            avg_regular_t_minus_4 = get_or_compute('avg_pitches_regular_t_minus_4', calculate_avg_pitches_regular, player_id, lahman_id, t_minus_4_season)
            avg_regular_t_minus_3 = get_or_compute('avg_pitches_regular_t_minus_3', calculate_avg_pitches_regular, player_id, lahman_id, t_minus_3_season)
            avg_regular_t_minus_2 = get_or_compute('avg_pitches_regular_t_minus_2', calculate_avg_pitches_regular, player_id, lahman_id, t_minus_2_season)
            avg_regular_t_minus_1 = get_or_compute('avg_pitches_regular_t_minus_1', calculate_avg_pitches_regular, player_id, lahman_id, t_minus_1_season)
            avg_regular_t_plus_1 = get_or_compute('avg_pitches_regular_t_plus_1', calculate_avg_pitches_regular, player_id, lahman_id, t_plus_1_season)
            avg_regular_t_plus_2 = get_or_compute('avg_pitches_regular_t_plus_2', calculate_avg_pitches_regular, player_id, lahman_id, t_plus_2_season)
            avg_regular_t_plus_3 = get_or_compute('avg_pitches_regular_t_plus_3', calculate_avg_pitches_regular, player_id, lahman_id, t_plus_3_season)
            avg_regular_t_plus_4 = get_or_compute('avg_pitches_regular_t_plus_4', calculate_avg_pitches_regular, player_id, lahman_id, t_plus_4_season)
            
            avg_spin_t_minus_4 = get_or_compute('avg_spin_rate_t_minus_4', calculate_avg_spin_rate, player_id, t_minus_4_season)
            avg_spin_t_minus_3 = get_or_compute('avg_spin_rate_t_minus_3', calculate_avg_spin_rate, player_id, t_minus_3_season)
            avg_spin_t_minus_2 = get_or_compute('avg_spin_rate_t_minus_2', calculate_avg_spin_rate, player_id, t_minus_2_season)
            avg_spin_t_minus_1 = get_or_compute('avg_spin_rate_t_minus_1', calculate_avg_spin_rate, player_id, t_minus_1_season)
            avg_spin_t_plus_1 = get_or_compute('avg_spin_rate_t_plus_1', calculate_avg_spin_rate, player_id, t_plus_1_season)
            avg_spin_t_plus_2 = get_or_compute('avg_spin_rate_t_plus_2', calculate_avg_spin_rate, player_id, t_plus_2_season)
            avg_spin_t_plus_3 = get_or_compute('avg_spin_rate_t_plus_3', calculate_avg_spin_rate, player_id, t_plus_3_season)
            avg_spin_t_plus_4 = get_or_compute('avg_spin_rate_t_plus_4', calculate_avg_spin_rate, player_id, t_plus_4_season)
            
            avg_velocity_t_minus_4 = get_or_compute('avg_velocity_t_minus_4', calculate_avg_pitch_velocity, player_id, t_minus_4_season)
            avg_velocity_t_minus_3 = get_or_compute('avg_velocity_t_minus_3', calculate_avg_pitch_velocity, player_id, t_minus_3_season)
            avg_velocity_t_minus_2 = get_or_compute('avg_velocity_t_minus_2', calculate_avg_pitch_velocity, player_id, t_minus_2_season)
            avg_velocity_t_minus_1 = get_or_compute('avg_velocity_t_minus_1', calculate_avg_pitch_velocity, player_id, t_minus_1_season)
            avg_velocity_t_plus_1 = get_or_compute('avg_velocity_t_plus_1', calculate_avg_pitch_velocity, player_id, t_plus_1_season)
            avg_velocity_t_plus_2 = get_or_compute('avg_velocity_t_plus_2', calculate_avg_pitch_velocity, player_id, t_plus_2_season)
            avg_velocity_t_plus_3 = get_or_compute('avg_velocity_t_plus_3', calculate_avg_pitch_velocity, player_id, t_plus_3_season)
            avg_velocity_t_plus_4 = get_or_compute('avg_velocity_t_plus_4', calculate_avg_pitch_velocity, player_id, t_plus_4_season)
            
            avg_velocity_playoff_t_minus_4 = get_or_compute('avg_velocity_playoff_t_minus_4', calculate_avg_velocity_playoff, player_id, t_minus_4_season)
            avg_velocity_playoff_t_minus_3 = get_or_compute('avg_velocity_playoff_t_minus_3', calculate_avg_velocity_playoff, player_id, t_minus_3_season)
            avg_velocity_playoff_t_minus_2 = get_or_compute('avg_velocity_playoff_t_minus_2', calculate_avg_velocity_playoff, player_id, t_minus_2_season)
            avg_velocity_playoff_t_minus_1 = get_or_compute('avg_velocity_playoff_t_minus_1', calculate_avg_velocity_playoff, player_id, t_minus_1_season)
            avg_velocity_playoff_t_plus_1 = get_or_compute('avg_velocity_playoff_t_plus_1', calculate_avg_velocity_playoff, player_id, t_plus_1_season)
            avg_velocity_playoff_t_plus_2 = get_or_compute('avg_velocity_playoff_t_plus_2', calculate_avg_velocity_playoff, player_id, t_plus_2_season)
            avg_velocity_playoff_t_plus_3 = get_or_compute('avg_velocity_playoff_t_plus_3', calculate_avg_velocity_playoff, player_id, t_plus_3_season)
            avg_velocity_playoff_t_plus_4 = get_or_compute('avg_velocity_playoff_t_plus_4', calculate_avg_velocity_playoff, player_id, t_plus_4_season)
            
            gs_t_minus_4 = get_or_compute('gs_t_minus_4', calculate_games_started, player_id, lahman_id, t_minus_4_season)
            gs_t_minus_3 = get_or_compute('gs_t_minus_3', calculate_games_started, player_id, lahman_id, t_minus_3_season)
            gs_t_minus_2 = get_or_compute('gs_t_minus_2', calculate_games_started, player_id, lahman_id, t_minus_2_season)
            gs_t_minus_1 = get_or_compute('gs_t_minus_1', calculate_games_started, player_id, lahman_id, t_minus_1_season)
            gs_t_plus_1 = get_or_compute('gs_t_plus_1', calculate_games_started, player_id, lahman_id, t_plus_1_season)
            gs_t_plus_2 = get_or_compute('gs_t_plus_2', calculate_games_started, player_id, lahman_id, t_plus_2_season)
            gs_t_plus_3 = get_or_compute('gs_t_plus_3', calculate_games_started, player_id, lahman_id, t_plus_3_season)
            gs_t_plus_4 = get_or_compute('gs_t_plus_4', calculate_games_started, player_id, lahman_id, t_plus_4_season)
            
            sv_t_minus_4 = get_or_compute('sv_t_minus_4', calculate_saves, player_id, lahman_id, t_minus_4_season)
            sv_t_minus_3 = get_or_compute('sv_t_minus_3', calculate_saves, player_id, lahman_id, t_minus_3_season)
            sv_t_minus_2 = get_or_compute('sv_t_minus_2', calculate_saves, player_id, lahman_id, t_minus_2_season)
            sv_t_minus_1 = get_or_compute('sv_t_minus_1', calculate_saves, player_id, lahman_id, t_minus_1_season)
            sv_t_plus_1 = get_or_compute('sv_t_plus_1', calculate_saves, player_id, lahman_id, t_plus_1_season)
            sv_t_plus_2 = get_or_compute('sv_t_plus_2', calculate_saves, player_id, lahman_id, t_plus_2_season)
            sv_t_plus_3 = get_or_compute('sv_t_plus_3', calculate_saves, player_id, lahman_id, t_plus_3_season)
            sv_t_plus_4 = get_or_compute('sv_t_plus_4', calculate_saves, player_id, lahman_id, t_plus_4_season)
            
            relief_app_t_minus_4 = get_or_compute('relief_app_t_minus_4', calculate_relief_appearances, player_id, lahman_id, t_minus_4_season)
            relief_app_t_minus_3 = get_or_compute('relief_app_t_minus_3', calculate_relief_appearances, player_id, lahman_id, t_minus_3_season)
            relief_app_t_minus_2 = get_or_compute('relief_app_t_minus_2', calculate_relief_appearances, player_id, lahman_id, t_minus_2_season)
            relief_app_t_minus_1 = get_or_compute('relief_app_t_minus_1', calculate_relief_appearances, player_id, lahman_id, t_minus_1_season)
            relief_app_t_plus_1 = get_or_compute('relief_app_t_plus_1', calculate_relief_appearances, player_id, lahman_id, t_plus_1_season)
            relief_app_t_plus_2 = get_or_compute('relief_app_t_plus_2', calculate_relief_appearances, player_id, lahman_id, t_plus_2_season)
            relief_app_t_plus_3 = get_or_compute('relief_app_t_plus_3', calculate_relief_appearances, player_id, lahman_id, t_plus_3_season)
            relief_app_t_plus_4 = get_or_compute('relief_app_t_plus_4', calculate_relief_appearances, player_id, lahman_id, t_plus_4_season)
            
            def get_pitch_mix_value(pitch_mix_dict, pitch_type, period):
                col_name = f'{pitch_type.lower()}_pct_{period}'
                if col_name in cleaned_data.columns and pd.notna(cleaned_data.at[idx, col_name]):
                    return cleaned_data.at[idx, col_name]
                if pitch_mix_dict is None:
                    return None
                return pitch_mix_dict.get(pitch_type, 0.0)
            
            pitch_mix_t_minus_4 = calculate_pitch_mix(player_id, t_minus_4_season)
            pitch_mix_t_minus_3 = calculate_pitch_mix(player_id, t_minus_3_season)
            pitch_mix_t_minus_2 = calculate_pitch_mix(player_id, t_minus_2_season)
            pitch_mix_t_minus_1 = calculate_pitch_mix(player_id, t_minus_1_season)
            pitch_mix_t_plus_1 = calculate_pitch_mix(player_id, t_plus_1_season)
            pitch_mix_t_plus_2 = calculate_pitch_mix(player_id, t_plus_2_season)
            pitch_mix_t_plus_3 = calculate_pitch_mix(player_id, t_plus_3_season)
            pitch_mix_t_plus_4 = calculate_pitch_mix(player_id, t_plus_4_season)
            
            ff_pct_t_minus_4 = get_pitch_mix_value(pitch_mix_t_minus_4, 'FF', 't_minus_4')
            ff_pct_t_minus_3 = get_pitch_mix_value(pitch_mix_t_minus_3, 'FF', 't_minus_3')
            ff_pct_t_minus_2 = get_pitch_mix_value(pitch_mix_t_minus_2, 'FF', 't_minus_2')
            ff_pct_t_minus_1 = get_pitch_mix_value(pitch_mix_t_minus_1, 'FF', 't_minus_1')
            ff_pct_t_plus_1 = get_pitch_mix_value(pitch_mix_t_plus_1, 'FF', 't_plus_1')
            ff_pct_t_plus_2 = get_pitch_mix_value(pitch_mix_t_plus_2, 'FF', 't_plus_2')
            ff_pct_t_plus_3 = get_pitch_mix_value(pitch_mix_t_plus_3, 'FF', 't_plus_3')
            ff_pct_t_plus_4 = get_pitch_mix_value(pitch_mix_t_plus_4, 'FF', 't_plus_4')
            
            si_pct_t_minus_4 = get_pitch_mix_value(pitch_mix_t_minus_4, 'SI', 't_minus_4')
            si_pct_t_minus_3 = get_pitch_mix_value(pitch_mix_t_minus_3, 'SI', 't_minus_3')
            si_pct_t_minus_2 = get_pitch_mix_value(pitch_mix_t_minus_2, 'SI', 't_minus_2')
            si_pct_t_minus_1 = get_pitch_mix_value(pitch_mix_t_minus_1, 'SI', 't_minus_1')
            si_pct_t_plus_1 = get_pitch_mix_value(pitch_mix_t_plus_1, 'SI', 't_plus_1')
            si_pct_t_plus_2 = get_pitch_mix_value(pitch_mix_t_plus_2, 'SI', 't_plus_2')
            si_pct_t_plus_3 = get_pitch_mix_value(pitch_mix_t_plus_3, 'SI', 't_plus_3')
            si_pct_t_plus_4 = get_pitch_mix_value(pitch_mix_t_plus_4, 'SI', 't_plus_4')
            
            sl_pct_t_minus_4 = get_pitch_mix_value(pitch_mix_t_minus_4, 'SL', 't_minus_4')
            sl_pct_t_minus_3 = get_pitch_mix_value(pitch_mix_t_minus_3, 'SL', 't_minus_3')
            sl_pct_t_minus_2 = get_pitch_mix_value(pitch_mix_t_minus_2, 'SL', 't_minus_2')
            sl_pct_t_minus_1 = get_pitch_mix_value(pitch_mix_t_minus_1, 'SL', 't_minus_1')
            sl_pct_t_plus_1 = get_pitch_mix_value(pitch_mix_t_plus_1, 'SL', 't_plus_1')
            sl_pct_t_plus_2 = get_pitch_mix_value(pitch_mix_t_plus_2, 'SL', 't_plus_2')
            sl_pct_t_plus_3 = get_pitch_mix_value(pitch_mix_t_plus_3, 'SL', 't_plus_3')
            sl_pct_t_plus_4 = get_pitch_mix_value(pitch_mix_t_plus_4, 'SL', 't_plus_4')
            
            cu_pct_t_minus_4 = get_pitch_mix_value(pitch_mix_t_minus_4, 'CU', 't_minus_4')
            cu_pct_t_minus_3 = get_pitch_mix_value(pitch_mix_t_minus_3, 'CU', 't_minus_3')
            cu_pct_t_minus_2 = get_pitch_mix_value(pitch_mix_t_minus_2, 'CU', 't_minus_2')
            cu_pct_t_minus_1 = get_pitch_mix_value(pitch_mix_t_minus_1, 'CU', 't_minus_1')
            cu_pct_t_plus_1 = get_pitch_mix_value(pitch_mix_t_plus_1, 'CU', 't_plus_1')
            cu_pct_t_plus_2 = get_pitch_mix_value(pitch_mix_t_plus_2, 'CU', 't_plus_2')
            cu_pct_t_plus_3 = get_pitch_mix_value(pitch_mix_t_plus_3, 'CU', 't_plus_3')
            cu_pct_t_plus_4 = get_pitch_mix_value(pitch_mix_t_plus_4, 'CU', 't_plus_4')
            
            ch_pct_t_minus_4 = get_pitch_mix_value(pitch_mix_t_minus_4, 'CH', 't_minus_4')
            ch_pct_t_minus_3 = get_pitch_mix_value(pitch_mix_t_minus_3, 'CH', 't_minus_3')
            ch_pct_t_minus_2 = get_pitch_mix_value(pitch_mix_t_minus_2, 'CH', 't_minus_2')
            ch_pct_t_minus_1 = get_pitch_mix_value(pitch_mix_t_minus_1, 'CH', 't_minus_1')
            ch_pct_t_plus_1 = get_pitch_mix_value(pitch_mix_t_plus_1, 'CH', 't_plus_1')
            ch_pct_t_plus_2 = get_pitch_mix_value(pitch_mix_t_plus_2, 'CH', 't_plus_2')
            ch_pct_t_plus_3 = get_pitch_mix_value(pitch_mix_t_plus_3, 'CH', 't_plus_3')
            ch_pct_t_plus_4 = get_pitch_mix_value(pitch_mix_t_plus_4, 'CH', 't_plus_4')
            
            fc_pct_t_minus_4 = get_pitch_mix_value(pitch_mix_t_minus_4, 'FC', 't_minus_4')
            fc_pct_t_minus_3 = get_pitch_mix_value(pitch_mix_t_minus_3, 'FC', 't_minus_3')
            fc_pct_t_minus_2 = get_pitch_mix_value(pitch_mix_t_minus_2, 'FC', 't_minus_2')
            fc_pct_t_minus_1 = get_pitch_mix_value(pitch_mix_t_minus_1, 'FC', 't_minus_1')
            fc_pct_t_plus_1 = get_pitch_mix_value(pitch_mix_t_plus_1, 'FC', 't_plus_1')
            fc_pct_t_plus_2 = get_pitch_mix_value(pitch_mix_t_plus_2, 'FC', 't_plus_2')
            fc_pct_t_plus_3 = get_pitch_mix_value(pitch_mix_t_plus_3, 'FC', 't_plus_3')
            fc_pct_t_plus_4 = get_pitch_mix_value(pitch_mix_t_plus_4, 'FC', 't_plus_4')
            
            return (idx, avg_t_minus_4, avg_t_minus_3, avg_t_minus_2, avg_before, avg_after, avg_t_plus_2, avg_t_plus_3, avg_t_plus_4,
                    avg_regular_t_minus_4, avg_regular_t_minus_3, avg_regular_t_minus_2, avg_regular_t_minus_1, avg_regular_t_plus_1, avg_regular_t_plus_2, avg_regular_t_plus_3, avg_regular_t_plus_4,
                    avg_spin_t_minus_4, avg_spin_t_minus_3, avg_spin_t_minus_2, avg_spin_t_minus_1, avg_spin_t_plus_1, avg_spin_t_plus_2, avg_spin_t_plus_3, avg_spin_t_plus_4,
                    avg_velocity_t_minus_4, avg_velocity_t_minus_3, avg_velocity_t_minus_2, avg_velocity_t_minus_1, avg_velocity_t_plus_1, avg_velocity_t_plus_2, avg_velocity_t_plus_3, avg_velocity_t_plus_4,
                    avg_velocity_playoff_t_minus_4, avg_velocity_playoff_t_minus_3, avg_velocity_playoff_t_minus_2, avg_velocity_playoff_t_minus_1, avg_velocity_playoff_t_plus_1, avg_velocity_playoff_t_plus_2, avg_velocity_playoff_t_plus_3, avg_velocity_playoff_t_plus_4,
                    gs_t_minus_4, gs_t_minus_3, gs_t_minus_2, gs_t_minus_1, gs_t_plus_1, gs_t_plus_2, gs_t_plus_3, gs_t_plus_4,
                    sv_t_minus_4, sv_t_minus_3, sv_t_minus_2, sv_t_minus_1, sv_t_plus_1, sv_t_plus_2, sv_t_plus_3, sv_t_plus_4,
                    relief_app_t_minus_4, relief_app_t_minus_3, relief_app_t_minus_2, relief_app_t_minus_1, relief_app_t_plus_1, relief_app_t_plus_2, relief_app_t_plus_3, relief_app_t_plus_4,
                    ff_pct_t_minus_4, ff_pct_t_minus_3, ff_pct_t_minus_2, ff_pct_t_minus_1, ff_pct_t_plus_1, ff_pct_t_plus_2, ff_pct_t_plus_3, ff_pct_t_plus_4,
                    si_pct_t_minus_4, si_pct_t_minus_3, si_pct_t_minus_2, si_pct_t_minus_1, si_pct_t_plus_1, si_pct_t_plus_2, si_pct_t_plus_3, si_pct_t_plus_4,
                    sl_pct_t_minus_4, sl_pct_t_minus_3, sl_pct_t_minus_2, sl_pct_t_minus_1, sl_pct_t_plus_1, sl_pct_t_plus_2, sl_pct_t_plus_3, sl_pct_t_plus_4,
                    cu_pct_t_minus_4, cu_pct_t_minus_3, cu_pct_t_minus_2, cu_pct_t_minus_1, cu_pct_t_plus_1, cu_pct_t_plus_2, cu_pct_t_plus_3, cu_pct_t_plus_4,
                    ch_pct_t_minus_4, ch_pct_t_minus_3, ch_pct_t_minus_2, ch_pct_t_minus_1, ch_pct_t_plus_1, ch_pct_t_plus_2, ch_pct_t_plus_3, ch_pct_t_plus_4,
                    fc_pct_t_minus_4, fc_pct_t_minus_3, fc_pct_t_minus_2, fc_pct_t_minus_1, fc_pct_t_plus_1, fc_pct_t_plus_2, fc_pct_t_plus_3, fc_pct_t_plus_4)
        
        players_no_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(compute_averages, idx, row['player_id'], row['lahman_id'], row['Injury_Year']) for idx, row in cleaned_data.iterrows()]
            for future in concurrent.futures.as_completed(futures):
                (idx, avg_t_minus_4, avg_t_minus_3, avg_t_minus_2, avg_before, avg_after, avg_t_plus_2, avg_t_plus_3, avg_t_plus_4,
                 avg_regular_t_minus_4, avg_regular_t_minus_3, avg_regular_t_minus_2, avg_regular_t_minus_1, avg_regular_t_plus_1, avg_regular_t_plus_2, avg_regular_t_plus_3, avg_regular_t_plus_4,
                 avg_spin_t_minus_4, avg_spin_t_minus_3, avg_spin_t_minus_2, avg_spin_t_minus_1, avg_spin_t_plus_1, avg_spin_t_plus_2, avg_spin_t_plus_3, avg_spin_t_plus_4,
                 avg_velocity_t_minus_4, avg_velocity_t_minus_3, avg_velocity_t_minus_2, avg_velocity_t_minus_1, avg_velocity_t_plus_1, avg_velocity_t_plus_2, avg_velocity_t_plus_3, avg_velocity_t_plus_4,
                 avg_velocity_playoff_t_minus_4, avg_velocity_playoff_t_minus_3, avg_velocity_playoff_t_minus_2, avg_velocity_playoff_t_minus_1, avg_velocity_playoff_t_plus_1, avg_velocity_playoff_t_plus_2, avg_velocity_playoff_t_plus_3, avg_velocity_playoff_t_plus_4,
                 gs_t_minus_4, gs_t_minus_3, gs_t_minus_2, gs_t_minus_1, gs_t_plus_1, gs_t_plus_2, gs_t_plus_3, gs_t_plus_4,
                 sv_t_minus_4, sv_t_minus_3, sv_t_minus_2, sv_t_minus_1, sv_t_plus_1, sv_t_plus_2, sv_t_plus_3, sv_t_plus_4,
                 relief_app_t_minus_4, relief_app_t_minus_3, relief_app_t_minus_2, relief_app_t_minus_1, relief_app_t_plus_1, relief_app_t_plus_2, relief_app_t_plus_3, relief_app_t_plus_4,
                 ff_pct_t_minus_4, ff_pct_t_minus_3, ff_pct_t_minus_2, ff_pct_t_minus_1, ff_pct_t_plus_1, ff_pct_t_plus_2, ff_pct_t_plus_3, ff_pct_t_plus_4,
                 si_pct_t_minus_4, si_pct_t_minus_3, si_pct_t_minus_2, si_pct_t_minus_1, si_pct_t_plus_1, si_pct_t_plus_2, si_pct_t_plus_3, si_pct_t_plus_4,
                 sl_pct_t_minus_4, sl_pct_t_minus_3, sl_pct_t_minus_2, sl_pct_t_minus_1, sl_pct_t_plus_1, sl_pct_t_plus_2, sl_pct_t_plus_3, sl_pct_t_plus_4,
                 cu_pct_t_minus_4, cu_pct_t_minus_3, cu_pct_t_minus_2, cu_pct_t_minus_1, cu_pct_t_plus_1, cu_pct_t_plus_2, cu_pct_t_plus_3, cu_pct_t_plus_4,
                 ch_pct_t_minus_4, ch_pct_t_minus_3, ch_pct_t_minus_2, ch_pct_t_minus_1, ch_pct_t_plus_1, ch_pct_t_plus_2, ch_pct_t_plus_3, ch_pct_t_plus_4,
                 fc_pct_t_minus_4, fc_pct_t_minus_3, fc_pct_t_minus_2, fc_pct_t_minus_1, fc_pct_t_plus_1, fc_pct_t_plus_2, fc_pct_t_plus_3, fc_pct_t_plus_4) = future.result()
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
                cleaned_data.at[idx, 'avg_spin_rate_t_minus_4'] = avg_spin_t_minus_4
                cleaned_data.at[idx, 'avg_spin_rate_t_minus_3'] = avg_spin_t_minus_3
                cleaned_data.at[idx, 'avg_spin_rate_t_minus_2'] = avg_spin_t_minus_2
                cleaned_data.at[idx, 'avg_spin_rate_t_minus_1'] = avg_spin_t_minus_1
                cleaned_data.at[idx, 'avg_spin_rate_t_plus_1'] = avg_spin_t_plus_1
                cleaned_data.at[idx, 'avg_spin_rate_t_plus_2'] = avg_spin_t_plus_2
                cleaned_data.at[idx, 'avg_spin_rate_t_plus_3'] = avg_spin_t_plus_3
                cleaned_data.at[idx, 'avg_spin_rate_t_plus_4'] = avg_spin_t_plus_4
                cleaned_data.at[idx, 'avg_velocity_t_minus_4'] = avg_velocity_t_minus_4
                cleaned_data.at[idx, 'avg_velocity_t_minus_3'] = avg_velocity_t_minus_3
                cleaned_data.at[idx, 'avg_velocity_t_minus_2'] = avg_velocity_t_minus_2
                cleaned_data.at[idx, 'avg_velocity_t_minus_1'] = avg_velocity_t_minus_1
                cleaned_data.at[idx, 'avg_velocity_t_plus_1'] = avg_velocity_t_plus_1
                cleaned_data.at[idx, 'avg_velocity_t_plus_2'] = avg_velocity_t_plus_2
                cleaned_data.at[idx, 'avg_velocity_t_plus_3'] = avg_velocity_t_plus_3
                cleaned_data.at[idx, 'avg_velocity_t_plus_4'] = avg_velocity_t_plus_4
                cleaned_data.at[idx, 'avg_velocity_playoff_t_minus_4'] = avg_velocity_playoff_t_minus_4
                cleaned_data.at[idx, 'avg_velocity_playoff_t_minus_3'] = avg_velocity_playoff_t_minus_3
                cleaned_data.at[idx, 'avg_velocity_playoff_t_minus_2'] = avg_velocity_playoff_t_minus_2
                cleaned_data.at[idx, 'avg_velocity_playoff_t_minus_1'] = avg_velocity_playoff_t_minus_1
                cleaned_data.at[idx, 'avg_velocity_playoff_t_plus_1'] = avg_velocity_playoff_t_plus_1
                cleaned_data.at[idx, 'avg_velocity_playoff_t_plus_2'] = avg_velocity_playoff_t_plus_2
                cleaned_data.at[idx, 'avg_velocity_playoff_t_plus_3'] = avg_velocity_playoff_t_plus_3
                cleaned_data.at[idx, 'avg_velocity_playoff_t_plus_4'] = avg_velocity_playoff_t_plus_4
                cleaned_data.at[idx, 'gs_t_minus_4'] = gs_t_minus_4
                cleaned_data.at[idx, 'gs_t_minus_3'] = gs_t_minus_3
                cleaned_data.at[idx, 'gs_t_minus_2'] = gs_t_minus_2
                cleaned_data.at[idx, 'gs_t_minus_1'] = gs_t_minus_1
                cleaned_data.at[idx, 'gs_t_plus_1'] = gs_t_plus_1
                cleaned_data.at[idx, 'gs_t_plus_2'] = gs_t_plus_2
                cleaned_data.at[idx, 'gs_t_plus_3'] = gs_t_plus_3
                cleaned_data.at[idx, 'gs_t_plus_4'] = gs_t_plus_4
                cleaned_data.at[idx, 'sv_t_minus_4'] = sv_t_minus_4
                cleaned_data.at[idx, 'sv_t_minus_3'] = sv_t_minus_3
                cleaned_data.at[idx, 'sv_t_minus_2'] = sv_t_minus_2
                cleaned_data.at[idx, 'sv_t_minus_1'] = sv_t_minus_1
                cleaned_data.at[idx, 'sv_t_plus_1'] = sv_t_plus_1
                cleaned_data.at[idx, 'sv_t_plus_2'] = sv_t_plus_2
                cleaned_data.at[idx, 'sv_t_plus_3'] = sv_t_plus_3
                cleaned_data.at[idx, 'sv_t_plus_4'] = sv_t_plus_4
                cleaned_data.at[idx, 'relief_app_t_minus_4'] = relief_app_t_minus_4
                cleaned_data.at[idx, 'relief_app_t_minus_3'] = relief_app_t_minus_3
                cleaned_data.at[idx, 'relief_app_t_minus_2'] = relief_app_t_minus_2
                cleaned_data.at[idx, 'relief_app_t_minus_1'] = relief_app_t_minus_1
                cleaned_data.at[idx, 'relief_app_t_plus_1'] = relief_app_t_plus_1
                cleaned_data.at[idx, 'relief_app_t_plus_2'] = relief_app_t_plus_2
                cleaned_data.at[idx, 'relief_app_t_plus_3'] = relief_app_t_plus_3
                cleaned_data.at[idx, 'relief_app_t_plus_4'] = relief_app_t_plus_4
                cleaned_data.at[idx, 'ff_pct_t_minus_4'] = ff_pct_t_minus_4
                cleaned_data.at[idx, 'ff_pct_t_minus_3'] = ff_pct_t_minus_3
                cleaned_data.at[idx, 'ff_pct_t_minus_2'] = ff_pct_t_minus_2
                cleaned_data.at[idx, 'ff_pct_t_minus_1'] = ff_pct_t_minus_1
                cleaned_data.at[idx, 'ff_pct_t_plus_1'] = ff_pct_t_plus_1
                cleaned_data.at[idx, 'ff_pct_t_plus_2'] = ff_pct_t_plus_2
                cleaned_data.at[idx, 'ff_pct_t_plus_3'] = ff_pct_t_plus_3
                cleaned_data.at[idx, 'ff_pct_t_plus_4'] = ff_pct_t_plus_4
                cleaned_data.at[idx, 'si_pct_t_minus_4'] = si_pct_t_minus_4
                cleaned_data.at[idx, 'si_pct_t_minus_3'] = si_pct_t_minus_3
                cleaned_data.at[idx, 'si_pct_t_minus_2'] = si_pct_t_minus_2
                cleaned_data.at[idx, 'si_pct_t_minus_1'] = si_pct_t_minus_1
                cleaned_data.at[idx, 'si_pct_t_plus_1'] = si_pct_t_plus_1
                cleaned_data.at[idx, 'si_pct_t_plus_2'] = si_pct_t_plus_2
                cleaned_data.at[idx, 'si_pct_t_plus_3'] = si_pct_t_plus_3
                cleaned_data.at[idx, 'si_pct_t_plus_4'] = si_pct_t_plus_4
                cleaned_data.at[idx, 'sl_pct_t_minus_4'] = sl_pct_t_minus_4
                cleaned_data.at[idx, 'sl_pct_t_minus_3'] = sl_pct_t_minus_3
                cleaned_data.at[idx, 'sl_pct_t_minus_2'] = sl_pct_t_minus_2
                cleaned_data.at[idx, 'sl_pct_t_minus_1'] = sl_pct_t_minus_1
                cleaned_data.at[idx, 'sl_pct_t_plus_1'] = sl_pct_t_plus_1
                cleaned_data.at[idx, 'sl_pct_t_plus_2'] = sl_pct_t_plus_2
                cleaned_data.at[idx, 'sl_pct_t_plus_3'] = sl_pct_t_plus_3
                cleaned_data.at[idx, 'sl_pct_t_plus_4'] = sl_pct_t_plus_4
                cleaned_data.at[idx, 'cu_pct_t_minus_4'] = cu_pct_t_minus_4
                cleaned_data.at[idx, 'cu_pct_t_minus_3'] = cu_pct_t_minus_3
                cleaned_data.at[idx, 'cu_pct_t_minus_2'] = cu_pct_t_minus_2
                cleaned_data.at[idx, 'cu_pct_t_minus_1'] = cu_pct_t_minus_1
                cleaned_data.at[idx, 'cu_pct_t_plus_1'] = cu_pct_t_plus_1
                cleaned_data.at[idx, 'cu_pct_t_plus_2'] = cu_pct_t_plus_2
                cleaned_data.at[idx, 'cu_pct_t_plus_3'] = cu_pct_t_plus_3
                cleaned_data.at[idx, 'cu_pct_t_plus_4'] = cu_pct_t_plus_4
                cleaned_data.at[idx, 'ch_pct_t_minus_4'] = ch_pct_t_minus_4
                cleaned_data.at[idx, 'ch_pct_t_minus_3'] = ch_pct_t_minus_3
                cleaned_data.at[idx, 'ch_pct_t_minus_2'] = ch_pct_t_minus_2
                cleaned_data.at[idx, 'ch_pct_t_minus_1'] = ch_pct_t_minus_1
                cleaned_data.at[idx, 'ch_pct_t_plus_1'] = ch_pct_t_plus_1
                cleaned_data.at[idx, 'ch_pct_t_plus_2'] = ch_pct_t_plus_2
                cleaned_data.at[idx, 'ch_pct_t_plus_3'] = ch_pct_t_plus_3
                cleaned_data.at[idx, 'ch_pct_t_plus_4'] = ch_pct_t_plus_4
                cleaned_data.at[idx, 'fc_pct_t_minus_4'] = fc_pct_t_minus_4
                cleaned_data.at[idx, 'fc_pct_t_minus_3'] = fc_pct_t_minus_3
                cleaned_data.at[idx, 'fc_pct_t_minus_2'] = fc_pct_t_minus_2
                cleaned_data.at[idx, 'fc_pct_t_minus_1'] = fc_pct_t_minus_1
                cleaned_data.at[idx, 'fc_pct_t_plus_1'] = fc_pct_t_plus_1
                cleaned_data.at[idx, 'fc_pct_t_plus_2'] = fc_pct_t_plus_2
                cleaned_data.at[idx, 'fc_pct_t_plus_3'] = fc_pct_t_plus_3
                cleaned_data.at[idx, 'fc_pct_t_plus_4'] = fc_pct_t_plus_4
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
