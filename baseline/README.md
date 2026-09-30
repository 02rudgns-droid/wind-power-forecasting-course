# Baseline 모델

본 Baseline은 최적 성능을 목표로 하는 완성형 모델이 아니라, 전체 풍력발전량 예측 파이프라인을 이해하기 위한 기준 모델이다.

## 전체 구조

```text
2020~2023 ASOS
      ↓
  LightGBM
      ↓
발전량 관계 학습

2024 LDAPS
      ↓
StandardScaler + Ridge
      ↓
2024 ASOS 추정
      ↓
2024 End-to-End 검증

2025 LDAPS
      ↓
StandardScaler + Ridge
      ↓
2025 ASOS 추정
      ↓
  LightGBM
      ↓
2025 전북 풍력발전량
      ↓
prediction.csv
```

## Stage 1. 기상관측 → 발전량

Baseline에서는 다음 전북 ASOS 5개 지점을 사용한다.

- 군산
- 부안
- 정읍
- 전주
- 임실

각 지점에서 다음 변수를 사용한다.

- `u_ms`
- `v_ms`
- `풍속_ms`
- `기온_C`
- `습도_pct`
- `현지기압_hPa`

2020~2023 자료를 이용하여 LightGBM을 학습한다.

검증은 Leave-One-Year-Out 4-Fold CV를 사용한다.

```text
Fold 1: 2021~2023 학습 / 2020 검증
Fold 2: 2020, 2022, 2023 학습 / 2021 검증
Fold 3: 2020, 2021, 2023 학습 / 2022 검증
Fold 4: 2020~2022 학습 / 2023 검증
```

## Stage 2. LDAPS → 기상관측

각 ASOS 지점에 대해 `격자순위 == 1`인 가장 가까운 LDAPS 격자 하나를 사용한다.

LDAPS 입력변수는 다음과 같다.

- `u_ms`
- `v_ms`
- `기온_C`
- `습도_pct`
- `기압_hPa`

각 ASOS 변수별로 다음 파이프라인을 학습한다.

```text
StandardScaler
      ↓
Ridge Regression
```

검증은 2024년을 대상으로 Leave-One-Month-Out 12-Fold CV를 사용한다.

`풍속_ms`는 별도 Ridge로 예측하지 않고 추정된 `u_ms`, `v_ms`에서 계산한다.

```math
WS = \sqrt{u^2 + v^2}
```

## Stage 3. 별도 보정 없음

Baseline에서는 LDAPS → ASOS 과정의 오차가 최종 발전량 예측으로 전달되는 문제를 별도로 보정하지 않는다.

2024년 OOF 기상추정값을 LightGBM에 입력하여 End-to-End NMAE만 확인한다.

이 부분은 학생이 개선할 수 있는 영역으로 남겨둔다.

예를 들어 다음과 같은 개선이 가능하다.

- ASOS 지점 선정 변경
- 최근접 LDAPS 1개 대신 여러 격자 활용
- LDAPS bias correction
- Ridge 이외의 기상 보정모델
- 2024 발전량을 활용한 최종 잔차 보정
- LightGBM 개선
- Ensemble
- End-to-End 모델링

## 실행

먼저 공식 Conda 환경을 활성화한다.

```powershell
conda activate wind-forecast
python baseline/baseline.py
```

실행이 끝나면 저장소 루트에 `prediction.csv`가 생성된다.
