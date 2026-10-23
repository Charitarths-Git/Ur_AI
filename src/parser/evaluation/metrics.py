"""GT metrics with explicit counts/denominators and identity-aware ancestry."""

from collections import Counter
from datetime import date
from statistics import mean

from parser.evaluation.alignment import align_rows
from parser.evaluation.data import Table, value_at
from parser.normalize import label_key, parse_period_end


def ratio(numerator, denominator, description):
    return {
        "numerator": numerator,
        "denominator": denominator,
        "score": numerator / denominator if denominator else None,
        "meaning": description,
    }


def ancestor_ids(row, rows_by_id):
    ancestors, seen = [], {row.row_id}
    parent = row.parent_row_id
    while parent is not None:
        if parent in seen or parent not in rows_by_id:
            ancestors.append(f"__invalid_parent__:{parent}")
            break
        seen.add(parent)
        ancestors.append(parent)
        parent = rows_by_id[parent].parent_row_id
    return tuple(ancestors)


def score_tables(
    prediction: Table, gt: Table, *, threshold=0.5, predicted_json=None, gt_meta=None
) -> dict:
    alignment = align_rows(prediction, gt, threshold)
    p_to_g = {prediction.rows[i].row_id: gt.rows[j].row_id for i, j in alignment.pairs}
    g_to_p = {j: i for i, j in alignment.pairs}
    pred_ids = {r.row_id: r for r in prediction.rows}
    gt_ids = {r.row_id: r for r in gt.rows}
    counts, mismatches, confusion = Counter(), [], Counter()
    for j, expected in enumerate(gt.rows):
        pred = prediction.rows[g_to_p[j]] if j in g_to_p else None

        def mismatch(field, wanted, actual):
            mismatches.append(
                {
                    "gt_row_id": expected.row_id,
                    "pred_row_id": pred.row_id if pred else None,
                    "label": expected.label,
                    "field": field,
                    "expected": wanted,
                    "predicted": actual,
                }
            )

        if pred is None:
            mismatch("missing_row", expected.row_id, None)
            confusion[expected.row_type, "__missing__"] += 1
        else:
            confusion[expected.row_type, pred.row_type] += 1
        values_correct = True
        for role in gt.columns:
            gv, gr, gvalid = value_at(gt, expected, role)
            pv, pr, pvalid = value_at(prediction, pred, role) if pred else (None, None, False)
            correct = pred is not None and pvalid and gvalid and pv == gv
            counts["cell_accuracy_all"] += correct
            if gr != "":
                counts["printed_cells"] += 1
                counts["cell_accuracy_printed"] += correct
            counts["raw_accuracy"] += pred is not None and pr == gr and role in prediction.columns
            if not correct:
                values_correct = False
                mismatch(role + "_value", gv, pv)
                if pred is not None and (not pvalid or role not in prediction.columns):
                    mismatches[-1]["reason"] = "missing role or invalid prediction value"
            if pred is None or pr != gr or role not in prediction.columns:
                mismatch(role + "_raw", gr, pr)
                if role not in prediction.columns:
                    mismatches[-1]["reason"] = "missing prediction role"
        exact = pred is not None and pred.label == expected.label
        key = pred is not None and label_key(pred.label) == label_key(expected.label)
        kind = pred is not None and pred.row_type == expected.row_type
        level = pred is not None and pred.level == expected.level
        if pred is None:
            parent = path = False
            jac = 0.0
        else:
            parent = (pred.parent_row_id is None and expected.parent_row_id is None) or (
                pred.parent_row_id is not None
                and expected.parent_row_id is not None
                and p_to_g.get(pred.parent_row_id) == expected.parent_row_id
            )
            path = pred.parent_path == expected.parent_path
            mapped = {p_to_g.get(a, f"__unaligned__:{a}") for a in ancestor_ids(pred, pred_ids)}
            wanted = set(ancestor_ids(expected, gt_ids))
            union = mapped | wanted
            jac = len(mapped & wanted) / len(union) if union else 1.0
        for name, correct in [
            ("label_exact", exact),
            ("label_key", key),
            ("row_type", kind),
            ("level", level),
            ("parent", parent),
            ("parent_path", path),
        ]:
            counts[name] += correct
            if not correct:
                field = "label" if name.startswith("label") else name
                wanted = (
                    expected.parent_row_id
                    if name == "parent"
                    else getattr(expected, field, expected.label)
                )
                actual = (
                    (pred.parent_row_id if name == "parent" else getattr(pred, field, None))
                    if pred
                    else None
                )
                # Exact and normalized label metrics share a single mismatch record.
                if name != "label_key":
                    mismatch(field, wanted, actual)
        counts["ancestor_jaccard"] += jac
        if jac != 1:
            mismatch(
                "ancestor_chain",
                list(ancestor_ids(expected, gt_ids)),
                list(ancestor_ids(pred, pred_ids)) if pred else None,
            )
        counts["fully_correct_rows"] += exact and values_correct and kind and parent and level
    for i in alignment.unmatched_prediction:
        row = prediction.rows[i]
        mismatches.append(
            {
                "gt_row_id": None,
                "pred_row_id": row.row_id,
                "label": row.label,
                "field": "extra_row",
                "expected": None,
                "predicted": row.row_id,
            }
        )
    ng, np, matched = len(gt.rows), len(prediction.rows), len(alignment.pairs)
    meanings = {
        "label_exact": "exact printed labels / all GT rows (missing rows wrong)",
        "label_key": "matching label_key / all GT rows",
        "row_type": "correct row types / all GT rows",
        "level": "correct ancestor-count levels / all GT rows",
        "parent": "parents mapped by row alignment (both roots correct) / all GT rows",
        "parent_path": "exact printed ancestor paths / all GT rows",
        "ancestor_jaccard": "sum of alignment-mapped ancestor-set Jaccards / all GT rows",
        "fully_correct_rows": "exact label, both/all values, type, mapped parent and "
        "level / all GT rows",
    }
    metrics = {name: ratio(counts[name], ng, meaning) for name, meaning in meanings.items()}
    metrics.update(
        {
            "cell_accuracy_all": ratio(
                counts["cell_accuracy_all"],
                ng * len(gt.columns),
                "correct integer/null cells / all GT row-column cells",
            ),
            "cell_accuracy_printed": ratio(
                counts["cell_accuracy_printed"],
                counts["printed_cells"],
                "correct integer/null cells / GT cells with nonempty raw",
            ),
            "raw_accuracy": ratio(
                counts["raw_accuracy"],
                ng * len(gt.columns),
                "identical raw strings / all GT row-column cells",
            ),
            "row_precision": ratio(matched, np, "aligned rows / predicted rows"),
            "row_recall": ratio(matched, ng, "aligned rows / GT rows"),
            "row_f1": ratio(2 * matched, np + ng, "2 * aligned rows / (prediction rows + GT rows)"),
        }
    )
    role_correct = period_correct = col_den = 0
    if predicted_json is not None and gt_meta is not None:
        expected_cols = [("previous_year", "previous"), ("current_year", "current")]
        predicted_cols = predicted_json.get("columns", [])
        col_den = max(len(expected_cols), len(predicted_cols))
        for index, (role, key) in enumerate(expected_cols):
            matches = [c for c in predicted_cols if c.get("index") == index]
            role_correct += len(matches) == 1 and matches[0].get("role") == role
            end = parse_period_end(gt_meta["period_end_dates"][key])
            iso = date(*end).isoformat() if end else None
            period_correct += len(matches) == 1 and matches[0].get("period_end") == iso
            if (
                len(matches) != 1
                or matches[0].get("role") != role
                or matches[0].get("period_end") != iso
            ):
                mismatches.append(
                    {
                        "gt_row_id": None,
                        "pred_row_id": None,
                        "label": "",
                        "field": f"column:{role}",
                        "expected": {"index": index, "role": role, "period_end": iso},
                        "predicted": matches,
                    }
                )
        for col in predicted_cols:
            if col.get("index") not in range(len(expected_cols)):
                mismatches.append(
                    {
                        "gt_row_id": None,
                        "pred_row_id": None,
                        "label": "",
                        "field": "extra_column",
                        "expected": None,
                        "predicted": col,
                    }
                )
    metrics["column_roles"] = ratio(
        role_correct,
        col_den,
        "correct role at each unique expected column index / max(expected,predicted "
        "columns); optional JSON/meta",
    )
    metrics["column_periods"] = ratio(
        period_correct,
        col_den,
        "correct date at each unique expected column index / max(expected,predicted "
        "columns); optional JSON/meta",
    )
    return {
        "metrics": metrics,
        "alignment": {
            "threshold": threshold,
            "matched": matched,
            "predicted_rows": np,
            "gt_rows": ng,
            "pairs": [
                {
                    "prediction": prediction.rows[i].row_id,
                    "gt": gt.rows[j].row_id,
                    "similarity": sim,
                }
                for (i, j), sim in zip(alignment.pairs, alignment.similarities, strict=True)
            ],
            "unmatched_prediction": [
                prediction.rows[i].row_id for i in alignment.unmatched_prediction
            ],
            "unmatched_gt": [gt.rows[j].row_id for j in alignment.unmatched_gt],
        },
        "confusion_matrix": {
            kind: {p: confusion[kind, p] for p in sorted({b for a, b in confusion if a == kind})}
            for kind in sorted({a for a, _ in confusion})
        },
        "mismatches": mismatches,
        "input_issues": list(prediction.issues) + list(gt.issues),
    }


