"""Knowledge-base tools that expose local markdown references to the agent.

These helpers treat each immediate subdirectory of ``knowledge/`` as a standalone
collection. Adding a new folder with ``.md`` files automatically makes the
content discoverable via the list/search/read tools below.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

from agents.tool import function_tool


KNOWLEDGE_ROOT = Path(__file__).resolve().parents[2] / "knowledge"
MARKDOWN_SUFFIXES = {".md", ".markdown"}


@dataclass
class KnowledgeDoc:
    collection: str
    path: Path
    title: str
    content: str


def _iter_collections() -> Iterable[Tuple[str, Path]]:
    if not KNOWLEDGE_ROOT.exists():
        return []
    collections: List[Tuple[str, Path]] = []
    for child in sorted(KNOWLEDGE_ROOT.iterdir()):
        if child.is_dir() and not child.name.startswith("."):
            collections.append((child.name, child))
    return collections


def _load_documents(collection: str | None = None) -> List[KnowledgeDoc]:
    docs: List[KnowledgeDoc] = []
    targets = (
        [(collection, KNOWLEDGE_ROOT / collection)]
        if collection
        else list(_iter_collections())
    )

    for collection_name, collection_path in targets:
        if not collection_path.exists() or not collection_path.is_dir():
            continue
        for file_path in sorted(collection_path.rglob("*.md")):
            if file_path.suffix.lower() not in MARKDOWN_SUFFIXES:
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except OSError:
                continue
            title = file_path.stem.replace("_", " ")
            docs.append(
                KnowledgeDoc(
                    collection=collection_name,
                    path=file_path,
                    title=title,
                    content=content,
                )
            )
    return docs


def _summarize_content(content: str, limit: int = 240) -> str:
    text = content.strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _score_document(content: str, query: str) -> float:
    text = content.lower()
    terms = [term for term in re.split(r"\W+", query.lower()) if term]
    if not terms:
        return 0.0
    score = 0.0
    for term in terms:
        occurrences = text.count(term)
        if occurrences:
            score += occurrences * len(term)
    return score


def _extract_snippet(content: str, query: str, snippet_size: int = 200) -> str:
    lowered = content.lower()
    query_lower = query.lower()
    index = lowered.find(query_lower)
    if index == -1:
        return _summarize_content(content, limit=snippet_size)
    start = max(0, index - snippet_size // 2)
    end = min(len(content), index + len(query) + snippet_size // 2)
    snippet = content[start:end].strip().replace("\n", " ")
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet += "..."
    return snippet


@function_tool
def list_knowledge_collections() -> str:
    """List available knowledge collections and their document counts."""

    collections = []
    for name, path in _iter_collections():
        doc_count = sum(
            1
            for file in path.rglob("*")
            if file.is_file() and file.suffix.lower() in MARKDOWN_SUFFIXES
        )
        collections.append(
            {
                "name": name,
                "path": str(path),
                "documents": doc_count,
            }
        )

    return json.dumps({
        "knowledge_root": str(KNOWLEDGE_ROOT),
        "collections": collections,
    })


@function_tool
def search_knowledge(
    query: str,
    collection: str | None = None,
    top_k: int = 5,
) -> str:
    """Search knowledge markdown files for a query.

    Args:
        query: Natural language search string.
        collection: Optional collection name. When omitted, all collections are searched.
        top_k: Maximum number of results to return (default 5).
    """

    if not query or not query.strip():
        return json.dumps({
            "error": "Query must be a non-empty string.",
        })

    docs = _load_documents(collection)
    if collection and not any(doc.collection == collection for doc in docs):
        return json.dumps({
            "error": f"Collection '{collection}' not found.",
        })

    scored = []
    for doc in docs:
        score = _score_document(doc.content, query)
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)

    results = []
    for score, doc in scored[: max(1, top_k)]:
        results.append(
            {
                "collection": doc.collection,
                "document": doc.path.name,
                "path": str(doc.path),
                "score": score,
                "snippet": _extract_snippet(doc.content, query),
            }
        )

    return json.dumps({
        "query": query,
        "collection": collection,
        "results": results,
    })


@function_tool
def read_knowledge_document(collection: str, document: str) -> str:
    """Return the full text of a knowledge document.

    Args:
        collection: Name of the collection (subfolder under ``knowledge``).
        document: Filename within the collection.
    """

    if not collection or not document:
        return json.dumps({
            "error": "Collection and document parameters are required.",
        })

    target = KNOWLEDGE_ROOT / collection / document
    if not target.exists() or target.suffix.lower() not in MARKDOWN_SUFFIXES:
        return json.dumps({
            "error": f"Document '{document}' not found in collection '{collection}'.",
        })

    try:
        content = target.read_text(encoding="utf-8")
    except OSError as exc:
        return json.dumps({
            "error": f"Unable to read document: {exc}",
        })

    return json.dumps({
        "collection": collection,
        "document": document,
        "path": str(target),
        "content": content,
    })


