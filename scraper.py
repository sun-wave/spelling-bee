import cloudscraper
import asyncio
import logging
from bs4 import BeautifulSoup
from datetime import datetime

# Keeping REF_DATE and REF_NUM for compatibility if needed elsewhere, 
# though we are moving to date-based fetching.
REF_DATE = datetime(2026, 3, 29)
REF_NUM = 2882

def get_sb_number(date_obj):
    # Ensure date_obj is at midnight for accurate delta
    date_obj = datetime(date_obj.year, date_obj.month, date_obj.day)
    delta = (date_obj - REF_DATE).days
    return REF_NUM + delta

async def fetch_sb_data(date_obj):
    # URL format: https://nytbee.com/Bee_YYYYMMDD.html
    date_str = date_obj.strftime("%Y%m%d")
    url = f"https://nytbee.com/Bee_{date_str}.html"
    
    try:
        # Use cloudscraper for better handling of potential protections
        scraper = cloudscraper.create_scraper()
        
        # cloudscraper is synchronous, so run it in a thread to avoid blocking the event loop
        response = await asyncio.to_thread(scraper.get, url)
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch {url} with status code {response.status_code}")
            return None

        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        
        # Find all words and pangrams
        words = []
        pangrams = []
        
        # The words are in <div class="flex-list-item">
        items = soup.find_all("div", class_="flex-list-item")
        for item in items:
            # Extract word: usually the first child or before the <a> tag
            # If it's a pangram, it's wrapped in <strong> or <mark><strong>
            strong_tag = item.find("strong")
            if strong_tag:
                word = strong_tag.get_text(strip=True).upper()
                words.append(word)
                pangrams.append(word)
            else:
                # Normal word, it's just text before the <a> tag
                # Get the text but strip the definition link part (which is an <a> tag)
                text = item.get_text(strip=True)
                # Usually the word is at the beginning, followed by some non-alpha characters and the definition link
                # We can just take the first word-like part
                import re
                match = re.match(r'^([A-Za-z]+)', text)
                if match:
                    word = match.group(1).upper()
                    words.append(word)

        if not words:
            logging.error(f"No words found for {url}")
            return None
            
        if not pangrams:
            logging.error(f"No pangrams found for {url}")
            # Even if no pangrams, we can't reliably identify the 7 letters without them
            # But NYT always has at least one pangram.
            return None

        # Identify center letter and outer letters
        # Center letter is the only letter present in ALL words.
        all_letters = set("".join(pangrams)) # Should be exactly 7 letters
        
        center = None
        for letter in all_letters:
            if all(letter in word for word in words):
                center = letter
                break
        
        if not center:
            logging.error(f"Could not identify center letter for {url}")
            return None
            
        outer = sorted(list(all_letters - {center}))
        
        return {
            "center": center,
            "outer": outer,
            "words": words,
            "pangrams": pangrams
        }
    except Exception as e:
        logging.error(f"An error occurred while fetching data from {url}: {e}")
        return None
