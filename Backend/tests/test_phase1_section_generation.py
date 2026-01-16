import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
backend_dir = ROOT / "Backend"
if backend_dir.exists() and str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from models.rag_state import RAGState  # noqa: E402
import Backend.nodes.DesktopAgent.doc_generation.section_generator as sg  # noqa: E402
import Backend.nodes.DesktopAgent.doc_generation.report_generator as rg  # noqa: E402
import importlib.util

# Load pipeline and resolver modules from paths (space in folder name)
LA_ROOT = ROOT / "Local Agent" / "info_retrieval" / "src"
if str(LA_ROOT) not in sys.path:
    sys.path.append(str(LA_ROOT))
pipeline_path = LA_ROOT / "ingest" / "pipeline.py"
resolver_path = LA_ROOT / "templates" / "template_resolver.py"

# Stub minimal modules to satisfy pipeline imports (avoid heavy deps)
import types

stubs = {
    "ingest": types.ModuleType("ingest"),
    "embeddings.embedding_service": types.ModuleType("embeddings.embedding_service"),
    "storage.vector_store": types.ModuleType("storage.vector_store"),
    "storage.metadata_db": types.ModuleType("storage.metadata_db"),
    "ingest.chunking": types.ModuleType("ingest.chunking"),
    "ingest.document_parser": types.ModuleType("ingest.document_parser"),
    "ingest.metadata_extractor": types.ModuleType("ingest.metadata_extractor"),
    "ingest.style_filter": types.ModuleType("ingest.style_filter"),
}

class _StubEmbeddingService:
    def __init__(self, *args, **kwargs):
        pass

    def embed_batch(self, texts):
        return [[0.0] for _ in texts]


class _StubVectorStore:
    pass


class _StubMetadataDB:
    def insert_document(self, record): ...

    def insert_chunk_metadata(self, record): ...

    def get_style_frequency(self, normalized_text, section_type=None):
        return 0


def _stub_parse(path, company_id=None):
    return SimpleNamespace(sections=[])


def _stub_chunk(parsed):
    return []


class _StubMetadataExtractor:
    def extract_metadata(self, parsed, company_id=None):
        return {
            "artifact_id": "a1",
            "version_id": "v1",
            "doc_type": "design_report",
            "section_types": {"Intro": "intro", "Methodology": "methodology"},
            "tags": [],
        }


class _StubStyleFilter:
    def _normalize(self, text): return text

    def compute_quality_score(self, text): return 0.0

    def is_style_exemplar(self, text, style_meta, quality_score): return False


stubs["embeddings.embedding_service"].EmbeddingService = _StubEmbeddingService
class _StubChunk:
    def __init__(self, id=None, text=None, embedding=None, metadata=None):
        self.id = id
        self.text = text
        self.embedding = embedding
        self.metadata = metadata

stubs["storage.vector_store"].Chunk = _StubChunk
stubs["storage.vector_store"].VectorStore = _StubVectorStore
stubs["storage.metadata_db"].MetadataDB = _StubMetadataDB
stubs["ingest.chunking"].chunk_pdf_pages = _stub_chunk
stubs["ingest.chunking"].smart_chunk = _stub_chunk
stubs["ingest.document_parser"].parse_docx = _stub_parse
stubs["ingest.document_parser"].parse_pdf = _stub_parse
stubs["ingest.metadata_extractor"].MetadataExtractor = _StubMetadataExtractor
stubs["ingest.style_filter"].StyleExemplarFilter = _StubStyleFilter

sys.modules.update(stubs)
# Ensure ingest is recognized as a package for relative imports
sys.modules["ingest"].__path__ = [str(LA_ROOT / "ingest")]

spec_pipe = importlib.util.spec_from_file_location("ingest.pipeline", pipeline_path)
pipeline = importlib.util.module_from_spec(spec_pipe)
spec_pipe.loader.exec_module(pipeline)  # type: ignore
IngestionPipeline = pipeline.IngestionPipeline

spec_res = importlib.util.spec_from_file_location("template_resolver_mod", resolver_path)
template_resolver = importlib.util.module_from_spec(spec_res)
spec_res.loader.exec_module(template_resolver)  # type: ignore


