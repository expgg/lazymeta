from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class PostItem:
    index: int
    images: list[Path] = field(default_factory=list)
    caption: str = ""
    scheduled_time: datetime | None = None
    scheduled_publish_time: int | None = None

    @property
    def is_multi_image(self) -> bool:
        return len(self.images) > 1

    @property
    def primary_image(self) -> Path | None:
        return self.images[0] if self.images else None

    def summary(self, max_len: int = 50) -> str:
        clean = " ".join(self.caption.replace("\n", " ").split())
        if len(clean) > max_len:
            return clean[:max_len - 3] + "..."
        return clean or "(No caption)"


@dataclass
class SchedulePlan:
    posts: list[PostItem]
    start_time: datetime
    end_time: datetime
    total_days: int
    posts_per_day: int


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
