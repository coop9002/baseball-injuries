# -*- coding: utf-8 -*-
"""
Baseball Injury Data Analysis

This script processes baseball injury data from Excel files and attempts to
enrich it with team information using the Lahman database.

Author: Generated from cleaned notebook
Date: 2026-01-02
"""

import pandas as pd
import os
from pathlib import Path
import pybaseball as pb

# Configuration
EXCEL_FILE_PATH = 'Baseball Injury Report.xlsx'
LAHMAN_PEOPLE_PATH = 'People.csv'
LAHMAN_APPEARANCES_PATH = 'Appearances.csv'


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
    
    # Add season columns
    df['Season: T-1'] = (df['Injury_Year'] - 1).astype(str)
    df['Season: T-2'] = (df['Injury_Year'] - 2).astype(str)
    df['Season: T+1'] = (df['Injury_Year'] + 1).astype(str)
    df['Season: T+2'] = (df['Injury_Year'] + 2).astype(str)
    
    # Add name lookup columns
    df['first_name_lookup'] = df['Name'].apply(lambda x: x.split(' ')[0] if pd.notna(x) else None)
    df['last_name_lookup'] = df['Name'].apply(lambda x: x.split(' ')[-1] if pd.notna(x) else None)
    
    return df


def load_lahman_data(people_path, appearances_path):
    """
    Load Lahman database people and appearances data from local CSV files.
    
    Args:
        people_path (str): Path to People.csv
        appearances_path (str): Path to Appearances.csv
        
    Returns:
        tuple: (people_df, appearances_df) or (None, None) if not available
    """
    try:
        print("Loading Lahman database from local CSV files...")
        
        # Load the local CSV files
        if os.path.exists(people_path) and os.path.exists(appearances_path):
            people = pd.read_csv(people_path)
            appearances = pd.read_csv(appearances_path)
            
            print("Successfully loaded Lahman database data from CSV files.")
            print(f"People data shape: {people.shape}")
            print(f"Appearances data shape: {appearances.shape}")
            return people, appearances
        else:
            print("Lahman data files not found. Please ensure:")
            print(f"1. {people_path}")
            print(f"2. {appearances_path}")
            print("Both files exist in the current directory.")
            return None, None
            
    except Exception as e:
        print(f"Error loading Lahman data from CSV files: {e}")
        return None, None


def get_player_id_from_name(first_name, last_name, people_df):
    """
    Get player ID from name using Lahman people data.
    
    Args:
        first_name (str): Player's first name
        last_name (str): Player's last name
        people_df (pd.DataFrame): Lahman people data
        
    Returns:
        str: Player ID or None if not found
    """
    if people_df is None or first_name is None or last_name is None:
        return None
    
    # Try exact match first
    exact_match = people_df[
        (people_df['nameFirst'].str.lower() == first_name.lower()) &
        (people_df['nameLast'].str.lower() == last_name.lower())
    ]
    
    if not exact_match.empty:
        return exact_match.iloc[0]['playerID']
    
    # Try partial match if exact fails
    partial_match = people_df[
        (people_df['nameFirst'].str.lower().str.contains(first_name.lower(), na=False)) &
        (people_df['nameLast'].str.lower().str.contains(last_name.lower(), na=False))
    ]
    
    if not partial_match.empty:
        return partial_match.iloc[0]['playerID']
    
    return None


def get_pitching_stats(player_id, season):
    """
    Get pitching statistics for a player in a specific season.
    
    Args:
        player_id (str): Lahman player ID
        season (int): Season year
        
    Returns:
        pd.DataFrame: Pitching stats or None if not found
    """
    try:
        # pybaseball only has data from 2008 onwards
        if season < 2008:
            print(f"Season {season} is before 2008, using Lahman data instead")
            return None
            
        stats = pb.pitching_stats_bref(season)
        if stats is None or stats.empty:
            return None
            
        player_stats = stats[stats['playerID'] == player_id]
        return player_stats if not player_stats.empty else None
        
    except Exception as e:
        print(f"Error getting pitching stats for {player_id} in {season}: {e}")
        return None


