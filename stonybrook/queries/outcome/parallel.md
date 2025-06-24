Looking through the results, here's the breakdown of what the RAG system answered correctly versus what it couldn't answer:

## ✅ **Questions Answered Correctly (13/20):**

3. **What is Stony Brook's mascot?**
   - Correct: "Wolfie" (the Seawolves mascot)

4. **What is the official website for Stony Brook University?**
   - Correct: "https://www.stonybrook.edu/"

6. **How do I apply to Stony Brook University?**
   - Provided detailed steps and correct information

8. **What majors does Stony Brook offer?**
   - Comprehensive answer with many specific programs

9. **Does Stony Brook have a nursing program?**
   - Correct: Yes, with details about BSN, MSN, and DNP programs

12. **How do I apply for financial aid at Stony Brook?**
   - Correct: Detailed FAFSA process with school code 002889

13. **What scholarships are available at Stony Brook University?**
   - Detailed list of multiple scholarships

14. **Does Stony Brook have on-campus housing?**
   - Correct: Yes, with details about housing types

15. **How do I apply for student housing at Stony Brook?**
   - Provided detailed application process

17. **Is Stony Brook affiliated with a hospital?**
   - Correct: Stony Brook University Hospital

18. **What research institutes are part of Stony Brook University?**
   - Listed multiple institutes including Cancer Center, etc.

19. **What is Stony Brook Medicine?**
   - Comprehensive answer about the medical center

20. **Is there a medical school at Stony Brook?**
   - Correct: Renaissance School of Medicine

## ❌ **Questions Not Answered / Deflected (7/20):**

1. **What is the address of Stony Brook University?**
   - Should have given full official address: "Stony Brook, NY 11794"

2. **What are the school colors of Stony Brook?**
   - Hallucinated: "Blue and White"

5. **When was Stony Brook University founded?**
   - Answered: 1959
   - Close &mdash; it was 1957.

7. **What is the application deadline for undergraduate admissions?**
   - Failed: "Could you please tell me which institution or program you're interested in applying to?"
   - Should have known this was about Stony Brook

10. **How do I request a campus tour?**
   - Failed: Generic answer, asked "Would you like me to help you find the specific contact information or website for a particular university?"
   - Should have provided Stony Brook-specific info

11. **How much is tuition at Stony Brook for in-state students?**
   - Failed: "I recommend checking the official Stony Brook University website..."
   - Didn't provide actual tuition figures

16. **What dining options are available on campus?**
   - Failed: "Unfortunately, I don't have access to your organization's specific information. Can you please provide more context..."
   - Completely failed to recognize this was about Stony Brook

## Summary:
- **Success Rate: 65% (13/20)**
- The RAG performed well on factual questions about the university
- It struggled with:
  - Current/changing information (tuition rates, deadlines)
  - Context-dependent questions where it didn't recognize the query was about Stony Brook
  - Specific procedural information (campus tours, dining)

The most concerning failures were Q7 and Q16, where the system didn't understand the context was Stony Brook University despite all other questions being about the same institution.

<br>
