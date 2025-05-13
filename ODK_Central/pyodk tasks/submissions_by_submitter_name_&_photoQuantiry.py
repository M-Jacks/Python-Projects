import os
import pandas as pd
from pyodk.client import Client

# Initialize ODK client
client = Client()

# Fetch submissions
data = client.submissions.get_table(form_id='Image Safari Crop Scout (Phone Approach)')
records = data['value']

# Normalize nested JSON
df = pd.json_normalize(records)

# Handle missing submitter names
df['submitter'] = df['__system.submitterName'].fillna('unknown')

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

# Save final output
output_file = os.path.join(output_dir, 'pivoted_photo_summary5.csv')
pivot_combined.to_csv(output_file)

# Print to terminal and confirm
print(pivot_combined)
print(f"✅ Pivoted photo summary with durations saved to: {output_file}")
