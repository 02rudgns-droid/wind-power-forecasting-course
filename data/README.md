# 데이터 안내

## 1. 학습 및 분석용 데이터

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
- `ldaps_2024.parquet`: 2024년 LDAPS 기상예보자료

학생은 공개된 과거자료의 활용 방법을 자유롭게 결정할 수 있습니다.

## 2. 최종 예측용 데이터

```text
data/test/
└─ ldaps_2025.parquet
```

2025년에는 **LDAPS 기상예보자료만 공개합니다.**

2025년 실제 풍력발전량, ASOS 관측자료 및 설비용량은 제공하지 않습니다.

## 3. 정적 정보

```text
data/static/
├─ wind_turbine_location_jeonbuk.csv
└─ asos_station_info.xls
```

- 전북 지역 풍력기 위치정보
- ASOS 관측지점 메타정보

어떤 ASOS 지점을 사용할지, 몇 개의 관측소를 결합할지, 위치정보를 사용할지 등은 학생이 판단합니다.

## 4. 시간 기준

발전량 파일의 `시간`은 해당 1시간 구간의 **시작시각**입니다.

예:

```text
2024-01-01 00:00 → 00:00~01:00 구간
```
