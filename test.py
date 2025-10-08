import requests
import unicodedata
from bs4 import BeautifulSoup
import re
url =   "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/jora-sadaqah-karna-hadees"

def extract_fatwa_HTML(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "ur,en;q=0.9"
    }

    res = requests.get(url, headers=headers)
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

   return(text)

def parse_fatwa(text):
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Define the markers
    question_start_marker = 'dr'
    question_end_marker = 'بِسْمِ اللہِ الرَّحْمٰنِ الرَّحِیْمِ اَلْجَوَابُ بِعَوْنِ الْمَلِکِ الْوَھَّابِ اَللّٰھُمَّ ھِدَایَۃَ الْحَقِّ وَالصَّوَابِ'
    answer_end_marker = 'وَاللہُ اَعْلَمُ عَزَّوَجَلَّ وَرَسُوْلُہ اَعْلَم صَلَّی اللّٰہُ تَعَالٰی عَلَیْہِ وَاٰلِہٖ وَسَلَّم'

    # Extract question: everything after question_start_marker and before question_end_marker
    question_start = text.find(question_start_marker)
    question_end = text.find(question_end_marker)

    if question_start == -1 or question_end == -1:
        question = "Question not found."
    else:
        question = text[question_start + len(question_start_marker):question_end].strip()

    # Extract answer: everything after question_end_marker and before answer_end_marker (inclusive)
    answer_start = question_end
    answer_end = text.find(answer_end_marker)

    if answer_start == -1 or answer_end == -1:
        answer = "Answer not found."
    else:
        answer = text[answer_start:answer_end + len(answer_end_marker)].strip()

    return {
        'question': question,
        'answer': answer
    }

# html = extract_fatwa_HTML(url)

# text = extract_fatwa_data(html)

# text = text.replace('اھلسنت','dis')
# text = text.replace('بِسْمِ','khutba')
# text = text.replace('مجیب','mujeeb')

# ques_stage_1 = text.split('dis')[1]

# ques_stage_2 = ques_stage_1.split('khutba')[0]

# ques_start_index = ques_stage_2.find('سوال')
# ques_end = ' جواب'

# question = ques_stage_2[ques_start_index + len('سوال'):len(ques_stage_2)-len(ques_end)]
# answer = ques_stage_1.split('khutba')[1]

# answer = answer.split('mujeeb')[0]
# answer = answer[:0] + 'بِسْمِ' + answer[0:]

# print('question ----> ',question)
# print('answer ----> ',answer)

def remove_diacritics(text):
    # Normalize to NFD (decompose characters + diacritics)
    text = unicodedata.normalize("NFD", text)
    # Remove all combining marks (Arabic harakat)
    text = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)
    return unicodedata.normalize("NFC", text)



def get_ques(text):
    text = text.replace('سوال','dis')
    text = text.replace('بِسْمِ','khutba')
    text = text.replace('مجیب','mujeeb')

    ques_stage_1 = text.split('dis')[1]

    ques_stage_2 = ques_stage_1.split('khutba')[0]

    ques_start_index = ques_stage_2.find('سوال')
    ques_stage_2 = ques_stage_2.replace('جواب','')

    question = ques_stage_2[ques_start_index + len('سوال'):]

    print('ques_stage_1 ---------->  ' , ques_stage_1)

    answer = ques_stage_1.split('khutba')[1]

    answer = answer.split('mujeeb')[0]
    answer = answer[:0] + 'بِسْمِ' + answer[0:]

    return {
        'question':question,
        'answer':answer
    }


Ten_URLS = [ "https://www.fatwaqa.com/ur/fatawa/halal-haram/sar-mundwaye-rakhne-ka-hukum",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/jahan-insurance-lazmi-ho-wahan-insurance-ka-hukum",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/haram-parinde-ka-anda-pani-mein-toot-jaye-to-pani-ka-hukum",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/chori-ke-connection-se-pani-istemal-karna",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/parindon-aur-janwaron-ki-shakal-ke-guldan-istemal-karna",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/jaifal-khane-ka-hukum",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/haram-ke-paison-se-bani-dukan-se-kharidari-karna",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/panda-halal-hai-ya-haram",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/jandar-ki-tasveer-wala-calendar-lagana",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/baap-ka-baligha-beti-ko-gale-lagana",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/khatna-mein-baal-na-kate-to-bari-umar-mein-katwana",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/besan-muh-par-lagane-ka-hukum",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/kafir-shakhs-se-dam-karwane-ka-hukum",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/alcohol-wali-sanitizer-istemal-karne-ka-hukum",
  "https://www.fatwaqa.com/ur/fatawa/halal-haram/kya-mard-par-chandi-haram-hai"]
 
Ten_HTMLS = []

for url in Ten_URLS:
    Ten_HTMLS.append(extract_fatwa_HTML(url))

Ten_Texts = []

for html in Ten_HTMLS:
    Ten_Texts.append(extract_fatwa_data(html))

Ten_questions = []

for text in Ten_Texts:
    Ten_questions.append(get_ques(text))

print(Ten_questions)






# fatwa_obj = parse_fatwa(text)

# print(fatwa_obj)

# print(json.dumps(result, ensure_ascii=False, indent=2))