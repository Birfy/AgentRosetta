"""Pytest wrapper around the reference implementation's built-in suite.

The assertions live next to the code they describe, in `agentrosetta.py`, so that
`python3 agentrosetta.py` is a complete self-check with no test runner installed.
This file exists so `pytest` works too, and so CI fails loudly on a regression.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def test_self_test_suite_passes():
    """Every assertion in agentrosetta.py --test must pass."""
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "agentrosetta.py"), "--test"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "ALL PASS" in proc.stdout
    assert proc.stdout.count("PASS") > 100, "the suite shrank; did assertions get dropped?"


def test_demo_runs_clean():
    """The demos must not raise, and must not print trailing whitespace."""
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "agentrosetta.py"), "--demo"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    offenders = [ln for ln in proc.stdout.splitlines() if ln != ln.rstrip()]
    assert not offenders, f"trailing whitespace in demo output: {offenders[:3]}"


def test_samples_validate_without_errors():
    """Every shipped sample transcript must be free of ERROR diagnostics."""
    from agentrosetta import Session, parse

    sample_dir = os.path.join(ROOT, "samples")
    names = [n for n in os.listdir(sample_dir) if n.endswith(".rose")]
    assert names, "no samples found"
    for name in names:
        with open(os.path.join(sample_dir, name), encoding="utf-8") as fh:
            messages = parse(fh.read())
        assert messages, f"{name} parsed to nothing"
        session = Session()
        errors = [
            f"{m.id}: {d}"
            for m in messages
            for d in session.add(m)
            if d.level == "ERROR"
        ]
        assert not errors, f"{name} has errors: {errors}"


def test_bench_is_runnable():
    """The token comparison must run even without tiktoken installed."""
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "bench", "token_compare.py")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "rosetta" in proc.stdout


def test_fidelity_checks_pass():
    """Round-trip fidelity and information recovery must be perfect."""
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "bench", "fidelity.py")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "All fidelity checks pass" in proc.stdout
