import chromadb

client = chromadb.PersistentClient(path="/app/backend/data/vector_db")
collection = client.get_collection(name="3c0b5e64-0cde-44f5-b785-3ed5ad8af070")

print("=== Examining COVID-19 Data Commons documents ===")

# Get the specific documents
sources_to_check = [
    "www_stonybrook_edu_commcms_iedm_news_COVID_19_Data_Commons_and_Analytic_Environment.md",
    "www_stonybrook_edu_commcms_iedm_news_COVID_19%20Data_Commons_and%20Analytic_Environment.md"
]

for source in sources_to_check:
    print(f"\n--- Document: {source} ---")
    
    # Get all documents with this source
    all_docs = collection.get(
        where={"source": source},
        include=["documents", "metadatas"]
    )
    
    if all_docs['ids']:
        print(f"Found {len(all_docs['ids'])} chunks from this source")
        
        # Show the full content of each chunk
        for i, (doc_id, content) in enumerate(zip(all_docs['ids'], all_docs['documents'])):
            print(f"\nChunk {i+1} (ID: {doc_id}):")
            print("Content length:", len(content))
            
            # Show the content, looking for actual article text
            if len(content) > 500:  # If it's a substantial chunk
                print("First 500 chars:", content[:500])
                print("...")
                print("Last 500 chars:", content[-500:])
            else:
                print("Full content:", content)
            
            # Check if this is just navigation or has real content
            if "COVID" in content and len(content) > 1000:
                print("\n*** This chunk appears to have article content! ***")

print("\n=== Diagnosis ===")
print("If the documents only contain navigation/header content, the issue is that")
print("the web scraping only captured the page structure, not the article text.")
print("\nThis is a common issue with JavaScript-heavy websites where content")
print("loads dynamically after the initial page load.")
