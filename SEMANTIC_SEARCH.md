# Semantic Search with EmbeddingGemma

Doctown now supports **semantic search** - search by concepts, vibes, and intentions rather than exact keywords!

## What is Semantic Search?

Instead of searching for exact keyword matches, semantic search understands the *meaning* of your query and finds relevant code even if it doesn't contain those exact words.

### Example Queries

- "error handling patterns" → Finds try/catch blocks, error classes, logging
- "configuration loading" → Finds config parsers, env readers, settings
- "authentication flow" → Finds login, tokens, session management
- "printing and output formatting" → Finds formatting functions, print statements
- "function that adds numbers together" → Finds calculation functions

## Technology

Uses **EmbeddingGemma-300m** from Google:
- 🪶 Lightweight: Only 600MB
- 💻 On-device: No API calls needed
- 🌍 Multilingual: Trained on 100+ languages
- 🎯 State-of-the-art: Best-in-class for its size
- 📱 Efficient: Works on laptops, desktops, even mobile

## Setup

### 1. Install Dependencies

```bash
cd documenter
source .venv/bin/activate
pip install sentence-transformers
```

### 2. Build Embeddings for Your Docpack

```bash
# Option 1: Use the helper script
./scripts/build_embeddings.sh path/to/your.docpack

# Option 2: Run directly
cd documenter
python embeddings.py path/to/your.docpack
```

This will:
- Load the EmbeddingGemma-300m model (downloads ~600MB on first run)
- Split your code into chunks
- Generate embeddings for each chunk
- Save to `your.docpack/index/embeddings.json`

### 3. Enable the Tool

Make sure `semantic_search` is in your docpack's tool list:

```json
{
  "environment": {
    "tools": [
      "list_files",
      "read_file",
      "semantic_search",  // ← Add this
      "write_output"
    ]
  }
}
```

Or use `--all-tools` when creating the docpack:

```bash
localdoc ingest ./source --out ./my.docpack --all-tools
```

## Usage in Agent

The agent can now use `semantic_search`:

```python
# Search for error handling code
semantic_search(query="error handling and exception management", top_k=5)

# Search for authentication logic
semantic_search(query="user login and authentication", top_k=3)

# Search for data validation
semantic_search(query="input validation and sanitization")
```

### Response Format

```json
{
  "results": [
    {
      "file": "utils/auth.py",
      "chunk": "def authenticate_user(username, password):\n    ...",
      "score": 0.789,
      "start_pos": 0,
      "end_pos": 500
    }
  ]
}
```

## How It Works

1. **Indexing Phase**:
   - Code is split into 500-character chunks
   - Each chunk is encoded using EmbeddingGemma
   - Embeddings stored as 768-dimensional vectors

2. **Query Phase**:
   - Your natural language query is encoded
   - Cosine similarity computed with all chunks
   - Top-k most similar chunks returned

3. **Matryoshka Representation Learning**:
   - Embeddings can be truncated to 512, 256, or 128 dimensions
   - Smaller sizes = faster search, less storage
   - (Future optimization)

## Performance

- **First run**: ~10-30 seconds (model download)
- **Subsequent runs**: Instant (model cached)
- **Indexing**: ~0.1 seconds per file
- **Search**: <100ms per query

## Tips for Best Results

1. **Be descriptive**: "database connection pooling" > "db"
2. **Use concepts**: "error handling patterns" works great
3. **Natural language**: Write like you're asking a person
4. **Combine with keyword search**: Use both tools for comprehensive coverage

## Comparison with Keyword Search

| Feature | Keyword Search | Semantic Search |
|---------|----------------|-----------------|
| Speed | Very fast | Fast |
| Exact matches | ✅ Perfect | ⚠️ May miss |
| Concept matching | ❌ No | ✅ Excellent |
| Synonyms | ❌ No | ✅ Yes |
| Context aware | ❌ No | ✅ Yes |
| Setup | None | Build embeddings |

## Future Enhancements

- [ ] Integrate into `localdoc ingest` CLI
- [ ] Support different chunk sizes
- [ ] Implement MRL truncation for faster search
- [ ] Add hybrid search (semantic + keyword)
- [ ] Cache embeddings for faster reindexing
- [ ] Support incremental updates

## Troubleshooting

### "No embeddings available"

Run `build_embeddings.sh` or `python embeddings.py <docpack>` first.

### Model download fails

Check internet connection. The model downloads from HuggingFace (~600MB).

### Out of memory

Reduce chunk size or process fewer files at once. Default 500 chars works for most cases.

### Low similarity scores

This is normal! Scores above 0.3 are usually relevant. The model is conservative.

---

Built with ❤️ using [EmbeddingGemma](https://huggingface.co/google/embeddinggemma-300m) from Google.
