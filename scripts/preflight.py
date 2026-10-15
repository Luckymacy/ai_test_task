import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CHECKS = []


def run_command(name, command, cwd=None):
    print(f"\n[CHECK] {name}")

    result = subprocess.run(
        command,
        cwd=cwd or ROOT,
        shell=True,
        text=True,
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout.strip())

    if result.stderr:
        print(result.stderr.strip())

    if result.returncode == 0:
        print(f"[PASS] {name}")
        CHECKS.append((name, True))
        return True

    print(f"[FAIL] {name}")
    CHECKS.append((name, False))
    return False


def check_file_exists(relative_path):
    path = ROOT / relative_path
    name = f"File exists: {relative_path}"

    print(f"\n[CHECK] {name}")

    if path.exists():
        print(f"[PASS] {name}")
        CHECKS.append((name, True))
        return True

    print(f"[FAIL] {name}")
    CHECKS.append((name, False))
    return False


def check_env_gitignore():
    name = ".env is ignored by Git"
    print(f"\n[CHECK] {name}")

    gitignore = ROOT / ".gitignore"

    if not gitignore.exists():
        print("[FAIL] .gitignore not found")
        CHECKS.append((name, False))
        return False

    content = gitignore.read_text(encoding="utf-8")

    ignored = any(
        line.strip() == ".env"
        for line in content.splitlines()
    )

    if ignored:
        print(f"[PASS] {name}")
        CHECKS.append((name, True))
        return True

    print("[FAIL] .env is not listed in .gitignore")
    CHECKS.append((name, False))
    return False


def check_env_example():
    name = ".env.example contains placeholders only"
    print(f"\n[CHECK] {name}")

    path = ROOT / ".env.example"

    if not path.exists():
        print("[FAIL] .env.example not found")
        CHECKS.append((name, False))
        return False

    content = path.read_text(encoding="utf-8")

    suspicious_prefixes = (
        "sk-",
        "postgresql://",
        "postgres://",
    )

    for line in content.splitlines():
        if "=" not in line:
            continue

        _, value = line.split("=", 1)
        value = value.strip()

        if value.startswith(suspicious_prefixes):
            print(
                "[FAIL] Possible real secret found "
                "in .env.example"
            )
            CHECKS.append((name, False))
            return False

    print(f"[PASS] {name}")
    CHECKS.append((name, True))
    return True


def check_dockerfile():
    name = "Dockerfile contains Render/Uvicorn startup"
    print(f"\n[CHECK] {name}")

    path = ROOT / "Dockerfile"

    if not path.exists():
        print("[FAIL] Dockerfile not found")
        CHECKS.append((name, False))
        return False

    content = path.read_text(encoding="utf-8")

    required_parts = [
        "uvicorn",
        "app.api:app",
        "0.0.0.0",
        "PORT",
    ]

    missing = [
        part
        for part in required_parts
        if part not in content
    ]

    if missing:
        print(
            "[FAIL] Dockerfile is missing: "
            + ", ".join(missing)
        )
        CHECKS.append((name, False))
        return False

    print(f"[PASS] {name}")
    CHECKS.append((name, True))
    return True


def main():
    print("=== The Muse Edit Preflight ===")

    check_file_exists("app/api.py")
    check_file_exists("app/assistant.py")
    check_file_exists("admin/package.json")
    check_file_exists("Dockerfile")
    check_file_exists(".env.example")

    run_command(
        "Python compile check",
        f"{sys.executable} -m compileall app",
    )

    run_command(
        "FastAPI import check",
        (
            f"{sys.executable} -c "
            "\"from app.api import app; "
            "print(app.title)\""
        ),
    )

    run_command(
        "React production build",
        "npm run build",
        cwd=ROOT / "admin",
    )

    check_dockerfile()
    check_env_gitignore()
    check_env_example()

    print("\n=== Preflight Summary ===")

    passed = sum(
        1 for _, success in CHECKS if success
    )
    total = len(CHECKS)

    for name, success in CHECKS:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {name}")

    print(f"\nPassed {passed}/{total} checks")

    if passed != total:
        print("\nPreflight failed.")
        sys.exit(1)

    print("\nPreflight passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()