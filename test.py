import faiss
import numpy as np

print("="*80)
print("🔍 FAISS Index Inspector")
print("="*80)

# Load the flat index
index = faiss.read_index("fatwa_index_flat.faiss")

print(f"\n📊 Basic Info:")
print(f"   Index Type: {type(index)}")
print(f"   Total Vectors: {index.ntotal}")
print(f"   Dimension: {index.d}")
print(f"   Is Trained: {index.is_trained}")

# Extract all vectors from the flat index
print(f"\n🔄 Extracting vectors from index...")
all_vectors = np.zeros((index.ntotal, index.d), dtype=np.float32)

for i in range(index.ntotal):
    all_vectors[i] = index.reconstruct(i)

print(f"✅ Extracted {all_vectors.shape[0]} vectors")

# Statistical analysis
print(f"\n📈 Statistical Analysis:")
print(f"   Mean: {all_vectors.mean():.6f}")
print(f"   Std Dev: {all_vectors.std():.6f}")
print(f"   Min: {all_vectors.min():.6f}")
print(f"   Max: {all_vectors.max():.6f}")

# Check for issues
print(f"\n⚠️  Potential Issues:")
print(f"   All zeros? {np.all(all_vectors == 0)}")
print(f"   All same? {np.all(all_vectors == all_vectors[0])}")
print(f"   Contains NaN? {np.isnan(all_vectors).any()}")
print(f"   Contains Inf? {np.isinf(all_vectors).any()}")

# Check diversity
print(f"\n🎲 Diversity Check:")
unique_vectors = len(np.unique(all_vectors, axis=0))
print(f"   Unique vectors: {unique_vectors} / {index.ntotal}")
if unique_vectors < index.ntotal:
    print(f"   ⚠️  WARNING: {index.ntotal - unique_vectors} duplicate vectors found!")

# Sample vectors
print(f"\n📝 Sample Vectors (first 10 dimensions):")
for i in range(min(5, index.ntotal)):
    print(f"   Vector {i}: {all_vectors[i][:10]}")

# Test search functionality
print(f"\n🔍 Testing Search Functionality:")
test_query = all_vectors[0]  # Use first vector as query
distances, indices = index.search(test_query.reshape(1, -1), k=5)

print(f"   Query: Vector 0")
print(f"   Top 5 results:")
for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
    print(f"      {i+1}. Index: {idx}, Distance: {dist:.6f}")

if indices[0][0] != 0:
    print(f"   ⚠️  WARNING: First result should be index 0 (itself)!")

# Test with different query
if index.ntotal > 1:
    test_query2 = all_vectors[100] if index.ntotal > 100 else all_vectors[1]
    distances2, indices2 = index.search(test_query2.reshape(1, -1), k=5)
    
    print(f"\n   Query: Vector {100 if index.ntotal > 100 else 1}")
    print(f"   Top 5 results:")
    for i, (dist, idx) in enumerate(zip(distances2[0], indices2[0])):
        print(f"      {i+1}. Index: {idx}, Distance: {dist:.6f}")
    
    # Check if results are always the same
    if np.array_equal(indices[0], indices2[0]):
        print(f"   🚨 CRITICAL ERROR: Different queries returning SAME results!")
    else:
        print(f"   ✅ Different queries return different results (Good!)")

print(f"\n{'='*80}")
print("✅ Inspection Complete!")
print("="*80)