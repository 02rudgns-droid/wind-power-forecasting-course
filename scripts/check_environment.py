"""
수업용 Python/라이브러리 환경 검증 스크립트

실행:
    python scripts/check_environment.py

정상일 경우 exit code 0,
문제가 있을 경우 exit code 1을 반환합니다.
"""

import sys
import importlib


def version_tuple(version: str):
    nums = []
    for part in version.split("."):
        digits = ""
        for ch in part:
            if ch.isdigit():
                digits += ch
            else:
                break
        if digits:
            nums.append(int(digits))
        else:
            break
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])


def in_range(version, minimum, maximum):
    v = version_tuple(version)
    return version_tuple(minimum) <= v < version_tuple(maximum)


checks = [
    ("numpy", "numpy", "1.26", "2.0"),
    ("pandas", "pandas", "2.2", "2.3"),
    ("scikit-learn", "sklearn", "1.5", "1.6"),
    ("LightGBM", "lightgbm", "4.5", "4.6"),
    ("PyArrow", "pyarrow", "17.0", "18.0"),
    ("Matplotlib", "matplotlib", "3.9", "3.10"),
    ("xlrd", "xlrd", "2.0", "2.1"),
]

errors = []

print("=" * 64)
print("Wind Power Forecasting Course - 환경 검증")
print("=" * 64)

py = sys.version_info
python_ok = (py.major, py.minor) == (3, 11)

if python_ok:
    print(f"[OK]   Python {py.major}.{py.minor}.{py.micro}")
else:
    print(
        f"[FAIL] Python {py.major}.{py.minor}.{py.micro} "
        "(필요: Python 3.11.x)"
    )
    errors.append("Python 버전")

for label, module_name, min_v, max_v in checks:
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "unknown")

        if version == "unknown":
            print(f"[WARN] {label}: 버전 확인 불가")
            continue

        if in_range(version, min_v, max_v):
            print(f"[OK]   {label}: {version}")
        else:
            print(
                f"[FAIL] {label}: {version} "
                f"(필요: >= {min_v}, < {max_v})"
            )
            errors.append(label)

    except Exception as e:
        print(f"[FAIL] {label}: import 실패 ({e})")
        errors.append(label)

print("-" * 64)

if errors:
    print("[실패] 환경에 문제가 있습니다.")
    print("문제 항목:", ", ".join(errors))
    print()
    print("권장 해결 방법:")
    print("  conda deactivate")
    print("  conda env remove -n wind-forecast")
    print("  conda env create -f environment.yml")
    print("  conda activate wind-forecast")
    sys.exit(1)

print("[성공] 수업용 Python 환경이 정상입니다.")
sys.exit(0)
