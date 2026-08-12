#!/usr/bin/env python3
"""AI-LSC Framework Guardrail Validator.

Runs after any agent edit to catch:
  1. Bloat — files that grew >200% without architectural reason
  2. Size — files exceeding max_module_lines (default 300)
  3. Subprocess leakage — UI files touching subprocess/psutil directly
  4. Parent coupling — UI files reaching into self.parent instead of protocol
  5. os.path contamination — should use pathlib
  6. Lint — ruff check (if available)

Usage:
    python3 guardrails.py                  # validate ai_lsc/ in cwd
    python3 guardrails.py --baseline       # snapshot current sizes
    python3 guardrails.py --fix            # auto-fix ruff issues
"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BASELINE_FILE = BASE_DIR / ".guardrail_baseline.json"
MAX_MODULE_LINES = 300
MAX_GROWTH_FACTOR = 2.0

# Directories where subprocess/psutil calls are ALLOWED
RUNTIME_ALLOWED_DIRS = {"utils", "runtime", "core", "scripts", "agents"}

# Directories where os.path usage is ALLOWED (legacy tolerance)
OSPATH_ALLOWED_DIRS = {"utils"}

# Directories where self.parent access is ALLOWED
PARENT_ALLOWED_DIRS: set[str] = set()


def _iter_py_files() -> list[Path]:
    """M-14: return every Python file under BASE_DIR, sorted."""
    return sorted(BASE_DIR.rglob("*.py"))


def _read_source(py_file: Path) -> str | None:
    """M-14: read a Python file's source, returning None on error."""
    try:
        return py_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _is_parent_access(node: ast.AST) -> bool:
    """M-12: return True if *node* is a ``self.parent.<attr>`` access."""
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Attribute)
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "self"
        and node.value.attr == "parent"
    )


