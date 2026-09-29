"""
Baseline: LDAPS -> ASOS -> Wind Power

Stage 1 (2020~2023)
- 실제 ASOS 5개 지점 관측기상 -> 전북 풍력발전량
- LightGBM
- Leave-One-Year-Out CV
- 최종 발전량 모델은 2020~2023 전체 자료로 학습

Stage 2 (2024)
- 2024 LDAPS -> 2024 ASOS 관측기상
- 각 ASOS 지점의 최근접 LDAPS 격자(격자순위 == 1) 사용
- 기상변수별 StandardScaler + Ridge
- Leave-One-Month-Out CV
- 해당 월의 실제 ASOS 값은 해당 월 Ridge fitting에 사용하지 않음
- 다만 해당 월의 LDAPS 전체 시간에 대해서는 ASOS 기상값을 예측함
- 최종 기상모델은 2024 전체 자료로 학습

2024 전체 파이프라인 검증
- 2024 LDAPS
  -> 월별 OOF 기상모델(Ridge)
  -> 추정 ASOS
  -> 발전량모델(LightGBM)
  -> 2024 발전량 예측
- 발전량 보정모델은 사용하지 않음

2025 최종 예측
- 2025 LDAPS
  -> 2024 전체로 학습한 기상모델(Ridge)
  -> 추정 ASOS
  -> 2020~2023으로 학습한 발전량모델(LightGBM)
  -> prediction.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]

OBS_PATH = ROOT / "data" / "train" / "asos_observation_2020_2024.parquet"
GEN_PATH = ROOT / "data" / "train" / "generation_jeonbuk_2020_2024.csv"
CAPACITY_PATH = ROOT / "data" / "train" / "capacity_jeonbuk_2020_2024.csv"
LDAPS_2024_PATH = ROOT / "data" / "train" / "ldaps_2024.parquet"
LDAPS_2025_PATH = ROOT / "data" / "test" / "ldaps_2025.parquet"
OUTPUT_PATH = ROOT / "prediction.csv"

SELECTED_STATIONS = ["군산", "부안", "정읍", "전주", "임실"]

OBS_FEATURES = [
    "u_ms",
    "v_ms",
    "풍속_ms",
    "기온_C",
    "습도_pct",
    "현지기압_hPa",
]

LDAPS_FEATURES = [
    "u_ms",
    "v_ms",
    "기온_C",
    "습도_pct",
    "기압_hPa",
]

RIDGE_TARGETS = [
    "u_ms",
    "v_ms",
    "기온_C",
    "습도_pct",
    "현지기압_hPa",
]

RANDOM_STATE = 42


def check_required_columns(df, required, name):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"[{name}] 필요한 컬럼이 없습니다: {missing}\n"
            f"현재 컬럼: {list(df.columns)}"
        )


def check_stations(df, name):
    stations = set(df["지점명"].dropna().astype(str).unique())
    missing = [s for s in SELECTED_STATIONS if s not in stations]
    if missing:
        raise ValueError(
            f"[{name}] 다음 지점을 찾을 수 없습니다: {missing}\n"
            "SELECTED_STATIONS를 데이터에 존재하는 지점명으로 수정하세요."
        )


def nmae(y_true, y_pred, capacity):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if np.isscalar(capacity):
        capacity = np.full(len(y_true), float(capacity))
    else:
        capacity = np.asarray(capacity, dtype=float)

    return np.mean(np.abs(y_true - y_pred) / capacity) * 100.0


def load_reference_capacity():
    capacity = pd.read_csv(CAPACITY_PATH, encoding="utf-8-sig")
    check_required_columns(capacity, ["연월", "설비용량_mw"], "capacity")

    mask_2024 = capacity["연월"].astype(str).str.startswith("2024")
    values = capacity.loc[mask_2024, "설비용량_mw"].astype(float)

    if len(values) == 0:
        raise ValueError("2024년 설비용량을 찾을 수 없습니다.")

    return float(values.mean())


# =========================================================
# Stage 1 (2020~2023): ASOS -> 발전량
# =========================================================

def make_asos_wide(obs):
    check_required_columns(obs, ["지점명", "일시"] + OBS_FEATURES, "ASOS")
    check_stations(obs, "ASOS")

    obs = obs[obs["지점명"].isin(SELECTED_STATIONS)].copy()
    obs["일시"] = pd.to_datetime(obs["일시"])

    wide = obs.pivot_table(
        index="일시",
        columns="지점명",
        values=OBS_FEATURES,
        aggfunc="mean",
    )

    wide.columns = [f"{station}_{variable}" for variable, station in wide.columns]

    expected_columns = [
        f"{station}_{variable}"
        for station in SELECTED_STATIONS
        for variable in OBS_FEATURES
    ]

    return wide.reindex(columns=expected_columns).sort_index()


def load_generation():
    generation = pd.read_csv(GEN_PATH, encoding="utf-8-sig")
    check_required_columns(generation, ["시간", "발전량"], "generation")

    generation["시간"] = pd.to_datetime(generation["시간"])
    generation["발전량"] = pd.to_numeric(generation["발전량"], errors="coerce")
    return generation


def build_stage1_dataset(obs_wide, generation):
    generation = generation.set_index("시간")

    df = obs_wide.join(generation[["발전량"]], how="inner")
    df = df[(df.index >= "2020-01-01") & (df.index < "2024-01-01")].copy()
    df = df.dropna()

    feature_columns = list(obs_wide.columns)
    return df[feature_columns], df["발전량"], feature_columns


def stage1_year_cv(X, y, capacity):
    years = X.index.year
    scores = []

    print("\n" + "=" * 72)
    print("Stage 1 (2020~2023): 실제 ASOS 관측기상 -> 전북 풍력발전량")
    print("검증 방법: Leave-One-Year-Out CV / 모델: LightGBM")
    print("=" * 72)

    for valid_year in sorted(np.unique(years)):
        train_mask = years != valid_year
        valid_mask = years == valid_year

        model = LGBMRegressor(
            n_estimators=400,
            learning_rate=0.05,
            num_leaves=31,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            verbosity=-1,
        )
        model.fit(X.loc[train_mask], y.loc[train_mask])

        pred = np.clip(model.predict(X.loc[valid_mask]), 0, None)
        score = nmae(y.loc[valid_mask], pred, capacity)
        scores.append(score)

        print(
            f"검증연도 {valid_year}: "
            f"NMAE = {score:.4f}% "
            f"(평가시간={valid_mask.sum():,})"
        )

    print(f"Stage 1 CV 평균 NMAE = {np.mean(scores):.4f}%")
    return scores


def train_stage1_final(X, y):
    model = LGBMRegressor(
        n_estimators=400,
        learning_rate=0.05,
        num_leaves=31,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbosity=-1,
    )
    model.fit(X, y)
    return model


# =========================================================
# Stage 2 (2024): LDAPS -> ASOS
# =========================================================

def prepare_ldaps(ldaps):
    check_required_columns(
        ldaps,
        ["지점명", "격자순위", "유효시각_kst"] + LDAPS_FEATURES,
        "LDAPS",
    )
    check_stations(ldaps, "LDAPS")

    ldaps = ldaps[ldaps["지점명"].isin(SELECTED_STATIONS)].copy()
    ldaps = ldaps[pd.to_numeric(ldaps["격자순위"], errors="coerce") == 1].copy()
    ldaps["유효시각_kst"] = pd.to_datetime(ldaps["유효시각_kst"])

    return (
        ldaps.groupby(["지점명", "유효시각_kst"], as_index=False)[LDAPS_FEATURES]
        .mean()
    )


def get_station_obs_2024(obs, station):
    station_obs = obs[obs["지점명"] == station].copy()
    station_obs["일시"] = pd.to_datetime(station_obs["일시"])
    station_obs = station_obs[
        (station_obs["일시"] >= "2024-01-01")
        & (station_obs["일시"] < "2025-01-01")
    ].copy()

    keep = ["일시", "u_ms", "v_ms", "기온_C", "습도_pct", "현지기압_hPa"]
    station_obs = station_obs[keep].groupby("일시", as_index=False).mean()

    return station_obs.rename(
        columns={c: f"asos_{c}" for c in RIDGE_TARGETS}
    )


def get_station_ldaps(ldaps, station):
    station_ldaps = ldaps[ldaps["지점명"] == station].copy()
    station_ldaps = station_ldaps.rename(columns={"유효시각_kst": "일시"})
    station_ldaps = station_ldaps[["일시"] + LDAPS_FEATURES]

    return station_ldaps.rename(
        columns={c: f"ldaps_{c}" for c in LDAPS_FEATURES}
    )


def make_ridge():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("ridge", Ridge(alpha=1.0)),
    ])


def stage2_fit_station(station, obs_2024, ldaps_2024, ldaps_2025):
    obs_station = get_station_obs_2024(obs_2024, station)
    ldaps_train = get_station_ldaps(ldaps_2024, station).sort_values("일시").reset_index(drop=True)
    ldaps_test = get_station_ldaps(ldaps_2025, station).sort_values("일시").reset_index(drop=True)

    X_columns = [f"ldaps_{c}" for c in LDAPS_FEATURES]

    # LDAPS 전체 시간을 기준으로 ASOS를 LEFT JOIN한다.
    # ASOS 결측은 Ridge fitting/MAE 계산에는 제외하지만,
    # OOF 기상 예측 자체는 해당 월의 LDAPS 전체 시간에 대해 생성한다.
    train = ldaps_train.merge(obs_station, on="일시", how="left")
    train = train.sort_values("일시").reset_index(drop=True)

    if len(train) != 8784:
        raise ValueError(
            f"{station}: 2024 LDAPS 시간 수가 8,784개가 아닙니다: {len(train):,}"
        )

    if len(ldaps_test) != 8760:
        raise ValueError(
            f"{station}: 2025 LDAPS 시간 수가 8,760개가 아닙니다: {len(ldaps_test):,}"
        )

    if train[X_columns].isna().any().any():
        bad = int(train[X_columns].isna().any(axis=1).sum())
        raise ValueError(
            f"{station}: 2024 LDAPS 입력변수에 결측이 있습니다. "
            f"결측 시간 수: {bad}"
        )

    if ldaps_test[X_columns].isna().any().any():
        bad = int(ldaps_test[X_columns].isna().any(axis=1).sum())
        raise ValueError(
            f"{station}: 2025 LDAPS 입력변수에 결측이 있습니다. "
            f"결측 시간 수: {bad}"
        )

    oof = pd.DataFrame({"일시": train["일시"].copy()})
    test_prediction = pd.DataFrame({"일시": ldaps_test["일시"].copy()})

    print("\n" + "-" * 72)
    print(f"[{station}]")
    print("-" * 72)

    month_all = train["일시"].dt.month

    for target in RIDGE_TARGETS:
        y_col = f"asos_{target}"
        fit_available = train[y_col].notna()

        oof_target = pd.Series(np.nan, index=train.index, dtype=float)
        fold_mae = []
        eval_count = 0

        for valid_month in range(1, 13):
            train_rows = fit_available & (month_all != valid_month)
            predict_rows = month_all == valid_month

            if train_rows.sum() == 0 or predict_rows.sum() == 0:
                continue

            model = make_ridge()
            model.fit(
                train.loc[train_rows, X_columns],
                train.loc[train_rows, y_col],
            )

            pred_all = model.predict(train.loc[predict_rows, X_columns])
            oof_target.loc[predict_rows] = pred_all

            eval_rows = predict_rows & fit_available
            if eval_rows.sum() > 0:
                pred_eval = oof_target.loc[eval_rows]
                fold_mae.append(
                    mean_absolute_error(
                        train.loc[eval_rows, y_col],
                        pred_eval,
                    )
                )
                eval_count += int(eval_rows.sum())

        if oof_target.isna().any():
            missing = int(oof_target.isna().sum())
            raise ValueError(
                f"{station} {target}: 2024 OOF 기상예측에 "
                f"{missing}개 결측이 남았습니다."
            )

        oof[target] = oof_target.values

        mean_mae = np.mean(fold_mae) if fold_mae else np.nan
        print(
            f"{target:>12s}: "
            f"12개월 OOF MAE = {mean_mae:.4f} | "
            f"OOF 예측={oof_target.notna().sum():,}/8,784 | "
            f"MAE 평가={eval_count:,}"
        )

        final_model = make_ridge()
        final_model.fit(
            train.loc[fit_available, X_columns],
            train.loc[fit_available, y_col],
        )

        test_prediction[target] = final_model.predict(ldaps_test[X_columns])

    oof["풍속_ms"] = np.sqrt(oof["u_ms"] ** 2 + oof["v_ms"] ** 2)
    test_prediction["풍속_ms"] = np.sqrt(
        test_prediction["u_ms"] ** 2 + test_prediction["v_ms"] ** 2
    )

    return oof, test_prediction


def combine_estimated_stations(station_predictions):
    frames = []

    for station, df in station_predictions.items():
        temp = df.copy().set_index("일시")
        temp = temp[OBS_FEATURES]
        temp.columns = [f"{station}_{col}" for col in temp.columns]
        frames.append(temp)

    result = pd.concat(frames, axis=1, join="outer").sort_index()

    expected_columns = [
        f"{station}_{variable}"
        for station in SELECTED_STATIONS
        for variable in OBS_FEATURES
    ]
    return result.reindex(columns=expected_columns)


def main():
    print("데이터 로딩 중...")

    obs = pd.read_parquet(OBS_PATH)
    ldaps_2024_raw = pd.read_parquet(LDAPS_2024_PATH)
    ldaps_2025_raw = pd.read_parquet(LDAPS_2025_PATH)
    generation = load_generation()
    capacity = load_reference_capacity()

    obs_wide = make_asos_wide(obs)
    X_stage1, y_stage1, feature_columns = build_stage1_dataset(obs_wide, generation)

    stage1_year_cv(X_stage1, y_stage1, capacity)

    print(
        "\nStage 1 최종모델 학습: "
        "2020~2023 실제 ASOS 관측기상 + 전북 발전량 전체 사용"
    )
    stage1_model = train_stage1_final(X_stage1, y_stage1)

    print("\n" + "=" * 72)
    print("Stage 2 (2024): LDAPS -> ASOS 기상모델")
    print("검증 방법: Leave-One-Month-Out CV / 모델: StandardScaler + Ridge")
    print(
        "각 검증월의 실제 ASOS는 Ridge fitting에 사용하지 않고, "
        "해당 월 LDAPS 전체 시간에 대해 기상을 예측"
    )
    print("=" * 72)

    ldaps_2024 = prepare_ldaps(ldaps_2024_raw)
    ldaps_2025 = prepare_ldaps(ldaps_2025_raw)

    oof_2024_by_station = {}
    test_2025_by_station = {}

    for station in SELECTED_STATIONS:
        oof_2024, pred_2025 = stage2_fit_station(
            station=station,
            obs_2024=obs,
            ldaps_2024=ldaps_2024,
            ldaps_2025=ldaps_2025,
        )
        oof_2024_by_station[station] = oof_2024
        test_2025_by_station[station] = pred_2025

    print("\n" + "=" * 72)
    print("[2024 전체 파이프라인 검증]")
    print(
        "2024 LDAPS -> 기상모델(Ridge) -> 추정 ASOS "
        "-> 발전량모델(LightGBM) -> 전북 풍력발전량 예측"
    )
    print("=" * 72)

    estimated_asos_2024 = combine_estimated_stations(oof_2024_by_station)

    expected_2024 = pd.date_range(
        "2024-01-01 00:00",
        "2024-12-31 23:00",
        freq="h",
    )
    estimated_asos_2024 = estimated_asos_2024.reindex(expected_2024)

    if estimated_asos_2024.isna().any().any():
        missing_rows = int(estimated_asos_2024.isna().any(axis=1).sum())
        raise ValueError(
            f"2024 추정 ASOS Feature에 결측이 있습니다. "
            f"결측 시간 수: {missing_rows}"
        )

    gen_2024 = generation[
        (generation["시간"] >= "2024-01-01")
        & (generation["시간"] < "2025-01-01")
    ].copy().set_index("시간")

    validation_2024 = estimated_asos_2024.join(
        gen_2024[["발전량"]],
        how="left",
    )

    if validation_2024["발전량"].isna().any():
        missing = int(validation_2024["발전량"].isna().sum())
        raise ValueError(
            f"2024 실제 발전량에 결측이 있습니다. 결측 시간 수: {missing}"
        )

    if len(validation_2024) != 8784:
        raise ValueError(
            f"2024 전체 파이프라인 검증 시간 수가 "
            f"8,784개가 아닙니다: {len(validation_2024):,}"
        )

    pred_2024 = np.clip(
        stage1_model.predict(validation_2024[feature_columns]),
        0,
        None,
    )

    score_2024 = nmae(
        validation_2024["발전량"],
        pred_2024,
        capacity,
    )

    print(
        f"2024 전체 파이프라인 NMAE = {score_2024:.4f}% "
        f"(평가시간={len(validation_2024):,}/8,784)"
    )

    print("\n" + "=" * 72)
    print("[2025 최종 예측]")
    print(
        "2025 LDAPS -> 2024 전체로 학습한 기상모델(Ridge) "
        "-> 추정 ASOS -> 2020~2023으로 학습한 발전량모델(LightGBM) "
        "-> 전북 풍력발전량 예측"
    )
    print("=" * 72)

    estimated_asos_2025 = combine_estimated_stations(test_2025_by_station)

    expected_2025 = pd.date_range(
        "2025-01-01 00:00",
        "2025-12-31 23:00",
        freq="h",
    )
    estimated_asos_2025 = estimated_asos_2025.reindex(expected_2025)

    if estimated_asos_2025.isna().any().any():
        missing_rows = int(estimated_asos_2025.isna().any(axis=1).sum())
        raise ValueError(
            f"2025 추정 ASOS Feature에 결측이 있습니다. "
            f"결측 시간 수: {missing_rows}"
        )

    prediction = np.clip(
        stage1_model.predict(estimated_asos_2025[feature_columns]),
        0,
        None,
    )

    submission = pd.DataFrame({
        "시간": expected_2025.strftime("%Y-%m-%d %H:%M"),
        "발전량": prediction,
    })

    if len(submission) != 8760:
        raise ValueError(
            f"제출 행 수가 8,760개가 아닙니다: {len(submission):,}"
        )

    submission.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 72)
    print("Baseline 실행 완료")
    print(f"prediction.csv 생성: {OUTPUT_PATH}")
    print(f"행 수: {len(submission):,}/8,760")
    print("=" * 72)


if __name__ == "__main__":
    main()
