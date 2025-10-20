"""
1. Load JSON → 9,659 fatwa objects (question, answer, category, url)

2. Create Documents → Each fatwa becomes a Document object with:
   - page_content: cleaned question + answer text
   - metadata: {category, url}
   
3. Extract Texts → Pull out just the text for embedding (preserving order)

4. Generate Embeddings → 
   - Process texts in batches (12 at a time)
   - Each text → 1,024-dimensional vector
   - Result: 9,659 × 1,024 NumPy array
   - Checkpoint every 50 docs for crash recovery

5. Build FAISS Index →
   - Flat (brute force) index for 100% accuracy
   - Stores all embedding vectors
   - Assigns positions: 0, 1, 2, ..., 9658

6. Create Docstore →
   - Dictionary storing full Document objects (content + metadata)
   - Keys: '0', '1', '2', ..., '9658'

7. Create Mapping →
   - Bridges FAISS positions (integers) to docstore keys (strings)
   - {0: '0', 1: '1', 245: '245', ...}

8. Package as LangChain Vectorstore →
   - Bundles: FAISS index + Docstore + Mapping + Embedding model
   - Saves to disk as 'fatwa_index/'

🔍 HOW SEARCH WORKS:
------------------
Query "نماز" → Embedding Model → Query Vector [1024 numbers]
  ↓
FAISS searches all 9,659 vectors → Returns closest positions [245, 12, 789]
  ↓
Mapping: position 245 → docstore key '245'
  ↓
Docstore['245'] → Returns full Document (content + metadata)
  ↓
User gets: text, category, url

KEY CONCEPT:
-------------
Position/Index is the glue connecting everything:
  embeddings[245] = vector for docs[245]
  FAISS position 245 = docstore key '245' = original docs[245]

Order is SACRED - never shuffle, always preserve array positions!

OUTPUT FILES:
--------------
- fatwa_embeddings.npy (raw vectors, reusable for other experiments)
- fatwa_index/ (LangChain vectorstore for production use)
- checkpoint files (for resuming if interrupted)

=================================================================================
"""

import os

print("="*80)
print("VECTOR STORE BUILDER")
print("="*80)

if os.path.exists("fatwa_index"):
    print("\n✅ Vector index already exists. Skipping embedding generation.")
    print("   Delete 'fatwa_index' folder to rebuild from scratch.\n")

