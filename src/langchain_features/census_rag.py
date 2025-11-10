"""
RAG (Retrieval Augmented Generation) system for Census variables.
Helps LLM understand Census variable meanings and select better matches.
"""
import os
from pathlib import Path
from typing import List, Dict
import sys

import chromadb
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "single_agent"))

from resolver import get_census_variables_cached, clean_census_label

# PDF parsing (optional - graceful fallback if not installed)
try:
    from pdfminer.high_level import extract_text
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  pdfminer.six not installed - PDF documentation will be skipped")


class CensusVariableRAG:
    """
    Vector database for Census variables with semantic search.
    Helps LLM find relevant variables based on natural language queries.
    
    Now includes ACS documentation PDFs for enhanced context.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db", rebuild: bool = False, 
                 include_docs: bool = True, docs_dir: str = "./acs_docs"):
        self.persist_directory = persist_directory
        self.embeddings = OllamaEmbeddings(model="phi3:mini")
        self.vectorstore = None
        self.include_docs = include_docs
        self.docs_dir = Path(docs_dir)
        
        if rebuild or not Path(persist_directory).exists():
            self._build_vectorstore()
        else:
            self._load_vectorstore()
    
    def _build_vectorstore(self):
        """Build vector database from Census variables and ACS documentation."""
        print("Building Census variable vector database...")
        
        documents = []
        
        # 1. Get all Census variables
        print("Loading Census variable metadata...")
        df = get_census_variables_cached(year=2023)
        
        # Create documents from variables
        for _, row in df.iterrows():
            # Clean labels
            clean_label = clean_census_label(row['label'])
            clean_concept = clean_census_label(row.get('concept', ''))
            
            # Create rich document content
            content_parts = [
                f"Variable ID: {row['variable_id']}",
                f"Label: {clean_label}",
                f"Concept: {clean_concept}",
            ]
            
            # Add description if available
            if 'description' in row and row['description']:
                content_parts.append(f"Description: {row['description']}")
            
            # Add table info
            if 'table' in row and row['table']:
                content_parts.append(f"Table: {row['table']}")
            
            content = "\n".join(content_parts)
            
            # Metadata
            metadata = {
                "source": "census_api",
                "doc_type": "variable",
                "variable_id": row['variable_id'],
                "label": clean_label,
                "concept": clean_concept,
                "table": row.get('table', ''),
                "description": row.get('description', '')
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        print(f"✅ Loaded {len(documents)} Census variables")
        
        # 2. Load ACS documentation PDFs and Excel files
        if self.include_docs and self.docs_dir.exists():
            doc_count = self._load_acs_documentation(documents)
            print(f"✅ Loaded {doc_count} documentation chunks")
        elif self.include_docs:
            print(f"⚠️  Documentation directory not found: {self.docs_dir}")
        
        print(f"Creating vector embeddings for {len(documents)} total documents...")
        print(f"⏳ This will take ~15-30 minutes on CPU. Please be patient...")
        print(f"💡 Tip: Open another terminal and run 'ollama ps' to see progress")
        
        # Create vectorstore (this is where the long wait happens)
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        print(f"✅ Vector database created with {len(documents)} documents")
    
    def _load_acs_documentation(self, documents: List[Document]) -> int:
        """Load ACS documentation PDFs and Excel files into documents list."""
        initial_count = len(documents)
        
        # Load PDF files
        if PDF_AVAILABLE:
            for pdf_file in self.docs_dir.glob("*.pdf"):
                print(f"  📄 Processing: {pdf_file.name}")
                try:
                    chunks = self._parse_pdf(pdf_file)
                    documents.extend(chunks)
                except Exception as e:
                    print(f"    ⚠️  Error parsing {pdf_file.name}: {e}")
        else:
            print("  ⚠️  Skipping PDFs (pdfminer.six not installed)")
        
        # Load Excel files
        for excel_file in self.docs_dir.glob("*.xls*"):
            print(f"  📊 Processing: {excel_file.name}")
            try:
                chunks = self._parse_excel(excel_file)
                documents.extend(chunks)
            except Exception as e:
                print(f"    ⚠️  Error parsing {excel_file.name}: {e}")
        
        return len(documents) - initial_count
    
    def _parse_pdf(self, pdf_path: Path, chunk_size: int = 1200, overlap: int = 200) -> List[Document]:
        """Parse PDF into chunks for embedding."""
        if not PDF_AVAILABLE:
            return []
        
        # Extract text
        raw_text = extract_text(str(pdf_path))
        
        # Normalize whitespace
        normalized = " ".join(raw_text.split())
        
        # Chunk the text
        chunks = []
        start = 0
        length = len(normalized)
        chunk_num = 0
        
        while start < length:
            end = min(length, start + chunk_size)
            chunk_text = normalized[start:end]
            
            # Create document
            doc = Document(
                page_content=chunk_text,
                metadata={
                    "source": pdf_path.name,
                    "doc_type": "pdf",
                    "chunk": chunk_num,
                    "file_type": "documentation"
                }
            )
            chunks.append(doc)
            
            chunk_num += 1
            if end >= length:
                break
            start = max(0, end - overlap)
        
        return chunks
    
    def _parse_excel(self, excel_path: Path) -> List[Document]:
        """Parse Excel file (DataProductList) into documents."""
        try:
            df = pd.read_excel(excel_path)
        except Exception as e:
            print(f"    Error reading Excel: {e}")
            return []
        
        documents = []
        
        for _, row in df.iterrows():
            # Extract relevant columns (adjust based on actual Excel structure)
            table_id = str(row.get("Table ID") or row.get("TableID") or "").strip()
            subject = str(row.get("Subject Area") or row.get("Subject", "")).strip()
            title = str(row.get("Table Title") or row.get("Title", "")).strip()
            universe = str(row.get("Universe", "")).strip()
            
            # Build description
            parts = []
            if subject:
                parts.append(f"Subject: {subject}")
            if universe:
                parts.append(f"Universe: {universe}")
            if title:
                parts.append(f"Title: {title}")
            
            if not parts:
                continue
            
            content = "\n".join(parts)
            
            # Create document
            doc = Document(
                page_content=content,
                metadata={
                    "source": excel_path.name,
                    "doc_type": "excel",
                    "table_id": table_id or None,
                    "subject": subject,
                    "title": title,
                    "file_type": "documentation"
                }
            )
            documents.append(doc)
        
        return documents
    
    def _load_vectorstore(self):
        """Load existing vector database."""
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
    
    def search(self, query: str, top_k: int = 5, filter_type: str = None) -> List[Dict]:
        """
        Semantic search for Census variables and documentation.
        
        Args:
            query: Natural language query (e.g., "median household income")
            top_k: Number of results to return
            filter_type: Optional filter - "variable", "pdf", "excel", or None for all
            
        Returns:
            List of dictionaries with results and metadata
        """
        if not self.vectorstore:
            self._load_vectorstore()
        
        # Build filter if specified
        search_kwargs = {"k": top_k}
        if filter_type:
            search_kwargs["filter"] = {"doc_type": filter_type}
        
        # Perform similarity search with scores
        results = self.vectorstore.similarity_search_with_score(query, k=top_k)
        
        matches = []
        for doc, score in results:
            doc_type = doc.metadata.get("doc_type", "unknown")
            
            # Build result based on document type
            result = {
                "doc_type": doc_type,
                "source": doc.metadata.get("source", "unknown"),
                "score": 1.0 - score,  # Convert distance to similarity (0-1)
                "relevance": "high" if (1.0 - score) > 0.8 else "medium" if (1.0 - score) > 0.6 else "low",
                "content": doc.page_content[:500]  # Preview
            }
            
            # Add type-specific metadata
            if doc_type == "variable":
                result.update({
                    "variable_id": doc.metadata.get("variable_id"),
                    "label": doc.metadata.get("label"),
                    "concept": doc.metadata.get("concept"),
                    "description": doc.metadata.get("description"),
                })
            elif doc_type == "excel":
                result.update({
                    "table_id": doc.metadata.get("table_id"),
                    "subject": doc.metadata.get("subject"),
                    "title": doc.metadata.get("title"),
                })
            elif doc_type == "pdf":
                result.update({
                    "chunk": doc.metadata.get("chunk"),
                })
            
            matches.append(result)
        
        return matches
    
    def search_variables_only(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Semantic search for Census variables only (backward compatible).
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            
        Returns:
            List of variable matches with variable_id, label, score
        """
        all_results = self.search(query, top_k=top_k * 2)  # Get more to filter
        
        # Filter to only variables
        variable_results = [r for r in all_results if r.get("doc_type") == "variable"]
        
        # Return top_k variables
        return variable_results[:top_k]
    
    def get_context_for_query(self, query: str, top_k: int = 3) -> str:
        """
        Get relevant Census variable context for LLM prompt augmentation.
        
        Args:
            query: Natural language query
            top_k: Number of relevant variables to include
            
        Returns:
            Formatted context string for LLM
        """
        matches = self.search(query, top_k=top_k)
        
        if not matches:
            return "No relevant Census variables found."
        
        context_lines = ["Relevant Census Variables:"]
        for i, match in enumerate(matches, 1):
            context_lines.append(f"\n{i}. {match['variable_id']}")
            context_lines.append(f"   Label: {match['label']}")
            if match.get('description'):
                context_lines.append(f"   {match['description']}")
            context_lines.append(f"   Relevance: {match['relevance']} ({match['score']:.2f})")
        
        return "\n".join(context_lines)


