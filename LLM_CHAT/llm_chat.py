import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

# =====================================================
# Page Configuration
st.set_page_config(
    page_title="AI  - Fatwa Assistant",
    page_icon="🕌",
    layout="wide"
)

# =====================================================
# Load vectorstore (cached for performance)
@st.cache_resource
def load_vectorstore():
    """Load the FAISS vectorstore - runs only once"""
    embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
    vectorstore = FAISS.load_local(
        "../fatwa_index", 
        embedding_model,
        allow_dangerous_deserialization=True
    )
    return vectorstore

@st.cache_resource
def load_llm():
    """Load the LLM - runs only once"""
    # You can also use OpenAI, Anthropic, or any other LLM
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY")  # Set in environment or Streamlit secrets
    )
    return llm

# =====================================================
# Main UI
st.title("🕌 AI  - Islamic Fatwa Assistant")
st.markdown("### Get answers to your Islamic questions based on authentic fatwas")
st.divider()

# Load resources
try:
    with st.spinner("Loading AI  system..."):
        vectorstore = load_vectorstore()
        llm = load_llm()
    st.success("✅ AI  is ready!")
except Exception as e:
    st.error(f"❌ Error loading system: {str(e)}")
    st.info("💡 Make sure to set GROQ_API_KEY in your environment or use Streamlit secrets")
    st.stop()

# =====================================================
# Handle example queries from sidebar (must be before text_input)
if 'example_query' in st.session_state:
    default_query = st.session_state.example_query
    del st.session_state.example_query
else:
    default_query = ""

# =====================================================
# Search Interface
col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "🔍 اپنا سوال پوچھیں (Ask your question):",
        value=default_query,
        placeholder="e.g., نماز میں سورہ فاتحہ پڑھنا ضروری ہے؟",
        help="Type your question in Urdu, Arabic, or English",
        key="query_input"
    )

with col2:
    k = st.number_input(
        "📊 Fatwas to retrieve:",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        help="Number of relevant fatwas to use for context"
    )

search_button = st.button("🤖 Ask AI ", type="primary", use_container_width=True)

# =====================================================
# Custom Prompt Template
prompt_template = """
آپ ایک اسلامی عالم اور مفتی ہیں جو صرف دیے گئے فتاوی کی بنیاد پر جواب دیتے ہیں۔

فتاوی (Context):
{context}

سوال (Question): {question}

ہدایات (Instructions):
1. تمام فتاوی کو بغور پڑھیں اور انہی کے اندر موجود معلومات کی بنیاد پر جواب تیار کریں۔  
2. جواب **ساختہ انداز (structured format)** میں دیں، درج ذیل حصوں کے ساتھ:
   - **خلاصہ (Summary):** فتاوی کے مطابق مختصر نتیجہ۔  
   - **تفصیل (Explanation):** فتاوی میں بیان کردہ اصل تفصیلی بات۔  
   - **دلائل یا حوالے (References):** وہی آیات، احادیث یا فقہی ماخذ جو فتاوی میں ذکر ہوں۔  
   - **نتیجہ (Conclusion):** فتاوی کے مطابق حتمی حکم یا فیصلہ۔  
3. فتاوی کے الفاظ کو ممکن حد تک برقرار رکھیں؛ صرف معمولی نحوی تبدیلی کریں اگر جملہ ناقص ہو۔  
4. اپنی طرف سے کوئی نئی بات، وضاحت، تشریح، یا مثال **شامل نہ کریں۔**  
5. اگر سوال کا مکمل جواب فتاوی میں نہ ہو تو واضح طور پر لکھیں:
   **"معذرت، اس سوال کا مکمل جواب موجودہ فتاوی میں نہیں ملا۔"**  
6. اگر کسی فتوے میں تضاد یا اختلاف ہو تو صرف وہی لکھیں جو فتاوی میں مذکور ہے؛ اپنا فیصلہ نہ دیں۔  
7. ادب اور سادگی کے ساتھ اردو میں لکھیں۔

جواب (Answer):
"""

PROMPT = PromptTemplate(
    template=prompt_template, 
    input_variables=["context", "question"]
)

# =====================================================
# Search and Get LLM Response
if search_button:
    if not query.strip():
        st.warning("⚠️ براہ کرم اپنا سوال درج کریں (Please enter your question)")
    else:
        # Create retriever
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        
        # Create RAG chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        # Get response
        with st.spinner("🤔 AI  is thinking..."):
            try:
                result = qa_chain.invoke({"query": query})
                
                # Display AI Response
                st.markdown("## 🤖 AI 's Response")
                st.markdown("---")
                
                # Response in a nice box
                st.markdown(result['result'], unsafe_allow_html=True)
                
                
                st.markdown("---")
                
                # Show retrieved documents for transparency
                st.markdown("## 📚 Source Fatwas Used (For Verification)")
                st.info("👇 These are the fatwas that were provided to the AI. You can verify the answer against these sources.")
                
                for i, doc in enumerate(result['source_documents'], 1):
                    with st.expander(f"📄 Source Fatwa #{i} - {doc.metadata.get('category', 'N/A')}", expanded=False):
                        # Metadata
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"**📁 Category:** {doc.metadata.get('category', 'N/A')}")
                        with col_b:
                            url = doc.metadata.get('url', '#')
                            if url != '#':
                                st.markdown(f"**🔗 Source:** [View Original Fatwa]({url})")
                            else:
                                st.markdown(f"**🔗 Source:** N/A")
                        
                        st.divider()
                        
                        # Content
                        st.markdown("**📝 Full Content:**")
                        st.text_area(
                            label="Content",
                            value=doc.page_content,
                            height=300,
                            key=f"source_content_{i}",
                            label_visibility="collapsed"
                        )
                
            except Exception as e:
                st.error(f"❌ Error generating response: {str(e)}")
                st.info("💡 Make sure your GROQ_API_KEY is set correctly")

# =====================================================
# Sidebar - Info and Examples
with st.sidebar:
    st.header("ℹ️ About AI ")
    st.markdown("""
    This AI assistant uses:
    - **Retrieval Augmented Generation (RAG)**
    - **Authentic Fatwa Database**
    - **Advanced Language Model**
    
    **How it works:**
    1. Your question is converted to a vector
    2. Most relevant fatwas are retrieved
    3. AI reads these fatwas
    4. AI provides answer based ONLY on these fatwas
    5. Source fatwas are shown for verification
    """)
    
    st.divider()
    
    st.header("⚠️ Important Notes")
    st.warning("""
    - AI answers are based on the fatwa database
    - Always verify important matters with qualified scholars
    - Check the source fatwas provided
    - AI may refuse if information is insufficient
    """)
    
    st.divider()
    
    st.header("💡 Example Questions")
    examples = [
        "نماز میں سورہ فاتحہ پڑھنا ضروری ہے؟",
        "روزے کی نیت کب تک کی جا سکتی ہے؟",
        "زکوٰۃ کی شرح کیا ہے؟",
        "وضو کے فرائض کیا ہیں؟",
        "جمعہ کی نماز کتنے رکعت ہے؟"
    ]
    
    for example in examples:
        if st.button(example, use_container_width=True, key=f"example_{example[:10]}"):
            st.session_state.example_query = example
            st.rerun()

# =====================================================
# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    🕌 AI  System | Powered by RAG, FAISS & LLM<br>
    <small>For educational purposes - Always consult qualified scholars for important matters</small>
    </div>
    """,
    unsafe_allow_html=True
)