from concurrent.futures import ThreadPoolExecutor
import sys
import threading
import types

import numpy as np
import pytest

from retrieval import (
    EmbeddingUnavailable, HybridRetriever, MODEL_ID, MODEL_REVISION,
    QUERY_INSTRUCTION, tokenize,
)


class RecordingEncoder:
    """Deterministic test vectors; BM25 and fusion remain real in these tests."""

    def __init__(self, vectors=None, query_vector=(1.0, 0.0)):
        self.vectors = vectors or {}
        self.query_vector = query_vector
        self.calls = []

    def encode(self, texts, **kwargs):
        self.calls.append((list(texts), kwargs))
        return np.asarray([
            self.query_vector if text.startswith("Instruct: ")
            else self.vectors.get(text, (1.0, 0.0))
            for text in texts
        ], dtype=np.float32)


def job(identifier, text):
    return {"id": identifier, "search_text": text}


def test_startup_prepares_only_query_encoder_without_building_document_cache(tmp_path):
    encoder = RecordingEncoder()
    retriever = HybridRetriever(tmp_path, encoder=encoder)
    retriever.prepare_query_encoder()
    assert len(encoder.calls) == 1
    assert encoder.calls[0][0] == [f"Instruct: {QUERY_INSTRUCTION}\nQuery: Python SQL Datenanalyse"]
    assert not list(tmp_path.rglob('*.npy'))
    assert retriever.search([job('a', 'Python data')], 'Python')[0]['job']['id'] == 'a'


def test_tokenizer_preserves_specialist_keywords_and_unicode():
    assert tokenize("C++ C# .NET Python Qualitätsprüfung München") == [
        "c++", "c#", ".net", "python", "qualitätsprüfung", "münchen"
    ]
    assert "c" not in tokenize("C++ C#")


def test_hybrid_fusion_uses_both_rankings_and_normalized_cosine(tmp_path):
    jobs = [job("a", "Python data"), job("b", "C++ firmware"), job("c", "Python models")]
    encoder = RecordingEncoder({
        "Python data": (8.0, 0.0),
        "C++ firmware": (0.8, 0.6),
        "Python models": (0.0, 4.0),
    }, query_vector=(5.0, 0.0))
    results = HybridRetriever(tmp_path, encoder=encoder).search(jobs, "Python")
    assert [item["job"]["id"] for item in results] == ["a", "c", "b"]
    assert results[0]["job"] is jobs[0]
    assert results[0]["rrf_score"] == pytest.approx(2 / 61)
    assert results[0]["semantic_score"] == pytest.approx(1.0)
    assert results[1]["rrf_score"] == pytest.approx(1 / 62 + 1 / 63)
    assert results[2]["bm25_rank"] is None
    assert results[2]["bm25_score"] is None
    assert results[2]["rrf_score"] == pytest.approx(1 / 62)
    assert encoder.calls[0][0] == [f"Instruct: {QUERY_INSTRUCTION}\nQuery: Python"]
    assert encoder.calls[1][0] == [item["search_text"] for item in jobs]
    assert encoder.calls[1][1]["normalize_embeddings"] is True


def test_no_lexical_match_has_no_arbitrary_rrf_boost(tmp_path):
    jobs = [job("b", "Finance"), job("a", "Engineering")]
    results = HybridRetriever(tmp_path, encoder=RecordingEncoder()).search(jobs, "healthcare")
    assert [item["job"]["id"] for item in results] == ["a", "b"]
    assert all(item["bm25_rank"] is None for item in results)
    assert results[0]["rrf_score"] == pytest.approx(1 / 61)
    assert results[1]["rrf_score"] == pytest.approx(1 / 62)


def test_one_job_and_zero_idf_matches_are_retained(tmp_path):
    retriever = HybridRetriever(tmp_path, encoder=RecordingEncoder())
    single = retriever.search([job("a", "C++")], "C++")
    assert single[0]["bm25_rank"] == 1
    assert single[0]["semantic_rank"] == 1
    # With two documents and one match, BM25's IDF is exactly zero.
    result = retriever.search([job("a", "C++"), job("b", "Java")], "C++")
    assert result[0]["bm25_score"] == pytest.approx(0)
    assert result[0]["bm25_rank"] == 1


def test_empty_corpus_never_initializes_model(tmp_path):
    retriever = HybridRetriever(tmp_path)
    assert retriever.search([], "Python") == []
    assert retriever.warmup([]) is None
    assert retriever._encoder is None
    assert not list(tmp_path.iterdir())


