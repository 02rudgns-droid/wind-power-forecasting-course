"""
수업용 데이터 검증 스크립트

실행:
    python scripts/check_data.py

확인 항목:
- 필수 파일 존재
- CSV / Parquet 읽기 가능 여부
- 발전량 기간 및 행 수
- 설비용량 기간
- ASOS 필수 변수 및 대표 5개 지점
- LDAPS 필수 변수, 대표 5개 지점, 격자순위 1 존재
- 2024 / 2025 LDAPS 기간
"""

from pathlib import Path
import sys
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "발전량": ROOT / "data" / "train" / "generation_jeonbuk_2020_2024.csv",
    "설비용량": ROOT / "data" / "train" / "capacity_jeonbuk_2020_2024.csv",
    "ASOS": ROOT / "data" / "train" / "asos_observation_2020_2024.parquet",
    "LDAPS 2024": ROOT / "data" / "train" / "ldaps_2024.parquet",
    "LDAPS 2025": ROOT / "data" / "test" / "ldaps_2025.parquet",
    "풍력기 위치": ROOT / "data" / "static" / "wind_turbine_location_jeonbuk.csv",
    "ASOS 지점정보": ROOT / "data" / "static" / "asos_station_info.xls",
}

SELECTED_STATIONS = ["군산", "부안", "정읍", "전주", "임실"]


def find_col(columns, candidates):
    for name in candidates:
        if name in columns:
            return name
    return None


def require_alias(df, candidates, label, errors):
    col = find_col(df.columns, candidates)
    if col is None:
        errors.append(
            f"{label} 컬럼 없음 (허용 후보: {', '.join(candidates)})"
        )
    return col


def check_hourly_range(times, expected_start, expected_end, label, errors):
    times = pd.to_datetime(times, errors="coerce").dropna()
    unique = pd.DatetimeIndex(times.unique()).sort_values()

    if len(unique) == 0:
        errors.append(f"{label}: 유효한 시간값 없음")
        return

    print(
        f"       기간: {unique.min()} ~ {unique.max()} "
        f"/ 고유시각 {len(unique):,}개"
    )

    if unique.min() > pd.Timestamp(expected_start):
        errors.append(
            f"{label}: 시작시각 부족 "
            f"({unique.min()} > {expected_start})"
        )

    if unique.max() < pd.Timestamp(expected_end):
        errors.append(
            f"{label}: 종료시각 부족 "
            f"({unique.max()} < {expected_end})"
        )


errors = []

print("=" * 72)
print("Wind Power Forecasting Course - 데이터 검증")
print("=" * 72)

# ------------------------------------------------------------
# 파일 존재 검사
# ------------------------------------------------------------
print("\n[1] 필수 파일")

for label, path in FILES.items():
    if path.exists():
        size_mb = path.stat().st_size / (1024 ** 2)
        print(f"[OK]   {label:<12} {path.relative_to(ROOT)} ({size_mb:.2f} MB)")
    else:
        print(f"[FAIL] {label:<12} {path.relative_to(ROOT)}")
        errors.append(f"{label} 파일 없음")

if errors:
    print("\n[실패] 먼저 누락된 데이터 파일을 확인하세요.")
    sys.exit(1)

# ------------------------------------------------------------
# 발전량
# ------------------------------------------------------------
print("\n[2] 전북 발전량")

try:
    generation = pd.read_csv(FILES["발전량"], encoding="utf-8-sig")

    time_col = require_alias(
        generation,
        ["시간", "일시"],
        "발전량 시간",
        errors,
    )
    power_col = require_alias(
        generation,
        ["발전량", "발전량_mw"],
        "발전량",
        errors,
    )

    if time_col and power_col:
        generation[time_col] = pd.to_datetime(
            generation[time_col],
            errors="coerce",
        )

        print(f"       행 수: {len(generation):,}")

        if len(generation) != 43848:
            errors.append(
                f"발전량 행 수가 43,848이 아님: {len(generation):,}"
            )

        if generation[time_col].duplicated().any():
            errors.append("발전량 시간 중복 존재")

        if generation[power_col].isna().any():
            errors.append("발전량 결측값 존재")

        check_hourly_range(
            generation[time_col],
            "2020-01-01 00:00",
            "2024-12-31 23:00",
            "발전량",
            errors,
        )

        if not any("발전량" in e for e in errors):
            print("[OK]   발전량 데이터 기본 검증")

