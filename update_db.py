import toml
import os
import requests

secrets = toml.load('.streamlit/secrets.toml')
url = secrets['supabase']['URL']
key = secrets['supabase']['KEY']

print("URL:", url)
print("KEY length:", len(key))
