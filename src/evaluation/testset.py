from __future__ import annotations

from typing import Any
from pathlib import Path

import pandas as pd

from core.utils import write_json


def build_test_set(df: pd.DataFrame, output_path: Path) -> list[dict[str, Any]]:
    if len(df) < 3:
        raise ValueError("Cần ít nhất 3 document để tạo evaluation set.")
    rows = df.sort_values("paper_id").reset_index(drop=True)
    items: list[dict[str, Any]] = []
    definitions = [
        ("summary", "What is the main contribution described in '{title}'?", lambda r: r["summary"]),
        ("authors", "Who authored '{title}'?", lambda r: r["authors_joined"]),
        ("date", "When was '{title}' published?", lambda r: r["published"]),
        ("categories", "What categories are assigned to '{title}'?", lambda r: r["categories_joined"]),
    ]
    for offset, (kind, template, answer) in enumerate(definitions):
        for repeat, row in enumerate(rows.iloc[offset:offset + 3].itertuples(index=False)):
            row_dict = row._asdict()
            items.append({
                "id": f"q-{len(items) + 1:02d}", "question_type": kind,
                "question": template.format(title=row_dict["title"]),
                "ground_truth": str(answer(row_dict)), "ground_truth_doc_ids": [str(row_dict["paper_id"])],
            })
            if len(items) >= 10:
                break
        if len(items) >= 10:
            break
    write_json(output_path, items)
    return items

