# Wind Power Forecasting Course

2020~2024년 공개자료와 2025년 LDAPS 기상예보자료를 이용하여  
**2025년 전북권 시간별 풍력발전량을 예측**하는 수업용 프로젝트입니다.

이 README를 **위에서부터 순서대로** 따라 진행하면 설치 → Fork → Clone → 환경설정 → Baseline 실행 → 모델 개선 → 제출까지 완료할 수 있습니다.

---

# 0. 전체 진행 순서

```text
Anaconda / VS Code / Git 설치
        ↓
GitHub Repository Fork
        ↓
C:\wind-power-forecasting-course 로 Clone
        ↓
Conda 환경 생성
        ↓
VS Code PowerShell 사용
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
submission_info.json 수정
        ↓
git add prediction.csv submission_info.json
        ↓
Commit / Push
        ↓
Pull Request
        ↓
자동 검증 / 채점
        ↓
Leaderboard 확인
        ↓
Merge하지 않음
```

---

# 1. 과제 목표

- 예측 대상: **전북권 풍력발전량**
- 예측 기간: `2025-01-01 00:00` ~ `2025-12-31 23:00`
- 시간 해상도: 1시간
- 총 예측 시점: **8,760개**
- 평가 지표: **NMAE**
- 모델 및 특징변수 구성 방법: 자유

2025년 예측에서는 제공된 **2025 LDAPS 기상예보자료만** 사용할 수 있습니다.

2025년의 다음 정보는 학생에게 제공하지 않습니다.

- 실제 풍력발전량
- ASOS 관측자료
- 설비용량

2020~2024년 공개자료는 모델 학습 및 분석에 자유롭게 사용할 수 있습니다.

---

# 2. 사전 준비

수업 시작 전 다음 항목을 준비합니다.

- GitHub 계정
- Anaconda
- VS Code
- Git

## 2.1 GitHub 계정

GitHub 계정이 없는 경우 아래에서 계정을 생성합니다.

https://github.com/

---

## 2.2 Anaconda 설치

아래 공식 페이지에서 Windows용 Anaconda를 설치합니다.

https://www.anaconda.com/download

설치가 끝나면 Windows 시작 메뉴에서 **Anaconda Prompt**를 실행하고 다음 명령으로 설치를 확인합니다.

```powershell
conda --version
```

버전이 출력되면 정상입니다.

---

## 2.3 VS Code 설치

아래 공식 페이지에서 Visual Studio Code를 설치합니다.

https://code.visualstudio.com/

설치 후 VS Code의 **Extensions**에서 다음 확장을 설치합니다.

```text
Python
Publisher: Microsoft
```

Python Extension:

https://marketplace.visualstudio.com/items?itemName=ms-python.python

---

## 2.4 Git 설치

Git은 아래 두 방법 중 **하나만 선택**하여 설치하면 됩니다.

### 방법 A — PowerShell에서 설치

PowerShell을 실행하고 다음 명령을 입력합니다.

```powershell
winget install --id Git.Git -e --source winget
```

설치가 끝나면 PowerShell을 닫았다가 다시 실행한 뒤 확인합니다.

```powershell
git --version
```

### 방법 B — 공식 설치파일 사용

아래 Git 공식 페이지에서 **Git for Windows**를 설치합니다.

https://git-scm.com/install/windows

설치 후 PowerShell에서 확인합니다.

```powershell
git --version
```

> `winget` 명령을 사용할 수 없는 경우 방법 B를 사용합니다.

---

# 3. 강의자 Repository Fork

강의자 Repository:

https://github.com/Im-spec/wind-power-forecasting-course

1. 위 Repository에 접속합니다.
2. 오른쪽 상단의 **Fork**를 클릭합니다.
3. Owner가 **본인의 GitHub 계정**인지 확인합니다.
4. Repository name은 `wind-power-forecasting-course`를 그대로 사용합니다.
5. **Create fork**를 클릭합니다.

Fork가 완료되면 다음과 같이 본인 계정 아래에 Repository가 생성됩니다.

```text
https://github.com/<본인 GitHub ID>/wind-power-forecasting-course
```

학생은 이후 **본인의 Fork Repository에서 작업**합니다.

---

# 4. Fork Repository Clone

본인의 Fork Repository에서:

```text
Code → HTTPS → 주소 복사
```

을 선택합니다.

처음 설치 및 환경설정은 **Anaconda Prompt** 사용을 권장합니다.

Anaconda Prompt에서 다음 위치로 이동합니다.

```powershell
cd C:\
```

