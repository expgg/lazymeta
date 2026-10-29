from pathlib import Path
from lazymeta.state import StateManager


def test_state_manager_lifecycle(tmp_path: Path):
    state_file = tmp_path / ".test_state.json"
    manager = StateManager(state_file)

    assert manager.count() == 0
    assert not manager.is_already_scheduled(1, ["photo1.jpg"])

    manager.record_success(
        post_index=1,
        image_names=["photo1.jpg"],
        scheduled_time="2026-11-01T09:00:00",
        scheduled_timestamp=1793523600,
        meta_id="123456789_meta",
    )

    assert manager.count() == 1
    assert manager.is_already_scheduled(1, ["photo1.jpg"])
    assert manager.get_meta_id(1, ["photo1.jpg"]) == "123456789_meta"

    # Reload from disk
    reloaded = StateManager(state_file)
    assert reloaded.count() == 1
    assert reloaded.is_already_scheduled(1, ["photo1.jpg"])

    reloaded.clear()
    assert reloaded.count() == 0
    assert not state_file.exists()
