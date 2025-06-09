import subprocess
import json
from datetime import datetime

# Latest Stony Brook questions
# questions = [
#     "What are the most popular undergraduate majors at Stony Brook University?",
#     "How does Stony Brook support undergraduate research and experiential learning?",
#     "What partnerships does Stony Brook have with industry or national research labs?",
#     "What are the current campus expansion or construction projects underway?",
#     "How does Stony Brook rank nationally and internationally in terms of research output?",
#     "What sustainability and climate action initiatives has Stony Brook implemented?",
#     "What unique programs or honors colleges are available to high-achieving students?",
#     "What are the housing options and living-learning communities on campus?",
#     "How does Stony Brook support diversity, equity, and inclusion among students and faculty?",
#     "What is the economic impact of Stony Brook University on Long Island and New York State?"
# ]
# REALLY REQUIRES RAG
questions = [
    "What academic support services are offered by the Academic Success & Tutoring Center at Stony Brook?",
    "What steps should students follow during a shelter-in-place order according to Stony Brook’s emergency guide?",
    "Which bus routes connect the Health Sciences Center to West Campus, according to the 2023 campus map?",
    "Which buildings house large lecture halls (over 250 seats) for Fall 2023 classes?",
    "According to the 2013 diversity plan, what were the top 3 institutional goals for increasing faculty diversity?",
    "Where are faculty and staff permitted to park near the Health Sciences Center?",
    "Who is listed as the director of networking services in the IT department staff directory?",
    "Which courses are required for first-semester nursing students in Fall 2023?",
    "What is the deductible and out-of-pocket max for the 2023–2024 student health insurance plan?",
    "What are the quiet hours in Stony Brook's residential communities, and how are violations handled?"
]

MODEL = "llama4:latest"  # Change if you want another model
OUTPUT_FILE = f"ollama_stonybrook_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

results = []

for idx, question in enumerate(questions, 1):
    print(f"\n[{idx}] Q: {question}")
    # Prepare prompt (you can tweak the prompt if you want more directness)
    prompt = question

    # Use ollama's CLI
    completed = subprocess.run(
        ["ollama", "run", MODEL, prompt],
        capture_output=True,
        text=True
    )

    answer = completed.stdout.strip()
    print(f"A: {answer[:200]}{'...' if len(answer) > 200 else ''}")

    results.append({
        "question": question,
        "answer": answer
    })

# Save to JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nAll results saved to {OUTPUT_FILE}")

