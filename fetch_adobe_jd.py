import requests
from bs4 import BeautifulSoup
import json
import re

url = "https://careers.adobe.com/us/en/job/R162016/Senior-Product-Manager-Adobe-GenStudio-Ad-Trafficking-and-Activation"
resp = requests.get(url)
soup = BeautifulSoup(resp.text, 'html.parser')

# Phenom People often embeds the JD in a script tag with type application/ld+json
for script in soup.find_all('script', type='application/ld+json'):
    try:
        data = json.loads(script.string)
        if '@type' in data and data['@type'] == 'JobPosting':
            print("Title:", data.get('title'))
            # Description is HTML
            desc_soup = BeautifulSoup(data.get('description', ''), 'html.parser')
            print("\nDescription:")
            print(desc_soup.get_text(separator='\n', strip=True))
            break
    except:
        pass