본인의 Fork 주소를 사용하여 Clone합니다.

```powershell
git clone https://github.com/<본인 GitHub ID>/wind-power-forecasting-course.git wind-power-forecasting-course
```

Clone이 끝나면 프로젝트 폴더로 이동합니다.

```powershell
cd C:\wind-power-forecasting-course
```

원격 Repository가 본인 Fork를 가리키는지 확인합니다.

```powershell
git remote -v
```

`origin`이 본인의 GitHub 계정을 가리키면 정상입니다.

> Windows 경로 문제를 줄이기 위해 바탕화면, 문서, OneDrive, 한글 또는 공백이 포함된 경로보다 `C:\wind-power-forecasting-course` 사용을 권장합니다.

---

# 5. Conda 환경 생성

Repository를 처음 Clone한 뒤 **최초 1회만** 실행합니다.

Anaconda Prompt에서:

```powershell
cd C:\wind-power-forecasting-course
conda env create -f environment.yml
```

환경이 생성되었는지 확인합니다.

```powershell
conda env list
```

목록에 다음 환경이 있어야 합니다.

```text
wind-forecast
```

공식 환경은 `environment.yml`에 정의되어 있으며 주요 버전은 다음과 같습니다.

- Python 3.11
- NumPy 1.26
- pandas 2.2
- scikit-learn 1.5
- LightGBM 4.5
- PyArrow 17
- Matplotlib 3.9
- xlrd 2.0

---

# 6. VS Code PowerShell에서 Conda 사용 설정

최초 1회 Anaconda Prompt에서 다음 명령을 실행합니다.

```powershell
conda init powershell
```

명령 실행 후 **VS Code와 PowerShell을 모두 닫았다가 다시 실행**합니다.

이후 프로젝트 폴더를 VS Code에서 엽니다.

```powershell
cd C:\wind-power-forecasting-course
code .
```

VS Code에서:

```text
Terminal → New Terminal
```

을 선택하면 PowerShell 터미널을 사용할 수 있습니다.

환경을 활성화합니다.

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

Python 3.11.x가 출력되면 정상입니다.

> 일반 PowerShell에서 `conda`를 찾을 수 없는 경우 Anaconda Prompt를 열어 `conda init powershell`을 다시 실행한 뒤 PowerShell을 재시작합니다.

---

# 7. VS Code Python Interpreter 설정

VS Code에서:

1. `Ctrl + Shift + P`
2. `Python: Select Interpreter`
3. `wind-forecast` 환경의 Python 선택

터미널에서도 다음 명령으로 확인할 수 있습니다.

```powershell
python --version
```

---

# 8. Repository 구조

초기 Repository 구조는 다음과 같습니다.

```text
wind-power-forecasting-course/
│
├─ README.md
├─ environment.yml
├─ requirements.txt
├─ .gitignore
├─ submission_info.json
│
├─ baseline/
│  ├─ baseline.py
│  ├─ baseline_prediction.csv
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
│  ├─ check_data.py
│  ├─ grade_submission.py
│  └─ publish_grading_result.py
│
├─ submission/
│  ├─ README.md
│  └─ sample_submission.csv
│
└─ .github/
   └─ workflows/
      ├─ collect-submission.yml
      └─ grade-submission.yml
```

> Repository 최상위의 `prediction.csv`는 처음부터 제공되지 않습니다. Baseline 또는 학생이 작성한 모델을 실행하여 직접 생성합니다.

`baseline/baseline_prediction.csv`는 Baseline 결과를 참고하기 위한 파일입니다.  
실제 제출 대상은 **Repository 최상위의 `prediction.csv`**입니다.

---

# 9. 환경 검증

VS Code PowerShell에서 다음 명령을 실행합니다.

```powershell
conda activate wind-forecast
python scripts/check_environment.py
```

정상적인 경우 마지막에 다음 메시지가 출력됩니다.

```text
[성공] 수업용 Python 환경이 정상입니다.
```

---

# 10. 데이터 검증

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

# 11. 제공 데이터

## 11.1 학습 및 분석용 데이터

```text
data/train/
├─ generation_jeonbuk_2020_2024.csv
├─ capacity_jeonbuk_2020_2024.csv
├─ asos_observation_2020_2024.parquet
└─ ldaps_2024.parquet
```

- `generation_jeonbuk_2020_2024.csv`: 2020~2024 전북권 시간별 풍력발전량
- `capacity_jeonbuk_2020_2024.csv`: 2020~2024 전북권 월별 설비용량
- `asos_observation_2020_2024.parquet`: 2020~2024 ASOS 관측자료
- `ldaps_2024.parquet`: 2024 LDAPS 기상예보자료