class StubGen:
    def __init__(self):
        self.calls = []

    def draft_section(self, company_id, user_request, overrides=None):
        overrides = overrides or {}
        self.calls.append(overrides)
        return {
            "draft_text": f"draft for {overrides.get('section_type')}",
            "citations": [{"id": "c1"}],
            "warnings": [],
            "metadata": {
                "template_id": overrides.get("template_id"),
                "section_id": overrides.get("section_id"),
            },
        }


def _make_state(section_queue=None, template_sections=None):
    return RAGState(
        user_query="Generate methodology section",
        doc_type="design_report",
        section_type=None,
        template_id="tmpl-123",
        template_sections=template_sections,
        section_queue=section_queue,
        approved_sections=[],
    )


def test_report_generates_single_section_and_status(monkeypatch):
    # Prepare template with three sections, none approved
    template_sections = [
        {"section_id": "s1", "section_type": "executive_summary", "position_order": 1, "status": "pending"},
        {"section_id": "s2", "section_type": "methodology", "position_order": 2, "status": "pending"},
        {"section_id": "s3", "section_type": "results", "position_order": 3, "status": "pending"},
    ]
    state = _make_state(section_queue=[], template_sections=template_sections)

    stub = StubGen()
    monkeypatch.setattr(rg, "_load_services", lambda: {"generator": stub})

    res = rg.node_doc_generate_report(state)
    dgr = res["doc_generation_result"]

    # Generator called exactly once with section_id/section_type of the first pending section
    assert len(stub.calls) == 1
    call = stub.calls[0]
    assert call.get("section_id") == "s1"
    assert call.get("section_type") == "executive_summary"

    # Only one section draft is produced
    assert dgr.get("draft_text") == "draft for executive_summary"
    assert "sections" not in dgr or not dgr.get("sections")

    # Status transitions: first = draft, others = locked
    statuses = {s["section_type"]: s["status"] for s in dgr.get("section_status", [])}
    assert statuses["executive_summary"] == "draft"
    assert statuses["methodology"] == "locked"
    assert statuses["results"] == "locked"

    # Template context propagated
    assert dgr.get("template_sections")
    assert dgr.get("template_id") == "tmpl-123"
    assert res.get("current_section_id") == "s1"


def test_section_generator_carries_template_and_status(monkeypatch):
    section_queue = [
        {"section_id": "s1", "section_type": "intro", "position_order": 1, "status": "approved"},
        {"section_id": "s2", "section_type": "methodology", "position_order": 2, "status": "pending"},
        {"section_id": "s3", "section_type": "results", "position_order": 3, "status": "pending"},
    ]
    template_sections = section_queue
    state = _make_state(section_queue=section_queue, template_sections=template_sections)

    stub = StubGen()
    monkeypatch.setattr(sg, "_load_services", lambda: {"generator": stub})

    res = sg.node_doc_generate_section(state)
    dgr = res["doc_generation_result"]

    # Generator called once for the next pending section (s2)
    assert len(stub.calls) == 1
    call = stub.calls[0]
    assert call.get("section_id") == "s2"
    assert call.get("section_type") == "methodology"
    assert call.get("template_id") == "tmpl-123"

    # Status: approved stays approved, current draft set to draft, future locked
    statuses = {s["section_type"]: s["status"] for s in dgr.get("section_status", [])}
    assert statuses["intro"] == "approved"
    assert statuses["methodology"] == "draft"
    assert statuses["results"] == "locked"

    # Template context propagated into result metadata
    assert dgr.get("metadata", {}).get("template_id") == "tmpl-123"
    assert dgr.get("metadata", {}).get("section_id") == "s2"
    assert res.get("current_section_id") == "s2"


