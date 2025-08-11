# rag-python/app/rag/chroma_manager.py

import chromadb
import logging
from typing import List
from langchain.docstore.document import Document
from sentence_transformers import SentenceTransformer
import uuid

logger = logging.getLogger(__name__)

class ChromaManager:
    """ChromaDBとのインタラクションを管理するクラス (マルチテナント対応版)"""

    def __init__(self, persist_directory: str, embedding_model_name: str):
        logger.info(f"Initializing ChromaDB client at {persist_directory}")
        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.persist_directory = persist_directory

        self.embedding_model = SentenceTransformer(
            model_name_or_path=embedding_model_name,
            device='cpu',
            trust_remote_code=True
        )
        self.client = chromadb.PersistentClient(path=self.persist_directory)

    def _get_collection(self, collection_name: str):
        """指定された名前のコレクションを取得または作成する"""
        try:
            return self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Failed to get or create collection '{collection_name}': {e}", exc_info=True)
            raise RuntimeError(f"Could not access collection '{collection_name}'")

    def _embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.embedding_model.encode(
            texts,
            prompt_name="Retrieval-passage",
            normalize_embeddings=True
        )
        return embeddings.tolist()

    def _embed_query(self, text: str) -> List[float]:
        embedding = self.embedding_model.encode(
            text,
            prompt_name="Retrieval-query",
            normalize_embeddings=True
        )
        return embedding.tolist()

    def add_documents(self, documents: List[Document], collection_name: str):
        collection = self._get_collection(collection_name)
        if not documents:
            logger.warning("No documents provided to add.")
            return

        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        # IDをUUIDで生成し、一意性を保証
        ids = [str(uuid.uuid4()) for _ in texts]

        embeddings = self._embed_documents(texts)

        collection.add(embeddings=embeddings, metadatas=metadatas, documents=texts, ids=ids)
        logger.info(f"Added {len(documents)} documents to collection '{collection_name}'.")

    def search(self, query: str, collection_name: str, k: int = 3) -> List[Document]:
        collection = self._get_collection(collection_name)
        if not query:
            return []

        query_embedding = self._embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=['documents', 'metadatas', 'distances']
        )

        retrieved_docs: List[Document] = []
        if not results or not results.get('ids') or not results['ids'][0]:
            return []
            
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i] or {}
            if 'distances' in results and results['distances']:
                 metadata['distance'] = results['distances'][0][i]
            retrieved_docs.append(Document(
                page_content=results['documents'][0][i],
                metadata=metadata
            ))
        return retrieved_docs