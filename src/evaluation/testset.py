from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json

TEST_PLAN: tuple[tuple[int, str], ...] = (
    (0, "summary"),
    (1, "authors"),
    (2, "date"),
    (4, "categories"),
    (5, "summary"),
    (8, "summary"),
    (13, "date"),
    (14, "date"),
    (18, "authors"),
    (20, "categories"),
)


def _question(question_type: str, title: str) -> str:
    if question_type == "authors":
        return f"Who authored the paper '{title}'?"
    if question_type == "date":
        return f"When was the paper '{title}' published?"
    if question_type == "categories":
        return f"What categories does the paper '{title}' belong to?"
    return f"What is the summary of the paper '{title}'?"


def _ground_truth(question_type: str, row: pd.Series) -> str:
    if question_type == "authors":
        return str(row["authors_joined"])
    if question_type == "date":
        return str(row["published"])
    if question_type == "categories":
        return str(row["categories_joined"] or row["primary_category"])
    return first_sentence(str(row["summary"]))


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if len(df) < 21:
        raise ValueError(f"Test-set generation requires at least 21 cleaned documents, found {len(df)}.")

    ordered = df.reset_index(drop=True)
    test_set: list[dict[str, Any]] = []
    for number, (position, question_type) in enumerate(TEST_PLAN, start=1):
        row = ordered.iloc[position]
        title = str(row["title"])
        ground_truth = _ground_truth(question_type, row)
        if not title or not ground_truth or not str(row["paper_id"]):
            raise ValueError(f"Invalid test-set source row at position {position}.")
        test_set.append(
            {
                "id": f"eval_{number:03d}",
                "question_type": question_type,
                "question": _question(question_type, title),
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [str(row["paper_id"])],
            }
        )

    write_json(Path(output_path), test_set)
    return test_set
