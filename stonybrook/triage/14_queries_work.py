# Provide suggested improved queries to better match Open WebUI's retrieval system.
queries_to_try = [
    "Tell me about the Renaissance School of Medicine COVID data commons",
    "Describe the COVID-19 data analytics developed by Renaissance School and Engineering",
    "What COVID data commons supports integrated management at Stony Brook?",
]

print("=== Queries that should work better ===")
for q in queries_to_try:
    print(f"• {q}")

print("\n=== Why your original query might fail ===")
print("The exact phrase 'COVID 19 Data Commons and Analytic Environment' might be")
print(
    "triggering Open WebUI to look for an EXACT match rather than semantic similarity."
)
print("\nUsing more natural language often works better with RAG systems.")
