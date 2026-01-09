from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional

from ..ingest.document_parser import ParsedDocument


class ClassifierProvider(ABC):
    """
    Interface for metadata classifiers that can be backed by rules or LLMs.
    """

    @abstractmethod
    def classify_doc_type(self, document: ParsedDocument) -> str:
        raise NotImplementedError

    @abstractmethod
    def classify_sections(self, document: ParsedDocument) -> Dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def classify_calc_type(self, document: ParsedDocument) -> Optional[str]:
        raise NotImplementedError
