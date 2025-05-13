from pyodk.client import Client

# Initialize Client using ~/.pyodk_config.toml
client = Client()

# Step 1: List available forms in the project
# Get a list of forms
forms = client.forms.list()
# print(forms)

# Step 2: If forms exist, fetch submissions from the first one
if forms:
    # Get submissions for a form
    submissions = client.submissions.get_table(form_id='Image Safari Crop Scout (Phone Approach)')
    print(submissions)
else:
    print("⚠️ No forms found.")
