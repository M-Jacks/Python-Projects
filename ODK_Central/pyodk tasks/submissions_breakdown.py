import os
import pandas as pd
from pyodk.client import Client

client = Client()

data = client.submissions.get_table(form_id='Image Safari Crop Scout (Phone Approach)')
records = data['value']

records = data['value']

df = pd.json_normalize(records)

# Extract 'photoQuantity' from 'photos', ignoring None values
df['photo_count'] = df['photos.photoQuantity'].fillna(0).astype(int)

# Group by 'today' and sum the counts
photo_summary = df.groupby('today')['photo_count'].sum().reset_index()

# Create output directory path
output_dir = os.path.join(os.path.dirname(__file__), 'output_files')
os.makedirs(output_dir, exist_ok=False)

output_file = os.path.join(output_dir, 'photo_summary_by_day.csv')
photo_summary.to_csv(output_file, index=True)
print(photo_summary)

print(f"✅ Photo summary saved to: {output_file}")
