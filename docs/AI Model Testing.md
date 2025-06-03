Here's an ADHD-friendly summary of your document with clear bullet points to help you move forward:

### Summary of the Project:

* You're testing AI models (especially Llama models) to answer questions about Stony Brook University and Medicine sites.
* The goal: see if AI can effectively become an ambassador to institutional knowledge.

### Key Points and Next Steps:

1. **Experiment Goals:**

   * Test if AI can answer specific questions effectively.
   * Check AI capabilities at identifying top experts or resources, e.g., "Who are the top 3 experts for arrhythmia?"

2. **Models and Infrastructure:**

   * You’re currently using a local Llama model (version 3.x).
   * High-end models (e.g., GPT-4, Gemini, Grok) usually perform better.
   * Experimenting with larger Llama models (70B+) on Grace Hopper server to compare with high-end models.
   * Local models avoid costly cloud bills but may be limited in capability.

3. **Technical Insights:**

   * **Thinking Models:** New versions of Llama (like 0.9) support clearer output of model reasoning (the "thinking" parameter).
   * **RAG (Retrieval-Augmented Generation):** You must manage chunk sizes, overlap, and embeddings carefully for optimal results.

4. **Infrastructure Considerations:**

   * Nexus is handling your RAG/vector database tasks.
   * Grace Hopper can host larger AI models (but currently without direct RAG/Open WebUI).
   * Routing calls from Nexus to Grace for LLM inference is feasible.

5. **Scale and Impact:**

   * Initial experiments at departmental level; scale up to university-wide queries.
   * Proving the value could unlock additional resources (hardware, funds) from stakeholders like Dave Cyril.

### Immediate Actions:

* **Test Questions:** Start by testing specific, targeted questions on your existing infrastructure.
* **Scaling Experiments:** Set up experiments on Grace Hopper to test large-scale model capabilities.
* **Technical Setup:** Explore integrating Grace Hopper (LLM host) with Nexus (vector DB/RAG).
* **Resource Planning:** Communicate results clearly to stakeholders (Joel, Joe, Bridge, Dave Cyril) to secure further resources and scale the project.

This gives you a straightforward checklist and ensures you're clear on what's happening next—go smash those experiments! 🚀✨

---

<br>

Here are 10 engaging, practical questions you could ask your scraped data from stonybrook.edu:

1. **"What standard operating procedures (SOPs) exist for managing patient records at Stony Brook Medicine?"**

2. **"Who are the top three experts at Stony Brook University specializing in cardiovascular diseases?"**

3. **"Can you outline the primary research focuses of the Department of Pharmacological Sciences?"**

4. **"What emergency protocols does Stony Brook Medicine follow for infectious disease outbreaks?"**

5. **"What collaborations exist between the biomedical informatics department and other research departments?"**

6. **"Who should I contact if I'm interested in joining clinical trials at Stony Brook?"**

7. **"List key services provided by the Stony Brook University Hospital for cancer patients."**

8. **"What guidelines or resources are provided to students and staff for mental health support?"**

9. **"Describe recent initiatives taken by Stony Brook to advance AI applications in healthcare."**

10. **"How does Stony Brook University ensure compliance with data privacy regulations (like HIPAA)?"**

These targeted questions will leverage the breadth and depth of your scraped data effectively. Happy exploring! 🌟

<br>
