from typing import TypedDict, Annotated, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from test import extract_fatwa_HTML, extract_fatwa_data

load_dotenv()

system_prompt = """
You are a precise text extractor.

You will be given the complete text of a fatwa page.
Your task is to extract the specified parts *verbatim*, exactly as they appear — 
without summarizing, paraphrasing, translating, or omitting anything.

Rules:
1. Copy the relevant portions exactly as shown in the source text.
2. Preserve line breaks, punctuation, spacing, Arabic diacritics, and Urdu script exactly.
3. Do not normalize or fix formatting.
4. Do not interpret meaning or rewrite.
5. Do not insert ellipses (…) or shorten the text in any way.
6. If a field is missing, return null.
7. The output must strictly follow the provided structured schema.

Return only the structured JSON object, with each field’s text copied verbatim.
"""


model = ChatGroq(
    model='llama-3.3-70b-versatile',
    temperature=0
)

class Fatwa(TypedDict):
    title: Annotated[
        str, 
        "Title of the fatwa — usually everything before 'دار الافتاء اھلسنت'. (verbatim, no summarization)"
    ]
    question: Annotated[
        str, 
        "Question text — typically everything between 'سوال' and 'جواب' (bounds not included). (verbatim, no summarization)"
    ]
    answer: Annotated[
        str, 
        "Answer text — typically everything between 'بِسْمِ اللہِ الرَّحْمٰنِ الرَّحِيْمِ' and 'وَ اللہُ اَعْلَمُ عَزَّ وَ جَلَّ وَ رَسُوْلُہ اَعْلَم صَلَّی اللہُ تَعَالٰی عَلَیْہِ وَ اٰلِہٖ وَ سَلَّم' (bounds included). (verbatim, no summarization)"
    ]
    mufti: Annotated[
        Optional[str], 
        "The 'مجيب' — the scholar who issued the fatwa. (verbatim, no summarization)"
    ]
    musaddiq: Annotated[
        Optional[str], 
        "The 'مصدق' — the scholar who authorized or verified the fatwa (optional). (verbatim, no summarization)"
    ]
    fatwa_no: Annotated[
        Optional[str], 
        "Fatwa number, usually formatted like 'ABC-123'. (verbatim, no summarization)"
    ]
    date: Annotated[
        Optional[str], 
        "Date of issuance — includes both Islamic (Hijri) and Gregorian dates, typically after 'تاریخ اجراء'. (verbatim, no summarization)"
    ]

structured_model = model.with_structured_output(Fatwa)


url = "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/fajr-ki-sunnat-reh-jana"
html = extract_fatwa_HTML(url)
text = extract_fatwa_data(html, url)


result = structured_model.invoke([
    SystemMessage(content=system_prompt),
    HumanMessage(content=text)
])
print('obj ==> ',result)