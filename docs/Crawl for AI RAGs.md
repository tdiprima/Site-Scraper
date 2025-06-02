## 🧵 Project Recap

* 🧠 **Project Idea**: Use "Crawl for AI" to convert websites (starting with your own) into RAGs (Retrieval-Augmented Generation datasets) to let LLMs intelligently query site content.

* 🕵️ **Initial Target**: Start with your internal BMI site, then move to TCIA (The Cancer Imaging Archive) to explore their structure, value, and potential AI enhancements.

* 💡 **Use Cases**:

  * Ask LLMs smart questions about site content
  * Identify what users are building *outside* TCIA and why
  * Empower agents to notify or fetch related datasets

  * Ask intelligent questions about a site
  * Analyze user needs based on prior projects/products
  * Potentially integrate with agents for smarter data queries (e.g. find related data, alerts for new datasets)

* 🛠️ **Proof-of-Concept Focus**: Test "Crawl for AI" and similar tools. Evaluate if they can run **fully offline** with local control — avoiding SaaS fees or external dependencies.

* ⚙️ **Tool Trials**:

  * ❌ **Crawl for AI app** (hosted version) failed to work
  * ✅ **Crawl for AI Python module** worked well locally
  * ⚠️ **Firecrawl**:

    * Web version works with limits (only \~5-page previews unless you pay) 💵
    * CLI version failed immediately due to requiring a paid API key 🔐

* 🧪 **Embedding Model Experiments**:

  * Tried `all-MiniLM-L12-v2`
  * ✅ Switched to `Snowflake/snowflake-arctic-embed-l-v2.0` — significantly faster & more effective in Open WebUI 🚀

* 🧰 **RAG Setup**:

  * Built a functioning RAG using Open WebUI with custom embedding
  * Looking into building BMI-only and potentially full Stony Brook collections

* 🧩 **Big Picture**: Help justify TCIA's future via grant work by showing how AI can:

  * Surface insights from user needs
  * Analyze helpdesk ticket patterns
  * Identify missing features or community-built tools

  * What's working ✅
  * What's missing ❌
  * What AI could improve or automate 🤖

* 🔁 **Ongoing QA Loop**: Use LLMs not just to answer questions, but to *monitor quality* and find trends from past user interactions.

* 📌 **Why This Matters**: It's not just a favor to TCIA — it's foundational AI infrastructure. You're proving what works, what's worth scaling, and building a system that might outlast one-off tools.

* 🗣️ Communication Plan: You'll let Joel know what you're doing. It's not just a TCI favor — it could benefit your group and future AI infra 💬

<br>
