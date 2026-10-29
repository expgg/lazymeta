from datetime import datetime, date, time, timedelta
from typing import Sequence
from .models import PostItem, SchedulePlan
from .config import MIN_SCHEDULE_MINUTES, MAX_SCHEDULE_DAYS, DEFAULT_SLOTS


class SchedulingWindowError(ValueError):
    """Raised when a scheduled post falls outside Meta's strict 10-minute to 30-day window."""
    pass


def parse_time_slot(slot_str: str) -> time:
    """Parses a string like '09:00' or '14:30' into a time object."""
    parts = slot_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time slot format '{slot_str}', expected 'HH:MM'")
    hour, minute = int(parts[0]), int(parts[1])
    return time(hour=hour, minute=minute)


def build_schedule_plan(
    posts: Sequence[PostItem],
    slots: Sequence[str] = DEFAULT_SLOTS,
    start_date: date | None = None,
    now: datetime | None = None,
) -> SchedulePlan:
    """
    Computes scheduled publish times for a sequence of posts.
    
    Guarantees:
    1. Every post timestamp is >= now + MIN_SCHEDULE_MINUTES (15 mins).
    2. Every post timestamp is <= now + MAX_SCHEDULE_DAYS (29 days, 23 hours).
    3. Posts are evenly distributed across the defined daily time slots (e.g. 3/day).
    """
    if not posts:
        raise ValueError("Cannot schedule an empty list of posts.")

    if now is None:
        now = datetime.now().astimezone()

    parsed_slots = sorted([parse_time_slot(s) for s in slots])
    if not parsed_slots:
        raise ValueError("At least one daily time slot must be provided.")

    min_allowed = now + timedelta(minutes=MIN_SCHEDULE_MINUTES)
    max_allowed = now + timedelta(days=MAX_SCHEDULE_DAYS, hours=23, minutes=45)

    # Determine initial day
    current_day = start_date if start_date is not None else now.date()

    # Generate candidate slot datetimes
    scheduled_posts: list[PostItem] = []
    post_idx = 0
    total_posts = len(posts)

    # Search forward for valid slots
    while post_idx < total_posts:
        for slot_time in parsed_slots:
            slot_dt = datetime.combine(current_day, slot_time, tzinfo=now.tzinfo)

            # If slot is too soon, skip to next slot
            if slot_dt < min_allowed:
                continue

            # Strict upper-bound check
            if slot_dt > max_allowed:
                raise SchedulingWindowError(
                    f"Post #{post_idx + 1} scheduled for {slot_dt.isoformat()} exceeds Meta's strict 30-day "
                    f"window (Max allowed: {max_allowed.isoformat()}). "
                    f"Consider increasing posts per day or reducing the total post queue."
                )

            # Assign schedule to post
            original_post = posts[post_idx]
            original_post.scheduled_time = slot_dt
            original_post.scheduled_publish_time = int(slot_dt.timestamp())
            scheduled_posts.append(original_post)

            post_idx += 1
            if post_idx >= total_posts:
                break

        current_day += timedelta(days=1)

    start_time = scheduled_posts[0].scheduled_time
    end_time = scheduled_posts[-1].scheduled_time
    total_days = (end_time.date() - start_time.date()).days + 1

    return SchedulePlan(
        posts=scheduled_posts,
        start_time=start_time,
        end_time=end_time,
        total_days=total_days,
        posts_per_day=len(parsed_slots),
    )


def validate_schedule_window(plan: SchedulePlan, now: datetime | None = None) -> list[str]:
    """
    Validates that all scheduled items adhere to Meta's hard constraints:
    - Must be at least 10 minutes in the future.
    - Must be at most 30 days in the future.
    """
    if now is None:
        now = datetime.now().astimezone()

    hard_min = now + timedelta(minutes=10)
    hard_max = now + timedelta(days=30)
    violations: list[str] = []

    for post in plan.posts:
        if post.scheduled_time is None:
            violations.append(f"Post #{post.index} has no scheduled time.")
            continue

        if post.scheduled_time < hard_min:
            diff_min = (hard_min - post.scheduled_time).total_seconds() / 60
            violations.append(
                f"Post #{post.index} scheduled at {post.scheduled_time.strftime('%Y-%m-%d %H:%M')} "
                f"is less than 10 minutes away ({diff_min:.1f}m too early). Meta will reject it."
            )

        if post.scheduled_time > hard_max:
            violations.append(
                f"Post #{post.index} scheduled at {post.scheduled_time.strftime('%Y-%m-%d %H:%M')} "
                f"exceeds Meta's 30-day limit. Meta will reject it."
            )

    return violations
