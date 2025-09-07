# Diagnose retrieval issues by testing multiple queries and identifying possible configuration problems.
import chromadb

client = chromadb.PersistentClient(path="/app/backend/data/vector_db")
collection = client.get_collection(name="3c0b5e64-0cde-44f5-b785-3ed5ad8af070")

print("=== Testing different search strategies ===")

# Test 1: Direct search with the exact title
queries = [
    "COVID 19 Data Commons and Analytic Environment",
    "Renaissance School of Medicine COVID data commons",
    "COVID 19 data commons integrated management",
    "statistical artificial intelligence COVID prediction",
]

for query in queries:
    print(f"\nQuery: '{query}'")
    results = collection.query(query_texts=[query], n_results=3)

    for i, (doc_id, distance, source) in enumerate(
        zip(results["ids"][0], results["distances"][0], results["metadatas"][0])
    ):
        print(
            f"  Result {i+1}: Distance={distance:.3f}, Source={source.get('source', 'Unknown')[:50]}..."
        )

        # Check if it's finding the COVID doc
        if "COVID_19" in source.get("source", ""):
            print("  ✓ Found COVID document!")

print("\n=== Checking Open WebUI's search settings ===")
print("\nPossible issues:")
print("1. Open WebUI might be using a different similarity threshold")
print("2. The search might be limited to top N results that don't include this doc")
print("3. The query reformulation might be changing your search")

print("\n=== Suggestions ===")
print("1. Try asking with more context:")
print(
    '   "Tell me about the COVID-19 Data Commons developed by Renaissance School of Medicine"'
)
print("")
print("2. Try being more specific:")
print(
    '   "What is the COVID-19 data commons at Stony Brook that supports integrated management?"'
)
print("")
print("3. Check Open WebUI settings:")
print("   - Go to Settings → Models → Check the RAG settings")
print("   - Try increasing 'Top K' value (number of chunks to retrieve)")
print("   - Try lowering the similarity threshold if there is one")
print("")
print("4. Or try a Reindex:")
print("   - Go to Knowledge → Select 'Stony Brook Clean' → Click Reindex")
print("   - This typically takes 5-15 minutes for ~24k documents")

# Let's also check the exact content that should be returned
print("\n=== Content Preview ===")
covid_docs = collection.get(
    where={
        "source": "www_stonybrook_edu_commcms_iedm_news_COVID_19_Data_Commons_and_Analytic_Environment.md"
    },
    include=["documents"],
)

if covid_docs["documents"]:
    content = covid_docs["documents"][0]
    # Find the main content section
    start = content.find("The Renaissance School")
    if start > 0:
        print("\nKey excerpt from the document:")
        print(content[start : start + 400] + "...")
