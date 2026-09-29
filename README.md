# Wind Power Forecasting Course

2020~2024년 공개자료와 2025년 LDAPS 기상예보자료를 이용하여  
**2025년 전북권 시간별 풍력발전량을 예측**하는 수업용 프로젝트입니다.

---

# 1. 과제 목표

- 예측 대상: 전북권 풍력발전량
- 예측 기간: `2025-01-01 00:00` ~ `2025-12-31 23:00`
- 시간 해상도: 1시간
- 총 예측 시점: 8,760개
- 평가 지표: NMAE
- 모델 및 특징변수 구성 방법: 자유

2025년 예측에서는 제공된 **LDAPS 기상예보자료만** 사용할 수 있습니다.

2025년의 다음 정보는 학생에게 제공하지 않습니다.

- 실제 풍력발전량
- ASOS 관측자료
- 설비용량

2020~2024년 공개자료는 모델 학습 및 분석에 자유롭게 사용할 수 있습니다.

---

# 2. 시작하기 전에

Anaconda, Git, VS Code 설치와 GitHub Fork/Clone 과정은  
별도로 제공되는 **초기 설치 가이드**를 따라 진행합니다.

본 README는 Repository가 다음 위치에 Clone되어 있다고 가정합니다.

```text
C:\wind-power-forecasting-course
```

Windows 경로 문제를 줄이기 위해 바탕화면, 문서, OneDrive, 한글 경로는 사용하지 않는 것을 권장합니다.

---

# 3. Repository 구조

```text
wind-power-forecasting-course/
│
├─ README.md
├─ environment.yml
├─ requirements.txt
├─ .gitignore
├─ prediction.csv
│
├─ baseline/
│  ├─ baseline.py
│  └─ README.md
│
├─ data/
│  ├─ README.md
│  │
│  ├─ train/
│  │  ├─ asos_observation_2020_2024.parquet
│  │  ├─ capacity_jeonbuk_2020_2024.csv
│  │  ├─ generation_jeonbuk_2020_2024.csv
│  │  └─ ldaps_2024.parquet
│  │
│  ├─ test/
│  │  └─ ldaps_2025.parquet
│  │
│  └─ static/
│     ├─ asos_station_info.xls
│     └─ wind_turbine_location_jeonbuk.csv
│
├─ scripts/
│  ├─ check_environment.py
│  └─ check_data.py
│
├─ submission/
│  ├─ README.md
│  └─ sample_submission.csv
│
└─ .github/
   └─ workflows/
```

---

# 4. Conda 환경 생성

Repository를 처음 Clone한 뒤 **최초 1회만** 실행합니다.

VS Code 또는 Anaconda Prompt에서 프로젝트 폴더로 이동합니다.

```powershell
cd C:\wind-power-forecasting-course
```

Conda 환경을 생성합니다.

```powershell
conda env create -f environment.yml
```

생성된 환경을 확인합니다.

```powershell
conda env list
```

목록에 다음 환경이 있어야 합니다.

```text
wind-forecast
```

---

# 5. 수업 시작 시 환경 활성화

두 번째 실행부터는 환경을 다시 만들 필요가 없습니다.

VS Code에서 Repository를 열고 PowerShell 터미널에서 다음 명령을 실행합니다.

```powershell
conda activate wind-forecast
```

정상적으로 활성화되면 다음과 같이 표시됩니다.

```text
(wind-forecast) PS C:\wind-power-forecasting-course>
```

Python 버전을 확인합니다.

```powershell
python --version
```

정상 환경에서는 Python 3.11.x가 출력됩니다.

---

# 6. 환경 검증

다음 명령을 실행합니다.

```powershell
python scripts/check_environment.py
```

정상적인 경우 마지막에 다음 메시지가 출력됩니다.

```text
[성공] 수업용 Python 환경이 정상입니다.
```

공식 Baseline 환경은 다음과 같습니다.

