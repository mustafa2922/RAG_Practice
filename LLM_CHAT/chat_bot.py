import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

# =====================================================
# Page Configuration
st.set_page_config(
    page_title="AI - Fatwa Chatbot",
    page_icon="🕌",
    layout="wide"
)

# =====================================================
# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

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
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY")
    )
    return llm

def create_qa_chain(vectorstore, llm, k=3):
    """Create conversational retrieval chain with memory"""
    
    # Custom Prompt Template
    prompt_template = """
آپ ایک اسلامی عالم اور مفتی ہیں جو صرف دیے گئے فتاوی کی بنیاد پر جواب دیتے ہیں۔

پچھلی گفتگو (Chat History):
{chat_history}

فتاوی (Context):
{context}

سوال (Question): {question}

ہدایات (Instructions):
1. اگر سوال پچھلے سوالات سے متعلق ہے تو گفتگو کا تسلسل برقرار رکھیں۔
2. تمام فتاوی کو بغور پڑھیں اور انہی کے اندر موجود معلومات کی بنیاد پر جواب تیار کریں۔  
3. جواب **ساختہ انداز (structured format)** میں دیں، درج ذیل حصوں کے ساتھ:
   - **خلاصہ (Summary):** فتاوی کے مطابق مختصر نتیجہ۔  
   - **تفصیل (Explanation):** فتاوی میں بیان کردہ اصل تفصیلی بات۔  
   - **دلائل یا حوالے (References):** وہی آیات، احادیث یا فقہی ماخذ جو فتاوی میں ذکر ہوں۔  
   - **نتیجہ (Conclusion):** فتاوی کے مطابق حتمی حکم یا فیصلہ۔  
4. فتاوی کے الفاظ کو ممکن حد تک برقرار رکھیں؛ صرف معمولی نحوی تبدیلی کریں اگر جملہ ناقص ہو۔  
5. اپنی طرف سے کوئی نئی بات، وضاحت، تشریح، یا مثال **شامل نہ کریں۔**  
6. اگر سوال کا مکمل جواب فتاوی میں نہ ہو تو واضح طور پر لکھیں:
   **"معذرت، اس سوال کا مکمل جواب موجودہ فتاوی میں نہیں ملا۔"**  
7. اگر کسی فتوے میں تضاد یا اختلاف ہو تو صرف وہی لکھیں جو فتاوی میں مذکور ہے؛ اپنا فیصلہ نہ دیں۔  
8. ادب اور سادگی کے ساتھ اردو میں لکھیں۔

جواب (Answer):
"""
    
    CONDENSE_QUESTION_PROMPT = PromptTemplate(
        template="""پچھلی گفتگو اور نیا سوال دیکھ کر، ایک مکمل اور واضح standalone سوال بنائیں جو تمام ضروری سیاق و سباق کو شامل کرے۔ یہ سوال مکمل طور پر خود کفیل ہونا چاہیے تاکہ بغیر پچھلی گفتگو دیکھے بھی سمجھ آ سکے۔

مثال:
اگر نیا سوال ہے: "اور اس کی سنتیں کیا ہیں؟"
اور پچھلا سوال نماز کے بارے میں تھا
تو standalone سوال ہو گا: "نماز کی سنتیں کیا ہیں؟"

پچھلی گفتگو:
{chat_history}

نیا سوال: {question}

Standalone سوال (صرف سوال لکھیں، کوئی اضافی بات نہیں):""",
        input_variables=["chat_history", "question"]
    )
    
    QA_PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question", "chat_history"]
    )
    
    # Create retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )
    
    # Create memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    
    # Create conversational chain
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
        condense_question_prompt=CONDENSE_QUESTION_PROMPT,
        condense_question_llm=llm,  # Explicitly set LLM for question condensing
        return_generated_question=True,  # Return the condensed question for debugging
        verbose=False
    )
    
    return qa_chain

# =====================================================
# Main UI
st.title("🕌 AI - Islamic Fatwa Chatbot")
st.markdown("### Get answers to your Islamic questions with conversation memory")
st.divider()