def aggregate_reports(reports: list[dict]) -> dict:
    """Micro sum of counts; macro mean of defined per-page scores, with page counts."""
    keys = sorted({key for report in reports for key in report["metrics"]})
    micro, macro = {}, {}
    for key in keys:
        values = [report["metrics"][key] for report in reports if key in report["metrics"]]
        micro[key] = ratio(
            sum(v["numerator"] for v in values),
            sum(v["denominator"] for v in values),
            "pooled counts across pages",
        )
        defined = [v["score"] for v in values if v["score"] is not None]
        macro[key] = {
            "score": mean(defined) if defined else None,
            "defined_pages": len(defined),
            "total_pages": len(reports),
        }
    for name, numerator, denominator in [
        ("accounting_pass_rate", "passed", "evaluable"),
        ("evaluable_fraction", "evaluable", "applicable"),
        ("truncation_fraction", "truncation_inside", "truncation_evaluable"),
    ]:
        accounts = [
            r["accounting"] for r in reports if "accounting" in r and denominator in r["accounting"]
        ]
        if accounts:
            micro[name] = ratio(
                sum(a[numerator] for a in accounts),
                sum(a[denominator] for a in accounts),
                "pooled accounting counts across pages",
            )
            defined = [a[numerator] / a[denominator] for a in accounts if a[denominator]]
            macro[name] = {
                "score": mean(defined) if defined else None,
                "defined_pages": len(defined),
                "total_pages": len(reports),
            }
    return {
        "pages": len(reports),
        "micro": micro,
        "macro": macro,
        "note": "With a single page, defined micro and macro scores coincide.",
    }
