import io
import json
import os
import re
import sys
import base64
import urllib.parse
from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

from PIL import Image

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STUDIO_DIR = Path(__file__).resolve().parent
STATIC_DIR = STUDIO_DIR / "static"
STATE_FILE = PROJECT_ROOT / ".lazymeta_studio.json"


def get_studio_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_folder": None, "recent_folders": []}


def save_studio_state(state: dict[str, Any]) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[Studio] Warning: could not save state: {e}")


def list_campaign_folders() -> list[dict[str, Any]]:
    campaigns_dir = PROJECT_ROOT / "campaigns"
    folders: list[Path] = []
    if campaigns_dir.exists():
        for item in campaigns_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                folders.append(item)

    state = get_studio_state()
    for rec in state.get("recent_folders", []):
        p = Path(rec)
        if p.exists() and p.is_dir() and p not in folders:
            folders.append(p)

    result = []
    for f in folders:
        captions_file = f / "captions.json"
        has_captions = captions_file.exists()
        images_dir = f / "images"
        image_count = len(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))) if images_dir.exists() else 0

        post_count = 0
        if has_captions:
            try:
                data = json.loads(captions_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    post_count = len(data)
                elif isinstance(data, dict) and "posts" in data and isinstance(data["posts"], list):
                    post_count = len(data["posts"])
            except Exception:
                pass

        result.append({
            "name": f.name,
            "path": str(f.resolve()),
            "has_captions": has_captions,
            "post_count": post_count,
            "image_count": image_count,
        })
    return result


def extract_prompts_from_md(md_file: Path) -> dict[int, str]:
    """Extracts prompts from prompts.md if available."""
    prompts = {}
    if not md_file.exists():
        return prompts
    try:
        content = md_file.read_text(encoding="utf-8")
        blocks = re.split(r'\n(?=###?\s+(?:Image|Post)?\s*\d+)', content)
        for block in blocks:
            m_id = re.search(r'###?\s+(?:Image|Post)?\s*(\d+)', block, re.IGNORECASE)
            if not m_id:
                continue
            pid = int(m_id.group(1))
            m_prompt = re.search(
                r'(?:\*{0,2}Prompt\*{0,2}[:\s]*\n?\s*>\s*|\n>\s*)([^\n]+(?:\n(?!\n|---|###|\*)[^\n]+)*)',
                block,
                re.IGNORECASE
            )
            if m_prompt:
                clean = ' '.join(
                    line.lstrip('> ').strip()
                    for line in m_prompt.group(1).splitlines()
                    if line.strip()
                )
                prompts[pid] = clean
    except Exception as e:
        print(f"[Studio] Warning: failed to parse prompts.md: {e}")
    return prompts


def load_campaign_data(folder_path: Path) -> dict[str, Any]:
    folder_path = folder_path.resolve()
    if not folder_path.exists() or not folder_path.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    # Remember last folder
    state = get_studio_state()
    state["last_folder"] = str(folder_path)
    recents = state.get("recent_folders", [])
    str_path = str(folder_path)
    if str_path in recents:
        recents.remove(str_path)
    recents.insert(0, str_path)
    state["recent_folders"] = recents[:10]
    save_studio_state(state)

    captions_file = folder_path / "captions.json"
    images_dir = folder_path / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    prompts_md_file = folder_path / "prompts.md"
    extracted_prompts = extract_prompts_from_md(prompts_md_file)

    posts_data: list[dict[str, Any]] = []
    if captions_file.exists():
        try:
            raw = json.loads(captions_file.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                posts_data = raw
            elif isinstance(raw, dict) and "posts" in raw and isinstance(raw["posts"], list):
                posts_data = raw["posts"]
        except Exception as e:
            raise ValueError(f"Failed to read captions.json: {e}")

    # Build enriched posts list
    enriched_posts = []
    total_images_needed = len(posts_data)
    images_ready = 0

    for idx, p in enumerate(posts_data):
        post_id = p.get("id", idx + 1)
        day = p.get("day", ((idx // 3) + 1))
        slot = p.get("slot", ["morning", "afternoon", "evening"][idx % 3])
        bucket = p.get("bucket", "Viral Post")
        caption = p.get("caption", "")

        # Prompt resolution: from JSON first, fallback to prompts.md
        prompt = p.get("prompt") or extracted_prompts.get(post_id, "")

        # Image resolution
        img_list = p.get("images", [])
        if not img_list:
            expected_name = f"{post_id:02d}.jpg"
            img_list = [expected_name]

        resolved_images = []
        for img_name in img_list:
            img_file = images_dir / img_name
            exists = img_file.exists()
            file_size_str = ""
            dimensions = None
            if exists:
                try:
                    size_kb = img_file.stat().st_size / 1024
                    file_size_str = f"{size_kb:.0f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"
                    with Image.open(img_file) as im:
                        dimensions = f"{im.width}x{im.height}"
                except Exception:
                    pass

            resolved_images.append({
                "filename": img_name,
                "exists": exists,
                "size_str": file_size_str,
                "dimensions": dimensions,
                "url": f"/api/image?folder={urllib.parse.quote(str(folder_path))}&filename={urllib.parse.quote(img_name)}" if exists else None
            })

        has_all_images = len(resolved_images) > 0 and all(img["exists"] for img in resolved_images)
        if has_all_images:
            images_ready += 1

        enriched_posts.append({
            "id": post_id,
            "day": day,
            "slot": slot,
            "bucket": bucket,
            "caption": caption,
            "prompt": prompt,
            "images": resolved_images,
            "is_ready": has_all_images,
        })

    completion_percent = round((images_ready / total_images_needed * 100), 1) if total_images_needed > 0 else 0

    brand_file = folder_path / "brand.json"
    brand_data = None
    if brand_file.exists():
        try:
            brand_data = json.loads(brand_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "folder_name": folder_path.name,
        "folder_path": str(folder_path),
        "total_posts": total_images_needed,
        "images_ready": images_ready,
        "images_missing": total_images_needed - images_ready,
        "completion_percent": completion_percent,
        "brand": brand_data,
        "posts": enriched_posts,
    }


class StudioRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        # Keep console uncluttered
        pass

    def send_json(self, data: Any, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def send_error_json(self, message: str, status: int = 400) -> None:
        self.send_json({"error": message}, status=status)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API: List Campaigns
        if path == "/api/campaigns":
            state = get_studio_state()
            campaigns = list_campaign_folders()
            self.send_json({
                "campaigns": campaigns,
                "last_folder": state.get("last_folder"),
            })
            return

        # 2. API: Load Campaign Details
        if path == "/api/campaign":
            folder_str = query.get("folder", [None])[0]
            if not folder_str:
                state = get_studio_state()
                folder_str = state.get("last_folder")
                if not folder_str:
                    camps = list_campaign_folders()
                    if camps:
                        folder_str = camps[0]["path"]

            if not folder_str:
                self.send_error_json("No campaign folder selected.", status=404)
                return

            try:
                data = load_campaign_data(Path(folder_str))
                self.send_json(data)
            except Exception as e:
                self.send_error_json(str(e), status=400)
            return

        # 3. API: Serve Image Binary
        if path == "/api/image":
            folder_str = query.get("folder", [None])[0]
            filename = query.get("filename", [None])[0]
            if not folder_str or not filename:
                self.send_error_json("Missing folder or filename", status=400)
                return

            img_file = Path(folder_str) / "images" / filename
            if not img_file.exists():
                self.send_error_json("Image not found", status=404)
                return

            try:
                content = img_file.read_bytes()
                mime = "image/jpeg"
                if filename.lower().endswith(".png"):
                    mime = "image/png"
                elif filename.lower().endswith(".webp"):
                    mime = "image/webp"

                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error_json(str(e), status=500)
            return

        # 4. API: Doctor Check
        if path == "/api/doctor":
            from lazymeta.config import Config
            from lazymeta.api import MetaClient
            try:
                cfg = Config.from_env()
                client = MetaClient(cfg)
                info = client.verify_credentials()
                self.send_json({
                    "success": True,
                    "page_name": info.get("page_name"),
                    "page_id": info.get("page_id"),
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        # 5. Serve Static index.html
        if path in ("/", "/index.html"):
            index_file = STATIC_DIR / "index.html"
            if not index_file.exists():
                self.send_error_json("index.html not found", status=404)
                return

            raw = index_file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        # Fallback 404
        self.send_error_json("Route not found", status=404)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length)

        try:
            req_data = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            self.send_error_json("Invalid JSON body", status=400)
            return

        # 1. API: Upload & Auto-Rename
        if path == "/api/upload":
            folder_str = req_data.get("folder")
            post_id = req_data.get("post_id")
            image_data = req_data.get("image_data")
            filename = req_data.get("filename", "")

            if not folder_str or post_id is None or not image_data:
                self.send_error_json("Missing folder, post_id, or image_data")
                return

            try:
                folder_path = Path(folder_str).resolve()
                images_dir = folder_path / "images"
                images_dir.mkdir(parents=True, exist_ok=True)

                # Decode Base64 (strip data:image/...;base64, header if present)
                if "," in image_data:
                    image_data = image_data.split(",", 1)[1]
                raw_bytes = base64.b64decode(image_data)

                captions_file = folder_path / "captions.json"
                target_filename = f"{int(post_id):02d}.jpg"

                # Check if post has a specific existing filename in captions.json
                raw_captions = None
                posts_list = []
                is_dict_format = False
                if captions_file.exists():
                    raw_captions = json.loads(captions_file.read_text(encoding="utf-8"))
                    if isinstance(raw_captions, dict) and "posts" in raw_captions and isinstance(raw_captions["posts"], list):
                        posts_list = raw_captions["posts"]
                        is_dict_format = True
                    elif isinstance(raw_captions, list):
                        posts_list = raw_captions

                    for p in posts_list:
                        if p.get("id") == int(post_id):
                            existing_imgs = p.get("images", [])
                            if existing_imgs and isinstance(existing_imgs[0], str) and existing_imgs[0].strip():
                                target_filename = Path(existing_imgs[0].strip()).name
                            break

                target_path = images_dir / target_filename

                from lazymeta.studio.sanitizer import sanitize_and_stamp_image
                sanitize_and_stamp_image(
                    input_source=raw_bytes,
                    target_path=target_path,
                    quality=95
                )

                # Update captions.json
                if captions_file.exists() and raw_captions is not None:
                    found = False
                    for p in posts_list:
                        if p.get("id") == int(post_id):
                            p["images"] = [target_filename]
                            found = True
                            break
                    if not found and len(posts_list) >= int(post_id):
                        posts_list[int(post_id) - 1]["images"] = [target_filename]

                    to_write = raw_captions if is_dict_format else posts_list
                    captions_file.write_text(json.dumps(to_write, indent=2, ensure_ascii=False), encoding="utf-8")

                self.send_json({
                    "success": True,
                    "filename": target_filename,
                    "url": f"/api/image?folder={urllib.parse.quote(str(folder_path))}&filename={urllib.parse.quote(target_filename)}",
                    "post_id": post_id,
                })
            except Exception as e:
                self.send_error_json(f"Upload failed: {e}", status=500)
            return

        # 2. API: Update Post (Caption, Prompt, Slot, Bucket)
        if path == "/api/update_post":
            folder_str = req_data.get("folder")
            post_id = req_data.get("post_id")
            caption = req_data.get("caption")
            prompt = req_data.get("prompt")
            slot = req_data.get("slot")
            bucket = req_data.get("bucket")
            day = req_data.get("day")

            if not folder_str or post_id is None:
                self.send_error_json("Missing folder or post_id")
                return

            try:
                folder_path = Path(folder_str).resolve()
                captions_file = folder_path / "captions.json"
                if not captions_file.exists():
                    self.send_error_json("captions.json not found", status=404)
                    return

                raw_captions = json.loads(captions_file.read_text(encoding="utf-8"))
                is_dict_format = False
                posts_list = []
                if isinstance(raw_captions, dict) and "posts" in raw_captions and isinstance(raw_captions["posts"], list):
                    posts_list = raw_captions["posts"]
                    is_dict_format = True
                elif isinstance(raw_captions, list):
                    posts_list = raw_captions

                for p in posts_list:
                    if p.get("id") == int(post_id):
                        if caption is not None:
                            p["caption"] = caption
                        if prompt is not None:
                            p["prompt"] = prompt
                        if slot is not None:
                            p["slot"] = slot
                        if bucket is not None:
                            p["bucket"] = bucket
                        if day is not None:
                            p["day"] = int(day)
                        break

                to_write = raw_captions if is_dict_format else posts_list
                captions_file.write_text(json.dumps(to_write, indent=2, ensure_ascii=False), encoding="utf-8")
                self.send_json({"success": True})
            except Exception as e:
                self.send_error_json(str(e), status=500)
            return

        # 3. API: Delete Image
        if path == "/api/delete_image":
            folder_str = req_data.get("folder")
            post_id = req_data.get("post_id")
            filename = req_data.get("filename")

            if not folder_str or post_id is None or not filename:
                self.send_error_json("Missing folder, post_id, or filename")
                return

            try:
                folder_path = Path(folder_str).resolve()
                img_file = folder_path / "images" / filename
                if img_file.exists():
                    img_file.unlink()

                # Remove from captions.json
                captions_file = folder_path / "captions.json"
                if captions_file.exists():
                    raw_captions = json.loads(captions_file.read_text(encoding="utf-8"))
                    is_dict_format = False
                    posts_list = []
                    if isinstance(raw_captions, dict) and "posts" in raw_captions and isinstance(raw_captions["posts"], list):
                        posts_list = raw_captions["posts"]
                        is_dict_format = True
                    elif isinstance(raw_captions, list):
                        posts_list = raw_captions

                    for p in posts_list:
                        if p.get("id") == int(post_id):
                            imgs = p.get("images", [])
                            if filename in imgs:
                                imgs.remove(filename)
                            p["images"] = imgs
                            break

                    to_write = raw_captions if is_dict_format else posts_list
                    captions_file.write_text(json.dumps(to_write, indent=2, ensure_ascii=False), encoding="utf-8")

                self.send_json({"success": True})
            except Exception as e:
                self.send_error_json(str(e), status=500)
            return

        # 4. API: Create Campaign
        if path == "/api/create_campaign":
            folder_name = req_data.get("name", "").strip()
            if not folder_name:
                self.send_error_json("Campaign folder name is required")
                return

            safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', folder_name).lower()
            new_folder = PROJECT_ROOT / "campaigns" / safe_name
            try:
                new_folder.mkdir(parents=True, exist_ok=True)
                (new_folder / "images").mkdir(exist_ok=True)
                captions_path = new_folder / "captions.json"
                if not captions_path.exists():
                    captions_path.write_text("[]\n", encoding="utf-8")

                state = get_studio_state()
                state["last_folder"] = str(new_folder)
                recents = state.get("recent_folders", [])
                if str(new_folder) in recents:
                    recents.remove(str(new_folder))
                recents.insert(0, str(new_folder))
                state["recent_folders"] = recents[:10]
                save_studio_state(state)

                self.send_json({"success": True, "path": str(new_folder), "name": safe_name})
            except Exception as e:
                self.send_error_json(str(e), status=500)
            return

        # 5. API: Schedule Campaign to Meta
        if path == "/api/schedule_campaign":
            folder_str = req_data.get("folder")
            slots = req_data.get("slots", ["09:00", "14:00", "20:00"])
            start_date_str = req_data.get("start_date")
            dry_run = bool(req_data.get("dry_run", False))
            reset_state = bool(req_data.get("reset_state", False))

            if not folder_str:
                self.send_error_json("Campaign folder path is required")
                return

            try:
                from datetime import datetime
                from lazymeta.config import Config
                from lazymeta.parser import parse_captions_file, validate_posts
                from lazymeta.scheduler import build_schedule_plan, validate_schedule_window
                from lazymeta.api import MetaClient
                from lazymeta.state import StateManager

                folder_path = Path(folder_str).resolve()
                captions_file = folder_path / "captions.json"
                images_dir = folder_path / "images"

                if not captions_file.exists():
                    self.send_error_json("captions.json not found in campaign folder", status=404)
                    return

                cfg = Config.from_env()
                state = StateManager(cfg.state_file)
                if reset_state:
                    state.clear()

                client = MetaClient(cfg)
                if not dry_run:
                    client.verify_credentials()

                parsed_start_date = None
                if start_date_str:
                    parsed_start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

                posts = parse_captions_file(captions_file, images_dir=images_dir)
                val = validate_posts(posts, images_dir=images_dir)
                if not val.is_valid:
                    self.send_error_json(f"Post validation failed: {', '.join(val.errors)}", status=400)
                    return

                plan = build_schedule_plan(posts, slots=slots, start_date=parsed_start_date)
                violations = validate_schedule_window(plan)
                if violations:
                    self.send_error_json(f"Scheduling window violations: {'; '.join(violations)}", status=400)
                    return

                results = []
                for p in plan.posts:
                    img_names = [img.name for img in p.images]
                    if state.is_already_scheduled(p.index, img_names):
                        results.append({
                            "index": p.index,
                            "day": p.day,
                            "slot": p.slot,
                            "scheduled_time": p.scheduled_time.isoformat() if p.scheduled_time else None,
                            "status": "already_scheduled",
                            "skipped": True
                        })
                        continue

                    if dry_run:
                        results.append({
                            "index": p.index,
                            "day": p.day,
                            "slot": p.slot,
                            "scheduled_time": p.scheduled_time.isoformat() if p.scheduled_time else None,
                            "status": "simulated",
                            "skipped": False
                        })
                    else:
                        publish_ts = p.scheduled_publish_time
                        if len(p.images) == 1:
                            res = client.schedule_single_photo(
                                image_path=p.images[0],
                                caption=p.caption,
                                scheduled_publish_time=publish_ts,
                            )
                        else:
                            res = client.schedule_multi_photo(
                                image_paths=p.images,
                                caption=p.caption,
                                scheduled_publish_time=publish_ts,
                            )
                        meta_post_id = res.get("id")
                        state.record_success(
                            index=p.index,
                            post_id=meta_post_id,
                            scheduled_time=p.scheduled_time.isoformat() if p.scheduled_time else "",
                            images=img_names
                        )
                        results.append({
                            "index": p.index,
                            "day": p.day,
                            "slot": p.slot,
                            "scheduled_time": p.scheduled_time.isoformat() if p.scheduled_time else None,
                            "meta_post_id": meta_post_id,
                            "status": "scheduled",
                            "skipped": False
                        })

                self.send_json({
                    "success": True,
                    "dry_run": dry_run,
                    "total_posts": len(plan.posts),
                    "results": results
                })
            except Exception as e:
                self.send_error_json(f"Scheduling failed: {e}", status=500)
            return

        # 6. API: Sanitize & Stamp All Images
        if path == "/api/sanitize_all":
            folder_str = req_data.get("folder")
            if not folder_str:
                self.send_error_json("Folder path is required")
                return

            try:
                from lazymeta.studio.sanitizer import sanitize_and_stamp_image
                folder_path = Path(folder_str).resolve()
                images_dir = folder_path / "images"
                if not images_dir.exists():
                    self.send_error_json("Images directory not found", status=404)
                    return

                sanitized = []
                for img_path in sorted(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.webp"))):
                    target_jpg = images_dir / f"{img_path.stem}.jpg"
                    res = sanitize_and_stamp_image(img_path, target_jpg)
                    if img_path.suffix.lower() != ".jpg" and img_path.exists() and target_jpg.exists():
                        img_path.unlink()
                    sanitized.append(res["filename"])

                self.send_json({"success": True, "count": len(sanitized), "files": sanitized})
            except Exception as e:
                self.send_error_json(str(e), status=500)
            return

        self.send_error_json("Route not found", status=404)


def start_studio_server(port: int = 5000, initial_folder: Path | None = None) -> None:
    if initial_folder:
        state = get_studio_state()
        state["last_folder"] = str(initial_folder.resolve())
        save_studio_state(state)

    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, StudioRequestHandler)
    print(f"[LazyMeta Studio] Serving on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[LazyMeta Studio] Shutting down.")
        httpd.server_close()
