import zipfile
import os
import shutil
from pathlib import Path

def extract_lahman_database(zip_path):
    """Extract the Lahman baseball database from the downloaded zip file."""
    
    print(f"Extracting Lahman database from: {zip_path}")
    
    try:
        # Extract the zip file
        print("Extracting files...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        print("Files extracted successfully!")
        
        # Check if files were extracted
        people_path = Path("People.csv")
        appearances_path = Path("Appearances.csv")
        
        # Also check in subdirectories
        if not people_path.exists():
            people_files = list(Path(".").glob("**/People.csv"))
            if people_files:
                people_path = people_files[0]
                print(f"Found People.csv at: {people_path}")
        
        if not appearances_path.exists():
            appearances_files = list(Path(".").glob("**/Appearances.csv"))
            if appearances_files:
                appearances_path = appearances_files[0]
                print(f"Found Appearances.csv at: {appearances_path}")
        
        if people_path.exists() and appearances_path.exists():
            print(f"Successfully extracted Lahman database")
            print(f"People.csv: {people_path}")
            print(f"Appearances.csv: {appearances_path}")
            
            # Copy files to root if they're in subdirectories
            if str(people_path) != "People.csv":
                shutil.copy2(people_path, "People.csv")
                print("Copied People.csv to root directory")
            
            if str(appearances_path) != "Appearances.csv":
                shutil.copy2(appearances_path, "Appearances.csv")
                print("Copied Appearances.csv to root directory")
            
            return True
        else:
            print("Files not found after extraction")
            print("Available files:", list(Path(".").glob("**/*.csv")))
            return False
            
    except Exception as e:
        print(f"Error extracting: {e}")
        return False

if __name__ == "__main__":
    zip_path = r"C:\Users\Owner\Downloads\lahman_1871-2025_csv.zip"
    extract_lahman_database(zip_path)