def get_file_sizes() -> dict[str, int]:
    """Return {relative_path: line_count} for every .py in the package."""
    sizes: dict[str, int] = {}
    for py_file in _iter_py_files():
        rel = py_file.relative_to(BASE_DIR)
        try:
            sizes[str(rel)] = sum(1 for _ in py_file.open(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            sizes[str(rel)] = -1
    return sizes


def save_baseline(sizes: dict[str, int]) -> None:
    BASELINE_FILE.write_text(
        json.dumps(sizes, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"Baseline saved: {len(sizes)} files tracked in {BASELINE_FILE}")


def load_baseline() -> dict[str, int]:
    if not BASELINE_FILE.exists():
        return {}
    return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))


def check_bloat(sizes: dict[str, int], baseline: dict[str, int]) -> list[str]:
    """Detect files that grew > MAX_GROWTH_FACTOR without baseline."""
    errors: list[str] = []
    for path, new_size in sizes.items():
        if new_size <= 0:
            continue
        old_size = baseline.get(path, 0)
        if old_size <= 0:
            continue  # new file, skip
        if new_size > old_size * MAX_GROWTH_FACTOR:
            growth_pct = (new_size / old_size - 1) * 100
            errors.append(
                f"BLOAT: {path} grew {old_size} -> {new_size} lines "
                f"(+{growth_pct:.0f}%, limit {MAX_GROWTH_FACTOR}x)"
            )
    return errors


def check_size_limits(sizes: dict[str, int]) -> list[str]:
    """Flag files exceeding max module line count."""
    errors: list[str] = []
    for path, size in sizes.items():
        if size > MAX_MODULE_LINES and not path.endswith("__init__.py"):
            errors.append(
                f"OVERSIZED: {path} is {size} lines "
                f"(limit {MAX_MODULE_LINES})"
            )
    return errors


def check_subprocess_leakage() -> list[str]:
    """Flag UI files that directly call subprocess/psutil."""
    errors: list[str] = []
    dangerous_patterns = [
        "subprocess.run", "subprocess.Popen", "subprocess.call",
        "threading.Thread", "os.system", "os.popen",
        "psutil.process_iter", "psutil.cpu_percent",
    ]
    for py_file in _iter_py_files():
        rel = str(py_file.relative_to(BASE_DIR))
        parts = rel.split(os.sep)
        # Skip if in allowed directory
        if any(part in RUNTIME_ALLOWED_DIRS for part in parts):
            continue
        source = _read_source(py_file)
        if source is None:
            continue
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                full = f"{node.value}.{node.attr}" if isinstance(
                    node.value, ast.Name
                ) else None
                if full and full in dangerous_patterns:
                    errors.append(
                        f"SUBPROCESS_LEAK: {rel}:{node.lineno} "
                        f"calls {full} (should delegate to runtime/)"
                    )
    return errors


def check_parent_coupling() -> list[str]:
    """Flag UI files accessing self.parent.* directly."""
    errors: list[str] = []
    for py_file in _iter_py_files():
        rel = str(py_file.relative_to(BASE_DIR))
        # M-27: PARENT_ALLOWED_DIRS is empty, so the old `any(...) or not any(...)`
        # check was a tautology.  Just always check.
        source = _read_source(py_file)
        if source is None:
            continue
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if _is_parent_access(node):
                errors.append(
                    f"PARENT_COUPLING: {rel}:{node.lineno} "
                    f"accesses self.parent.{node.attr} "
                    f"(use MainWindowProtocol instead)"
                )
    return errors


def check_ospath_contamination() -> list[str]:
    """Flag files using os.path instead of pathlib."""
    errors: list[str] = []
    for py_file in _iter_py_files():
        rel = str(py_file.relative_to(BASE_DIR))
        parts = rel.split(os.sep)
        if any(part in OSPATH_ALLOWED_DIRS for part in parts):
            continue
        source = _read_source(py_file)
        if source is None:
            continue
        count = source.count("os.path.")
        if count > 0:
            errors.append(
                f"OSPATH: {rel} has {count} os.path.* calls "
                f"(use pathlib.Path)"
            )
    return errors


def run_ruff(fix: bool = False) -> list[str]:
    """Run ruff if available, return error output."""
    import shutil
    ruff_bin = shutil.which("ruff")
    if not ruff_bin:
        try:
            import ruff as _  # noqa: F401
            ruff_bin = sys.executable + " -m ruff"
        except ImportError:
            return ["RUFF: not installed (pip install ruff)"]
    import subprocess
    cmd = [sys.executable, "-m", "ruff", "check", str(BASE_DIR)]
    if fix:
        cmd.append("--fix")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip() + result.stderr.strip()
        if output:
            return [f"RUFF:\n{output}"]
        return []
    except Exception as e:
        return [f"RUFF: failed to run: {e}"]


def main() -> int:
    args = set(sys.argv[1:])

    if "--baseline" in args:
        sizes = get_file_sizes()
        save_baseline(sizes)
        return 0

    sizes = get_file_sizes()
    baseline = load_baseline()

    all_errors: list[str] = []

    print("=" * 60)
    print("AI-LSC Framework Guardrail Validation")
    print("=" * 60)

    # 1. Bloat check
    errors = check_bloat(sizes, baseline)
    if errors:
        all_errors.extend(errors)
        print(f"\n[FAIL] Bloat detection: {len(errors)} violations")
    elif baseline:
        print("\n[PASS] Bloat detection: no abnormal growth")
    else:
        print("\n[SKIP] Bloat detection: no baseline (run with --baseline)")

    # 2. Size limits
    errors = check_size_limits(sizes)
    if errors:
        all_errors.extend(errors)
        print(f"[FAIL] Size limits: {len(errors)} oversized modules")
    else:
        print(f"[PASS] Size limits: all modules under {MAX_MODULE_LINES} lines")

    # 3. Subprocess leakage
    errors = check_subprocess_leakage()
    if errors:
        all_errors.extend(errors)
        print(f"[FAIL] Subprocess leakage: {len(errors)} violations")
    else:
        print("[PASS] Subprocess leakage: clean")

    # 4. Parent coupling
    errors = check_parent_coupling()
    if errors:
        all_errors.extend(errors)
        print(f"[FAIL] Parent coupling: {len(errors)} violations")
    else:
        print("[PASS] Parent coupling: clean")

    # 5. os.path contamination
    errors = check_ospath_contamination()
    if errors:
        all_errors.extend(errors)
        print(f"[FAIL] os.path: {len(errors)} files with os.path.* calls")
    else:
        print("[PASS] os.path: clean")

    # 6. Ruff lint
    fix_mode = "--fix" in args
    errors = run_ruff(fix=fix_mode)
    if errors:
        all_errors.extend(errors)
        print(f"[{'FIXED' if fix_mode else 'FAIL'}] Ruff lint: see above")
    else:
        print("[PASS] Ruff lint: clean")

    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"RESULT: {len(all_errors)} guardrail violations")
        for e in all_errors:
            # Truncate long ruff output
            lines = e.split("\n")
            for line in lines[:5]:
                print(f"  {line}")
            if len(lines) > 5:
                print(f"  ... ({len(lines) - 5} more lines)")
        return 1
    else:
        print("RESULT: ALL GUARDRAILS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