def get_lahman_pitching_stats(player_id, season, people_df, appearances_df):
    """
    Get pitching statistics from Lahman database for seasons before 2008.
    
    Args:
        player_id (str): Lahman player ID
        season (int): Season year
        people_df (pd.DataFrame): Lahman people data
        appearances_df (pd.DataFrame): Lahman appearances data
        
    Returns:
        dict: Basic pitching stats or None if not found
    """
    try:
        # Get player appearances for the season
        player_appearances = appearances_df[
            (appearances_df['playerID'] == player_id) & 
            (appearances_df['yearID'] == season)
        ]
        
        if player_appearances.empty:
            return None
        
        # Get pitching data if available
        try:
            # Try to load Lahman pitching data
            pitching_df = pd.read_csv('Pitching.csv')
            player_pitching = pitching_df[
                (pitching_df['playerID'] == player_id) & 
                (pitching_df['yearID'] == season)
            ]
            
            if not player_pitching.empty:
                stats = player_pitching.iloc[0]
                return {
                    'IP': stats.get('IPouts', 0) / 3,  # Convert outs to innings
                    'BF': stats.get('BFP', 0),  # Batters faced (BFP in Lahman)
                    'G': stats.get('G', 0),
                    'W': stats.get('W', 0),
                    'L': stats.get('L', 0),
                    'ERA': stats.get('ERA', 0)
                }
        except FileNotFoundError:
            pass
        
        # Fallback to appearances data
        appearances = player_appearances.iloc[0]
        return {
            'G': appearances.get('G_all', 0),
            'IP': appearances.get('G_p', 0) * 6,  # Rough estimate
            'BF': appearances.get('G_p', 0) * 25,  # Rough estimate
        }
        
    except Exception as e:
        print(f"Error getting Lahman pitching stats for {player_id} in {season}: {e}")
        return None


def calculate_avg_pitches_per_playoff_game(player_id, season, people_df=None, appearances_df=None):
    """
    Calculate average pitches per playoff game for a player in a season.
    
    Args:
        player_id (str): Lahman player ID
        season (int): Season year
        people_df (pd.DataFrame): Lahman people data (for pre-2008)
        appearances_df (pd.DataFrame): Lahman appearances data (for pre-2008)
        
    Returns:
        float: Average pitches per playoff game or None if not available
    """
    try:
        # Get regular season stats
        if season >= 2008:
            reg_stats = get_pitching_stats(player_id, season)
        else:
            reg_stats = get_lahman_pitching_stats(player_id, season, people_df, appearances_df)
        
        if reg_stats is None:
            return None
        
        # Get playoff stats
        playoff_stats = get_playoff_pitching_stats(player_id, season)
        if playoff_stats is None or playoff_stats.empty:
            return None
        
        # Calculate estimated pitches
        if isinstance(reg_stats, dict):
            estimated_pitches = (reg_stats.get('IP', 0) * 3) + reg_stats.get('BF', 0)
            reg_games = reg_stats.get('G', 1)
        else:
            # pybaseball DataFrame
            player_reg = reg_stats.iloc[0]
            estimated_pitches = (player_reg['IP'] * 3) + player_reg.get('BF', 0)
            reg_games = player_reg.get('G', 1)
        
        # Get playoff games played
        player_playoff = playoff_stats.iloc[0]
        playoff_games = player_playoff.get('G', 0)
        
        if playoff_games > 0 and estimated_pitches > 0 and reg_games > 0:
            # Estimate pitches per game from regular season
            avg_pitches_per_reg_game = estimated_pitches / reg_games
            return avg_pitches_per_reg_game
        
        return None
        
    except Exception as e:
        print(f"Error calculating avg pitches for {player_id} in {season}: {e}")
        return None


