import sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import requests
from lazymeta.config import Config
from lazymeta.state import StateManager


def nuke_previous_posts():
    cfg = Config.from_env()
    state = StateManager(cfg.state_file)
    
    # Collect IDs from state file
    target_ids = []
    for item in state.records.values():
        meta_id = item.get("meta_id")
        if meta_id:
            target_ids.append(meta_id)

            
    # Hardcoded fallback of known test post IDs
    known_ids = [
        "1370812732788701_122095216449538053",
        "1370812732788701_122095216857538053",
        "1370812732788701_122095216965538053",
        "1370812732788701_122095217091538053",
        "1370812732788701_122095217355538053",
    ]
    all_ids = list(dict.fromkeys(target_ids + known_ids))
    
    print(f"Attempting to delete {len(all_ids)} previous test posts from Meta...")
    
    for pid in all_ids:
        url = f"https://graph.facebook.com/{cfg.api_version}/{pid}"
        resp = requests.delete(url, params={"access_token": cfg.access_token})
        if resp.status_code == 200 and resp.json().get("success"):
            print(f"✓ Successfully deleted post: {pid}")
        elif resp.status_code == 400 and resp.json().get("error", {}).get("code") == 100:
            print(f"ℹ Post already deleted or not found: {pid}")
        else:
            print(f"✗ Failed to delete {pid}: {resp.status_code} - {resp.text}")

    # Clear state journal
    state.clear()
    print("✓ Local resume state cleared.")

if __name__ == "__main__":
    nuke_previous_posts()
