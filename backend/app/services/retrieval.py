from typing import List, Tuple
from sqlalchemy.orm import Session
from app.entities import Shipment

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    TfidfVectorizer = None
    cosine_similarity = None

_vectorizer = None
_doc_texts: List[str] = []
_doc_ids: List[int] = []
_tfidf_matrix = None


def _build_text_for_shipment(s: Shipment) -> str:
    parts = [
        f"Ref: {s.shipment_ref}",
        f"Carrier: {s.carrier.carrier_name if s.carrier else ''}",
        f"Route: {getattr(s.route, 'origin_port', '')} -> {getattr(s.route, 'dest_port', '')}",
        f"Mode: {s.mode}",
        f"Status: {s.status}",
    ]
    if s.risk_score and s.risk_score.top_factors:
        try:
            import json
            factors = json.loads(s.risk_score.top_factors)
            parts.append("Top factors: " + ", ".join([f.get('factor','') for f in factors]))
        except Exception:
            pass
    # include history text if present
    if hasattr(s, 'history') and s.history:
        parts.append("History: " + "; ".join([f"{getattr(h, 'event_type', '')} ({getattr(h, 'delay_days', 0)}d delay)" for h in s.history]))
    return " \n ".join(parts)


def build_index(db: Session):
    global _vectorizer, _doc_texts, _doc_ids, _tfidf_matrix
    q = db.query(Shipment).all()
    texts = []
    ids = []
    for s in q:
        texts.append(_build_text_for_shipment(s))
        ids.append(s.shipment_id if hasattr(s, "shipment_id") else s.id)

    if not texts:
        _vectorizer = None
        _doc_texts = []
        _doc_ids = []
        _tfidf_matrix = None
        return

    _doc_texts = texts
    _doc_ids = ids

    if HAS_SKLEARN:
        try:
            vec = TfidfVectorizer(max_features=10000)
            mat = vec.fit_transform(texts)
            _vectorizer = vec
            _tfidf_matrix = mat
        except Exception:
            _vectorizer = None
            _tfidf_matrix = None


def query(query_text: str, top_k: int = 3) -> List[Tuple[int, str, float]]:
    """Return list of (shipment_id, text, score)"""
    global _vectorizer, _doc_texts, _doc_ids, _tfidf_matrix
    if not _doc_texts:
        return []

    if HAS_SKLEARN and _vectorizer is not None and _tfidf_matrix is not None:
        try:
            qv = _vectorizer.transform([query_text])
            sims = cosine_similarity(qv, _tfidf_matrix)[0]
            pairs = list(enumerate(sims))
            pairs.sort(key=lambda x: x[1], reverse=True)
            results = []
            for idx, score in pairs[:top_k]:
                results.append((_doc_ids[idx], _doc_texts[idx], float(score)))
            return results
        except Exception:
            pass

    # Simple word overlap fallback
    query_words = set(query_text.lower().split())
    scored = []
    for idx, text in enumerate(_doc_texts):
        doc_words = set(text.lower().split())
        overlap = len(query_words & doc_words)
        score = overlap / max(1, len(query_words))
        scored.append((_doc_ids[idx], text, float(score)))

    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:top_k]

