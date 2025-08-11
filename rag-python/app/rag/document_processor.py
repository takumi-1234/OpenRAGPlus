# rag-python/app/rag/document_processor.py

import os
import logging
from typing import List
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
}

TEXT_SPLITTER_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
}

def load_document(file_path: str) -> List[Document]:
    file_ext = os.path.splitext(file_path)[1].lower()
    loader_class = SUPPORTED_EXTENSIONS.get(file_ext)
    if not loader_class:
        raise ValueError(f"Unsupported file type: {file_ext}")
    
    loader = loader_class(file_path)
    return loader.load()

def split_documents(documents: List[Document]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(**TEXT_SPLITTER_CONFIG)
    return text_splitter.split_documents(documents)

def process_documents(file_path: str, unique_filename: str) -> List[Document]:
    loaded_docs = load_document(file_path)
    if not loaded_docs:
        return []

    split_docs = split_documents(loaded_docs)
    for doc in split_docs:
        if not isinstance(doc.metadata, dict):
            doc.metadata = {}
        doc.metadata["source"] = unique_filename
    
    return split_docs