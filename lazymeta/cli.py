import sys
from datetime import datetime
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table

from . import __version__
from .config import Config, check_git_security, DEFAULT_SLOTS
from .models import PostItem, SchedulePlan
from .parser import parse_captions_file, validate_posts, find_images_in_dir
from .scheduler import build_schedule_plan, validate_schedule_window, SchedulingWindowError
from .api import MetaClient, MetaAuthError, MetaRateLimitError, MetaApiError
from .state import StateManager

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()


def print_banner() -> None:
    banner_text = (
        f"[bold cyan]LazyMeta[/bold cyan] [dim]v{__version__}[/dim]\n"
        "[dim]High-Throughput 30-Day Automated Bulk Scheduler for Meta Graph API[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan"))


@click.group()
@click.version_option(__version__, message="%(prog)s %(version)s")
def main() -> None:
    """LazyMeta - Eliminate manual scheduling and queue 30 days of posts in minutes."""
    pass


@main.command()
@click.option("--env-file", type=click.Path(path_type=Path), default=None, help="Path to custom .env file")
def doctor(env_file: Path | None) -> None:
    """Validate Page Access Token, permissions, and security settings."""
    print_banner()
    console.print("[bold]Running Pre-Flight Health Checks...[/bold]\n")

    # 1. Check Git Security
    git_warnings = check_git_security()
    if git_warnings:
        for w in git_warnings:
            console.print(f"[bold red]✗ SECURITY WARNING:[/bold red] {w}")
    else:
        console.print("[bold green]✓ Git Security:[/bold green] Credentials are not tracked in git.")

    # 2. Check Configuration
    cfg = Config.from_env(env_path=env_file)
    if not cfg.page_id or not cfg.access_token:
        console.print("[bold red]✗ Credentials Missing:[/bold red] META_PAGE_ID or META_PAGE_ACCESS_TOKEN is not set.")
        console.print("[yellow]Hint: Copy .env.example to .env and fill in your Page ID and Access Token.[/yellow]")
        sys.exit(1)

    console.print(f"[bold green]✓ Configuration:[/bold green] API Version: {cfg.api_version}, Delay: {cfg.delay_seconds}s")

    # 3. Test Meta API Connection
    client = MetaClient(cfg)
    try:
        with console.status("[bold cyan]Connecting to Meta Graph API...[/bold cyan]"):
            info = client.verify_credentials()
        console.print(f"[bold green]✓ Meta Connection:[/bold green] Successfully connected as [bold]{info['page_name']}[/bold] (ID: {info['page_id']})")
        if not info.get("can_post", True):
            console.print("[bold yellow]! Warning:[/bold yellow] Token does not explicitly have 'can_post' permission.")
        else:
            console.print("[bold green]✓ Publishing Permissions:[/bold green] Page posting rights verified.")
    except MetaAuthError as e:
        console.print(f"[bold red]✗ Authentication Failed:[/bold red] {e}")
        console.print("[yellow]Action needed: Ensure your Page Access Token is active and has 'pages_manage_posts' permission.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ Connection Error:[/bold red] {e}")
        sys.exit(1)

    console.print("\n[bold green]All systems operational! LazyMeta is ready to schedule.[/bold green]")


def resolve_campaign_input(
    campaign: Path | None,
    captions: Path,
    images: Path,
) -> tuple[Path, Path]:
    """Resolves captions and images paths if a --campaign folder is provided."""
    if campaign:
        if not campaign.exists() or not campaign.is_dir():
            console.print(f"[bold red]Error:[/bold red] Campaign directory not found: {campaign}")
            sys.exit(1)

        json_file = campaign / "captions.json"
        txt_file = campaign / "captions.txt"
        if json_file.exists():
            captions = json_file
        elif txt_file.exists():
            captions = txt_file
        else:
            console.print(
                f"[bold red]Error:[/bold red] Neither 'captions.json' nor 'captions.txt' found inside campaign folder: {campaign}"
            )
            sys.exit(1)

        campaign_images = campaign / "images"
        if campaign_images.exists() and campaign_images.is_dir():
            images = campaign_images
        else:
            images = campaign

    return captions, images


