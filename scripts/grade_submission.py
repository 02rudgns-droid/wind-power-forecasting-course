from __future__ import annotations

import argparse
import csv
import html
import json
import math
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

EXPECTED_START = datetime(2025, 1, 1, 0, 0)
EXPECTED_HOURS = 8760
EXPECTED_TIMES = {
    EXPECTED_START + timedelta(hours=i) for i in range(EXPECTED_HOURS)
}
EXPECTED_MONTHS = {f"2025-{month:02d}" for month in range(1, 13)}


class ValidationError(Exception):
    pass


def _require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise ValidationError(f"{label} 파일을 찾을 수 없습니다.")
    if path.stat().st_size == 0:
        raise ValidationError(f"{label} 파일이 비어 있습니다.")


def _parse_number(text: str, label: str) -> float:
    try:
        value = float(text)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} 값이 숫자가 아닙니다.") from exc

    if not math.isfinite(value):
        raise ValidationError(f"{label} 값에 NaN 또는 무한대가 포함되어 있습니다.")
    return value


def load_prediction(path: Path) -> dict[datetime, float]:
    _require_file(path, "prediction.csv")

    if path.stat().st_size > 2_000_000:
        raise ValidationError("prediction.csv 파일 크기가 비정상적으로 큽니다.")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    if not rows:
        raise ValidationError("prediction.csv가 비어 있습니다.")

    if rows[0] != ["시간", "발전량"]:
        raise ValidationError(
            "prediction.csv의 컬럼은 정확히 '시간,발전량'이어야 합니다."
        )

    data_rows = rows[1:]
    if len(data_rows) != EXPECTED_HOURS:
        raise ValidationError(
            f"prediction.csv는 8760행이어야 합니다. 현재 {len(data_rows)}행입니다."
        )

    predictions: dict[datetime, float] = {}

    for row_number, row in enumerate(data_rows, start=2):
        if len(row) != 2:
            raise ValidationError(
                f"prediction.csv {row_number}행의 컬럼 수가 2개가 아닙니다."
            )

        time_text = row[0].strip()
        try:
            timestamp = datetime.strptime(time_text, "%Y-%m-%d %H:%M")
        except ValueError as exc:
            raise ValidationError(
                f"prediction.csv {row_number}행의 시간 형식이 잘못되었습니다: {time_text}"
            ) from exc

        if timestamp in predictions:
            raise ValidationError(f"중복된 시간이 있습니다: {time_text}")

        value = _parse_number(
            row[1].strip(), f"prediction.csv {row_number}행 발전량"
        )
        if value < 0:
            raise ValidationError(
                f"prediction.csv {row_number}행 발전량이 음수입니다."
            )

        predictions[timestamp] = value

    actual_times = set(predictions)
    if actual_times != EXPECTED_TIMES:
        missing = sorted(EXPECTED_TIMES - actual_times)
        extra = sorted(actual_times - EXPECTED_TIMES)

        parts = []
        if missing:
            parts.append(
                f"누락 시간 {len(missing)}개"
                + (f" (예: {missing[0]:%Y-%m-%d %H:%M})" if missing else "")
            )
        if extra:
            parts.append(
                f"범위 밖 시간 {len(extra)}개"
                + (f" (예: {extra[0]:%Y-%m-%d %H:%M})" if extra else "")
            )

        raise ValidationError(
            "2025년 1월 1일 00:00부터 12월 31일 23:00까지 "
            "모든 시간이 정확히 한 번씩 있어야 합니다. " + ", ".join(parts)
        )

    return predictions


def load_truth(path: Path) -> dict[datetime, float]:
    _require_file(path, "2025 실제 발전량 정답")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    if not rows or rows[0] != ["시간", "발전량"]:
        raise ValidationError("비공개 발전량 정답 파일 형식이 올바르지 않습니다.")

    values: dict[datetime, float] = {}
    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != 2:
            raise ValidationError(
                f"비공개 발전량 정답 {row_number}행의 형식이 올바르지 않습니다."
            )

        try:
            timestamp = datetime.strptime(row[0].strip(), "%Y-%m-%d %H:%M")
        except ValueError as exc:
            raise ValidationError("비공개 발전량 정답의 시간 형식이 잘못되었습니다.") from exc

        if timestamp in values:
            raise ValidationError("비공개 발전량 정답에 중복 시간이 있습니다.")

        value = _parse_number(row[1].strip(), "비공개 실제 발전량")
        if value < 0:
            raise ValidationError("비공개 발전량 정답에 음수 값이 있습니다.")
        values[timestamp] = value

    if len(values) != EXPECTED_HOURS or set(values) != EXPECTED_TIMES:
        raise ValidationError("비공개 발전량 정답이 2025년 8760시간과 일치하지 않습니다.")

    return values


