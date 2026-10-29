import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class PostRecord:
    post_index: int
    image_names: list[str]
    scheduled_time: str
    scheduled_timestamp: int
    meta_id: str
    uploaded_at: str


class StateManager:
    """Tracks successfully scheduled posts to enable seamless resume on interruption."""

    def __init__(self, state_file: Path = Path(".lazymeta_state.json")):
        self.state_file = state_file
        self.records: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                self.records = data.get("scheduled_posts", {})
            except Exception:
                self.records = {}
        else:
            self.records = {}

    def _save(self) -> None:
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "scheduled_posts": self.records,
        }
        temp_file = self.state_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temp_file.replace(self.state_file)

    def _make_key(self, post_index: int, image_names: list[str]) -> str:
        clean_names = sorted([Path(name).name for name in image_names])
        return f"{post_index}:{','.join(clean_names)}"

    def is_already_scheduled(self, post_index: int, image_names: list[str]) -> bool:
        key = self._make_key(post_index, image_names)
        return key in self.records

    def get_meta_id(self, post_index: int, image_names: list[str]) -> str | None:
        key = self._make_key(post_index, image_names)
        record = self.records.get(key)
        return record.get("meta_id") if record else None

    def record_success(
        self,
        post_index: int,
        image_names: list[str],
        scheduled_time: str,
        scheduled_timestamp: int,
        meta_id: str,
    ) -> None:
        key = self._make_key(post_index, image_names)
        record = PostRecord(
            post_index=post_index,
            image_names=[Path(name).name for name in image_names],
            scheduled_time=scheduled_time,
            scheduled_timestamp=scheduled_timestamp,
            meta_id=meta_id,
            uploaded_at=datetime.now().isoformat(),
        )
        self.records[key] = asdict(record)
        self._save()

    def count(self) -> int:
        return len(self.records)

    def clear(self) -> None:
        if self.state_file.exists():
            self.state_file.unlink()
        self.records = {}
