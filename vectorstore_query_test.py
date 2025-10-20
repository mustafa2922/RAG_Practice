import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# =====================================================
# Page Configuration
st.set_page_config(
    page_title="Fatwa Search System",
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
        "fatwa_index", 
        embedding_model,
        allow_dangerous_deserialization=True
    )
    return vectorstore

# =====================================================
# Main UI
st.title("🕌 Fatwa Search System")
st.markdown("### Search through Islamic fatwas using semantic search")
st.divider()

# Load vectorstore
try:
    with st.spinner("Loading vector store..."):
        vectorstore = load_vectorstore()
    st.success("✅ Vector store loaded successfully!")
except Exception as e:
    st.error(f"❌ Error loading vector store: {str(e)}")
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
        "🔍 Enter your query:",
        value=default_query,
        placeholder="e.g., نماز میں سورہ فاتحہ",
        help="Type your question in Urdu, Arabic, or English",
        key="query_input"
    )

with col2:
    k = st.number_input(
        "📊 Number of results:",
        min_value=1,
        max_value=50,
        value=10,
        step=1
    )

search_button = st.button("🚀 Search", type="primary", use_container_width=True)

# =====================================================
# Search and Display Results
if search_button:
    if not query.strip():
        st.warning("⚠️ Please enter a query")
    else:
        with st.spinner(f"Searching for top {k} relevant fatwas..."):
            results = vectorstore.similarity_search(query, k=k)
        
        st.success(f"✅ Found {len(results)} relevant fatwas!")
        st.divider()
        
        # Display results in expandable cards
        for i, doc in enumerate(results, 1):
            with st.expander(f"📄 Result #{i} - {doc.metadata.get('category', 'N/A')}", expanded=(i==1)):
                # Metadata
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**📁 Category:** {doc.metadata.get('category', 'N/A')}")
                with col_b:
                    url = doc.metadata.get('url', '#')
                    if url != '#':
                        st.markdown(f"**🔗 Source:** [View Fatwa]({url})")
                    else:
                        st.markdown(f"**🔗 Source:** N/A")
                
                st.divider()
                
                # Content
                st.markdown("**📝 Content:**")
                st.text_area(
                    label="Content",
                    value=doc.page_content,
                    height=200,
                    key=f"content_{i}",
                    label_visibility="collapsed"
                )

# =====================================================
# Sidebar - Info and Examples
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This system uses **semantic search** to find relevant Islamic fatwas based on your query.
    
    **How it works:**
    1. Enter your question
    2. Choose number of results
    3. Click Search
    4. Browse relevant fatwas
    """)
    
    st.divider()
    
    st.header("💡 Example Queries")
    examples = [
        "نماز میں سورہ فاتحہ پڑھنا",
        "روزے کی نیت کب تک",
        "زکوٰۃ کی شرح کیا ہے",
        "وضو کے فرائض",
        "عید کی نماز کا وقت"
    ]
    
    for example in examples:
        if st.button(example, use_container_width=True):
            st.session_state.example_query = example
            st.rerun()

# =====================================================
# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    🕌 Fatwa Search System | Powered by FAISS & Streamlit
    </div>
    """,
    unsafe_allow_html=True
)