@main.command()
@click.option("--campaign", "-C", type=click.Path(path_type=Path), default=None, help="Campaign directory containing captions.json (or captions.txt) and images/")
@click.option("--images", "-i", type=click.Path(path_type=Path), default=Path("images"), help="Directory containing post images")
@click.option("--captions", "-c", type=click.Path(path_type=Path), default=Path("captions.txt"), help="Captions file (captions.json or captions.txt)")
@click.option("--slots", "-s", type=str, default=",".join(DEFAULT_SLOTS), help="Comma-separated daily time slots (e.g. 09:00,14:00,20:00)")
@click.option("--start-date", "-d", type=str, default=None, help="Start date in YYYY-MM-DD format (default: today)")
def preview(campaign: Path | None, images: Path, captions: Path, slots: str, start_date: str | None) -> None:
    """Dry-run simulation of the 30-day posting queue without sending API requests."""
    print_banner()

    captions, images = resolve_campaign_input(campaign, captions, images)

    if not captions.exists():
        console.print(f"[bold red]Error:[/bold red] Captions file not found: {captions}")
        sys.exit(1)


    slot_list = [s.strip() for s in slots.split(",") if s.strip()]
    parsed_start_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            console.print("[bold red]Error:[/bold red] Invalid --start-date format. Expected YYYY-MM-DD.")
            sys.exit(1)

    # Parse and Validate
    try:
        posts = parse_captions_file(captions, images_dir=images)
    except Exception as e:
        console.print(f"[bold red]Parse Error:[/bold red] {e}")
        sys.exit(1)

    val = validate_posts(posts, images_dir=images)
    for err in val.errors:
        console.print(f"[bold red]✗ Error:[/bold red] {err}")
    for warn in val.warnings:
        console.print(f"[bold yellow]! Warning:[/bold yellow] {warn}")

    if not val.is_valid:
        console.print("\n[bold red]Preview halted due to post validation errors.[/bold red]")
        sys.exit(1)

    # Build Schedule
    try:
        plan = build_schedule_plan(posts, slots=slot_list, start_date=parsed_start_date)
    except SchedulingWindowError as e:
        console.print(f"[bold red]✗ Scheduling Window Error:[/bold red] {e}")
        sys.exit(1)

    window_violations = validate_schedule_window(plan)
    if window_violations:
        for v in window_violations:
            console.print(f"[bold red]✗ Window Violation:[/bold red] {v}")
        sys.exit(1)

    # Render Preview Table
    table = Table(title="[bold]LazyMeta 30-Day Scheduling Plan (Dry Run)[/bold]", show_lines=True)
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Scheduled Time", style="green", no_wrap=True)
    table.add_column("Type", style="magenta", no_wrap=True)
    table.add_column("Image File(s)", style="blue")
    table.add_column("Caption Snippet", style="white")

    now = datetime.now().astimezone()
    for p in plan.posts[:15]:  # Show first 15 in table
        img_str = ", ".join([img.name for img in p.images])
        post_type = f"Carousel ({len(p.images)})" if p.is_multi_image else "Single Photo"
        time_str = p.scheduled_time.strftime("%a %b %d, %Y %I:%M %p") if p.scheduled_time else "N/A"
        table.add_row(str(p.index), time_str, post_type, img_str, p.summary(45))

    console.print(table)
    if len(plan.posts) > 15:
        console.print(f"[dim]... and {len(plan.posts) - 15} more posts scheduled identically.[/dim]\n")

    # Render Summary
    duration_min = (len(plan.posts) * 2.5) / 60
    summary_box = (
        f"[bold]Total Posts Queued:[/bold] {len(plan.posts)}\n"
        f"[bold]Schedule Duration:[/bold] {plan.total_days} days ({plan.posts_per_day} posts/day)\n"
        f"[bold]First Post:[/bold] {plan.start_time.strftime('%Y-%m-%d %I:%M %p')}\n"
        f"[bold]Final Post:[/bold] {plan.end_time.strftime('%Y-%m-%d %I:%M %p')}\n"
        f"[bold]Est. Upload Duration:[/bold] ~{duration_min:.1f} minutes (at 2.5s safe delay/post)\n"
        f"[bold green]✓ All posts strictly fall within Meta's 10m - 30d window![/bold green]"
    )
    console.print(Panel(summary_box, title="[bold cyan]Queue Summary[/bold cyan]", border_style="cyan"))