- Python 3.11
- NumPy 1.26
- pandas 2.2
- scikit-learn 1.5
- LightGBM 4.5
- PyArrow 17
- Matplotlib 3.9
- xlrd 2.0

---

# 7. 데이터 검증

다음 명령을 실행합니다.

```powershell
python scripts/check_data.py
```

검증 항목은 다음과 같습니다.

- 필수 파일 존재 여부
- 전북 발전량 데이터 기간 및 행 수
- 전북 설비용량 데이터
- ASOS 자료
- Baseline ASOS 5개 지점
- 2024 LDAPS
- 2025 LDAPS
- 필수 기상변수
- 최근접 LDAPS 격자
- 시간 범위

정상적인 경우 마지막에 다음 메시지가 출력됩니다.

```text
[성공] 수업용 데이터 검증을 모두 통과했습니다.
```

---

# 8. Baseline 구조

Baseline은 두 개의 모델을 연결하여 2025년 발전량을 예측합니다.

## Stage 1 — 2020~2023 ASOS → 발전량

```text
2020~2023 실제 ASOS 관측기상
            ↓
         LightGBM
            ↓
    전북 풍력발전량
```

Baseline에서는 다음 ASOS 5개 지점을 사용합니다.

```text
군산
부안
정읍
전주
임실
```

검증 방법:

```text
Leave-One-Year-Out Cross Validation
```

즉 한 연도를 검증자료로 제외하고 나머지 연도로 학습하는 과정을 반복합니다.

---

## Stage 2 — 2024 LDAPS → ASOS 기상모델

```text
2024 LDAPS
     ↓
StandardScaler + Ridge
     ↓
2024 ASOS 기상값 추정
```

각 ASOS 지점에서 가장 가까운 LDAPS 격자인:

```text
격자순위 = 1
```

을 사용합니다.

검증 방법:

```text
Leave-One-Month-Out Cross Validation
```

각 검증월의 실제 ASOS 값은 해당 Fold의 Ridge fitting에 사용하지 않습니다.

단, 해당 월의 LDAPS가 존재하는 모든 시간에 대해서는 ASOS 기상값을 예측합니다.

따라서 2024년에는:

```text
OOF 기상예측 = 8,784 / 8,784시간
```

을 생성합니다.

---

# 9. 2024 전체 파이프라인 검증

2024년 자료를 이용하여 실제 2025년 예측과 동일한 흐름을 검증합니다.

```text
2024 LDAPS
    ↓
기상모델(Ridge)
    ↓
추정 ASOS
    ↓
발전량모델(LightGBM)
    ↓
2024 전북 풍력발전량 예측
    ↓
실제 2024 발전량과 비교
```

Baseline에서는 별도의 발전량 오차보정 모델을 적용하지 않습니다.

이 부분을 포함하여 기상모델, 발전량모델, 지점선정, 격자선정, 특징변수, 보정방법 등은 학생이 자유롭게 개선할 수 있습니다.

---

# 10. 2025 최종 예측

최종 예측은 다음 흐름으로 수행됩니다.

```text
2025 LDAPS
    ↓
2024 전체자료로 학습한 기상모델(Ridge)
    ↓
2025 ASOS 기상값 추정
    ↓
2020~2023으로 학습한 발전량모델(LightGBM)
    ↓
2025 전북 풍력발전량 예측
```

Baseline 실행:

```powershell
python baseline/baseline.py
```

정상적으로 실행되면 Repository 최상위에 다음 파일이 생성 또는 갱신됩니다.

```text
prediction.csv
```

정상적인 결과 파일은 8,760행을 가져야 합니다.

---

# 11. 제출 파일 형식

채점 대상 파일은 Repository 최상위의:

```text
prediction.csv
```

입니다.

컬럼은 반드시 다음 두 개만 사용합니다.

```text
시간,발전량
```

예:

```csv
시간,발전량
2025-01-01 00:00,10.25
2025-01-01 01:00,11.03
2025-01-01 02:00,9.84
```

