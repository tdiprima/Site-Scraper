First off, Not-RAG answered all questions confidently.

---

Here's a summary of which questions were **answered correctly ✅** and which ones the AI **didn't know ❌**, based on language like "I recommend checking," "I don't have," or "this information is not available."

---

### ✅ **Answered Correctly** (YES):

* What is Stony Brook's SAT code?
* What does URECA stand for?
* What is the email for undergraduate admissions?
* What are the different pathways to get research experience?
* What are the ways a transfer student can apply?
* Walk me through the housing application process.
* What are the requirements for URECA Summer Research?
* What does Stony Brook offer for pre-med students?
* What accommodations are available for dietary restrictions?
* What research is available for first-year students?
* How do international student requirements differ?
* What are AI research opportunities for CS majors?
* What are the costs of living on campus & financial aid?
* What's the impact of the Brookhaven National Lab partnership?
* What are the Fall 2026 application deadlines?
* What's the standardized testing policy?
* What's the best path for a marine bio research student?
* What to do if you're struggling academically?
* How to combine study abroad and research?

---

### ❌ **Not Answered / Recommended to Check / Missing Info** (NO):

* What is the housing deposit amount?
* Corridor-style vs. suite-style housing?
* Wolfie Deluxe vs. Wolfie Unlimited meal plan?
* Housing selection process for continuing students?
* What options are available if you missed the housing deposit deadline?
* Room selection priorities and lack of space?
* Frances Velay Fellowship qualifications?
* CSE 487 credit requirements?
* Mashgiach availability policy at Delancey Street Deli?
* Can graduate students live in first-year housing?
* Admission requirements for the "Super Scholars Program"?
* Cost to change your major?

### Hallucinated

* What are the first-year housing communities?

**First-Year Housing**  
Eleanor Roosevelt Community. These are corridor style, primarily double rooms with limited design three-person rooms and single rooms. ...  
Mendelsohn Community. Corridor style, double rooms. ...  
H Community. Corridor style, double rooms. ...  
Yang Hall. Living Learning Community suite style, double rooms.

https://www.stonybrook.edu/commcms/studentaffairs/res/First_Year_Student_Housing.php

---

**Spot-checked a few no's - we really don't have that info.**

<br>

Here's the count based on the breakdown:

* ✅ **Answered Correctly**: **19**
* ❌ **Not Answered / Uncertain**: **12**
* ❌ **Hallucinated** - at least 1

So, **19/32** were solid answers. The other **12** had hedging, missing details, or told you to go look elsewhere.

<br>

Both Ollama with no RAG, and Open WebUI with RAG, hallucinated the answer to this question: "What are the first-year housing communities?"

---

<br>

* **The second time it ran (with the newer RAG template), it got the following right (vs general knowledge):**

  * **Prompt:** *Compare the meal plan options at Stony Brook University – what's included in Wolfie Deluxe vs. Wolfie Unlimited?*

    * ✅ Answered correctly with detailed comparison.

* **This one was answered better the second time:**

  * **Prompt:** *What are all the requirements and steps to apply for the URECA Summer Research Program at Stony Brook University?*

    * Example: *"Letters of recommendation (2–3)"*
    * ✅ Gave a more complete and accurate response.

* **This one was weird both times:**

  * **Prompt:** *What's the complete process for a continuing student at Stony Brook to select housing for next year?*

    * ❌ Replied oddly with unrelated info like:

      *"To get the most accurate voting information, check with your local election office."*

* **This one was answered badly:**

  * **Prompt:** *What's Stony Brook University's current policy on standardized testing, and how does it affect different types of applicants?*

    * ❌ Gave vague, outdated info like:

      *"As of my last update..."*

* **This one was answered correctly by saying it didn't know:**

  * **Prompt:** *Can graduate students live in first-year housing communities at Stony Brook University?*

    * ✅ Response acknowledged lack of info — which is better than hallucinating.


<br>

### Newest RAG template and updated system prompt:

* **Answered totally wrong:**

  * **Prompt:** *What is the housing deposit amount for undergraduate students at Stony Brook University?*

    * ❌ Responded with:

      *"To get the most accurate voting information, check with your local election office."*
    * 💀 Completely irrelevant.

* **Still hallucinating:**

  * **Prompt:** *What are the three first-year housing communities at Stony Brook University?*

    * ❌ Invents or misrepresents info.

* **Improved – now gives a helpful answer:**

  * **Prompt:** *Compare the meal plan options at Stony Brook University*

    * ✅ Used to hallucinate, now provides useful info.

* **Improved – used to hallucinate, now better:**

  * **Prompt:** *What options are available for students who missed the housing deposit deadline at Stony Brook University?*

    * ✅ Now gives a solid answer.

* **Still outdated:**

  * **Prompt:** *What's Stony Brook University's current policy on standardized testing...?*

    * ❌ Still uses phrases like:

      *"As of my last update..."*

* **Got worse – used to be better:**

  * **Prompt:** *How do room selection priorities work at Stony Brook University, and what happens if there's not enough space?*

    * ❌ Now replies with unrelated content like:

      *"To get the most accurate voting information..."*

* **More accurate this time:**

  * **Prompt:** *What specific qualifications are needed for the Frances Velay Women and Science Research Fellowship at Stony Brook University?*

    * ✅ Gave a more precise response.

* **Answered badly this time:**

  * **Prompt:** *What are the exact requirements for CSE 487 (Research in Computer Science) credits to count toward major requirements at Stony Brook University?*

    * ❌ Responded with irrelevant voting office message again. Yikes.

* **Still solid:**

  * **Prompt:** *Can graduate students live in first-year housing communities at Stony Brook University?*

    * ✅ Maintains accurate response (says it doesn't know, which is appropriate).

<br>

Let's break it down real quick — side-by-side, straight to the point:

---

### ✅ **Correct / Improved Answers**

* **First Batch: 4/6 good**

  * Meal Plan Comparison ✅
  * URECA Requirements ✅
  * Grad Students in First-Year Housing ✅
  * URECA better the second time ✅

* **Second Batch: 4/9 good**

  * Meal Plan Comparison ✅ (was bad before, now better)
  * Missed Housing Deposit Options ✅ (now better)
  * Frances Velay Fellowship ✅ (more accurate now)
  * Grad Students in First-Year Housing ✅ (still accurate)

---

### ❌ **Incorrect / Weird / Outdated Answers**

* **First Batch: 2/6 flawed**

  * Housing Selection Process ❌ (weird voting info both times)
  * Standardized Testing Policy ❌ (outdated)

* **Second Batch: 5/9 flawed**

  * Housing Deposit Amount ❌ (voting hallucination)
  * First-Year Housing Communities ❌ (hallucination)
  * Standardized Testing Policy ❌ (still outdated)
  * Room Selection Priorities ❌ (was better before, now hallucinating)
  * CSE 487 Requirements ❌ (voting hallucination)

---

### 🏁 Verdict:

**The first batch fared better.**

* Higher accuracy rate (4/6 = \~67%)
* Fewer hallucinations or regressions
* Second batch had some improvements but more overall screw-ups (4/9 = \~44%)

So yeah — second run had some wins, but also more crashes. Still needs tuning.

**So I tuned it, queried these 11 questions, and it worked out better.**

<br>

### Llama3.1 RAG... was bad!

With the 11 questions, it kept saying, like, "I can't help you with that", "I couldn't find any information about it..."

<br>
