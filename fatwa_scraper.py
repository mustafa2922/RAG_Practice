from pathlib import Path
import json
import re
import requests
import unicodedata
import time
from bs4 import BeautifulSoup
import traceback

class FatwaDataManager:
    def __init__(self, data_dir='fatwa_data'):

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.raw_data_file = self.data_dir / "raw_fatwas.json"
        self.progress_file = self.data_dir / "progress.json"

    def save_raw_data(self, data):
        with open(self.raw_data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_raw_data(self):
        if self.raw_data_file.exists():
            with open(self.raw_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_progress(self, processed_count, total_count):
        progress = {
            'processed': processed_count,
            'total': total_count,
            'percentage': (processed_count / total_count * 100) if total_count > 0 else 0
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)

    def load_progress(self):
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'processed': 0, 'total': 0}
    
# =================== Scraper ================================================================

def scrape_single_fatwa(url):

    try:
        html = extract_fatwa_HTML(url)
        if not html:
            return {'url': url, 'error': 'No HTML found', 'question': None, 'answer': None}

        text = extract_fatwa_data(html)
        qa = extract_ques_ans(text)

        fatwa_data = {
            'url': url,
            'question': qa.get('question'),
            'answer': qa.get('answer'),
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        print(f"✅ Scraped: {url}")
        return fatwa_data

    except Exception as e:
        print(f"❌ Failed: {url} ({e})")
        traceback.print_exc()
        return {'url': url, 'error': str(e), 'question': None, 'answer': None}
 
def scrape_fatwas_batch(urls, start_idx=0, save_every=10, delay=1):

    data_manager = FatwaDataManager()
    all_fatwas = data_manager.load_raw_data()
    existing_urls = {f['url'] for f in all_fatwas}
    urls_to_scrape = [u for u in urls[start_idx:] if u not in existing_urls]

    print(f"🚀 Starting: {len(urls_to_scrape)} new URLs to scrape.\n")

    for i, url in enumerate(urls_to_scrape, start=1):
        print(f"Scraping {i}/{len(urls_to_scrape)}: {url}")
        
        # Scrape the fatwa
        result = scrape_single_fatwa(url)
        all_fatwas.append(result)
        
        # Periodically save data and progress
        if i % save_every == 0 or i == len(urls_to_scrape):
            data_manager.save_raw_data(all_fatwas)
            data_manager.save_progress(start_idx + i, len(urls))
            print(f"💾 Progress saved ({i}/{len(urls_to_scrape)})")
        
        # Rate limiting - sleep between requests (except after last one)
        if i < len(urls_to_scrape):
            time.sleep(delay)

    print(f"\n🎉 Done! Scraped {len(all_fatwas)} total fatwas.")
    return all_fatwas

#  =============================== constants ============================================================

tasmiya_pattern = r'بسم\s*الل[هہھ]\s*الرحم[ٰ]?[نں]\s*الرح[یيى]م'

start_pattern =  r'الجواب\s*بعون\s*الملک\s*الوھاب'
end_pattern = r'و\s*اللہ\s*اعلم\s*عز\s*و\s*جل\s*و\s*رسولہ\s*اعلم'

question_title = r'د[\u064B-\u0652\u0670]*\s*ا[\u064B-\u0652\u0670]*\s*ر[\u064B-\u0652\u0670]*\s*ا[\u064B-\u0652\u0670]*\s*ل[\u064B-\u0652\u0670]*\s*ا[\u064B-\u0652\u0670]*\s*ف[\u064B-\u0652\u0670]*\s*ت[\u064B-\u0652\u0670]*\s*ا[\u064B-\u0652\u0670]*\s*ء[\u064B-\u0652\u0670]*\s*ا[\u064B-\u0652\u0670]*\s*[هہھۃ][\u064B-\u0652\u0670]*\s*ل[\u064B-\u0652\u0670]*\s*س[\u064B-\u0652\u0670]*\s*[نں][\u064B-\u0652\u0670]*\s*ت[\u064B-\u0652\u0670]*'
answer_title = 'جواب'

ANSWER_START = 'بِسْمِ اللہِ الرَّحْمٰنِ الرَّحِیْمِ اَلْجَوَابُ بِعَوْنِ الْمَلِکِ الْوَھَّابِ'
ANSWER_END = 'وَاللہُ اَعْلَمُ عَزَّوَجَلَّ وَرَسُوْلُہ اَعْلَم صَلَّی اللہُ تَعَالٰی عَلَیْہِ وَاٰلِہٖ وَسَلَّم'

# ===================================== utility functions ======================================

def extract_fatwa_HTML(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "ur,en;q=0.9"
    }

    res = requests.get(url, headers=headers, timeout=30)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    capture_div = soup.find("div", id="captureDiv")

    if not capture_div:
        print("❌ No div with id='captureDiv' found.")
        return None

    return capture_div.prettify()

def extract_fatwa_data(html_content):
   
   soup = BeautifulSoup(html_content , 'html.parser')

   text = soup.get_text()
   # Replace non-breaking spaces and weird unicode spaces
   text = text.replace('\xa0', ' ').replace('\u200c', '').replace('\u200f', '')
   # Replace multiple newlines and tabs with a single space
   text = re.sub(r'[\r\n\t]+', ' ', text)
   # Replace multiple spaces with one
   text = re.sub(r'\s+', ' ', text)
   
   text = unicodedata.normalize("NFD", text)
   # Remove all combining marks (Arabic harakat)
   text = re.sub(r'[\u064B-\u0652]', '', text, flags=re.UNICODE)
   
   return unicodedata.normalize("NFC", text)

def extract_ques_ans(text):
    try:
        first_split = re.split(question_title, text)
        if len(first_split) < 2:
            raise ValueError("Question title pattern not found")
            
        second_split = re.split(start_pattern, first_split[1])
        if len(second_split) < 2:
            raise ValueError("Answer start pattern not found")

        question = second_split[0]
        question = question.replace(answer_title, '')
        question = re.sub(tasmiya_pattern, '', question)
        question = question[question.find('سوال')+len('سوال'):]

        third_split = re.split(end_pattern, second_split[1])
        if len(third_split) < 2:
            raise ValueError("Answer end pattern not found")

        answer = third_split[0]
        answer = ANSWER_START + answer + ANSWER_END

        return {'question': question.strip(), 'answer': answer.strip()}
    
    except Exception as e:
        raise ValueError(f"Failed to parse fatwa structure: {str(e)}")

# ==============================================================================================