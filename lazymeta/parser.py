import json
import re
from pathlib import Path
from .models import PostItem, ValidationResult

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def natural_sort_key(s: str) -> list[int | str]:
    """Sort strings containing numbers naturally (e.g. img_2 comes before img_10)."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", s)
    ]


def find_images_in_dir(images_dir: Path) -> list[Path]:
    """Finds and naturally sorts all supported image files in a directory."""
    if not images_dir.exists() or not images_dir.is_dir():
        return []

    images = [
        p for p in images_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    images.sort(key=lambda p: natural_sort_key(p.name))
    return images


def parse_captions_json(captions_path: Path, images_dir: Path | None = None) -> list[PostItem]:
    """
    Parses a structured JSON captions file.

    Supported JSON structures:
    1. Root array of post objects:
       [
         {"id": 1, "images": ["01.jpg"], "caption": "Hello world!"},
         {"id": 2, "images": ["02a.jpg", "02b.jpg"], "caption": "Carousel!"}
       ]
    2. Root object with a "posts" list:
       {
         "niche": "webdev",
         "posts": [
           {"id": 1, "images": ["01.jpg"], "caption": "Hello!"}
         ]
       }
    """
    if not captions_path.exists():
        raise FileNotFoundError(f"Captions file not found: {captions_path}")

    raw_data = json.loads(captions_path.read_text(encoding="utf-8"))

    if isinstance(raw_data, dict):
        raw_posts = raw_data.get("posts", [])
    elif isinstance(raw_data, list):
        raw_posts = raw_data
    else:
        raise ValueError("Invalid captions JSON: Root must be a list of posts or an object with a 'posts' array.")

    available_images = find_images_in_dir(images_dir) if images_dir else []
    base_dir = images_dir if images_dir else captions_path.parent
    post_items: list[PostItem] = []
    auto_image_idx = 0

    for idx, item in enumerate(raw_posts, start=1):
        if not isinstance(item, dict):
            continue

        caption = item.get("caption") or item.get("text") or item.get("content") or item.get("status") or ""
        specified_images: list[Path] = []

        raw_imgs = item.get("images") or item.get("image") or item.get("photos") or item.get("photo")
        if raw_imgs:
            if isinstance(raw_imgs, str):
                raw_imgs = [fn.strip() for fn in raw_imgs.split(",") if fn.strip()]
            elif isinstance(raw_imgs, list):
                raw_imgs = [str(fn).strip() for fn in raw_imgs if str(fn).strip()]
            else:
                raw_imgs = []

            for fn in raw_imgs:
                specified_images.append(base_dir / fn)

        if not specified_images:
            if auto_image_idx < len(available_images):
                specified_images = [available_images[auto_image_idx]]
                auto_image_idx += 1

        post_items.append(
            PostItem(
                index=idx,
                images=specified_images,
                caption=caption.strip(),
            )
        )

    return post_items


def parse_captions_file(captions_path: Path, images_dir: Path | None = None) -> list[PostItem]:
    """
    Parses a captions file formatted with markdown '---' dividers or JSON.
    Auto-detects JSON if file ends with .json.
    """
    if not captions_path.exists():
        raise FileNotFoundError(f"Captions file not found: {captions_path}")

    if captions_path.suffix.lower() == ".json":
        return parse_captions_json(captions_path, images_dir=images_dir)

    raw_text = captions_path.read_text(encoding="utf-8")
    
    # Split by lines that are strictly three or more dashes
    raw_blocks = re.split(r"(?m)^---+\s*$", raw_text)


    available_images = find_images_in_dir(images_dir) if images_dir else []
    post_items: list[PostItem] = []
    auto_image_idx = 0

    for block in raw_blocks:
        stripped = block.strip()
        if not stripped:
            continue

        lines = stripped.splitlines()
        specified_images: list[Path] = []
        caption_lines: list[str] = []

        # Check if first line or second line defines `images:` or `image:`
        for i, line in enumerate(lines):
            header_match = re.match(r"^(?:images?|photos?)\s*:\s*(.+)$", line, flags=re.IGNORECASE)
            if header_match and not specified_images:
                filenames_raw = header_match.group(1).split(",")
                for fn in filenames_raw:
                    clean_name = fn.strip()
                    if not clean_name:
                        continue
                    if images_dir:
                        img_path = images_dir / clean_name
                    else:
                        img_path = captions_path.parent / clean_name
                    specified_images.append(img_path)
            else:
                caption_lines.append(line)

        caption_text = "\n".join(caption_lines).strip()

        # If no explicit image header was supplied, auto-pair with next image in folder
        if not specified_images:
            if auto_image_idx < len(available_images):
                specified_images = [available_images[auto_image_idx]]
                auto_image_idx += 1

        post_index = len(post_items) + 1
        post_items.append(
            PostItem(
                index=post_index,
                images=specified_images,
                caption=caption_text,
            )
        )

    return post_items


def validate_posts(posts: list[PostItem], images_dir: Path | None = None) -> ValidationResult:
    """Performs integrity checks on parsed posts before scheduling."""
    errors: list[str] = []
    warnings: list[str] = []

    if not posts:
        errors.append("No posts found in captions file.")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    for p in posts:
        if not p.images:
            errors.append(f"Post #{p.index} has no associated image.")
        else:
            for img in p.images:
                if not img.exists():
                    errors.append(f"Post #{p.index}: Image file does not exist: {img.name}")
                elif img.stat().st_size == 0:
                    errors.append(f"Post #{p.index}: Image file is empty (0 bytes): {img.name}")
                elif img.stat().st_size > 10 * 1024 * 1024:
                    warnings.append(f"Post #{p.index}: Image {img.name} exceeds 10MB ({img.stat().st_size / 1024 / 1024:.1f}MB). Meta photo upload may fail or be slow.")

        if not p.caption:
            warnings.append(f"Post #{p.index} has an empty caption/message.")

    # Check available images vs posts
    if images_dir and images_dir.exists():
        disk_images = find_images_in_dir(images_dir)
        assigned_images = {img.resolve() for p in posts for img in p.images if img.exists()}
        unused = [img for img in disk_images if img.resolve() not in assigned_images]
        if unused:
            warnings.append(f"{len(unused)} image(s) in '{images_dir.name}' were not assigned to any post.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