def load_capacity(path: Path) -> dict[str, float]:
    _require_file(path, "2025 설비용량 정답")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    if not rows or rows[0] != ["연월", "설비용량_mw"]:
        raise ValidationError("비공개 설비용량 파일 형식이 올바르지 않습니다.")

    capacity: dict[str, float] = {}

    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != 2:
            raise ValidationError(
                f"비공개 설비용량 {row_number}행의 형식이 올바르지 않습니다."
            )

        month = row[0].strip()
        if month in capacity:
            raise ValidationError(f"비공개 설비용량에 중복 연월이 있습니다: {month}")

        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError as exc:
            raise ValidationError(
                f"비공개 설비용량의 연월 형식이 잘못되었습니다: {month}"
            ) from exc

        value = _parse_number(row[1].strip(), "비공개 설비용량")
        if value <= 0:
            raise ValidationError("비공개 설비용량은 0보다 커야 합니다.")
        capacity[month] = value

    if set(capacity) != EXPECTED_MONTHS:
        raise ValidationError("비공개 설비용량은 2025년 1월부터 12월까지 있어야 합니다.")

    return capacity


def load_submission_info(path: Path) -> tuple[str, str]:
    _require_file(path, "submission_info.json")

    if path.stat().st_size > 20_000:
        raise ValidationError("submission_info.json 파일 크기가 비정상적으로 큽니다.")

    try:
        with path.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationError("submission_info.json이 올바른 JSON 형식이 아닙니다.") from exc

    if not isinstance(data, dict):
        raise ValidationError("submission_info.json의 최상위 값은 객체여야 합니다.")

    name = data.get("name")
    model_name = data.get("model_name")

    for key, value, max_length in (
        ("name", name, 40),
        ("model_name", model_name, 100),
    ):
        if not isinstance(value, str):
            raise ValidationError(f"submission_info.json의 '{key}'는 문자열이어야 합니다.")

        cleaned = value.strip()
        if not cleaned:
            raise ValidationError(f"submission_info.json의 '{key}'가 비어 있습니다.")
        if len(cleaned) > max_length:
            raise ValidationError(
                f"submission_info.json의 '{key}'가 너무 깁니다. "
                f"최대 {max_length}자입니다."
            )
        if any(ord(char) < 32 for char in cleaned):
            raise ValidationError(
                f"submission_info.json의 '{key}'에 허용되지 않는 제어문자가 있습니다."
            )

    return name.strip(), model_name.strip()


def calculate_nmae(
    predictions: dict[datetime, float],
    truth: dict[datetime, float],
    capacity: dict[str, float],
) -> float:
    total = 0.0

    for timestamp in sorted(EXPECTED_TIMES):
        month = timestamp.strftime("%Y-%m")
        total += abs(truth[timestamp] - predictions[timestamp]) / capacity[month]

    return total / EXPECTED_HOURS * 100.0


def write_outputs(
    result_path: Path,
    comment_path: Path,
    *,
    valid: bool,
    name: str | None = None,
    model_name: str | None = None,
    score: float | None = None,
    error: str | None = None,
) -> None:
    timestamp = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")

    result = {
        "valid": valid,
        "name": name,
        "model_name": model_name,
        "nmae": score,
        "error": error,
        "graded_at": timestamp,
        "pr_number": int(os.environ.get("PR_NUMBER", "0")),
        "github_user": os.environ.get("GITHUB_USER", ""),
        "head_repo": os.environ.get("HEAD_REPO", ""),
        "head_sha": os.environ.get("HEAD_SHA", ""),
    }

    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    short_sha = result["head_sha"][:7] if result["head_sha"] else "-"

    if valid:
        safe_name = html.escape(name or "")
        safe_model = html.escape(model_name or "")
        body = f"""<!-- wind-grader-comment -->
## 자동 채점 결과 ✅

| 항목 | 결과 |
| --- | --- |
| 이름 | {safe_name} |
| 모델명 | {safe_model} |
| NMAE | **{score:.4f}%** |
| 제출 Commit | `{short_sha}` |

NMAE는 낮을수록 좋습니다.

같은 Pull Request에서 `prediction.csv` 또는 `submission_info.json`을 수정해 다시 `git push`하면 자동 재채점됩니다.
"""
    else:
        safe_error = html.escape(error or "알 수 없는 오류")
        body = f"""<!-- wind-grader-comment -->
## 자동 검증 결과 ❌

제출 형식 검증에 실패했습니다.

**사유:** {safe_error}

파일을 수정한 뒤 같은 Pull Request에 다시 `git push`하면 자동 재검증됩니다.
"""

    comment_path.write_text(body, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction", required=True, type=Path)
    parser.add_argument("--info", required=True, type=Path)
    parser.add_argument("--truth", required=True, type=Path)
    parser.add_argument("--capacity", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--comment", required=True, type=Path)
    args = parser.parse_args()

    try:
        name, model_name = load_submission_info(args.info)
        predictions = load_prediction(args.prediction)
        truth = load_truth(args.truth)
        capacity = load_capacity(args.capacity)
        score = calculate_nmae(predictions, truth, capacity)

        write_outputs(
            args.result,
            args.comment,
            valid=True,
            name=name,
            model_name=model_name,
            score=score,
        )
    except ValidationError as exc:
        write_outputs(
            args.result,
            args.comment,
            valid=False,
            error=str(exc),
        )


if __name__ == "__main__":
    main()
