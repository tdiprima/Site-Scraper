import json
import os
import time
from datetime import datetime
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from threading import Semaphore

import requests


class OpenWebUIClient:
    """Client for interacting with Open WebUI API with RAG support"""

    def __init__(self, base_url: str, api_key: str, max_concurrent_requests: int = 10):
        """
        Initialize the Open WebUI client

        Args:
            base_url: Base URL of your Open WebUI instance
            api_key: Your Open WebUI API key
            max_concurrent_requests: Maximum number of concurrent API requests
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # Semaphore to limit concurrent requests to avoid overwhelming the server
        self.request_semaphore = Semaphore(max_concurrent_requests)

    def ask_question(self, question: str, collection_id: str, model: str = "llama4:latest", 
                    question_index: int = 0) -> Dict:
        """
        Ask a question using the Open WebUI API with collection context

        Args:
            question: The question to ask
            collection_id: ID of the collection to use for context
            model: Model to use (default: llama4:latest)
            question_index: Index of the question for tracking

        Returns:
            Response dictionary with answer and metadata
        """
        # Acquire semaphore before making request
        with self.request_semaphore:
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
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60  # Add timeout to prevent hanging
                )

                elapsed_time = time.time() - start_time

                if not response.ok:
                    return {
                        "question": question,
                        "answer": f"Error: Server returned {response.status_code}",
                        "model": model,
                        "timestamp": datetime.now().isoformat(),
                        "error": response.text,
                        "index": question_index,
                        "processing_time": elapsed_time
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
                    "timestamp": datetime.now().isoformat(),
                    "index": question_index,
                    "processing_time": elapsed_time
                }

            except Exception as e:
                return {
                    "question": question,
                    "answer": f"Error: {str(e)}",
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "index": question_index,
                    "processing_time": time.time() - start_time if 'start_time' in locals() else 0
                }

    def process_questions_parallel(self, questions: List[str], collection_id: str,
                                 output_file: str = "qa_results.json",
                                 model: str = "llama4:latest",
                                 max_workers: int = None) -> None:
        """
        Process a list of questions in parallel and save results to file

        Args:
            questions: List of questions to ask
            collection_id: ID of the collection to use
            output_file: Output file path
            model: Model to use for queries
            max_workers: Maximum number of parallel workers (default: CPU count)
        """
        if max_workers is None:
            # Use CPU count but cap it to avoid overwhelming the server
            max_workers = min(multiprocessing.cpu_count(), 16)
        
        results = []
        total_questions = len(questions)
        
        print(f"Processing {total_questions} questions in parallel")
        print(f"Using {max_workers} worker threads")
        print(f"Using collection ID: {collection_id}")
        print(f"Model: {model}")
        print("-" * 80)
        
        start_time = time.time()
        completed = 0
        
        # Create a thread pool for parallel execution
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_question = {
                executor.submit(
                    self.ask_question, 
                    question, 
                    collection_id, 
                    model,
                    i
                ): (i, question) 
                for i, question in enumerate(questions)
            }
            
            # Process completed tasks as they finish
            for future in as_completed(future_to_question):
                question_index, question = future_to_question[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    # Print progress
                    print(f"\n[{completed}/{total_questions}] Completed (Q{question_index + 1}):")
                    print(f"Q: {question}")
                    
                    # Print the answer (truncated if too long)
                    answer = result['answer']
                    if len(answer) > 200:
                        print(f"A: {answer[:200]}...")
                    else:
                        print(f"A: {answer}")
                    print(f"Processing time: {result.get('processing_time', 0):.2f}s")
                    
                except Exception as e:
                    print(f"\nError processing question {question_index + 1}: {e}")
                    results.append({
                        "question": questions[question_index],
                        "answer": f"Error: {str(e)}",
                        "model": model,
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e),
                        "index": question_index
                    })
                    completed += 1
        
        # Sort results by original question order
        results.sort(key=lambda x: x.get('index', 0))
        
        total_time = time.time() - start_time
        
        print(f"\n{'=' * 80}")
        print(f"Completed {total_questions} questions in {total_time:.2f} seconds")
        print(f"Average time per question: {total_time/total_questions:.2f}s")
        print(f"Speedup vs sequential: {(total_questions * 2) / total_time:.1f}x")
        print(f"\nResults saved to:")
        print(f"  - JSON: {output_file}")
        print(f"  - Text: {output_file.replace('.json', '_readable.txt')}")
        
        # Save results
        self._save_results(results, output_file)
        self._save_readable_results(results, output_file.replace('.json', '_readable.txt'))

    def process_questions(self, questions: List[str], collection_id: str,
                          output_file: str = "qa_results.json",
                          delay_between_questions: float = 1.0,
                          model: str = "llama4:latest") -> None:
        """
        Process a list of questions sequentially (original method)
        
        Args:
            questions: List of questions to ask
            collection_id: ID of the collection to use
            output_file: Output file path
            delay_between_questions: Delay in seconds between questions
            model: Model to use for queries
        """
        results = []
        total_questions = len(questions)

        print(f"Processing {total_questions} questions sequentially")
        print(f"Using collection ID: {collection_id}")
        print(f"Model: {model}")
        print("-" * 80)

        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{total_questions}] Processing question:")
            print(f"Q: {question}")

            # Ask the question
            result = self.ask_question(question, collection_id, model, i-1)
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
            f.write("TCIA Q&A Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"Question {i}:\n")
                f.write(f"{result['question']}\n\n")
                f.write(f"Answer:\n")
                f.write(f"{result['answer']}\n")
                if 'processing_time' in result:
                    f.write(f"\nProcessing time: {result['processing_time']:.2f} seconds\n")
                f.write("\n" + "-" * 80 + "\n\n")


def main():
    # Configuration
    BASE_URL = "http://localhost:3000"
    API_KEY = os.environ.get('OPENWEBUI_API_KEY', 'your-api-key-here')  # Uses env var if available
    COLLECTION_ID = "54e6a11e-bfd9-44dc-aea1-62584dd52cd2"  # Your collection ID
    MODEL = "llama4:latest"  # Change this if you want to use a different model
    OUTPUT_FILE = "tcia_qa_results.json"
    
    # Performance tuning options
    USE_PARALLEL = True  # Set to False to use sequential processing
    MAX_WORKERS = None  # None = auto-detect, or set a specific number
    MAX_CONCURRENT_REQUESTS = 10  # Limit concurrent API requests to avoid overwhelming server

    # Your questions
    questions = [
        # 🚀 Website Usability
        "What does the TCIA website say about how to search for datasets?",
        "How easy is it to download data from TCIA according to the website?",
        "What instructions does TCIA provide for new users?",
        "Does TCIA offer any video tutorials or walk-throughs for using the site?",
        "How does TCIA explain the process for accessing restricted collections?",

        # 🔍 Dataset Discovery & Metadata
        "What types of metadata does TCIA provide for its datasets?",
        "How does TCIA describe the process for submitting new datasets?",
        "What information does TCIA provide about imaging modalities?",
        "Does TCIA explain how to interpret the dataset descriptions?",
        "Are there any standardized terms or ontologies used in TCIA datasets?",

        # 🧠 Educational / Research Support
        "What educational materials or help guides does TCIA provide for researchers?",
        "Does TCIA offer recommendations for using its data in research studies?",
        "How does TCIA support reproducibility in imaging research?",
        "Does the TCIA website list any example studies or publications using their data?",

        # 🧩 Integration & Tools
        "Does TCIA provide APIs or programmatic access to datasets?",
        "What tools or software does TCIA recommend for analyzing its datasets?",
        "Does TCIA offer integration with external platforms like XNAT or NBIA?",
        "What does TCIA say about its DICOM support or tools for viewing images?",

        # 🔐 Privacy, Ethics, and Access
        "What does TCIA say about de-identification and patient privacy?",
        "How does TCIA ensure compliance with ethical guidelines?",
        "Are there any usage restrictions for downloading or publishing using TCIA data?",

        # 🧪 Community & Contributions
        "How can users contribute datasets to TCIA?",
        "Does the TCIA website explain how to cite datasets?",
        "What kind of user feedback mechanisms does TCIA mention?",
        "Are there any calls for data contributions or collaborations visible on TCIA?",

        # ✨ Wish List / Gaps (prompt hallucination for insight)
        "What important features does TCIA not currently have?",
        "Are there any challenges users may face when using TCIA?",
        "What suggestions does the TCIA website make for future improvements?"
    ]

    # Check API key
    if API_KEY == 'your-api-key-here':
        print("Warning: Using default API key. Set OPENWEBUI_API_KEY environment variable or update the script.")
        print("You can set it with: export OPENWEBUI_API_KEY='your-actual-key'")
        user_input = input("\nContinue anyway? (y/n): ")
        if user_input.lower() != 'y':
            return

    # Create client and process questions
    client = OpenWebUIClient(BASE_URL, API_KEY, max_concurrent_requests=MAX_CONCURRENT_REQUESTS)

    try:
        if USE_PARALLEL:
            client.process_questions_parallel(
                questions=questions,
                collection_id=COLLECTION_ID,
                output_file=OUTPUT_FILE,
                model=MODEL,
                max_workers=MAX_WORKERS
            )
        else:
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