제출 조건:

- 파일명: `prediction.csv`
- 행 수: 8,760
- 시간 범위: `2025-01-01 00:00` ~ `2025-12-31 23:00`
- 시간 간격: 1시간
- 중복 시간 없음
- 결측값 없음
- 발전량은 숫자형
- 발전량은 0 이상

2025년 설비용량은 학생에게 제공하지 않으므로 상한값 clipping은 제출 조건으로 강제하지 않습니다.

---

# 12. 평가 지표

평가에는 NMAE를 사용합니다.

$$
\mathrm{NMAE}
=
\frac{1}{N}
\sum_{t=1}^{N}
\frac{|P_t-\hat{P}_t|}{C_t}
\times 100
$$

- $P_t$: 실제 전북 풍력발전량
- $\hat{P}_t$: 예측 발전량
- $C_t$: 해당 시점의 실제 전북 설비용량
- $N$: 평가시간 수

**NMAE가 낮을수록 좋은 모델입니다.**

2025년 실제 발전량과 설비용량은 채점용 비공개 자료로 사용합니다.

---

# 13. 모델 개선

제공된 `baseline/baseline.py`는 출발점입니다.

학생은 자신의 Fork Repository에서 자유롭게 코드를 수정하거나 새로운 파일을 추가할 수 있습니다.

예를 들어 다음을 개선할 수 있습니다.

- ASOS 지점 선택
- LDAPS 격자 선택
- 여러 LDAPS 격자 활용
- 기상 특징변수 구성
- LDAPS 예보편향 보정
- 기상모델 변경
- LightGBM 하이퍼파라미터 조정
- 다른 발전량 예측모델 사용
- Ensemble
- 발전량 오차보정
- End-to-End 모델 구성

모델 구조에는 제한을 두지 않습니다.

단, 2025년 예측에는 제공된 2025 LDAPS 자료만 사용해야 합니다.

---

# 14. Git 제출 방법

모델 개발 후 `prediction.csv`를 생성합니다.

먼저 변경사항을 확인합니다.

```powershell
git status
```

**제출 파일만 Stage에 올립니다.**

```powershell
git add prediction.csv
```

> 제출 시 `git add .` 사용을 권장하지 않습니다.  
> 다른 코드나 데이터 파일이 함께 Commit될 수 있습니다.

Commit:

```powershell
git commit -m "Submit prediction"
```

본인의 GitHub Fork Repository로 Push:

```powershell
git push
```

그 후 본인의 Fork에서 강의자 Repository로 **Pull Request**를 생성합니다.

---

# 15. Pull Request 운영 방식

Pull Request는 **제출 및 자동채점을 위한 용도**로 사용합니다.

학생의 Pull Request는 강의자 Repository에 Merge하지 않습니다.

```text
학생 Fork
    ↓
prediction.csv 수정
    ↓
git add prediction.csv
    ↓
Commit / Push
    ↓
Pull Request
    ↓
자동 검증 및 채점
    ↓
점수 확인
    ↓
Merge하지 않음
```

따라서 학생의 제출물이 강의자 원본 Repository를 덮어쓰지 않습니다.

> Pull Request 자동검증 및 자동채점 기능은 이후 GitHub Actions를 통해 추가할 예정입니다.

---

# 16. 전체 진행 순서

```text
초기 설치 가이드
        ↓
Anaconda / Git / VS Code 설치
        ↓
GitHub Fork
        ↓
C:\wind-power-forecasting-course 로 Clone
        ↓
Conda 환경 생성
        ↓
VS Code PowerShell
        ↓
conda activate wind-forecast
        ↓
환경 검증
        ↓
데이터 검증
        ↓
Baseline 실행
        ↓
모델 개선
        ↓
prediction.csv 생성
        ↓
git add prediction.csv
        ↓
Commit / Push
        ↓
Pull Request
        ↓
자동 검증 / 채점
        ↓
Merge하지 않음
```