except Exception as e:
    errors.append(f"발전량 읽기 실패: {e}")
    print(f"[FAIL] 발전량 읽기 실패: {e}")

# ------------------------------------------------------------
# 설비용량
# ------------------------------------------------------------
print("\n[3] 전북 설비용량")

try:
    capacity = pd.read_csv(FILES["설비용량"], encoding="utf-8-sig")

    ym_col = require_alias(
        capacity,
        ["연월"],
        "설비용량 연월",
        errors,
    )
    cap_col = require_alias(
        capacity,
        ["설비용량_mw", "설비용량"],
        "설비용량",
        errors,
    )

    if ym_col and cap_col:
        print(f"       행 수: {len(capacity):,}")
        print(
            "       설비용량 고유값:",
            sorted(capacity[cap_col].dropna().astype(float).unique().tolist())
        )

        if len(capacity) != 60:
            errors.append(
                f"설비용량 행 수가 60이 아님: {len(capacity):,}"
            )

        print("[OK]   설비용량 데이터 읽기")

except Exception as e:
    errors.append(f"설비용량 읽기 실패: {e}")
    print(f"[FAIL] 설비용량 읽기 실패: {e}")

# ------------------------------------------------------------
# ASOS
# ------------------------------------------------------------
print("\n[4] ASOS 2020~2024")

try:
    asos = pd.read_parquet(FILES["ASOS"])

    station_col = require_alias(
        asos, ["지점명"], "ASOS 지점명", errors
    )
    time_col = require_alias(
        asos, ["일시", "시간"], "ASOS 시간", errors
    )

    aliases = {
        "u": ["u_ms", "u"],
        "v": ["v_ms", "v"],
        "풍속": ["풍속_ms", "풍속"],
        "기온": ["기온_C", "기온"],
        "습도": ["습도_pct", "습도"],
        "현지기압": ["현지기압_hPa", "현지기압"],
    }

    resolved_asos = {}
    for label, candidates in aliases.items():
        resolved_asos[label] = require_alias(
            asos, candidates, f"ASOS {label}", errors
        )

    if station_col:
        stations = set(asos[station_col].dropna().astype(str))
        missing = [s for s in SELECTED_STATIONS if s not in stations]

        print(f"       전체 지점 수: {len(stations):,}")
        print("       Baseline 지점:", ", ".join(SELECTED_STATIONS))

        if missing:
            errors.append(
                "ASOS Baseline 지점 없음: " + ", ".join(missing)
            )
        else:
            print("[OK]   Baseline ASOS 5개 지점 존재")

    if time_col:
        check_hourly_range(
            asos[time_col],
            "2020-01-01 00:00",
            "2024-12-31 23:00",
            "ASOS",
            errors,
        )

    print(
        "       인식된 변수:",
        ", ".join(
            f"{k}={v}" for k, v in resolved_asos.items() if v
        )
    )

except Exception as e:
    errors.append(f"ASOS 읽기 실패: {e}")
    print(f"[FAIL] ASOS 읽기 실패: {e}")

