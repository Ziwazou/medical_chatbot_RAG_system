import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEndpointEmbeddings


def load_documents(data_path: str):
    loader = DirectoryLoader(
        data_path,
        glob="*.pdf",
        loader_cls=PyPDFLoader
    )
    return loader.load()


def filter_metadata(documents):
    filtered_docs = []
    for doc in documents:
        filtered_docs.append(
            Document(
                metadata={'source': doc.metadata.get('source', 'Unknown')},
                page_content=doc.page_content
            )
        )
    return filtered_docs


def text_splitter(documents, chunk_size: int = 500, chunk_overlap: int = 20):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_documents(documents)


def get_embeddings():
    api_key = os.getenv('HUGGING_FACE_KEY')
    if not api_key:
        raise ValueError("HUGGING_FACE_KEY not found in environment variables.")
    
    return HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2",
        huggingfacehub_api_token=api_key
    )
