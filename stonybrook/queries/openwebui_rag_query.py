import requests
import json
import time
import os
from datetime import datetime
from typing import List, Dict


class OpenWebUIClient:
    """Client for interacting with Open WebUI API with RAG support"""

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the Open WebUI client

        Args:
            base_url: Base URL of your Open WebUI instance
            api_key: Your Open WebUI API key
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def ask_question(self, question: str, collection_id: str, model: str = "llama4:latest") -> Dict:
        """
        Ask a question using the Open WebUI API with collection context

        Args:
            question: The question to ask
            collection_id: ID of the collection to use for context
            model: Model to use (default: llama4:latest)

        Returns:
            Response dictionary with answer and metadata
        """
        # Format the question to include collection context
        formatted_content = f"Using knowledge base {collection_id}: {question}"

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": formatted_content
                }
            ]
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat/completions",
                headers=self.headers,
                json=payload
            )

            if not response.ok:
                return {
                    "question": question,
                    "answer": f"Error: Server returned {response.status_code}",
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                    "error": response.text
                }

            data = response.json()

            # Extract the answer from the response
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

            if not content:
                content = f"Unexpected response format: {json.dumps(data)[:200]}"

            return {
                "question": question,
                "answer": content,
                "model": model,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "question": question,
                "answer": f"Error: {str(e)}",
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    def process_questions(self, questions: List[str], collection_id: str,
                          output_file: str = "qa_results.json",
                          delay_between_questions: float = 1.0,
                          model: str = "llama4:latest") -> None:
        """
        Process a list of questions and save results to file

        Args:
            questions: List of questions to ask
            collection_id: ID of the collection to use
            output_file: Output file path
            delay_between_questions: Delay in seconds between questions
            model: Model to use for queries
        """
        results = []
        total_questions = len(questions)

        print(f"Processing {total_questions} questions")
        print(f"Using collection ID: {collection_id}")
        print(f"Model: {model}")
        print("-" * 80)

        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{total_questions}] Processing question:")
            print(f"Q: {question}")

            # Ask the question
            result = self.ask_question(question, collection_id, model)
            results.append(result)

            # Print the answer (truncated if too long)
            answer = result['answer']
            if len(answer) > 200:
                print(f"A: {answer[:200]}...")
            else:
                print(f"A: {answer}")

            # Save intermediate results
            self._save_results(results, output_file)

            # Delay between questions to avoid rate limiting
            if i < total_questions:
                time.sleep(delay_between_questions)

        print(f"\n{'=' * 80}")
        print(f"Completed! Results saved to:")
        print(f"  - JSON: {output_file}")
        print(f"  - Text: {output_file.replace('.json', '_readable.txt')}")

        # Save human-readable version
        self._save_readable_results(results, output_file.replace('.json', '_readable.txt'))

    def _save_results(self, results: List[Dict], output_file: str) -> None:
        """Save results to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    def _save_readable_results(self, results: List[Dict], output_file: str) -> None:
        """Save results in human-readable format"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Stony Brook Medicine Q&A Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"Question {i}:\n")
                f.write(f"{result['question']}\n\n")
                f.write(f"Answer:\n")
                f.write(f"{result['answer']}\n")
                f.write("\n" + "-" * 80 + "\n\n")


def main():
    # Configuration
    BASE_URL = "http://localhost:3000"
    API_KEY = os.environ.get('OPENWEBUI_API_KEY', 'your-api-key-here')  # Uses env var if available
    COLLECTION_ID = "3c0b5e64-0cde-44f5-b785-3ed5ad8af070"  # Your Stony Brook collection ID
    MODEL = "llama4:latest"  # Change this if you want to use a different model
    OUTPUT_FILE = "stonybrook_qa_results.json"

    # Your questions
    questions = [
        "What is Stony Brook's SAT code for standardized test reporting?",
        "What is the housing deposit amount for undergraduate students at Stony Brook University?",
        "What does URECA stand for at Stony Brook University?",
        "What are the three first-year housing communities at Stony Brook University?",
        "What is the email address for undergraduate admissions questions at Stony Brook University?",
        "What's the difference between corridor-style and suite-style housing at Stony Brook, and which communities offer each type?",
        "Compare the meal plan options at Stony Brook University – what's included in Wolfie Deluxe vs Wolfie Unlimited?",
        "What are the different pathways to get research experience at Stony Brook University, both on-campus and off-campus?",
        "What are all the ways a transfer student can apply to Stony Brook University, and how do their requirements differ from first-year students?",
        "Walk me through the complete housing application process for a new first-year student at Stony Brook University, including all deadlines.",
        "What are all the requirements and steps to apply for the URECA Summer Research Program at Stony Brook University?",
        "If I'm interested in pre-med, what specific programs, requirements, and opportunities does Stony Brook University offer?",
        "What's the complete process for a continuing student at Stony Brook to select housing for next year?",
        "What specific accommodations and services does Stony Brook University provide for students with dietary restrictions or food allergies?",
        "What options are available for students who missed the housing deposit deadline at Stony Brook University?",
        "What research opportunities are specifically available at Stony Brook University for first-year students who are new to research?",
        "How do international students' application requirements at Stony Brook University differ from domestic students?",
        "If I'm a computer science major at Stony Brook University interested in AI research, what specific faculty, labs, research opportunities, and funding options are available?",
        "What are all the costs associated with living on campus at Stony Brook (housing, meals, fees) and what financial aid options help cover them?",
        "How does Stony Brook University's partnership with Brookhaven National Laboratory create opportunities for students, and in which departments?",
        "What are all the important deadlines for a high school senior applying to Stony Brook University for Fall 2026 admission, including housing, financial aid, and special programs?",
        "What's Stony Brook University's current policy on standardized testing, and how does it affect different types of applicants?",
        "How do room selection priorities work at Stony Brook University, and what happens if there's not enough space?",
        "What specific qualifications are needed for the Frances Velay Women and Science Research Fellowship at Stony Brook University?",
        "What are the exact requirements for CSE 487 (Research in Computer Science) credits to count toward major requirements at Stony Brook University?",
        "What is the mashgiach availability policy for Delancey Street Deli's kosher supervision at Stony Brook University?",
        "I'm a prospective biology major at Stony Brook University interested in marine science and undergraduate research. Based on everything Stony Brook offers, what would be my best path through the university?",
        "What should a student at Stony Brook University do if they're struggling academically and need support services? What resources are available?",
        "I want to study abroad but also do research. How can I combine these goals at Stony Brook University?",
        "Can graduate students live in first-year housing communities at Stony Brook University?",
        "What are the admission requirements for the 'Super Scholars Program' at Stony Brook University?",
        "How much does it cost to change your major at Stony Brook University?"
    ]

    # Check API key
    if API_KEY == 'your-api-key-here':
        print("Warning: Using default API key. Set OPENWEBUI_API_KEY environment variable or update the script.")
        print("You can set it with: export OPENWEBUI_API_KEY='your-actual-key'")
        user_input = input("\nContinue anyway? (y/n): ")
        if user_input.lower() != 'y':
            return

    # Create client and process questions
    client = OpenWebUIClient(BASE_URL, API_KEY)

    try:
        client.process_questions(
            questions=questions,
            collection_id=COLLECTION_ID,
            output_file=OUTPUT_FILE,
            delay_between_questions=2.0,  # 2-second delay between questions
            model=MODEL
        )
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