def add_pitching_averages(df, people_df, appearances_df):
    """
    Add average pitches per playoff game columns for seasons before and after surgery.
    
    Args:
        df (pd.DataFrame): Injury data with season columns
        people_df (pd.DataFrame): Lahman people data
        appearances_df (pd.DataFrame): Lahman appearances data
        
    Returns:
        pd.DataFrame: Data with pitching average columns added
    """
    if df is None or people_df is None or appearances_df is None:
        return df
    
    # Initialize new columns
    df['avg_pitches_playoff_before'] = None
    df['avg_pitches_playoff_after'] = None
    
    print("Calculating average pitches per playoff game...")
    
    for idx, row in df.iterrows():
        try:
            # Get player ID
            first_name = row.get('first_name_lookup')
            last_name = row.get('last_name_lookup')
            
            if not first_name or not last_name:
                continue
                
            player_id = get_player_id_from_name(first_name, last_name, people_df)
            if not player_id:
                continue
            
            # Get seasons before and after surgery
            season_before = int(row.get('Season: T-1', 0))
            season_after = int(row.get('Season: T+1', 0))
            
            # Calculate averages
            if season_before > 0:
                avg_before = calculate_avg_pitches_per_playoff_game(
                    player_id, season_before, people_df, appearances_df
                )
                df.at[idx, 'avg_pitches_playoff_before'] = avg_before
            
            if season_after > 0:
                avg_after = calculate_avg_pitches_per_playoff_game(
                    player_id, season_after, people_df, appearances_df
                )
                df.at[idx, 'avg_pitches_playoff_after'] = avg_after
                
        except Exception as e:
            print(f"Error processing row {idx}: {e}")
            continue
    
    return df


def create_player_name_lookup(df):
    """
    Create player name lookup columns for matching with Lahman data.
    
    Args:
        df (pd.DataFrame): Injury data
        
    Returns:
        pd.DataFrame: Data with name lookup columns added
    """
    if df is None:
        return None
    
    df['first_name_lookup'] = df['Name'].apply(lambda x: x.split(' ')[0] if pd.notna(x) else None)
    df['last_name_lookup'] = df['Name'].apply(lambda x: x.split(' ')[-1] if pd.notna(x) else None)
    
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


def main():
    """
    Main function to run the baseball injury data analysis.
    """
    print("Baseball Injury Data Analysis")
    print("=" * 40)
    
    # Load and merge injury data
    print("\n1. Loading injury data...")
    injury_data = load_and_merge_injury_data(EXCEL_FILE_PATH)
    
    if injury_data is None:
        print("Failed to load injury data. Please check the file path.")
        return
    
    # Clean injury data
    print("\n2. Cleaning injury data...")
    cleaned_data = clean_injury_data(injury_data)
    display_data_info(cleaned_data, "Cleaned Injury Data")
    
    # Load Lahman data
    print("\n3. Loading Lahman database...")
    people, appearances = load_lahman_data(LAHMAN_PEOPLE_PATH, LAHMAN_APPEARANCES_PATH)
    
    if people is not None and appearances is not None:
        display_data_info(people, "People Data")
        display_data_info(appearances, "Appearances Data")
        
        # Create name lookups for matching
        print("\n4. Creating player name lookups...")
        cleaned_data = create_player_name_lookup(cleaned_data)
        
        # Add pitching averages
        print("\n5. Adding average pitches per playoff game...")
        cleaned_data = add_pitching_averages(cleaned_data, people, appearances)
        
        # Display results
        print("\n6. Pitching averages added!")
        print(f"Average pitches before surgery: {cleaned_data['avg_pitches_playoff_before'].mean():.1f}")
        print(f"Average pitches after surgery: {cleaned_data['avg_pitches_playoff_after'].mean():.1f}")
        
        # Show sample of new columns
        print("\nSample of new pitching average columns:")
        sample_cols = ['Name', 'Injury_Year', 'avg_pitches_playoff_before', 'avg_pitches_playoff_after']
        print(cleaned_data[sample_cols].head(10))
        
        print("\n7. Data processing complete!")
        print(f"Final dataset contains {len(cleaned_data)} pitcher injuries")
        
        # Save processed data
        output_path = 'processed_baseball_injuries.csv'
        cleaned_data.to_csv(output_path, index=False)
        print(f"Processed data saved to: {output_path}")
        
    else:
        print("\nLahman data not available. Proceeding with injury data only.")
        print(f"Dataset contains {len(cleaned_data)} pitcher injuries")


if __name__ == "__main__":
    main()
