import pandas as pd
from pyodk.client import Client

client = Client()

response = client.submissions.get_table(form_id='Image Safari Crop Scout (Phone Approach)')
data = response['Value']

df = pd.json_normalize(data)