# ------------------------------------------------------------
# LDAPS 공통 검사
# ------------------------------------------------------------
def validate_ldaps(df, year, label):
    station_col = require_alias(
        df, ["지점명"], f"{label} 지점명", errors
    )
    rank_col = require_alias(
        df, ["격자순위"], f"{label} 격자순위", errors
    )
    time_col = require_alias(
        df,
        ["유효시각_kst", "유효시각", "목표일", "시간"],
        f"{label} 유효시각",
        errors,
    )

    aliases = {
        "u": ["u_ms", "u"],
        "v": ["v_ms", "v"],
        "기온": ["기온_C", "기온"],
        "습도": ["습도_pct", "습도"],
        "기압": ["기압_hPa", "기압"],
    }

    resolved = {}
    for feature, candidates in aliases.items():
        resolved[feature] = require_alias(
            df, candidates, f"{label} {feature}", errors
        )

    if station_col:
        stations = set(df[station_col].dropna().astype(str))
        missing = [s for s in SELECTED_STATIONS if s not in stations]

        if missing:
            errors.append(
                f"{label} Baseline 지점 없음: " + ", ".join(missing)
            )
        else:
            print(f"[OK]   {label}: Baseline 5개 지점 존재")

    if station_col and rank_col:
        rank = pd.to_numeric(df[rank_col], errors="coerce")
        nearest = df.loc[rank == 1]

        for station in SELECTED_STATIONS:
            n = len(nearest[nearest[station_col].astype(str) == station])
            if n == 0:
                errors.append(
                    f"{label}: {station}의 격자순위 1 자료 없음"
                )

        print(f"[OK]   {label}: 최근접 격자(격자순위=1) 검사")

    if time_col:
        expected_hours = 8784 if year == 2024 else 8760

        check_hourly_range(
            df[time_col],
            f"{year}-01-01 00:00",
            f"{year}-12-31 23:00",
            label,
            errors,
        )

        # Baseline 대상 5지점 + 격자순위 1만 놓고 시간 완전성 점검
        if station_col and rank_col:
            temp = df.copy()
            temp[time_col] = pd.to_datetime(
                temp[time_col], errors="coerce"
            )
            rank = pd.to_numeric(temp[rank_col], errors="coerce")
            temp = temp[
                temp[station_col].astype(str).isin(SELECTED_STATIONS)
                & (rank == 1)
            ]

            for station in SELECTED_STATIONS:
                count = temp.loc[
                    temp[station_col].astype(str) == station,
                    time_col
                ].nunique()

                print(
                    f"       {station}: 최근접 격자 고유시각 "
                    f"{count:,}/{expected_hours:,}"
                )

                if count < expected_hours:
                    errors.append(
                        f"{label}: {station} 시간자료 부족 "
                        f"({count:,}/{expected_hours:,})"
                    )

    print(
        "       인식된 변수:",
        ", ".join(f"{k}={v}" for k, v in resolved.items() if v)
    )


print("\n[5] LDAPS 2024")

try:
    ldaps_2024 = pd.read_parquet(FILES["LDAPS 2024"])
    validate_ldaps(ldaps_2024, 2024, "LDAPS 2024")
except Exception as e:
    errors.append(f"LDAPS 2024 읽기 실패: {e}")
    print(f"[FAIL] LDAPS 2024 읽기 실패: {e}")


print("\n[6] LDAPS 2025")

try:
    ldaps_2025 = pd.read_parquet(FILES["LDAPS 2025"])
    validate_ldaps(ldaps_2025, 2025, "LDAPS 2025")
except Exception as e:
    errors.append(f"LDAPS 2025 읽기 실패: {e}")
    print(f"[FAIL] LDAPS 2025 읽기 실패: {e}")


# ------------------------------------------------------------
# 결과
# ------------------------------------------------------------
print("\n" + "=" * 72)

if errors:
    print("[실패] 데이터 검증 중 문제가 발견되었습니다.")
    print()
    for i, error in enumerate(errors, 1):
        print(f"{i}. {error}")
    sys.exit(1)

print("[성공] 수업용 데이터 검증을 모두 통과했습니다.")
print("이제 다음 명령으로 Baseline을 실행할 수 있습니다:")
print()
print("    python baseline/baseline.py")
sys.exit(0)