@main.command()
@click.option("--campaign", "-C", type=click.Path(path_type=Path), default=None, help="Campaign directory containing captions.json (or captions.txt) and images/")
@click.option("--images", "-i", type=click.Path(path_type=Path), default=Path("images"), help="Directory containing post images")
@click.option("--captions", "-c", type=click.Path(path_type=Path), default=Path("captions.txt"), help="Captions file (captions.json or captions.txt)")
@click.option("--slots", "-s", type=str, default=",".join(DEFAULT_SLOTS), help="Comma-separated daily time slots")
@click.option("--start-date", "-d", type=str, default=None, help="Start date in YYYY-MM-DD format")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--dry-run", is_flag=True, help="Simulate without making actual API calls")
@click.option("--reset-state", is_flag=True, help="Clear existing resume journal before scheduling")
def schedule(
    campaign: Path | None,
    images: Path,
    captions: Path,
    slots: str,
    start_date: str | None,
    yes: bool,
    dry_run: bool,
    reset_state: bool,
) -> None:
    """Execute the bulk scheduling queue to Meta's servers."""
    print_banner()

    captions, images = resolve_campaign_input(campaign, captions, images)

    # Pre-flight security check
    git_warnings = check_git_security()

    if git_warnings:
        for w in git_warnings:
            console.print(f"[bold red]✗ SECURITY ALERT:[/bold red] {w}")
        if not yes and not click.confirm("Proceed despite security warning?", default=False):
            sys.exit(1)

    cfg = Config.from_env()
    state = StateManager(cfg.state_file)

    if reset_state:
        state.clear()
        console.print("[yellow]Resume journal cleared.[/yellow]")

    client = MetaClient(cfg)

    # Token pre-flight
    if not dry_run:
        try:
            with console.status("[bold cyan]Verifying Meta Page Access Token...[/bold cyan]"):
                info = client.verify_credentials()
            console.print(f"[bold green]✓ Authenticated:[/bold green] Ready to publish to [bold]{info['page_name']}[/bold]\n")
        except Exception as e:
            console.print(f"[bold red]✗ Pre-flight check failed:[/bold red] {e}")
            sys.exit(1)

    # Parse and schedule calculations
    slot_list = [s.strip() for s in slots.split(",") if s.strip()]
    parsed_start_date = None
    if start_date:
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    posts = parse_captions_file(captions, images_dir=images)
    val = validate_posts(posts, images_dir=images)
    if not val.is_valid:
        for err in val.errors:
            console.print(f"[bold red]✗ {err}[/bold red]")
        sys.exit(1)

    plan = build_schedule_plan(posts, slots=slot_list, start_date=parsed_start_date)
    violations = validate_schedule_window(plan)
    if violations:
        for v in violations:
            console.print(f"[bold red]✗ {v}[/bold red]")
        sys.exit(1)

    # Check for already scheduled posts
    pending_posts: list[PostItem] = []
    skipped_count = 0
    for p in plan.posts:
        img_names = [img.name for img in p.images]
        if state.is_already_scheduled(p.index, img_names):
            skipped_count += 1
        else:
            pending_posts.append(p)

    if skipped_count > 0:
        console.print(f"[bold yellow]Resume Journal Active:[/bold yellow] {skipped_count} post(s) previously queued, skipping.")

    if not pending_posts:
        console.print("[bold green]All posts in this queue have already been scheduled![/bold green]")
        sys.exit(0)

    console.print(
        f"[bold]Queuing {len(pending_posts)} posts[/bold] across {plan.total_days} days. "
        f"Est. completion time: ~{(len(pending_posts) * 2.5) / 60:.1f} minutes."
    )

    if dry_run:
        console.print("\n[bold yellow]--dry-run enabled: No API calls will be made.[/bold yellow]")
        return

    if not yes:
        if not click.confirm("Proceed with bulk scheduling to Meta?", default=True):
            console.print("[yellow]Scheduling canceled.[/yellow]")
            sys.exit(0)

    console.print("\n[bold cyan]Uploading and scheduling posts...[/bold cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scheduling posts", total=len(pending_posts))

        for post in pending_posts:
            img_names = [img.name for img in post.images]
            desc = f"Post #{post.index} ({'Carousel' if post.is_multi_image else 'Single'}) -> {post.scheduled_time.strftime('%b %d %I:%M%p')}"
            progress.update(task, description=desc)

            try:
                if post.is_multi_image:
                    meta_id = client.schedule_multi_photo(
                        image_paths=post.images,
                        caption=post.caption,
                        scheduled_timestamp=post.scheduled_publish_time,
                    )
                else:
                    meta_id = client.schedule_single_photo(
                        image_path=post.images[0],
                        caption=post.caption,
                        scheduled_timestamp=post.scheduled_publish_time,
                    )

                state.record_success(
                    post_index=post.index,
                    image_names=img_names,
                    scheduled_time=post.scheduled_time.isoformat(),
                    scheduled_timestamp=post.scheduled_publish_time,
                    meta_id=meta_id,
                )

                progress.advance(task)

            except MetaRateLimitError as e:
                console.print(f"\n[bold red]Rate Limit Encounted on Post #{post.index}:[/bold red] {e}")
                console.print("[yellow]Progress saved! You can resume immediately by re-running this command.[/yellow]")
                sys.exit(1)
            except Exception as e:
                console.print(f"\n[bold red]Error scheduling Post #{post.index}:[/bold red] {e}")
                console.print("[yellow]Progress saved to journal. Fix the issue and re-run to resume.[/yellow]")
                sys.exit(1)

    console.print(
        Panel(
            "[bold green]Queue Complete![/bold green]\n"
            f"All {len(pending_posts)} posts have been accepted by Meta's servers.\n"
            "You can safely close this terminal or shut down your computer.\n"
            "Meta will publish each post automatically according to schedule.",
            title="[bold green]Success[/bold green]",
            border_style="green",
        )
    )


