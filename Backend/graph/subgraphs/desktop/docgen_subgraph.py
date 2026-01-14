"""Compatibility shim for document generation subgraph."""

from graph.subgraphs.document_generation_subgraph import (
    build_doc_generation_subgraph,
    call_doc_generation_subgraph,
)

__all__ = ["build_doc_generation_subgraph", "call_doc_generation_subgraph"]
