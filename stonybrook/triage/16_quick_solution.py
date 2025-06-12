import chromadb
import uuid

print("=== QUICK FIX: Adding COVID content with enhanced metadata ===")

client = chromadb.PersistentClient(path="/app/backend/data/vector_db")
collection = client.get_collection(name="3c0b5e64-0cde-44f5-b785-3ed5ad8af070")

# Get the COVID document content
covid_docs = collection.get(
    where={"source": "www_stonybrook_edu_commcms_iedm_news_COVID_19_Data_Commons_and_Analytic_Environment.md"},
    include=["documents"]
)

if covid_docs['documents']:
    content = covid_docs['documents'][0]
    
    # Extract the main content (after the navigation stuff)
    start = content.find("The Renaissance School of Medicine")
    if start > 0:
        main_content = content[start:]
    else:
        main_content = content
    
    # Add multiple versions with different metadata to ensure it's found
    versions = [
        {
            "id": f"covid_enhanced_{uuid.uuid4()}",
            "metadata": {
                "source": "COVID-19_Data_Commons_PRIORITY.md",
                "title": "COVID-19 Data Commons and Analytic Environment",
                "keywords": "COVID-19 COVID Data Commons Analytic Environment Renaissance School Medicine",
                "content_type": "article",
                "priority": "high"
            }
        },
        {
            "id": f"covid_enhanced_{uuid.uuid4()}",
            "metadata": {
                "source": "Research_COVID19_Data_Analytics.md",
                "title": "COVID-19 Research Data Platform",
                "keywords": "coronavirus pandemic data analytics medical research",
                "content_type": "research",
                "priority": "high"
            }
        }
    ]
    
    # Add both versions
    for v in versions:
        collection.add(
            ids=[v["id"]],
            documents=[main_content],
            metadatas=[v["metadata"]]
        )
        print(f"✓ Added: {v['metadata']['title']}")
    
    print("\n✅ SUCCESS! The COVID content has been re-added with better metadata.")
    print("\n🎯 NOW TRY IN OPEN WEBUI:")
    print("   - 'Tell me about the COVID-19 Data Commons'")
    print("   - 'COVID data analytics platform'")
    print("   - 'coronavirus research data'")
    
else:
    print("❌ Could not find the COVID document to enhance")

# Verify it was added
print("\n=== Verification ===")
test_results = collection.query(
    query_texts=["COVID-19 Data Commons"],
    n_results=5
)
print(f"Found {len(test_results['ids'][0])} results for 'COVID-19 Data Commons'")
for i, source in enumerate(test_results['metadatas'][0]):
    print(f"  {i+1}. {source.get('source', 'Unknown')}")
