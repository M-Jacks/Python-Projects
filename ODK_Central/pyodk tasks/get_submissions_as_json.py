import os
import json
from pyodk.client import Client

client = Client()

form_id = 'Image Safari Crop Scout (Phone Approach)'
submissions = client.submissions.get_table(form_id=form_id)

output_dir = os.path.join(os.path.dirname(__file__), 'output_files')
os.makedirs(output_dir, exist_ok=True)

# output file path
output_file_path = os.path.join(output_dir, "submissions.json")

# Save as JSON
with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(submissions, f, indent=2)

print(f"✅ Submissions saved to: {output_file_path}")
