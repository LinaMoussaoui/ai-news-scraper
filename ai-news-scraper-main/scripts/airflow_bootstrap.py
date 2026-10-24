"""Bootstrap Airflow by unpausing and triggering the main DAGs in order."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone

from airflow.models import DagRun
from airflow.settings import Session
from airflow.utils.state import DagRunState


DAG_SEQUENCE = [
    "bronze_ingestion_dag",
]


def run_airflow_command(*args: str) -> None:
    result = subprocess.run(["airflow", *args], check=False, text=True, capture_output=True)
    if result.returncode != 0:
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        raise RuntimeError(
            f"Airflow command failed: airflow {' '.join(args)}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
        )


def wait_for_dag_success(dag_id: str, run_id: str, timeout_seconds: int = 1800) -> None:
    deadline = time.time() + timeout_seconds
    session = Session()

    try:
        while time.time() < deadline:
            dag_run = session.query(DagRun).filter(
                DagRun.dag_id == dag_id,
                DagRun.run_id == run_id,
            ).one_or_none()

            if dag_run is None:
                time.sleep(5)
                continue

            if dag_run.state == DagRunState.SUCCESS:
                return

            if dag_run.state in {DagRunState.FAILED, DagRunState.UPSTREAM_FAILED}:
                raise RuntimeError(f"DAG {dag_id} failed with state {dag_run.state}")

            time.sleep(10)

        raise TimeoutError(f"Timed out waiting for {dag_id} run {run_id}")
    finally:
        session.close()


def main() -> int:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for dag_id in DAG_SEQUENCE:
        print(f"[bootstrap] Unpausing {dag_id}")
        run_airflow_command("dags", "unpause", dag_id)

    dag_id = DAG_SEQUENCE[0]
    run_id = f"startup__{timestamp}__{dag_id}"
    print(f"[bootstrap] Triggering {dag_id} ({run_id})")
    run_airflow_command("dags", "trigger", dag_id, "--run-id", run_id)
    print(f"[bootstrap] Waiting for {dag_id} to finish")
    wait_for_dag_success(dag_id, run_id)
    print(f"[bootstrap] {dag_id} completed successfully")
    print("[bootstrap] Bronze triggered Silver, which triggers Gold")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover - bootstrap should fail loudly
        print(f"[bootstrap] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)