"""
Semantic search using EmbeddingGemma-300m for code understanding.
Lightweight, on-device embedding model from Google.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np


class EmbeddingSearcher:
    """Semantic search using EmbeddingGemma-300m."""

    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self.embeddings_path = index_dir / "embeddings.json"
        self.model = None
        self._embeddings_cache = None

    def _load_model(self):
        """Lazy load the sentence transformer model."""
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            print("Loading EmbeddingGemma-300m model (first run may download ~600MB)...")
            self.model = SentenceTransformer("google/embeddinggemma-300m")
            print("Model loaded successfully!")
        return self.model

    def _load_embeddings_cache(self) -> Dict:
        """Load cached embeddings from disk."""
        if self._embeddings_cache is None:
            if self.embeddings_path.exists():
                with open(self.embeddings_path, 'r') as f:
                    self._embeddings_cache = json.load(f)
            else:
                self._embeddings_cache = {
                    "chunks": [],
                    "embeddings": [],
                    "metadata": {}
                }
        return self._embeddings_cache

    def build_embeddings(self, files_dir: Path, chunk_size: int = 500) -> None:
        """
        Build embeddings for all files in the docpack.

        Args:
            files_dir: Directory containing files to embed
            chunk_size: Number of characters per chunk (default 500)
        """
        model = self._load_model()
        chunks = []
        metadata = []

        print(f"Building embeddings from {files_dir}...")

        # Walk through all files and create chunks
        for file_path in files_dir.rglob('*'):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Skip empty files
                    if not content.strip():
                        continue

                    rel_path = file_path.relative_to(files_dir)

                    # Split into chunks
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i + chunk_size]
                        chunks.append(chunk)
                        metadata.append({
                            "file": str(rel_path),
                            "start_pos": i,
                            "end_pos": min(i + chunk_size, len(content))
                        })

                except Exception as e:
                    print(f"Warning: Could not process {file_path}: {e}")
                    continue

        if not chunks:
            print("No text content found to embed")
            return

        print(f"Encoding {len(chunks)} chunks...")

        # Encode all chunks as documents
        embeddings = model.encode_document(chunks, show_progress_bar=True)

        # Convert to list for JSON serialization
        embeddings_list = embeddings.tolist()

        # Save to disk
        data = {
            "chunks": chunks,
            "embeddings": embeddings_list,
            "metadata": {
                "chunk_count": len(chunks),
                "chunk_size": chunk_size,
                "model": "google/embeddinggemma-300m",
                "embedding_dim": len(embeddings_list[0]) if embeddings_list else 0,
                "file_metadata": metadata
            }
        }

        print(f"Saving embeddings to {self.embeddings_path}...")
        with open(self.embeddings_path, 'w') as f:
            json.dump(data, f)

        print(f"✓ Successfully built embeddings for {len(chunks)} chunks")
        self._embeddings_cache = data

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Semantic search for query.

        Args:
            query: Natural language query (e.g., "error handling patterns")
            top_k: Number of results to return

        Returns:
            List of dicts with 'file', 'chunk', 'score', and 'context'
        """
        embeddings_data = self._load_embeddings_cache()

        if not embeddings_data.get("chunks"):
            return {"error": "No embeddings available. Build embeddings first."}

        model = self._load_model()

        # Encode query
        query_embedding = model.encode_query(query)

        # Convert stored embeddings to numpy array with consistent dtype
        doc_embeddings = np.array(embeddings_data["embeddings"], dtype=np.float32)

        # Compute similarities
        similarities = model.similarity(query_embedding, doc_embeddings)[0]

        # Convert to numpy if it's a tensor
        if hasattr(similarities, 'cpu'):
            similarities = similarities.cpu().numpy()
        elif not isinstance(similarities, np.ndarray):
            similarities = np.array(similarities)

        # Get top-k results (argsort gives ascending order, so we reverse)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            idx = int(idx)
            file_meta = embeddings_data["metadata"]["file_metadata"][idx]

            results.append({
                "file": file_meta["file"],
                "chunk": embeddings_data["chunks"][idx],
                "score": float(similarities[idx]),
                "start_pos": file_meta["start_pos"],
                "end_pos": file_meta["end_pos"]
            })

        return results

    def find_neighbors(self, file_path: str, top_k: int = 5) -> List[Dict]:
        """
        Find files semantically similar to the given file.
        This is the inverse of semantic search - instead of searching for concepts,
        you provide a file and get similar files back.

        Args:
            file_path: Path to the file to find neighbors for (relative to files_dir)
            top_k: Number of similar files to return (default: 5)

        Returns:
            List of dicts with 'file', 'score', and 'representative_chunk'
        """
        embeddings_data = self._load_embeddings_cache()

        if not embeddings_data.get("chunks"):
            return {"error": "No embeddings available. Build embeddings first."}

        # Get all chunks for the target file
        file_chunks = []
        file_embeddings = []

        for i, meta in enumerate(embeddings_data["metadata"]["file_metadata"]):
            if meta["file"] == file_path:
                file_chunks.append(embeddings_data["chunks"][i])
                file_embeddings.append(embeddings_data["embeddings"][i])

        if not file_embeddings:
            return {"error": f"File '{file_path}' not found in embeddings"}

        # Compute average embedding for the target file
        file_embedding = np.mean(file_embeddings, axis=0)

        # Convert all embeddings to numpy
        doc_embeddings = np.array(embeddings_data["embeddings"], dtype=np.float32)

        # Compute similarities
        model = self._load_model()
        similarities = model.similarity(file_embedding, doc_embeddings)[0]

        # Convert to numpy if it's a tensor
        if hasattr(similarities, 'cpu'):
            similarities = similarities.cpu().numpy()
        elif not isinstance(similarities, np.ndarray):
            similarities = np.array(similarities)

        # Group by file and compute average similarity per file
        file_scores = {}
        file_representative_chunks = {}

        for i, meta in enumerate(embeddings_data["metadata"]["file_metadata"]):
            file = meta["file"]
            score = float(similarities[i])

            if file not in file_scores:
                file_scores[file] = []
                file_representative_chunks[file] = {
                    "chunk": embeddings_data["chunks"][i],
                    "score": score
                }

            file_scores[file].append(score)

            # Keep track of the highest-scoring chunk per file
            if score > file_representative_chunks[file]["score"]:
                file_representative_chunks[file] = {
                    "chunk": embeddings_data["chunks"][i],
                    "score": score
                }

        # Compute average score per file
        file_avg_scores = {
            file: np.mean(scores)
            for file, scores in file_scores.items()
        }

        # Sort by average score and exclude the query file itself
        sorted_files = sorted(
            [(f, s) for f, s in file_avg_scores.items() if f != file_path],
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        results = []
        for file, score in sorted_files:
            results.append({
                "file": file,
                "score": float(score),
                "representative_chunk": file_representative_chunks[file]["chunk"]
            })

        return results


def build_embeddings_cli(docpack_path: str):
    """CLI function to build embeddings for a docpack."""
    docpack = Path(docpack_path)
    files_dir = docpack / "files"
    index_dir = docpack / "index"

    if not files_dir.exists():
        print(f"Error: {files_dir} does not exist")
        return

    index_dir.mkdir(exist_ok=True)

    searcher = EmbeddingSearcher(index_dir)
    searcher.build_embeddings(files_dir)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python embeddings.py <path-to-docpack>")
        sys.exit(1)

    build_embeddings_cli(sys.argv[1])
