import tempfile
from pathlib import Path
import pytest
from lazymeta.parser import parse_captions_file, validate_posts, find_images_in_dir, natural_sort_key


def test_natural_sort_key():
    names = ["img_10.jpg", "img_1.jpg", "img_2.jpg", "img_20.jpg"]
    sorted_names = sorted(names, key=natural_sort_key)
    assert sorted_names == ["img_1.jpg", "img_2.jpg", "img_10.jpg", "img_20.jpg"]


def test_parse_captions_with_image_headers(tmp_path: Path):
    captions_file = tmp_path / "captions.txt"
    img1 = tmp_path / "photo1.jpg"
    img2 = tmp_path / "photo2.jpg"
    img1.write_bytes(b"test1")
    img2.write_bytes(b"test2")

    content = """---
images: photo1.jpg
Caption for single photo
#tag1
---
images: photo1.jpg, photo2.jpg
Caption for carousel post
#tag2
"""
    captions_file.write_text(content, encoding="utf-8")

    posts = parse_captions_file(captions_file, images_dir=tmp_path)
    assert len(posts) == 2
    assert posts[0].index == 1
    assert not posts[0].is_multi_image
    assert len(posts[0].images) == 1
    assert posts[0].images[0].name == "photo1.jpg"
    assert "Caption for single photo" in posts[0].caption

    assert posts[1].index == 2
    assert posts[1].is_multi_image
    assert len(posts[1].images) == 2
    assert posts[1].images[0].name == "photo1.jpg"
    assert posts[1].images[1].name == "photo2.jpg"


def test_parse_captions_auto_pairing(tmp_path: Path):
    for i in range(1, 4):
        (tmp_path / f"img_{i}.jpg").write_bytes(b"fake image data")

    captions_file = tmp_path / "captions.txt"
    content = """---
First post
---
Second post
---
Third post
"""
    captions_file.write_text(content, encoding="utf-8")

    posts = parse_captions_file(captions_file, images_dir=tmp_path)
    assert len(posts) == 3
    assert posts[0].images[0].name == "img_1.jpg"
    assert posts[1].images[0].name == "img_2.jpg"
    assert posts[2].images[0].name == "img_3.jpg"


def test_validate_posts_missing_image(tmp_path: Path):
    captions_file = tmp_path / "captions.txt"
    captions_file.write_text("---\nimages: nonexistent.jpg\nTest\n", encoding="utf-8")

    posts = parse_captions_file(captions_file, images_dir=tmp_path)
    val = validate_posts(posts, images_dir=tmp_path)
    assert not val.is_valid
    assert any("does not exist" in e for e in val.errors)


def test_parse_captions_json_array(tmp_path: Path):
    (tmp_path / "img_01.jpg").write_bytes(b"image 1")
    (tmp_path / "img_02a.jpg").write_bytes(b"image 2a")
    (tmp_path / "img_02b.jpg").write_bytes(b"image 2b")

    json_content = """[
        {
            "id": 1,
            "images": ["img_01.jpg"],
            "caption": "Hello from JSON post 1!"
        },
        {
            "id": 2,
            "images": ["img_02a.jpg", "img_02b.jpg"],
            "caption": "Carousel post from JSON 2!"
        }
    ]"""
    json_file = tmp_path / "captions.json"
    json_file.write_text(json_content, encoding="utf-8")

    posts = parse_captions_file(json_file, images_dir=tmp_path)
    assert len(posts) == 2
    assert posts[0].index == 1
    assert len(posts[0].images) == 1
    assert posts[0].images[0].name == "img_01.jpg"
    assert "Hello from JSON post 1!" in posts[0].caption

    assert posts[1].index == 2
    assert posts[1].is_multi_image
    assert len(posts[1].images) == 2
    assert posts[1].images[0].name == "img_02a.jpg"
    assert posts[1].images[1].name == "img_02b.jpg"


def test_parse_captions_json_dict_wrapper(tmp_path: Path):
    (tmp_path / "pic1.png").write_bytes(b"pic1")
    json_content = """{
        "niche": "freelancing",
        "posts": [
            {
                "id": 1,
                "images": "pic1.png",
                "caption": "Niche wrapped caption."
            }
        ]
    }"""
    json_file = tmp_path / "captions.json"
    json_file.write_text(json_content, encoding="utf-8")

    posts = parse_captions_file(json_file, images_dir=tmp_path)
    assert len(posts) == 1
    assert posts[0].images[0].name == "pic1.png"
    assert posts[0].caption == "Niche wrapped caption."

