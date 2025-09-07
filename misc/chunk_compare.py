def chunk_text(text, chunk_size=1000, chunk_overlap=150):
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == text_length:
            break
        start = end - chunk_overlap
    return chunks


def show_chunk_samples(chunks, label, n=3):
    print(f"\n--- {label} ---")
    print(f"Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks[:n]):
        print(f"\nChunk {i+1} (len={len(chunk)}):")
        print(chunk[:300] + ("..." if len(chunk) > 300 else ""))
    if len(chunks) > n:
        print(f"...({len(chunks)-n} more chunks)\n")


if __name__ == "__main__":
    # Insert scraped page text here
    with open("features_plugin_events.md", "r", encoding="utf-8") as f:
        text = f.read()

    # Config 1: 1000/150
    chunks_1000_150 = chunk_text(text, chunk_size=1000, chunk_overlap=150)
    show_chunk_samples(chunks_1000_150, "Chunks (1000/150)")

    # Config 2: 500/100
    chunks_500_100 = chunk_text(text, chunk_size=500, chunk_overlap=100)
    show_chunk_samples(chunks_500_100, "Chunks (500/100)")
