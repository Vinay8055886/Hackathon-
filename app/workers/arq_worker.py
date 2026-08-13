"""ARQ worker entrypoint.

Run with:  python -m app.workers.arq_worker
(or via docker-compose:  arq app.workers.arq_worker.WorkerSettings)
"""

from __future__ import annotations

from app.workers.tasks import worker_settings


class WorkerSettings:
    functions = worker_settings()["functions"]
    redis_settings = worker_settings()["redis_settings"]
    max_jobs = worker_settings()["max_jobs"]
    job_timeout = worker_settings()["job_timeout"]
    keep_result = worker_settings()["keep_result"]


if __name__ == "__main__":
    import arq

    arq.cli.run(WorkerSettings)
