from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from lazymeta.models import PostItem
from lazymeta.scheduler import build_schedule_plan, validate_schedule_window, SchedulingWindowError


def test_schedule_plan_90_posts():
    # Simulate 90 posts
    posts = [PostItem(index=i + 1, images=[Path(f"{i}.jpg")], caption=f"Post {i}") for i in range(90)]
    now = datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc)  # 8:00 AM UTC

    plan = build_schedule_plan(posts, slots=["09:00", "14:00", "20:00"], now=now)
    assert len(plan.posts) == 90
    assert plan.posts_per_day == 3
    assert plan.total_days == 30

    # Ensure every post timestamp is sequential
    for i in range(len(plan.posts) - 1):
        assert plan.posts[i].scheduled_publish_time < plan.posts[i + 1].scheduled_publish_time

    # Validate window
    violations = validate_schedule_window(plan, now=now)
    assert len(violations) == 0


def test_schedule_rejects_past_30_days():
    # 95 posts at 3 posts/day would require 32 days -> exceeds 30-day limit
    posts = [PostItem(index=i + 1, images=[Path(f"{i}.jpg")], caption=f"Post {i}") for i in range(95)]
    now = datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc)

    with pytest.raises(SchedulingWindowError) as exc_info:
        build_schedule_plan(posts, slots=["09:00", "14:00", "20:00"], now=now)

    assert "exceeds Meta's strict 30-day window" in str(exc_info.value)


def test_schedule_skips_slots_within_15_minutes():
    # If now is 8:55 AM and slot is 09:00 AM (only 5 min away < 15 min buffer), it must skip to 14:00 PM
    posts = [PostItem(index=1, images=[Path("1.jpg")], caption="Post 1")]
    now = datetime(2026, 11, 1, 8, 55, tzinfo=timezone.utc)

    plan = build_schedule_plan(posts, slots=["09:00", "14:00", "20:00"], now=now)
    # The first post should be at 14:00, not 09:00
    assert plan.posts[0].scheduled_time.hour == 14
    assert plan.posts[0].scheduled_time.minute == 0
