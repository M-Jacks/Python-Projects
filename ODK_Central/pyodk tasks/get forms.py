from pyodk.client import Client

client = Client()

forms = client.forms.list()

if (forms):
    print("forms are present")
    print(forms)