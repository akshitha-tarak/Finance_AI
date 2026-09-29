import requests
from typing import Dict, Any, List
from .vector_store import vector_store
from ..config import settings

class RAGEngine:
    """
    RAG (Retrieval-Augmented Generation) Engine.
    Combines vector retrieval over financial knowledge documents
    with LLM synthesis (Groq / Gemini / Local Extractive fallback).
    """
    def __init__(self):
        pass

    def answer_query(self, query: str) -> Dict[str, Any]:
        """
        Retrieves context chunks and generates an educational financial answer.
        """
        # Step 1: Retrieve relevant context chunks from vector store
        matches = vector_store.retrieve(query, top_k=3)
        
        if not matches:
            return {
                "reply": "I couldn't find a direct match in the current financial knowledge guides. However, you can ask about the 50/30/20 rule, emergency funds, debt snowball vs avalanche, index funds, 401(k), or credit scores!",
                "sources": [],
                "engine": "fallback"
            }

        context_texts = [f"[{chunk.source}]: {chunk.text}" for chunk, score in matches]
        combined_context = "\n\n".join(context_texts)
        sources = list(set([chunk.source for chunk, _ in matches]))

        # Step 2: Check if free Groq API key is configured
        if settings.GROQ_API_KEY:
            try:
                llm_response = self._call_groq_llm(query, combined_context)
                if llm_response:
                    return {
                        "reply": llm_response,
                        "sources": sources,
                        "engine": "groq-llama3"
                    }
            except Exception as e:
                print(f"Groq API call failed, falling back to local synthesizer: {e}")

        # Step 3: Check if Google Gemini API key is configured
        if settings.GEMINI_API_KEY:
            try:
                llm_response = self._call_gemini_llm(query, combined_context)
                if llm_response:
                    return {
                        "reply": llm_response,
                        "sources": sources,
                        "engine": "gemini-1.5-flash"
                    }
            except Exception as e:
                print(f"Gemini API call failed, falling back to local synthesizer: {e}")

        # Step 4: Intelligent Local RAG Synthesis Fallback (Zero external API dependencies)
        synthesized_reply = self._synthesize_local_response(query, matches)
        return {
            "reply": synthesized_reply,
            "sources": sources,
            "engine": "local-rag"
        }

    def _call_groq_llm(self, query: str, context: str) -> str:
        """Calls Groq's high-speed free Llama 3 API."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        system_prompt = (
            "You are an encouraging, certified Senior AI Financial Insights Assistant. "
            "Your job is to answer user personal finance questions with clear, actionable advice "
            "based strictly on the provided context passages. Use bullet points and markdown formatting."
        )
        user_prompt = f"Context:\n{context}\n\nUser Question: {query}\n\nAnswer:"
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 512
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"Groq error {resp.status_code}: {resp.text}")
            return None

    def _call_gemini_llm(self, query: str, context: str) -> str:
        """Calls Google Gemini API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        prompt = (
            f"You are a friendly Financial Assistant. Answer the question based on this context:\n\n"
            f"{context}\n\nQuestion: {query}\nAnswer with actionable advice:"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return None

    def _synthesize_local_response(self, query: str, matches: list) -> str:
        """
        Constructs a clean, human-readable answer directly from retrieved chunks.
        Used when no external LLM key is configured.
        """
        top_chunk, score = matches[0]
        sources_str = ", ".join(list(set([m[0].source for m in matches])))
        
        reply_lines = [
            f"### 💡 Financial Insights (Retrieved from `{sources_str}`)",
            "",
            top_chunk.text,
            ""
        ]

        if len(matches) > 1:
            reply_lines.append("#### Related Key Points:")
            for chunk, _ in matches[1:3]:
                # Extract first sentence or bullet
                snippet = chunk.text.split("\n")[0]
                reply_lines.append(f"- {snippet}")
            reply_lines.append("")

        reply_lines.append(
            "> ℹ️ *Tip: Add your free Groq or Gemini API key in `backend/.env` to unlock dynamic Llama-3 synthesis!*"
        )
        return "\n".join(reply_lines)

rag_engine = RAGEngine()
