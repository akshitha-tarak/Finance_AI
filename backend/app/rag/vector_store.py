import os
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from ..config import settings

class DocumentChunk:
    def __init__(self, text: str, source: str, chunk_id: int):
        self.text = text.strip()
        self.source = source
        self.chunk_id = chunk_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "chunk_id": self.chunk_id
        }

class FinancialVectorStore:
    """
    RAG Document Ingestion and Vector Store Engine.
    Loads financial education documents (TXT and PDF), chunks them,
    and performs cosine-similarity vector retrieval for user queries.
    """
    def __init__(self, docs_dir: Path = None):
        self.docs_dir = docs_dir or settings.KNOWLEDGE_DOCS_DIR
        self.chunks: List[DocumentChunk] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.chunk_vectors: List[Dict[int, float]] = []
        self.is_indexed = False
        self.build_index()

    def _extract_text_from_file(self, file_path: Path) -> str:
        """Extracts text from text files or PDFs."""
        if file_path.suffix.lower() == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif file_path.suffix.lower() == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(file_path))
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text
            except Exception as e:
                print(f"Warning: Failed to parse PDF {file_path}: {e}")
                return ""
        return ""

    def _split_into_chunks(self, text: str, source: str, chunk_size: int = 400, overlap: int = 50) -> List[DocumentChunk]:
        """Splits document text into overlapping semantic passages."""
        # Split on paragraph or double-newline breaks first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunks.append(DocumentChunk(current_chunk, source, chunk_idx))
                    chunk_idx += 1
                # If paragraph itself is larger than chunk_size, split by sentences
                if len(para) > chunk_size:
                    sentences = re.split(r'(?<=[.?!])\s+', para)
                    sub_chunk = ""
                    for s in sentences:
                        if len(sub_chunk) + len(s) <= chunk_size:
                            sub_chunk += (" " if sub_chunk else "") + s
                        else:
                            if sub_chunk:
                                chunks.append(DocumentChunk(sub_chunk, source, chunk_idx))
                                chunk_idx += 1
                            sub_chunk = s
                    if sub_chunk:
                        current_chunk = sub_chunk
                    else:
                        current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(DocumentChunk(current_chunk, source, chunk_idx))

        return chunks

    def _tokenize(self, text: str) -> List[str]:
        """Simple lowercase word tokenizer."""
        return re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', text.lower())

    def build_index(self):
        """Loads all knowledge files, chunks them, and builds TF-IDF vector embeddings."""
        if not self.docs_dir.exists():
            os.makedirs(self.docs_dir, exist_ok=True)
            return

        self.chunks = []
        for file_path in self.docs_dir.glob("*.*"):
            if file_path.suffix.lower() in [".txt", ".pdf"]:
                content = self._extract_text_from_file(file_path)
                if content:
                    file_chunks = self._split_into_chunks(content, file_path.name)
                    self.chunks.extend(file_chunks)

        if not self.chunks:
            return

        # Build TF-IDF Vocabulary and Embeddings
        doc_count = len(self.chunks)
        df_counts: Dict[str, int] = {}
        tokenized_chunks = []

        for chunk in self.chunks:
            tokens = self._tokenize(chunk.text)
            tokenized_chunks.append(tokens)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df_counts[token] = df_counts.get(token, 0) + 1

        # Create vocabulary
        self.vocabulary = {token: idx for idx, token in enumerate(df_counts.keys())}
        # Compute IDF
        self.idf = {
            token: math.log((doc_count + 1) / (count + 1)) + 1.0
            for token, count in df_counts.items()
        }

        # Vectorize each chunk
        self.chunk_vectors = []
        for tokens in tokenized_chunks:
            tf: Dict[int, float] = {}
            for t in tokens:
                if t in self.vocabulary:
                    v_idx = self.vocabulary[t]
                    tf[v_idx] = tf.get(v_idx, 0.0) + 1.0

            # Weight by IDF and calculate Euclidean norm
            norm_sq = 0.0
            weighted_vec = {}
            for v_idx, count in tf.items():
                token = list(self.vocabulary.keys())[v_idx]
                w = count * self.idf.get(token, 1.0)
                weighted_vec[v_idx] = w
                norm_sq += w * w

            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            # Normalize vector
            normed_vec = {v_idx: w / norm for v_idx, w in weighted_vec.items()}
            self.chunk_vectors.append(normed_vec)

        self.is_indexed = True

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[DocumentChunk, float]]:
        """
        Embeds the user query and retrieves the top-k most relevant document chunks
        using cosine similarity.
        """
        if not self.is_indexed or not self.chunks:
            self.build_index()
            if not self.chunks:
                return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Vectorize query
        q_tf: Dict[int, float] = {}
        for t in query_tokens:
            if t in self.vocabulary:
                v_idx = self.vocabulary[t]
                q_tf[v_idx] = q_tf.get(v_idx, 0.0) + 1.0

        if not q_tf:
            # Query has words outside vocabulary
            return []

        q_norm_sq = 0.0
        q_vec = {}
        for v_idx, count in q_tf.items():
            token = list(self.vocabulary.keys())[v_idx]
            w = count * self.idf.get(token, 1.0)
            q_vec[v_idx] = w
            q_norm_sq += w * w

        q_norm = math.sqrt(q_norm_sq) if q_norm_sq > 0 else 1.0
        q_normed = {v_idx: w / q_norm for v_idx, w in q_vec.items()}

        # Calculate cosine similarity with all chunks
        scores = []
        for idx, doc_vec in enumerate(self.chunk_vectors):
            dot_product = 0.0
            for v_idx, weight in q_normed.items():
                if v_idx in doc_vec:
                    dot_product += weight * doc_vec[v_idx]
            if dot_product > 0.01:
                scores.append((self.chunks[idx], dot_product))

        # Sort descending by similarity
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

# Singleton instance
vector_store = FinancialVectorStore()