@main.command()
@click.option("--limit", "-n", type=int, default=20, help="Number of scheduled posts to fetch")
def status(limit: int) -> None:
    """Check posts currently queued in Meta's servers for your page."""
    print_banner()
    cfg = Config.from_env()
    client = MetaClient(cfg)

    try:
        with console.status("[bold cyan]Fetching scheduled posts from Meta servers...[/bold cyan]"):
            posts = client.get_scheduled_posts(limit=limit)

        if not posts:
            console.print("[yellow]No scheduled posts found in Meta's queue for this Page.[/yellow]")
            return

        table = Table(title=f"Scheduled Posts on Meta ({len(posts)} found)", show_lines=True)
        table.add_column("ID", style="dim", no_wrap=True)
        table.add_column("Scheduled Publish Time", style="green", no_wrap=True)
        table.add_column("Created Time", style="cyan", no_wrap=True)
        table.add_column("Caption", style="white")

        for p in posts:
            sched_ts = p.get("scheduled_publish_time")
            sched_str = datetime.fromtimestamp(sched_ts).strftime("%Y-%m-%d %I:%M %p") if sched_ts else "N/A"
            created_str = p.get("created_time", "N/A")[:19].replace("T", " ")
            msg = p.get("message") or p.get("name") or p.get("caption") or "(Photo post)"
            clean_msg = " ".join(str(msg).split())[:50]
            table.add_row(p.get("id"), sched_str, created_str, clean_msg)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Failed to fetch status:[/bold red] {e}")
        sys.exit(1)


@main.command(name="reset-state")
def reset_state_cmd() -> None:
    """Clear local resume journal (.lazymeta_state.json)."""
    cfg = Config.from_env()
    state = StateManager(cfg.state_file)
    state.clear()
    console.print("[bold green]Local state journal cleared successfully.[/bold green]")


if __name__ == "__main__":
    main()
