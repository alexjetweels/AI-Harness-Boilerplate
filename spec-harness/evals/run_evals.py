#!/usr/bin/env python3
"""Minimal eval harness.

Runs the full pipeline on each golden case, scores acceptance, and fails if the
overall pass-rate regresses below baseline.json. Use it to gate prompt/template
changes — the thing that makes this a *harness* and not just a script.

Usage:
    EVAL_TEMPLATE=/path/to/spec-kit-initialized-repo python evals/run_evals.py

Each case is a dir under evals/cases/<name>/ with:
    prompt.md        the feature description fed to `harness run`
    acceptance.yaml  { checks: [ "<shell cmd that must exit 0>", ... ] }
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))


def run_case(case_dir: str, template: str) -> bool:
    prompt = open(os.path.join(case_dir, "prompt.md")).read().strip()
    accept = yaml.safe_load(open(os.path.join(case_dir, "acceptance.yaml"))) or {}

    work = tempfile.mkdtemp(prefix="eval-")
    try:
        # TODO: point EVAL_TEMPLATE at a spec-kit-initialized repo with this
        # harness installed (specify init + pip install -e ./spec-harness).
        shutil.copytree(template, work, dirs_exist_ok=True)

        rc = subprocess.run(
            ["harness", "run", "--feature", prompt, "--repo", work,
             "--config", os.path.join(work, "spec-harness", "harness.yaml")],
        ).returncode
        passed = rc == 0

        for cmd in accept.get("checks", []):
            if subprocess.run(cmd, shell=True, cwd=work).returncode != 0:
                passed = False
        return passed
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    template = os.environ.get("EVAL_TEMPLATE", "")
    if not template:
        print("Set EVAL_TEMPLATE to a spec-kit-initialized repo with spec-harness installed.")
        return 1

    results = {}
    for case in sorted(glob.glob(os.path.join(ROOT, "cases", "*"))):
        if os.path.isdir(case):
            name = os.path.basename(case)
            print(f"\u25b6 running case: {name}")
            results[name] = run_case(case, template)

    passrate = sum(results.values()) / max(len(results), 1)
    print(json.dumps({"passrate": passrate, "results": results}, indent=2))

    base_path = os.path.join(ROOT, "baseline.json")
    if os.path.exists(base_path):
        prev = json.load(open(base_path)).get("passrate", 0)
        if passrate < prev:
            print(f"\u274c Regression: {passrate:.0%} < baseline {prev:.0%}")
            return 1
        print(f"\u2705 No regression ({passrate:.0%} >= baseline {prev:.0%}).")
    else:
        json.dump({"passrate": passrate, "results": results}, open(base_path, "w"), indent=2)
        print(f"Wrote first baseline at {passrate:.0%}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
