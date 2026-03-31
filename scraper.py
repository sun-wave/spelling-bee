from curl_cffi import requests
from bs4 import BeautifulSoup
from datetime import datetime

REF_DATE = datetime(2026, 3, 29)
REF_NUM = 2882

def get_sb_number(date_obj):
    # Ensure date_obj is at midnight for accurate delta
    date_obj = datetime(date_obj.year, date_obj.month, date_obj.day)
    delta = (date_obj - REF_DATE).days
    return REF_NUM + delta

async def fetch_sb_data(sb_number):
    url = f"https://www.sbsolver.com/s/{sb_number}"
    try:
        r = requests.AsyncSession()
        response = await r.get(url, impersonate="chrome110")
        
        if response.status_code != 200:
            print(f"Failed to fetch {url} with status code {response.status_code}")
            return None

        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        
        # Letters: The first letter in the 'string' input is the center letter
        letters_input = soup.find("input", id="string")
        if not letters_input:
            letters_input = soup.find("input", {"name": "string"})
        
        if not letters_input:
            print(f"Could not find letters input for {url}")
            return None
        
        letters_str = letters_input.get("value", "")
        if not letters_str:
            print(f"Letters string is empty for {url}")
            return None
        
        center = letters_str[0].upper()
        outer = [c.upper() for c in letters_str[1:]]
        
        # Words
        words = []
        pangrams = []
        table = soup.find("table", class_="bee-set")
        if table:
            rows = table.find_all("tr")
            for row in rows:
                word_td = row.find("td", class_="bee-hover")
                if word_td:
                    word = word_td.get_text(strip=True).upper()
                    words.append(word)
                    if row.find("td", class_="bee-note", string="pangram"):
                        pangrams.append(word)
        
        if not words:
            print(f"No words found for {url}")
            return None
            
        return {
            "center": center,
            "outer": outer,
            "words": words,
            "pangrams": pangrams
        }
    except Exception as e:
        print(f"An error occurred while fetching data from {url}: {e}")
        return None
