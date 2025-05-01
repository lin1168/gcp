import pandas as pd
from tqdm import tqdm
import glob
import os
from datetime import datetime

# Define the directory where the CSV files are stored
data_dir = "/home/dexcom/cmu_exports/"

# Define the start and end dates
start_date_str = "2022_09"  
end_date_str = "2023_09"   

# Convert strings to datetime objects
start_date = datetime.strptime(start_date_str, "%Y_%m")
end_date = datetime.strptime(end_date_str, "%Y_%m")

# Get all CSV files matching the correct pattern
csv_files = sorted(glob.glob(f"{data_dir}/20[2-4][0-9]_[0-9][0-9]_data_*.csv"))

# Filter files based on extracted date
filtered_files = []
for file in csv_files:
    filename = os.path.basename(file)

    # Extract only the "YYYY_MM" portion from the filename
    file_date_str = filename.split("_data_")[0]  # Extracts "YYYY_MM"
    
    try:
        file_date = datetime.strptime(file_date_str, "%Y_%m")
        if start_date <= file_date <= end_date:
            filtered_files.append(file)
    except ValueError:
        print(f"Skipping {filename} - Invalid date format.")

# Print the matched files (for verification)
print("\nFiltered Files:")
for f in filtered_files:
    print(f)

# Load and process data with progress tracking
df_list = []
print("\nLoading CSV files...")
for file in tqdm(filtered_files, desc="Reading CSVs", unit="file"):
    df = pd.read_csv(file, parse_dates=['usage_date'])
    df_list.append(df)

# Combine all data
df = pd.concat(df_list, ignore_index=True)

# Aggregate by project and date
df_agg = df.groupby(['project_id', 'usage_date'])['total_cost'].sum().reset_index()

# Sort values for proper MA calculation
df_agg = df_agg.sort_values(['project_id', 'usage_date'])

# Define MA periods
ma_periods = [120, 90, 60, 30, 15, 7]

# Compute moving averages with progress tracking
print("\nComputing moving averages...")
for period in tqdm(ma_periods, desc="Calculating MAs", unit="MA"):
    df_agg[f'MA_{period}'] = df_agg.groupby('project_id')['total_cost'].transform(lambda x: x.rolling(period, min_periods=1).mean())

# Compute % and $ change with progress tracking
print("\nCalculating percentage and dollar changes...")
for period in tqdm(ma_periods, desc="Calculating changes", unit="MA"):
    df_agg[f'Change_%_{period}'] = ((df_agg['total_cost'] - df_agg[f'MA_{period}']) / df_agg[f'MA_{period}']) * 100
    df_agg[f'Change_$_{period}'] = df_agg['total_cost'] - df_agg[f'MA_{period}']

# Save processed data for Streamlit
output_file = "processed_data.parquet"
df_agg.to_parquet(output_file)
print(f"\nProcessing complete. Data saved as '{output_file}'.")
