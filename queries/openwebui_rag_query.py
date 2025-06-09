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
    COLLECTION_ID = "8481691e-f9f2-4653-9643-4910e2e3499b"  # Your Stony Brook collection ID
    MODEL = "llama4:latest"  # Change this if you want to use a different model
    OUTPUT_FILE = "stonybrook_qa_results.json"

    # Your questions
    # questions = [
    #     "What standard operating procedures (SOPs) exist for managing patient records at Stony Brook Medicine?",
    #     "Who are the top three experts at Stony Brook University specializing in cardiovascular diseases?",
    #     "Can you outline the primary research focuses of the Department of Pharmacological Sciences?",
    #     "What emergency protocols does Stony Brook Medicine follow for infectious disease outbreaks?",
    #     "What collaborations exist between the biomedical informatics department and other research departments?",
    #     "Who should I contact if I'm interested in joining clinical trials at Stony Brook?",
    #     "List key services provided by the Stony Brook University Hospital for cancer patients.",
    #     "What guidelines or resources are provided to students and staff for mental health support?",
    #     "Describe recent initiatives taken by Stony Brook to advance AI applications in healthcare.",
    #     "How does Stony Brook University ensure compliance with data privacy regulations (like HIPAA)?"
    # ]
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
    # REALLY REQUIRES RAG:
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
            delay_between_questions=2.0,  # 2 second delay between questions
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
