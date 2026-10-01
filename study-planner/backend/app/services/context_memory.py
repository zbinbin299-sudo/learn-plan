import sqlite3
from contextlib import contextmanager
from typing import Iterator

from ..config import settings
from ..models.schemas import StudyPlan, StudyTask, TaskStatus


class ContextMemory:
    def __init__(self) -> None:
        self.database_path = settings.resolved_database_path()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS plans (
                    plan_id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    due_date TEXT NOT NULL
                );
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def unfinished_tasks(self, learner_id: str) -> list[StudyTask]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM tasks WHERE learner_id = ? AND status != ? ORDER BY due_date",
                (learner_id, TaskStatus.completed.value),
            ).fetchall()
        return [StudyTask.model_validate_json(row["payload"]) for row in rows]

    def save_plan(self, plan: StudyPlan) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO plans (plan_id, learner_id, payload) VALUES (?, ?, ?)",
                (plan.plan_id, plan.learner_id, plan.model_dump_json()),
            )
            for task in plan.near_term_tasks:
                connection.execute(
                    "INSERT OR REPLACE INTO tasks (task_id, learner_id, plan_id, payload, status, due_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        task.id,
                        plan.learner_id,
                        plan.plan_id,
                        task.model_dump_json(),
                        task.status.value,
                        task.due_date.isoformat(),
                    ),
                )

    def latest_plan(self, learner_id: str) -> StudyPlan | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM plans WHERE learner_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1",
                (learner_id,),
            ).fetchone()
        return StudyPlan.model_validate_json(row["payload"]) if row else None

    def update_task(self, task_id: str, status: TaskStatus) -> StudyTask | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload, plan_id FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if not row:
                return None
            task = StudyTask.model_validate_json(row["payload"])
            task.status = status
            connection.execute(
                "UPDATE tasks SET payload = ?, status = ? WHERE task_id = ?",
                (task.model_dump_json(), status.value, task_id),
            )
            plan_row = connection.execute(
                "SELECT payload FROM plans WHERE plan_id = ?", (row["plan_id"],)
            ).fetchone()
            if plan_row:
                plan = StudyPlan.model_validate_json(plan_row["payload"])
                for index, existing in enumerate(plan.near_term_tasks):
                    if existing.id == task_id:
                        plan.near_term_tasks[index] = task
                        break
                connection.execute(
                    "UPDATE plans SET payload = ? WHERE plan_id = ?",
                    (plan.model_dump_json(), plan.plan_id),
                )
            return task