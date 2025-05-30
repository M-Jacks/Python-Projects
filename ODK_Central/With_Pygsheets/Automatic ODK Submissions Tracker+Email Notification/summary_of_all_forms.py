from pyodk.client import Client

client = Client()

def fetch_all_forms():
    """Fetches all forms from the ODK Central server."""
    project_id = client.config.central.default_project_id
    forms = client.forms.list(project_id=project_id)
    return forms

def fetch_records(form_id):
    """Fetches submission records from the ODK Central server."""
    project_id = client.config.central.default_project_id
    try:
        records = client.submissions.get_table(project_id=project_id, form_id=form_id)['value']
        return records
    except Exception as e:
        print(f"⚠️ Error fetching records for form '{form_id}': {e}")
        return []

# Main script logic
forms = fetch_all_forms()
print("📋 Available forms in the project:")
for form in forms:
    print(f"- {form.name} (ID: {form.xmlFormId})")

print("\n📥 Fetching submission records for each form...")
for form in forms:
    form_id = form.xmlFormId
    print(f"\n📄 Form: {form.name}")
    records = fetch_records(form_id)
    print(f"✅ Total records fetched: {len(records)}")
    record_number = 6
    if records:
        print(f"🔍 Displaying record #{record_number} preview:")
        print(records[record_number])
    else:
        print("⚠️ No records found.")
# Ensure the script runs only when executed directly
if __name__ == "__main__":
    print("\n✅ Script executed successfully.")