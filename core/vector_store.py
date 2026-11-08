import os
from langchain_chroma import  Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHROMA_DIR="vector_db"
COLLECTION_NAME="meeting-transcript"
EMBEDDING_MODEL="all-MiniLM-L6-v2"

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device":'cpu'}
    )

def build_vector_store(transcript:str)->Chroma: #as such no use here bt will come in use in langgraph
    print("BUILDIG VECTOR STORE")

    splitter=RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks=splitter.split_text(transcript)

    docs=[
        Document(page_content=chunk,meta_data={'index':i})
        for i,chunk in enumerate(chunks)
    ]

    embeddings=get_embeddings()
    vector_strore=Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR
    )
    return vector_strore

def load_vector_store()->Chroma:
    embedding=get_embeddings()
    vector_store=Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding,
        persist_directory=CHROMA_DIR
    )
    return vector_store

def get_retriever(vector_store:Chroma,k:int=4):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k":k}
    )