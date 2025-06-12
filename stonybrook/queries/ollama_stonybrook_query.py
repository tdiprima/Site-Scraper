import subprocess
import json
from datetime import datetime

# Latest Stony Brook questions
questions = [
    "What is Stony Brook's SAT code for standardized test reporting?",
    "What does URECA stand for at Stony Brook University?",
    "What are the three first-year housing communities at Stony Brook University?",
    "What is the email address for undergraduate admissions questions at Stony Brook University?",
    "What are the different pathways to get research experience at Stony Brook University, both on-campus and off-campus?",
    "What are all the ways a transfer student can apply to Stony Brook University, and how do their requirements differ from first-year students?",
    "Walk me through the complete housing application process for a new first-year student at Stony Brook University, including all deadlines.",
    "What are all the requirements and steps to apply for the URECA Summer Research Program at Stony Brook University?",
    "If I'm interested in pre-med, what specific programs, requirements, and opportunities does Stony Brook University offer?",
    "What specific accommodations and services does Stony Brook University provide for students with dietary restrictions or food allergies?",
    "What research opportunities are specifically available at Stony Brook University for first-year students who are new to research?",
    "How do international students' application requirements at Stony Brook University differ from domestic students?",
    "If I'm a computer science major at Stony Brook University interested in AI research, what specific faculty, labs, research opportunities, and funding options are available?",
    "What are all the costs associated with living on campus at Stony Brook (housing, meals, fees) and what financial aid options help cover them?",
    "How does Stony Brook University's partnership with Brookhaven National Laboratory create opportunities for students, and in which departments?",
    "What are all the important deadlines for a high school senior applying to Stony Brook University for Fall 2026 admission, including housing, financial aid, and special programs?",
    "What's Stony Brook University's current policy on standardized testing, and how does it affect different types of applicants?",
    "I'm a prospective biology major at Stony Brook University interested in marine science and undergraduate research. Based on everything Stony Brook offers, what would be my best path through the university?",
    "What should a student at Stony Brook University do if they're struggling academically and need support services? What resources are available?",
    "I want to study abroad but also do research. How can I combine these goals at Stony Brook University?"
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

