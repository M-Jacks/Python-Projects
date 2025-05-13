from pyodk.client import Client

client = Client()

Submission_count = client.submissions.get_table(form_id='Image Safari Crop Scout (Phone Approach)')

if Submission_count:
    print("sobmissions are available")
    print(Submission_count)