def test_lazy_model_initialization_is_pinned_and_shared_between_threads(tmp_path, monkeypatch):
    constructors = []

    class StubSentenceTransformer:
        def __init__(self, *args, **kwargs):
            constructors.append((args, kwargs))

    stub_module = types.ModuleType("sentence_transformers")
    stub_module.SentenceTransformer = StubSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", stub_module)
    retriever = HybridRetriever(tmp_path, device="cpu")
    assert constructors == []
    with ThreadPoolExecutor(max_workers=4) as pool:
        instances = list(pool.map(lambda _: retriever._get_encoder(), range(4)))
    assert constructors == [((MODEL_ID,), {"revision": MODEL_REVISION, "device": "cpu"})]
    assert all(instance is instances[0] for instance in instances)
    assert instances[0].max_seq_length == 512


def test_empty_lexical_documents_still_allow_semantic_search(tmp_path):
    results = HybridRetriever(tmp_path, encoder=RecordingEncoder()).search([job("a", "")], "Python")
    assert results[0]["bm25_rank"] is None
    assert results[0]["semantic_rank"] == 1


def test_each_leg_and_output_are_capped_at_twenty(tmp_path):
    jobs = [job(f"{index:02}", f"Python {index:02}") for index in range(45)]
    encoder = RecordingEncoder({
        item["search_text"]: (index + 1, 46 - index)
        for index, item in enumerate(jobs)
    })
    retriever = HybridRetriever(tmp_path, encoder=encoder)
    results = retriever.search(jobs, "Python", top_k=100)
    assert len(results) == 20
    assert all(item["bm25_rank"] is None or item["bm25_rank"] <= 20 for item in results)
    assert all(item["semantic_rank"] is None or item["semantic_rank"] <= 20 for item in results)
    assert retriever.search(jobs, "Python", top_k=5) == results[:5]


def test_persistent_document_cache_reused_and_text_changes_invalidate(tmp_path):
    jobs = [job("a", "Python data"), job("b", "Java backend")]
    first = RecordingEncoder()
    HybridRetriever(tmp_path, encoder=first).warmup(jobs)
    assert first.calls[0][0] == ["Python data", "Java backend"]
    second = RecordingEncoder()
    retriever = HybridRetriever(tmp_path, encoder=second)
    retriever.search(jobs, "Python")
    assert len(second.calls) == 1  # Only this request's query requires embedding.
    changed = [job("a", "Rust systems"), jobs[1]]
    retriever.search(changed, "Rust")
    assert second.calls[-1][0] == ["Rust systems"]


@pytest.mark.parametrize("invalid", [np.array([np.nan, 0]), np.array([0.0, 0]), np.ones(3)])
def test_invalid_or_wrong_dimension_cache_is_recomputed(tmp_path, invalid):
    encoder = RecordingEncoder()
    retriever = HybridRetriever(tmp_path, encoder=encoder)
    jobs = [job("a", "Python")]
    retriever.warmup(jobs)
    np.save(retriever._cache_path("Python"), invalid, allow_pickle=False)
    results = retriever.search(jobs, "Python")
    assert encoder.calls[-1][0] == ["Python"]
    assert results[0]["semantic_score"] == pytest.approx(1.0)
    assert np.load(retriever._cache_path("Python"), allow_pickle=False).shape == (2,)


def test_duplicate_documents_are_encoded_once(tmp_path):
    encoder = RecordingEncoder()
    retriever = HybridRetriever(tmp_path, encoder=encoder)
    results = retriever.search([job("a", "Python"), job("b", "Python")], "Python")
    assert len(results) == 2
    assert encoder.calls[-1][0] == ["Python"]


def test_sparse_and_dense_legs_execute_concurrently(tmp_path):
    retriever = HybridRetriever(tmp_path, encoder=RecordingEncoder())
    barrier = threading.Barrier(2, timeout=5)
    lexical, semantic = retriever._lexical, retriever._semantic

    def concurrent_lexical(jobs, query):
        barrier.wait()
        return lexical(jobs, query)

    def concurrent_semantic(jobs, query):
        barrier.wait()
        return semantic(jobs, query)

    retriever._lexical = concurrent_lexical
    retriever._semantic = concurrent_semantic
    assert retriever.search([job("a", "Python")], "Python")[0]["rrf_score"] == pytest.approx(2 / 61)


def test_encoder_failure_surfaces_without_fallback_or_internal_details(tmp_path):
    class BrokenEncoder:
        def encode(self, *args, **kwargs):
            raise RuntimeError("private credential details")

    with pytest.raises(EmbeddingUnavailable) as error:
        HybridRetriever(tmp_path, encoder=BrokenEncoder()).search([job("a", "Python")], "Python")
    assert "private credential" not in str(error.value)
    assert error.value.__cause__ is None


def test_blank_query_rejected_before_loading_model(tmp_path):
    retriever = HybridRetriever(tmp_path)
    with pytest.raises(ValueError, match="query"):
        retriever.search([job("a", "Python")], "  ")
    assert retriever._encoder is None