if __name__ == "__main__":
    # Test the RAG system
    print("Testing Census Variable RAG System with Documentation\n")
    
    rag = CensusVariableRAG(rebuild=True, include_docs=True)
    
    # Test queries
    test_queries = [
        ("median household income", "Should find B19013 variable + income documentation"),
        ("poverty rate", "Should find poverty variables + definitions"),
        ("population density", "Should find population variables + density info"),
        ("what does universe mean in ACS", "Should find documentation explaining 'universe'")
    ]
    
    for query, expected in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print(f"Expected: {expected}")
        print('='*70)
        
        # Search all document types
        matches = rag.search(query, top_k=5)
        for i, match in enumerate(matches, 1):
            doc_type = match['doc_type']
            score = match['score']
            
            if doc_type == "variable":
                print(f"\n{i}. [VARIABLE] {match['variable_id']} (score: {score:.3f})")
                print(f"   {match['label']}")
            elif doc_type == "pdf":
                print(f"\n{i}. [PDF] {match['source']} chunk #{match.get('chunk', 0)} (score: {score:.3f})")
                print(f"   {match['content'][:150]}...")
            elif doc_type == "excel":
                print(f"\n{i}. [TABLE] {match.get('table_id', 'N/A')} (score: {score:.3f})")
                print(f"   {match.get('title', 'No title')}")
    
    print("\n" + "="*70)
    print("Testing variable-only search (backward compatible)")
    print("="*70)
    variable_matches = rag.search_variables_only("median household income", top_k=3)
    for i, match in enumerate(variable_matches, 1):
        print(f"{i}. {match['variable_id']} - {match['label']} (score: {match['score']:.3f})")
