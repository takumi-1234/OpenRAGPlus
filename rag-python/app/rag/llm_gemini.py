# rag-python/app/rag/llm_gemini.py

import google.generativeai as genai
import logging
from typing import List, Optional
from langchain.docstore.document import Document

logger = logging.getLogger(__name__)

class GeminiChat:
    def __init__(self, api_key: str, model_name: str):
        if not api_key:
            raise ValueError("Gemini API Key not found.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"GeminiChat initialized with model: {model_name}")

    def _create_prompt_string(self, query: str, context_docs: Optional[List[Document]], system_prompt: str) -> str:
        context_text = ""
        if context_docs:
            doc_texts = []
            for i, doc in enumerate(context_docs):
                source = doc.metadata.get('source', '不明')
                doc_texts.append(f"--- 資料 {i+1} (出典: {source}) ---\n{doc.page_content}")
            context_text = "\n\n".join(doc_texts)

        prompt = f"""{system_prompt}

【参考資料】
{context_text if context_text else "参考資料はありません。"}

【質問】
{query}

【回答】
"""
        return prompt

    def generate_response(
        self,
        query: str,
        context_docs: Optional[List[Document]],
        system_prompt_override: Optional[str] = None
    ) -> str:
        if not query.strip():
            raise ValueError("質問内容を入力してください。")

        # デフォルトのシステムプロンプト
        default_system_prompt = "あなたは大学の講義に関する質問に答えるアシスタントです。提供された参考資料に基づいて、正確かつ簡潔に回答してください。資料に情報がない場合は、その旨を伝えてください。"
        
        final_system_prompt = system_prompt_override or default_system_prompt

        prompt = self._create_prompt_string(query, context_docs, final_system_prompt)
        
        try:
            response = self.model.generate_content(prompt)
            # レスポンスがブロックされた場合の簡易的なハンドリング
            if not response.parts and response.prompt_feedback.block_reason:
                reason = response.prompt_feedback.block_reason.name
                raise RuntimeError(f"回答生成がブロックされました。理由: {reason}")

            return response.text.strip()
        except Exception as e:
            logger.error(f"Error during Gemini API call: {e}", exc_info=True)
            raise e