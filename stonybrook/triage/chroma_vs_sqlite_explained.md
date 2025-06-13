### 🧠 **ChromaDB** = **Vector search engine**

**What's it for?**

* It stores your **documents** as **embeddings** (vectors).
* It lets you **search semantically**: ask natural-language questions, and it returns similar documents—even if the keywords don't match exactly.

**What it contains:**

* **Document text**
* **Metadata** (like `source`, `title`, `filename`, etc.)
* **Embeddings** (the vector representation of each document)

**How you use it:**

* `collection.add(...)` → add documents
* `collection.query(...)` → search documents by meaning
* `collection.get(...)` → pull specific docs based on filters

---

### 🗃️ **SQLite Database** = **App UI + user metadata**

**What's it for?**

* It powers the **Open WebUI interface** — basically tracks what the user sees and interacts with.
* Think of it as the **admin dashboard's brain**.

**What it contains:**

* **Knowledge base metadata** (name, ID, timestamps, user associations)
* **User settings** (RAG thresholds, top\_k, theme prefs)
* **Document table** (links ChromaDB doc IDs to UI display)
* **Config settings** (like reranking parameters or feature flags)

**How you use it:**

* You **update or fix config settings** here
* You **populate the UI's document table** so users can see document entries
* You **set thresholds** that control what gets shown to the user after a search

---

### 🚀 TL;DR:

| **System** | **Purpose**                                  | **Think of it as...**            |
| ---------- | -------------------------------------------- | -------------------------------- |
| ChromaDB   | Fast vector search of your documents         | The **search engine**            |
| SQLite DB  | App state, user config, UI document listings | The **control panel + metadata** |

You **need both**: ChromaDB for *what to retrieve*, and SQLite for *how and whether it shows up in the UI*.

<br>