else:
    print("\n🚀 Starting vector store creation process...\n")
    
    from langchain_core.documents import Document
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS as LC_FAISS
    from langchain_community.docstore.in_memory import InMemoryDocstore
    import re
    import unicodedata
    import ijson
    from tqdm import tqdm
    import numpy as np
    import faiss
    import time

    ANSWER_START = 'بِسْمِ اللہِ الرَّحْمٰنِ الرَّحِیْمِ اَلْجَوَابُ بِعَوْنِ الْمَلِکِ الْوَھَّابِ'
    ANSWER_END   = 'وَاللہُ اَعْلَمُ عَزَّوَجَلَّ وَرَسُوْلُہ اَعْلَم صَلَّی اللہُ تَعَالٰی عَلَیْہِ وَاٰلِہٖ وَسَلَّم'

    def clean_text(text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        text = text.replace(ANSWER_START, '')
        text = text.replace(ANSWER_END, '')
        text = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # =====================================================
    # STEP 1: Load Embedding Model
    # =====================================================
    print("📥 STEP 1: Loading embedding model...")
    print("   Model: intfloat/multilingual-e5-large")
    start_time = time.time()
    
    embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
    
    print(f"   ✅ Model loaded in {time.time() - start_time:.2f}s\n")

    # =====================================================
    # STEP 2: Load and Process Documents
    # =====================================================
    print("📂 STEP 2: Loading raw fatwa data...")
    
    with open('./fatwa_data/raw_fatwas.json', 'r', encoding='utf-8') as f:
        data = list(ijson.items(f, 'item'))
    
    print(f"   ✅ Loaded {len(data)} raw fatwas")
    
    print("   🔄 Creating document objects...")
    docs = [
        Document(
            page_content=f"سوال:\n{clean_text(q['question'])}\n\nجواب:\n{clean_text(q['answer'])}", 
            metadata={'category': q['category'], 'url': q['url']}
        )
        for q in data
    ]
    
    print(f"   ✅ Created {len(docs)} document objects\n")

    # =====================================================
    # STEP 3: Generate Embeddings with Checkpointing
    # =====================================================
    texts = [d.page_content for d in docs]
    metadatas = [d.metadata for d in docs]

    BATCH_SIZE = 12
    CHECKPOINT_INTERVAL = 50
    checkpoint_path = "fatwa_embeddings_checkpoint.npy"
    checkpoint_meta_path = "fatwa_embeddings_checkpoint_meta.npy"

    print("🧠 STEP 3: Generating embeddings...")
    print(f"   Total texts: {len(texts)}")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Checkpoint interval: {CHECKPOINT_INTERVAL}")
    
    # Check for existing checkpoint
    if os.path.exists(checkpoint_path) and os.path.exists(checkpoint_meta_path):
        all_embeddings = np.load(checkpoint_path)
        start_index = int(np.load(checkpoint_meta_path))
        print(f"   🔁 Resuming from checkpoint (index={start_index})")
        print(f"   📊 Progress: {start_index}/{len(texts)} ({start_index/len(texts)*100:.1f}%)\n")
    else:
        all_embeddings = np.zeros((len(texts), 1024), dtype=np.float32)
        start_index = 0
        print("   🆕 Starting fresh embedding generation\n")

    # Generate embeddings in batches
    start_time = time.time()
    
    for i in tqdm(range(start_index, len(texts), BATCH_SIZE), desc='   Embedding batches', unit='batch'):
        batch_text = texts[i:i+BATCH_SIZE]
        
        # Generate embeddings
        batch_embeds = embedding_model.embed_documents(batch_text)
        batch_embeds = np.array(batch_embeds, dtype=np.float32)
        
        # Store embeddings
        all_embeddings[i:i+len(batch_embeds)] = batch_embeds

        # Checkpoint periodically
        if (i + BATCH_SIZE) % CHECKPOINT_INTERVAL == 0:
            np.save(checkpoint_path, all_embeddings)
            np.save(checkpoint_meta_path, i + BATCH_SIZE)
            elapsed = time.time() - start_time
            remaining = (elapsed / (i + BATCH_SIZE - start_index)) * (len(texts) - i - BATCH_SIZE)
            print(f"\n   💾 Checkpoint saved at index {i + BATCH_SIZE}")
            print(f"   ⏱️  Elapsed: {elapsed/60:.1f}m | Estimated remaining: {remaining/60:.1f}m\n")

    total_time = time.time() - start_time
    print(f"\n   ✅ All embeddings generated in {total_time/60:.1f} minutes")
    print(f"   ⚡ Average speed: {len(texts)/total_time:.1f} texts/second\n")

    # =====================================================
    # STEP 4: Verify Embeddings
    # =====================================================
    print("🔍 STEP 4: Verifying embeddings quality...")
    print(f"   Shape: {all_embeddings.shape}")
    print(f"   Dtype: {all_embeddings.dtype}")
    print(f"   Mean: {all_embeddings.mean():.6f}")
    print(f"   Std: {all_embeddings.std():.6f}")
    print(f"   Min: {all_embeddings.min():.6f}")
    print(f"   Max: {all_embeddings.max():.6f}")
    print(f"   Sample vector: {all_embeddings[0][:5]}")
    
    # Quality check
    if all_embeddings.max() > 10.0 or all_embeddings.min() < -10.0:
        print("   ⚠️  WARNING: Embedding values look suspicious!")
    else:
        print("   ✅ Embedding values look correct!\n")

    # Save final embeddings
    print("   💾 Saving final embeddings to disk...")
    np.save("fatwa_embeddings.npy", all_embeddings)
    print("   ✅ Saved to: fatwa_embeddings.npy\n")

    # =====================================================
    # STEP 5: Create Flat FAISS Index (Brute Force)
    # =====================================================
    print("🔨 STEP 5: Building Flat FAISS index (brute force)...")
    print("   Index type: IndexFlatL2")
    print("   Search method: Exhaustive (100% accurate)")
    
    dimension = 1024
    flat_index = faiss.IndexFlatL2(dimension)
    
    print("   🔄 Adding vectors to index...")
    flat_index.add(all_embeddings)
    
    print(f"   ✅ Flat index created with {flat_index.ntotal} vectors")
    print(f"   📏 Dimension: {flat_index.d}\n")

    # =====================================================
    # STEP 6: Create LangChain-Compatible Vector Store
    # =====================================================
    print("🔗 STEP 6: Creating LangChain-compatible vector store...")
    
    # Create mappings
    index_to_docstore_id = {i: str(i) for i in range(len(docs))}
    docstore = InMemoryDocstore({str(i): doc for i, doc in enumerate(docs)})
    
    print("   🔄 Wrapping FAISS index with LangChain...")
    
    # Create LangChain FAISS vectorstore
    vectorstore = LC_FAISS(
        embedding_function=embedding_model,
        index=flat_index,
        docstore=docstore,
        index_to_docstore_id=index_to_docstore_id
    )
    
    # Save vectorstore
    print("   💾 Saving vector store to disk...")
    vectorstore.save_local("fatwa_index")
    print("   ✅ Saved to: fatwa_index/\n")


    # =====================================================
    # Summary
    # =====================================================
    print("="*80)
    print("✅ VECTOR STORE BUILD COMPLETE!")
    print("="*80)
    print("\n📦 Generated files:")
    print("   1. fatwa_embeddings.npy - Raw embeddings (9659 × 1024)")
    print("   2. fatwa_index/ - LangChain vector store (Flat/Brute Force)")
    print("   3. Checkpoint files - For resuming if needed")
    
    print("\n🎯 Index specifications:")
    print("   • Type: Flat (IndexFlatL2)")
    print("   • Method: Brute force exhaustive search")
    print("   • Accuracy: 100% (exact nearest neighbors)")
    print("   • Vectors: 9,659")
    print("   • Dimension: 1,024")
    
    print("\n🚀 Ready to use! Load with:")
    print("   vectorstore = FAISS.load_local('fatwa_index', embedding_model)")
    print("="*80 + "\n")