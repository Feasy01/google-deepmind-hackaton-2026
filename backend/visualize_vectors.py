#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "qdrant-client>=1.12.0",
#   "umap-learn>=0.5.0",
#   "plotly>=5.0.0",
#   "numpy>=1.24.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Vector Space Visualizer
-----------------------
Fetches all vectors from Qdrant (articles + podcasts),
reduces them to 2D with UMAP, and renders an interactive
Plotly HTML scatter plot.

Run with:
    uv run python visualize_vectors.py
"""

import os
import textwrap
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import numpy as np
from qdrant_client import QdrantClient
import umap
import plotly.graph_objects as go

QDRANT_URL = os.environ.get("QDRANT_URL", "http://192.168.10.191:6333")
ARTICLES_COLLECTION = "articles"
PODCASTS_COLLECTION = "podcast_episodes"
OUTPUT_FILE = Path(__file__).parent / "vector_space.html"


# ── Palette ──────────────────────────────────────────────────────────────────

ARTICLE_COLORS = [
    "#6EE7B7",  # mint
    "#34D399",  # emerald
    "#10B981",  # green
    "#059669",  # dark green
    "#6EE7F7",  # cyan
    "#22D3EE",  # sky
    "#38BDF8",  # light blue
    "#60A5FA",  # blue
]

PODCAST_COLORS = [
    "#F472B6",  # pink
    "#FB7185",  # rose
    "#F97316",  # orange
    "#FBBF24",  # amber
]


def fetch_all(client: QdrantClient, collection: str) -> tuple[list, list]:
    """Scroll through entire collection and return (vectors, payloads)."""
    vectors, payloads = [], []
    offset = None
    while True:
        results, next_offset = client.scroll(
            collection_name=collection,
            offset=offset,
            limit=250,
            with_vectors=True,
            with_payload=True,
        )
        for point in results:
            vectors.append(point.vector)
            payloads.append(point.payload)
        if next_offset is None:
            break
        offset = next_offset
    return vectors, payloads


def wrap(text: str, width: int = 60) -> str:
    return "<br>".join(textwrap.wrap(text[:400], width))


def main():
    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(url=QDRANT_URL)

    # ── Fetch vectors ─────────────────────────────────────────────────────────
    print("📥 Fetching articles...")
    art_vecs, art_payloads = fetch_all(client, ARTICLES_COLLECTION)
    print(f"   {len(art_vecs)} article vectors")

    print("📥 Fetching podcast episodes...")
    pod_vecs, pod_payloads = fetch_all(client, PODCASTS_COLLECTION)
    print(f"   {len(pod_vecs)} podcast vectors")

    all_vecs = art_vecs + pod_vecs
    all_payloads = art_payloads + pod_payloads
    labels = ["article"] * len(art_vecs) + ["podcast"] * len(pod_vecs)

    X = np.array(all_vecs, dtype=np.float32)
    print(f"\n🧮 Running UMAP on {len(X)} vectors ({X.shape[1]}D → 2D)...")
    print("   (this takes ~15–30 seconds)")

    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=20,
        min_dist=0.1,
        metric="cosine",
        random_state=42,
        verbose=False,
    )
    embedding = reducer.fit_transform(X)
    print("   UMAP done ✓")

    # ── Build Plotly traces ───────────────────────────────────────────────────
    traces = []

    # --- Articles: one trace per unique article title ---
    art_titles = sorted(set(p.get("article_title", "Unknown") for p in art_payloads))
    for i, title in enumerate(art_titles):
        color = ARTICLE_COLORS[i % len(ARTICLE_COLORS)]
        idxs = [j for j, p in enumerate(all_payloads) if labels[j] == "article" and p.get("article_title") == title]
        xs = embedding[idxs, 0]
        ys = embedding[idxs, 1]
        hovers = [
            f"<b>📄 {title}</b><br>"
            f"Chunk #{all_payloads[j].get('chunk_index', '?')}<br><br>"
            f"{wrap(all_payloads[j].get('chunk_text', ''))}"
            for j in idxs
        ]
        traces.append(go.Scatter(
            x=xs, y=ys,
            mode="markers",
            name=f"📄 {title[:40]}",
            legendgroup="articles",
            legendgrouptitle={"text": "Articles"} if i == 0 else {},
            marker=dict(size=7, color=color, opacity=0.85, line=dict(width=0.5, color="white")),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers,
        ))

    # --- Podcasts: one trace per unique episode ---
    ep_titles = sorted(set(p.get("episode_title", "Unknown") for p in pod_payloads))
    for i, title in enumerate(ep_titles):
        color = PODCAST_COLORS[i % len(PODCAST_COLORS)]
        idxs = [j for j, p in enumerate(all_payloads) if labels[j] == "podcast" and p.get("episode_title") == title]
        xs = embedding[idxs, 0]
        ys = embedding[idxs, 1]
        hovers = [
            f"<b>🎙️ {title}</b><br>"
            f"⏱ {all_payloads[j].get('timestamp_start', '?')} → {all_payloads[j].get('timestamp_end', '?')}<br><br>"
            f"{wrap(all_payloads[j].get('window_text', ''))}"
            for j in idxs
        ]
        traces.append(go.Scatter(
            x=xs, y=ys,
            mode="markers",
            name=f"🎙 {title[:40]}",
            legendgroup="podcasts",
            legendgrouptitle={"text": "Podcast Episodes"} if i == 0 else {},
            marker=dict(size=8, color=color, opacity=0.8, symbol="diamond", line=dict(width=0.5, color="white")),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers,
        ))

    # ── Layout ────────────────────────────────────────────────────────────────
    fig = go.Figure(traces)
    fig.update_layout(
        title=dict(
            text="🧠 RAG Vector Space — UMAP Projection (3072D → 2D, cosine)",
            font=dict(size=20, color="#E2E8F0"),
            x=0.5,
        ),
        paper_bgcolor="#0F172A",
        plot_bgcolor="#1E293B",
        font=dict(color="#CBD5E1", family="Inter, system-ui, sans-serif"),
        legend=dict(
            bgcolor="rgba(15,23,42,0.85)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(size=11),
            itemsizing="constant",
            groupclick="toggleitem",
        ),
        xaxis=dict(showgrid=True, gridcolor="#1E293B", zeroline=False, showticklabels=False, title="UMAP-1"),
        yaxis=dict(showgrid=True, gridcolor="#1E293B", zeroline=False, showticklabels=False, title="UMAP-2"),
        hoverlabel=dict(
            bgcolor="#1E293B",
            bordercolor="#475569",
            font=dict(size=12, color="#E2E8F0"),
        ),
        margin=dict(l=40, r=40, t=80, b=40),
        height=800,
    )

    # ── Export ────────────────────────────────────────────────────────────────
    fig.write_html(
        str(OUTPUT_FILE),
        include_plotlyjs="cdn",
        config={"scrollZoom": True, "displayModeBar": True},
    )
    print(f"\n✅ Saved to: {OUTPUT_FILE}")
    print("   Open it in your browser (scroll to zoom, drag to pan, hover for content)")

    # Try to auto-open
    import subprocess, sys
    subprocess.Popen(["open", str(OUTPUT_FILE)])


if __name__ == "__main__":
    main()
