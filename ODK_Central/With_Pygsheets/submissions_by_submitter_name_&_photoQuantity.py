import os
import pandas as pd
import pygsheets
from pyodk.client import Client
from dotenv import load_dotenv

load_dotenv()

sheet_name = os.getenv("SHEETNAME")
print(f"sheetname is: {sheet_name}")

service_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')

# Initialize ODK client
client = Client()

# Fetch submissions
data = client.submissions.get_table(form_id='Image Safari Crop Scout (Phone Approach)')
records = data['value']

# Normalize nested JSON
df = pd.json_normalize(records)

# Handle missing submitter names
df['submitter'] = df['__system.submitterName'].fillna('unknown')

allowed_sites = ['is_cimmyt', 'is_cip_ke', 'is_qed_mw']

df = df[df['submitter'].isin(allowed_sites)]

# Extract photo count and duration
df['photo_count'] = df['photos.photoQuantity'].fillna(0).astype(int)
df['duration'] = df['photos.photoSessionDuration'].fillna(0).astype(int)

# Group by date and submitter, then sum photo counts and durations
grouped = df.groupby(['today', 'submitter'])[['photo_count', 'duration']].sum().reset_index()

# Pivot both photo counts and durations
pivot_counts = grouped.pivot(index='today', columns='submitter', values='photo_count').fillna(0).astype(int)
pivot_duration = grouped.pivot(index='today', columns='submitter', values='duration').fillna(0).astype(int)

# Format to hh:mm:ss
def format_seconds_to_hhmmss(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f'{hours}:{minutes:02}:{secs:02}'

pivot_duration = pivot_duration.applymap(format_seconds_to_hhmmss)

# Optional: rename column levels for clarity
pivot_counts.columns = [f'{col}_count' for col in pivot_counts.columns]
pivot_duration.columns = [f'{col}_duration' for col in pivot_duration.columns]

# Combine the two pivot tables side by side
pivot_combined = pd.concat([pivot_counts, pivot_duration], axis=1)

# Sort columns for neatness
pivot_combined = pivot_combined.reindex(sorted(pivot_combined.columns), axis=1)

# Create output directory
output_dir = os.path.join(os.path.dirname(__file__), 'output_files')
os.makedirs(output_dir, exist_ok=True)

# Save final output as CSV
output_file = os.path.join(output_dir, 'pivoted_photo_summary5.csv')
pivot_combined.to_csv(output_file)

# Print to terminal and confirm
print(pivot_combined)
print(f"✅ Pivoted photo summary with durations saved to: {output_file}")

# Authenticate with Google Sheets (ensure you have a credentials.json file)
gc = pygsheets.authorize(service_file=service_file)

# Open the target Google Sheet (use the title of the spreadsheet)
spreadsheet = gc.open(sheet_name)

# Select the first worksheet
worksheet = spreadsheet.worksheet_by_title('Summary')

pivot_combined_reset = pivot_combined.reset_index()

# Update the sheet with the pivoted data
worksheet.set_dataframe(pivot_combined_reset, (2, 1))

# Confirm the update
print("✅ Google Sheets updated with the pivoted photo summary.")
