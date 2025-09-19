from __future__ import annotations

from typing import Dict, List, Optional

import streamlit as st


def render_post_cards(payload: Dict[str, object]) -> None:
    """Render posts as simple visual cards.

    Expects payload in shape: {"topic": str, "variants": [{"text": str, "image_query": str, "image_url": Optional[str]}]}
    """
    variants: List[Dict[str, Optional[str]]] = payload.get("variants", [])  # type: ignore[assignment]
    if not variants:
        st.warning("No variants to display.")
        return

    st.subheader("Generated Posts")
    cols_per_row = 2
    for i in range(0, len(variants), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, variant in enumerate(variants[i : i + cols_per_row]):
            with cols[j]:
                text = variant.get("text") or "(no text)"
                image_url = variant.get("image_url")
                image_query = variant.get("image_query") or ""

                with st.container(border=True):
                    if image_url:
                        st.image(image_url, use_container_width=True)
                    else:
                        st.markdown(
                            f"<div style='height:180px; background:#f0f2f6; display:flex; align-items:center; justify-content:center; color:#6b7280;'>No image (query: {image_query})</div>",
                            unsafe_allow_html=True,
                        )
                    st.markdown(f"<div style='margin-top:0.5rem; font-size:0.95rem;'>{text}</div>", unsafe_allow_html=True)


