import json
import os
import time
from datetime import datetime
from typing import List, Dict

import requests


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
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def test_connection(self) -> bool:
        """
        Test the connection and authentication with Open WebUI
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to get models list as a simple auth test
            response = requests.get(f"{self.base_url}/api/models", headers=self.headers, timeout=10)

            if response.status_code == 200:
                print("✓ Connection and authentication successful")
                models = response.json()
                if models:
                    print(f"✓ Available models: {len(models.get('data', []))} found")
                return True
            elif response.status_code == 401:
                print("✗ Authentication failed (401)")
                print("  - Check your API key")
                print("  - Verify the API key has proper permissions")
                return False
            else:
                print(f"✗ Connection failed ({response.status_code})")
                print(f"  Response: {response.text[:200]}")
                return False

        except requests.exceptions.ConnectionError:
            print("✗ Connection failed - cannot reach Open WebUI server")
            print(f"  - Check if Open WebUI is running at {self.base_url}")
            print("  - Verify the URL is correct")
            return False
        except Exception as e:
            print(f"✗ Connection test failed: {str(e)}")
            return False

    def ask_question(self, question: str, collection_id: str, model: str = "llama3.1:latest") -> Dict:
        """
        Ask a question using the Open WebUI API with collection context

        Args:
            question: The question to ask
            collection_id: ID of the collection to use for context
            model: Model to use (default: llama3.1:latest)

        Returns:
            Response dictionary with answer and metadata
        """
        # Format the question to include collection context
        formatted_content = f"Using knowledge base {collection_id}: {question}"

        # Ensure we get complete response
        payload = {"model": model, "messages": [{"role": "user", "content": formatted_content}], "stream": False}

        try:
            # 30 second timeout
            response = requests.post(f"{self.base_url}/api/chat/completions", headers=self.headers, json=payload, timeout=30)

            if not response.ok:
                error_msg = f"Server returned {response.status_code}"
                if response.status_code == 401:
                    error_msg += " - Authentication failed"
                elif response.status_code == 404:
                    error_msg += " - Model or endpoint not found"
                elif response.status_code == 500:
                    error_msg += " - Internal server error"

                # Limit error text
                return {"question": question, "answer": f"Error: {error_msg}", "model": model, "timestamp": datetime.now().isoformat(), "error": response.text[:500]}

            data = response.json()

            # Extract the answer from the response
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

            if not content:
                content = f"No content in response. Raw response: {json.dumps(data)[:200]}"

            return {"question": question, "answer": content, "model": model, "timestamp": datetime.now().isoformat()}

        except requests.exceptions.Timeout:
            return {"question": question, "answer": "Error: Request timed out after 30 seconds", "model": model,
                "timestamp": datetime.now().isoformat(), "error": "timeout"}
        except Exception as e:
            return {"question": question, "answer": f"Error: {str(e)}", "model": model,
                "timestamp": datetime.now().isoformat(), "error": str(e)}

    def process_questions(self, questions: List[str], collection_id: str, output_file: str = "qa_results.txt",
                          delay_between_questions: float = 1.0, model: str = "llama3.1:latest") -> None:
        """
        Process a list of questions and save results to text file only

        Args:
            questions: List of questions to ask
            collection_id: ID of the collection to use
            output_file: Output text file path
            delay_between_questions: Delay in seconds between questions
            model: Model to use for queries
        """
        results = []
        total_questions = len(questions)

        print(f"\nProcessing {total_questions} questions")
        print(f"Using collection ID: {collection_id}")
        print(f"Model: {model}")
        print(f"Output file: {output_file}")
        print("-" * 80)

        # Test connection first
        if not self.test_connection():
            print("\nCannot proceed - connection test failed")
            return

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

            # Save results after each question (in case of interruption)
            self._save_text_results(results, output_file)

            # Delay between questions to avoid rate limiting
            if i < total_questions:
                time.sleep(delay_between_questions)

        print(f"\n{'=' * 80}")
        print(f"Completed! Results saved to: {output_file}")

    def _save_text_results(self, results: List[Dict], output_file: str) -> None:
        """Save results in human-readable text format only"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Open WebUI Q&A Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"Question {i}:\n")
                f.write(f"Q: {result['question']}\n\n")
                f.write(f"Answer:\n")
                f.write(f"A: {result['answer']}\n\n")
                f.write(f"Model: {result['model']}\n")
                f.write(f"Timestamp: {result['timestamp']}\n")

                if 'error' in result:
                    f.write(f"Error Details: {result['error']}\n")

                f.write("\n" + "-" * 80 + "\n\n")


def main():
    # Configuration
    BASE_URL = "http://localhost:3000"  # Update this to match your Open WebUI URL
    API_KEY = os.environ.get('OPENWEBUI_API_KEY', 'your-api-key-here')
    COLLECTION_ID = "e23c5dd6-60e1-435f-a4f6-806e769cc74a"  # Your collection ID
    MODEL = "llama3.1:latest"  # Change this if you want to use a different model
    OUTPUT_FILE = "openwebui_qa_results.txt"  # Now outputs only text file

    # Your questions
    questions = ["What is the purpose of Open WebUI and what are its key features?",
        "What are the Docker commands to run Open WebUI with Nvidia GPU support?",
        "How can I install Open WebUI using the uv runtime manager on macOS?",
        "What is the difference between the main and dev branches of Open WebUI?",
        "How do I update Open WebUI using Watchtower for automatic updates?",
        "What Python version is recommended for installing Open WebUI with pip?",
        "How can I access Open WebUI after installing it with Docker?",
        "What are the benefits of using the uv runtime manager over pip for Open WebUI installation?",
        "What is the command to run Open WebUI bundled with Ollama for CPU-only systems?",
        "Who are the sponsors mentioned in the Open WebUI documentation?"]

    print("Open WebUI RAG Query Tool")
    print("=" * 40)

    # Check API key
    if API_KEY == 'your-api-key-here':
        print("\n⚠️  Warning: Using default API key")
        print("\nTo fix authentication:")
        print("1. Get your API key from Open WebUI (Profile -> Account -> API Keys)")
        print("2. Set environment variable: export OPENWEBUI_API_KEY='your-actual-key'")
        print("3. Or update the API_KEY variable in this script")

        user_input = input("\nContinue anyway? (y/n): ")
        if user_input.lower() != 'y':
            return

    # Verify configuration
    print(f"\nConfiguration:")
    print(f"  Base URL: {BASE_URL}")
    print(f"  API Key: {'*' * (len(API_KEY) - 4) + API_KEY[-4:] if len(API_KEY) > 4 else 'Not set'}")
    print(f"  Collection ID: {COLLECTION_ID}")
    print(f"  Model: {MODEL}")

    # Create client and process questions
    client = OpenWebUIClient(BASE_URL, API_KEY)

    try:
        # 2-second delay between questions
        client.process_questions(questions=questions, collection_id=COLLECTION_ID, output_file=OUTPUT_FILE,
            delay_between_questions=2.0,
            model=MODEL)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
