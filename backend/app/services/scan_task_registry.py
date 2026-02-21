"""
Scan Task Registry - In-memory singleton for tracking background wiki scan tasks.

Provides thread-safe tracking of scan progress so the frontend can poll for updates.
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict
import uuid


@dataclass
class ScanTask:
    """Represents a background scan task with progress tracking"""
    id: str
    world_id: str
    status: str = "running"  # running, completed, failed
    total_manuscripts: int = 0
    manuscripts_completed: int = 0
    current_manuscript_title: str = ""
    current_stage: str = ""
    progress_percent: float = 0.0
    total_changes: int = 0
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ScanTaskRegistry:
    """Thread-safe singleton registry for scan tasks"""

    _instance: Optional["ScanTaskRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ScanTaskRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, ScanTask] = {}
                    cls._instance._active_world_scans: Dict[str, str] = {}  # world_id -> task_id
                    cls._instance._task_lock = threading.Lock()
        return cls._instance

    def create_task(self, world_id: str, total_manuscripts: int) -> ScanTask:
        """Create a new scan task. Returns None-equivalent if world already has an active scan."""
        with self._task_lock:
            # Prevent duplicate scans per world
            if world_id in self._active_world_scans:
                existing_id = self._active_world_scans[world_id]
                existing = self._tasks.get(existing_id)
                if existing and existing.status == "running":
                    return existing

            task_id = str(uuid.uuid4())
            task = ScanTask(
                id=task_id,
                world_id=world_id,
                total_manuscripts=total_manuscripts,
            )
            self._tasks[task_id] = task
            self._active_world_scans[world_id] = task_id
            return task

    def get_task(self, task_id: str) -> Optional[ScanTask]:
        """Get a task by ID"""
        return self._tasks.get(task_id)

    def get_active_task_for_world(self, world_id: str) -> Optional[ScanTask]:
        """Get the active (running) scan task for a world, if any"""
        with self._task_lock:
            task_id = self._active_world_scans.get(world_id)
            if not task_id:
                return None
            task = self._tasks.get(task_id)
            if task and task.status == "running":
                return task
            return None

    def update_progress(
        self,
        task_id: str,
        manuscripts_completed: int = 0,
        current_manuscript_title: str = "",
        current_stage: str = "",
        progress_percent: float = 0.0,
        changes_so_far: int = 0,
    ) -> None:
        """Update progress on a running task"""
        task = self._tasks.get(task_id)
        if not task:
            return
        task.manuscripts_completed = manuscripts_completed
        task.current_manuscript_title = current_manuscript_title
        task.current_stage = current_stage
        task.progress_percent = progress_percent
        task.total_changes = changes_so_far

    def complete_task(self, task_id: str, total_changes: int) -> None:
        """Mark a task as completed"""
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.status = "completed"
            task.total_changes = total_changes
            task.progress_percent = 100.0
            task.completed_at = datetime.utcnow()
            # Remove from active scans
            if self._active_world_scans.get(task.world_id) == task_id:
                del self._active_world_scans[task.world_id]

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed"""
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.status = "failed"
            task.error = error
            task.completed_at = datetime.utcnow()
            if self._active_world_scans.get(task.world_id) == task_id:
                del self._active_world_scans[task.world_id]


# Module-level singleton access
scan_registry = ScanTaskRegistry()
