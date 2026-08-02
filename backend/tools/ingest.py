"""Ingest markdown docs from knowledge_base (EN) and knowledge_base_uk (UK) into Chroma."""

import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_community.vectorstores import Chroma
from embeddings import get_embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.rag_core import validate_api_key

load_dotenv()
load_dotenv(Path("tools") / ".env")

KNOWLEDGE_BASE_DIRS = {
    "en": Path("knowledge_base"),
    "uk": Path("knowledge_base_uk"),
}
CHROMA_DIR = "chroma_db"


def main() -> None:
    available = {
        lang: path for lang, path in KNOWLEDGE_BASE_DIRS.items()
        if path.exists() and any(path.rglob("*.md"))
    }
    if not available:
        print(
            "Error: no knowledge base folder ('knowledge_base' or 'knowledge_base_uk') "
            "contains .md files. Add markdown documents before running ingest."
        )
        sys.exit(1)

    # Ensure OpenRouter credentials are valid before doing any (slow) ingestion work.
    key_ok, key_msg = validate_api_key()
    if not key_ok:
        print(f"Error: {key_msg}")
        sys.exit(1)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    all_chunks = []
    for lang, kb_dir in available.items():
        loader = DirectoryLoader(
            str(kb_dir),
            glob="**/*.md",
            loader_cls=UnstructuredMarkdownLoader,
            show_progress=True,
        )
        documents = loader.load()
        print(f"[{lang}] Loaded {len(documents)} document(s) from '{kb_dir}'.")

        chunks = text_splitter.split_documents(documents)
        for chunk in chunks:
            chunk.metadata["lang"] = lang
        all_chunks.extend(chunks)
        print(f"[{lang}] Split into {len(chunks)} chunk(s).")

    print(f"Total chunks to index: {len(all_chunks)}")

    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )
    vectorstore.persist()

    print(f"Vector store saved to '{CHROMA_DIR}'.")


if __name__ == "__main__":
    main()