## 11.2 최종 예측용 데이터

```text
data/test/
└─ ldaps_2025.parquet
```

2025년에는 **LDAPS 기상예보자료만 공개**합니다.

2025년 실제 발전량, ASOS 관측자료 및 설비용량은 제공하지 않습니다.

## 11.3 정적 정보

```text
data/static/
├─ wind_turbine_location_jeonbuk.csv
└─ asos_station_info.xls
```

- 전북 지역 풍력기 위치정보
- ASOS 관측지점 메타정보

어떤 ASOS 지점을 사용할지, 몇 개의 관측소를 사용할지, 위치정보를 어떻게 활용할지는 자유입니다.

---

# 12. Baseline 구조

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

검증 방법은 **Leave-One-Year-Out Cross Validation**입니다.

한 연도를 검증자료로 제외하고 나머지 연도로 학습하는 과정을 반복합니다.

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

검증 방법은 **Leave-One-Month-Out Cross Validation**입니다.

각 검증월의 실제 ASOS 값은 해당 Fold의 Ridge fitting에 사용하지 않습니다.  
단, 해당 월의 LDAPS가 존재하는 모든 시간에 대해서는 ASOS 기상값을 예측합니다.

따라서 2024년에는:

```text
OOF 기상예측 = 8,784 / 8,784시간
```

을 생성합니다.

---

# 13. 2024 전체 파이프라인 검증

2024년 자료를 이용하여 실제 2025년 예측과 유사한 흐름을 검증합니다.

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

기상모델, 발전량모델, 지점선정, 격자선정, 특징변수, 보정방법 등은 학생이 자유롭게 개선할 수 있습니다.

---

# 14. Baseline 실행 및 2025 예측

2025년 최종 예측 흐름은 다음과 같습니다.

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

Baseline을 실행합니다.

```powershell
python baseline/baseline.py
```

정상적으로 실행되면 Repository 최상위에 다음 파일이 생성 또는 갱신됩니다.

```text
prediction.csv
```

정상적인 결과 파일은 **8,760행**을 가져야 합니다.

---

# 15. 모델 개선

`baseline/baseline.py`는 전체 파이프라인을 이해하기 위한 출발점입니다.

학생은 자신의 Fork Repository에서 자유롭게 코드를 수정하거나 새로운 파일을 추가할 수 있습니다.

예를 들어 다음과 같은 개선이 가능합니다.

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

단, **2025년 예측에는 제공된 2025 LDAPS 자료만 사용해야 합니다.**

---

# 16. 제출 파일 형식

채점 대상 예측 파일은 Repository 최상위의:

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
- 컬럼: `시간`, `발전량`
- 행 수: 8,760
- 시간 범위: `2025-01-01 00:00` ~ `2025-12-31 23:00`
- 시간 간격: 1시간
- 중복 시간 없음
- 결측값 없음
- 발전량은 숫자형
- 발전량은 0 이상

2025년 설비용량은 학생에게 제공하지 않으므로 상한값 clipping은 제출 조건으로 강제하지 않습니다.

---

# 17. 제출자 정보 입력

Repository 최상위의 `submission_info.json`을 수정합니다.

기본 형태:

```json
{
  "name": "홍길동",
  "model_name": "Baseline"
}
```

예를 들어:

```json
{
  "name": "김학생",
  "model_name": "LightGBM_v2"
}
```

- `name`: 학생 이름
- `model_name`: 이번 제출에 사용한 모델 이름

모델을 개선해 다시 제출하는 경우 `model_name`도 구분할 수 있도록 변경하는 것을 권장합니다.

---

# 18. 평가 지표

평가에는 NMAE를 사용합니다.

```math
\mathrm{NMAE}
=
\frac{1}{N}
\sum_{t=1}^{N}
\frac{\left|P_t-\hat{P}_t\right|}{C_t}
\times 100
```

- $P_t$: 실제 전북 풍력발전량
- $\hat{P}_t$: 예측 발전량
- $C_t$: 해당 시점의 실제 전북 설비용량
- $N = 8{,}760$: 평가시간 수

**NMAE가 낮을수록 좋은 모델입니다.**

2025년 실제 발전량과 설비용량은 채점용 비공개 자료로 사용합니다.

Public/Private Test를 별도로 나누지 않고 **2025년 전체 8,760시간**을 평가합니다.

---

# 19. Git 제출 방법

## 19.1 Git 사용자 정보 설정 — 최초 1회