def test_ingest_resolves_template_and_section_ids(monkeypatch):
    # Stub external dependencies
    class DummyEmbedding:
        def embed_batch(self, texts):
            return [[0.0] for _ in texts]

    class DummyVector:
        def upsert(self, records):
            return None

    inserted = {"docs": [], "chunks": []}

    class DummyMetadataDB:
        def insert_document(self, record):
            inserted["docs"].append(record)

        def insert_chunk_metadata(self, record):
            inserted["chunks"].append(record)

        def get_style_frequency(self, normalized_text, section_type=None):
            return 0

    # Stub file path behavior
    class DummyStat:
        st_size = 0

    class DummyPath:
        def __init__(self, p):
            self._p = p
            self.suffix = ".docx"
            self.name = "dummy.docx"

        def exists(self):
            return True

        def stat(self):
            return DummyStat()

        def resolve(self):
            return self

        def __truediv__(self, other):
            return DummyPath(f"{self._p}/{other}")

        def __str__(self):
            return self._p

    monkeypatch.setattr(pipeline, "Path", DummyPath)

    # Stub parser/chunkers
    parsed = SimpleNamespace(
        sections=[SimpleNamespace(title="Intro", content="content intro"), SimpleNamespace(title="Methodology", content="content m")],
    )
    monkeypatch.setattr(pipeline, "parse_docx", lambda path, company_id=None: parsed)
    monkeypatch.setattr(pipeline, "parse_pdf", lambda path, company_id=None: parsed)
    monkeypatch.setattr(pipeline, "smart_chunk", lambda parsed: [
        {"text": "chunk intro", "section_title": "Intro"},
        {"text": "chunk m", "section_title": "Methodology"},
    ])
    monkeypatch.setattr(pipeline, "chunk_pdf_pages", lambda parsed: [])

    # Stub template resolver to return ids
    monkeypatch.setattr(template_resolver, "resolve_template_sections", lambda company_id, doc_type: {
        "template_id": "tmpl-abc",
        "section_id_map": {"intro": "sec-intro", "methodology": "sec-meth"},
    })
    # Ensure pipeline's dynamic import hits the stubbed module
    import types as _types
    tmpl_module = _types.ModuleType("templates.template_resolver")
    tmpl_module.resolve_template_sections = lambda company_id, doc_type: {
        "template_id": "tmpl-abc",
        "section_id_map": {"intro": "sec-intro", "methodology": "sec-meth"},
    }
    monkeypatch.setitem(sys.modules, "templates.template_resolver", tmpl_module)

    ingestion = IngestionPipeline(
        embedding_service=DummyEmbedding(),
        vector_store=DummyVector(),
        metadata_db=DummyMetadataDB(),
        company_id="demo_company",
    )

    ingestion.ingest("dummy.docx", auto_resolve_template=True)

    # Template_id stamped on doc and chunks; section_id applied via map
    assert inserted["docs"][0]["company_id"] == "demo_company"
    for chunk in inserted["chunks"]:
        assert chunk["template_id"] == "tmpl-abc"
    sec_ids = {c["section_id"] for c in inserted["chunks"]}
    assert "sec-intro" in sec_ids and "sec-meth" in sec_ids


def test_approval_and_rejection_flow(monkeypatch):
    # Start with s1 pending, s2 locked
    section_queue = [
        {"section_id": "s1", "section_type": "intro", "position_order": 1, "status": "pending"},
        {"section_id": "s2", "section_type": "methodology", "position_order": 2, "status": "locked"},
    ]
    template_sections = section_queue
    state = _make_state(section_queue=section_queue, template_sections=template_sections)

    stub = StubGen()
    monkeypatch.setattr(sg, "_load_services", lambda: {"generator": stub})

    # First run: should draft s1 only
    res1 = sg.node_doc_generate_section(state)
    assert len(stub.calls) == 1
    assert stub.calls[0].get("section_id") == "s1"

    from Backend.nodes.DesktopAgent.doc_generation import approval

    # Approve s1, unlock s2
    queue_after_approve = approval.approve_section(res1["section_queue"], "s1")
    state.section_queue = queue_after_approve
    state.template_sections = queue_after_approve

    # Next run: should draft s2, not touch s1
    res2 = sg.node_doc_generate_section(state)
    assert len(stub.calls) == 2
    assert stub.calls[1].get("section_id") == "s2"
    statuses = {s["section_type"]: s["status"] for s in res2["doc_generation_result"]["section_status"]}
    assert statuses["intro"] == "approved"
    assert statuses["methodology"] == "draft"

    # Reject s2 and ensure regeneration hits only s2
    queue_after_reject = approval.reject_section(res2["section_queue"], "s2", feedback="fix it")
    state.section_queue = queue_after_reject
    state.template_sections = queue_after_reject
    res3 = sg.node_doc_generate_section(state)
    assert len(stub.calls) == 3
    assert stub.calls[2].get("section_id") == "s2"