# Load resources
try:
    with st.spinner("Loading AI system..."):
        vectorstore = load_vectorstore()
        llm = load_llm()
    st.success("✅ AI is ready!")
except Exception as e:
    st.error(f"❌ Error loading system: {str(e)}")
    st.info("💡 Make sure to set GROQ_API_KEY in your environment or use Streamlit secrets")
    st.stop()

# =====================================================
# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    k = st.number_input(
        "📊 Fatwas to retrieve:",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        help="Number of relevant fatwas to use for context"
    )
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    
    st.header("ℹ️ About AI")
    st.markdown("""
    This AI chatbot uses:
    - **Conversational Memory**
    - **RAG (Retrieval Augmented Generation)**
    - **Authentic Fatwa Database**
    - **Advanced Language Model**
    
    **How it works:**
    1. Remembers previous questions and answers
    2. Retrieves relevant fatwas from database
    3. Provides contextual answers
    4. Shows source fatwas for verification
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
# Display Chat History
st.markdown("## 💬 Conversation")

# Display all previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available
        if message["role"] == "assistant" and "sources" in message:
            with st.expander("📚 View Source Fatwas", expanded=False):
                for i, doc in enumerate(message["sources"], 1):
                    st.markdown(f"**📄 Source #{i} - {doc.metadata.get('category', 'N/A')}**")
                    
                    url = doc.metadata.get('url', '#')
                    if url != '#':
                        st.markdown(f"🔗 [View Original]({url})")
                    
                    st.text_area(
                        label="Content",
                        value=doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                        height=150,
                        key=f"msg_source_{message.get('timestamp', '')}_{i}",
                        label_visibility="collapsed"
                    )
                    st.divider()

# =====================================================
# Handle example queries from sidebar
if 'example_query' in st.session_state:
    user_input = st.session_state.example_query
    del st.session_state.example_query
else:
    user_input = None

# Chat input
if prompt := (user_input or st.chat_input("اپنا سوال پوچھیں (Ask your question)...")):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🤔 AI is thinking..."):
            try:
                # Create QA chain with current settings
                qa_chain = create_qa_chain(vectorstore, llm, k)
                
                # Load previous chat history into memory
                for msg in st.session_state.chat_history:
                    qa_chain.memory.chat_memory.add_user_message(msg["question"])
                    qa_chain.memory.chat_memory.add_ai_message(msg["answer"])
                
                # Get response
                result = qa_chain.invoke({"question": prompt})
                
                response = result['answer']
                source_docs = result['source_documents']
                
                # Debug: Show what question was actually used for retrieval
                if 'generated_question' in result:
                    with st.expander("🔍 Debug: Question used for retrieval", expanded=False):
                        st.write(f"**Original question:** {prompt}")
                        st.write(f"**Condensed question:** {result['generated_question']}")
                
                # Display response
                st.markdown(response)
                
                # Show sources in expander
                with st.expander("📚 View Source Fatwas", expanded=False):
                    for i, doc in enumerate(source_docs, 1):
                        st.markdown(f"**📄 Source #{i} - {doc.metadata.get('category', 'N/A')}**")
                        
                        url = doc.metadata.get('url', '#')
                        if url != '#':
                            st.markdown(f"🔗 [View Original]({url})")
                        
                        st.text_area(
                            label="Content",
                            value=doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                            height=150,
                            key=f"source_{i}",
                            label_visibility="collapsed"
                        )
                        st.divider()
                
                # Save to session state
                import time
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "sources": source_docs,
                    "timestamp": str(time.time())
                })
                
                # Update chat history for memory
                st.session_state.chat_history.append({
                    "question": prompt,
                    "answer": response
                })
                
            except Exception as e:
                error_msg = f"❌ Error generating response: {str(e)}"
                st.error(error_msg)
                st.info("💡 Make sure your GROQ_API_KEY is set correctly")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# =====================================================
# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    🕌 AI Chatbot System | Powered by RAG, FAISS & LLM with Memory<br>
    <small>For educational purposes - Always consult qualified scholars for important matters</small>
    </div>
    """,
    unsafe_allow_html=True
)