Commit 시 사용자 정보가 설정되어 있지 않다는 오류가 발생하면 다음을 입력합니다.

```powershell
git config --global user.name "본인 GitHub 이름 또는 ID"
git config --global user.email "본인 GitHub 이메일"
```

확인:

```powershell
git config --global user.name
git config --global user.email
```

## 19.2 제출 파일 확인

```powershell
git status
```

## 19.3 제출 파일만 Stage에 추가

```powershell
git add prediction.csv submission_info.json
```

> 제출 시 `git add .` 사용은 권장하지 않습니다. 불필요한 코드, 데이터 또는 임시파일이 함께 Commit될 수 있습니다.

## 19.4 Commit

```powershell
git commit -m "Submit prediction"
```

## 19.5 본인의 Fork로 Push

```powershell
git push
```

처음 Push할 때 GitHub 로그인 또는 브라우저 인증이 요청될 수 있습니다.

---

# 20. Pull Request 생성

Push가 완료되면 GitHub의 **본인 Fork Repository**로 이동합니다.

일반적으로 다음과 같은 버튼이 표시됩니다.

```text
Contribute → Open pull request
```

또는:

```text
Compare & pull request
```

Pull Request의 방향이 다음과 같은지 확인합니다.

```text
base repository : Im-spec/wind-power-forecasting-course
base branch     : main

head repository : <본인 GitHub ID>/wind-power-forecasting-course
compare branch  : main
```

확인 후 **Create pull request**를 클릭합니다.

학생의 Pull Request는 제출 및 자동채점을 위한 용도로 사용하며 **강의자 Repository에 Merge하지 않습니다.**

```text
학생 Fork
    ↓
prediction.csv + submission_info.json
    ↓
Commit / Push
    ↓
Pull Request
    ↓
자동 검증 및 채점
    ↓
결과 확인
    ↓
Merge하지 않음
```

---

# 21. 모델을 개선하여 다시 제출하는 방법

이미 Pull Request를 만든 뒤 모델을 개선했다면 **새 Pull Request를 만들 필요가 없습니다.**

새로운 `prediction.csv`를 생성하고 `submission_info.json`의 `model_name`을 변경한 뒤:

```powershell
git add prediction.csv submission_info.json
git commit -m "Update prediction"
git push
```

하면 기존 Pull Request가 자동으로 갱신됩니다.

Push할 때마다 자동으로 다시 검증 및 채점됩니다.

---

# 22. 자동 검증 / 채점 / Leaderboard

자동채점 시스템은 학생의 프로그램을 실행하지 않고 제출된 다음 두 파일만 읽습니다.

```text
prediction.csv
submission_info.json
```

검증 대상은 다음과 같습니다.

- 파일 존재 여부
- 컬럼 이름
- 8,760행 여부
- 전체 시간 범위
- 1시간 간격
- 중복 시간
- 결측값
- 숫자형 발전량
- 음수 발전량

검증을 통과하면 2025년 비공개 실제자료를 이용하여 NMAE를 계산하고 결과를 Pull Request에 표시합니다.

Leaderboard에는 다음 정보를 표시합니다.

```text
순위 | 이름 | 모델명 | NMAE
```

학생별 최고 성능과 제출 이력을 확인할 수 있습니다.

자동검증, 자동채점 및 Leaderboard는 GitHub Actions로 운영됩니다.

---

# 23. 자주 사용하는 명령어

수업을 다시 시작할 때:

```powershell
cd C:\wind-power-forecasting-course
conda activate wind-forecast
```

환경 확인:

```powershell
python scripts/check_environment.py
```

데이터 확인:

```powershell
python scripts/check_data.py
```

Baseline 실행:

```powershell
python baseline/baseline.py
```

현재 Git 상태 확인:

```powershell
git status
```

제출:

```powershell
git add prediction.csv submission_info.json
git commit -m "Submit prediction"
git push
```

---

# 24. 핵심 규칙 요약

1. 2025년 예측에는 제공된 **2025 LDAPS 자료만** 사용합니다.
2. 모델 구조와 특징변수 구성은 자유입니다.
3. 최종 `prediction.csv`는 **8,760행**이어야 합니다.
4. `submission_info.json`에 본인 이름과 모델명을 입력합니다.
5. 제출 시 `prediction.csv`와 `submission_info.json`을 Commit / Push합니다.
6. 본인의 Fork에서 강의자 Repository로 Pull Request를 생성합니다.
7. 모델을 개선하면 같은 Pull Request에 계속 Push할 수 있습니다.
8. 학생 Pull Request는 **Merge하지 않습니다.**
