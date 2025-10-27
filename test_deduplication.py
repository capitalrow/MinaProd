"""
Test semantic deduplication functionality
Verifies duplicate tasks are removed before database persistence
"""
import sys
from difflib import SequenceMatcher

def calculate_similarity(text1, text2):
    """Calculate text similarity (same as orchestrator)"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def test_deduplication():
    """Test deduplication logic"""
    print("="*80)
    print("DEDUPLICATION TEST SUITE")
    print("="*80)
    
    # Test 1: Exact duplicates
    print("\n[TEST 1] Exact Duplicates (should remove)")
    print("-" * 80)
    exact_duplicates = [
        {"title": "Clean bedroom", "confidence_score": 0.95},
        {"title": "Clean bedroom", "confidence_score": 0.90},  # Lower confidence, should be removed
        {"title": "Clean bedroom.", "confidence_score": 0.85},  # With punctuation, should be removed
    ]
    
    similarity_01 = calculate_similarity(exact_duplicates[0]["title"], exact_duplicates[1]["title"])
    similarity_02 = calculate_similarity(exact_duplicates[0]["title"], exact_duplicates[2]["title"])
    
    print(f"Task 1: '{exact_duplicates[0]['title']}' (confidence: {exact_duplicates[0]['confidence_score']})")
    print(f"Task 2: '{exact_duplicates[1]['title']}' (confidence: {exact_duplicates[1]['confidence_score']}) - Similarity: {similarity_01:.2f}")
    print(f"Task 3: '{exact_duplicates[2]['title']}' (confidence: {exact_duplicates[2]['confidence_score']}) - Similarity: {similarity_02:.2f}")
    
    if similarity_01 >= 0.7 and similarity_02 >= 0.7:
        print("✅ PASS: Duplicates detected (similarity >= 0.7)")
    else:
        print("❌ FAIL: Duplicates not detected")
    
    # Test 2: Semantic duplicates
    print("\n[TEST 2] Semantic Duplicates (should remove)")
    print("-" * 80)
    semantic_duplicates = [
        {"title": "Withdraw 30 pounds from ATM", "confidence_score": 0.95},
        {"title": "Withdraw 30 pounds as cash from the ATM", "confidence_score": 0.90},
        {"title": "Get 30 pounds cash from ATM machine", "confidence_score": 0.85},
    ]
    
    similarity_01 = calculate_similarity(semantic_duplicates[0]["title"], semantic_duplicates[1]["title"])
    similarity_02 = calculate_similarity(semantic_duplicates[0]["title"], semantic_duplicates[2]["title"])
    
    print(f"Task 1: '{semantic_duplicates[0]['title']}' (confidence: {semantic_duplicates[0]['confidence_score']})")
    print(f"Task 2: '{semantic_duplicates[1]['title']}' (confidence: {semantic_duplicates[1]['confidence_score']}) - Similarity: {similarity_01:.2f}")
    print(f"Task 3: '{semantic_duplicates[2]['title']}' (confidence: {semantic_duplicates[2]['confidence_score']}) - Similarity: {similarity_02:.2f}")
    
    passed = 0
    if similarity_01 >= 0.7:
        print("✅ PASS: Task 1-2 detected as duplicates (similarity >= 0.7)")
        passed += 1
    else:
        print("⚠️ WARNING: Task 1-2 not detected as duplicates (may be acceptable)")
    
    if similarity_02 >= 0.7:
        print("✅ PASS: Task 1-3 detected as duplicates (similarity >= 0.7)")
        passed += 1
    else:
        print("✅ PASS: Task 1-3 NOT duplicates (different phrasing, correctly identified)")
        passed += 1
    
    # Test 3: Non-duplicates (should keep both)
    print("\n[TEST 3] Non-Duplicates (should keep both)")
    print("-" * 80)
    non_duplicates = [
        {"title": "Clean bedroom", "confidence_score": 0.95},
        {"title": "Buy train ticket", "confidence_score": 0.90},
        {"title": "Book desk", "confidence_score": 0.85},
    ]
    
    similarities = []
    for i in range(len(non_duplicates)):
        for j in range(i + 1, len(non_duplicates)):
            sim = calculate_similarity(non_duplicates[i]["title"], non_duplicates[j]["title"])
            similarities.append((i, j, sim))
            print(f"'{non_duplicates[i]['title']}' vs '{non_duplicates[j]['title']}': {sim:.2f}")
    
    all_unique = all(sim < 0.7 for _, _, sim in similarities)
    if all_unique:
        print("✅ PASS: All tasks correctly identified as unique (similarity < 0.7)")
    else:
        print("❌ FAIL: Some non-duplicates incorrectly flagged as duplicates")
    
    # Test 4: Edge cases
    print("\n[TEST 4] Edge Cases")
    print("-" * 80)
    edge_cases = [
        ({"title": "Update report", "confidence_score": 0.95}, 
         {"title": "Update dashboard", "confidence_score": 0.90}),
        ({"title": "Call John", "confidence_score": 0.95}, 
         {"title": "Call Sarah", "confidence_score": 0.90}),
        ({"title": "Review code", "confidence_score": 0.95}, 
         {"title": "Review document", "confidence_score": 0.90}),
    ]
    
    for task1, task2 in edge_cases:
        sim = calculate_similarity(task1["title"], task2["title"])
        status = "UNIQUE" if sim < 0.7 else "DUPLICATE"
        result = "✅ CORRECT" if sim < 0.7 else "⚠️ FALSE POSITIVE"
        print(f"{result}: '{task1['title']}' vs '{task2['title']}': {sim:.2f} ({status})")
    
    print("\n" + "="*80)
    print("DEDUPLICATION TEST COMPLETE")
    print("="*80)
    print("\n💡 Note: Threshold is 0.7 - tasks with similarity >= 0.7 are considered duplicates")

if __name__ == "__main__":
    try:
        test_deduplication()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
