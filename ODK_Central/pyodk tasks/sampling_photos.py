import os
import random
from pyodk.client import Client

client = Client()

# Use default project ID from config
project_id = client.config.central.default_project_id

form_id = 'Image Safari Crop Scout (Phone Approach)'

# Fetch records
records = client.submissions.get_table(project_id=project_id, form_id=form_id)['value']

# Get authenticated session and base URL
base_url = client.config.central.base_url.rstrip('/')
session = client.session

# Sample 5 random records
sample = random.sample(records, min(5, len(records)))

output_dir = os.path.join(os.path.dirname(__file__), 'output_files', 'sample_photos')
os.makedirs(output_dir, exist_ok=True)

for record in sample:
    instance_id = record['__id']
    photos = record.get('photos', {})

    for part_key, filename in photos.items():
        if filename and str(filename).endswith('.zip'):
            print(f"📥 Downloading {filename} from {instance_id}...")
            url = f"{base_url}/v1/projects/{project_id}/forms/{form_id}/submissions/{instance_id}/attachments/{filename}"
            try:
                response = session.get(url)
                response.raise_for_status()
                file_path = os.path.join(output_dir, filename)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Saved to: {file_path}")
            except Exception as e:
                print(f"❌ Error downloading {filename}: {e}")

print("\n✅ Finished downloading sample zip files.")

