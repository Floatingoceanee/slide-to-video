import pytest
from unittest.mock import Mock, patch, MagicMock
from src.slide_to_video.project import TargetVoice, ItemType, Item, Task
from src.slide_to_video.tts_engine import TTSEngine


def test_target_voice_init():
    voice = TargetVoice(model="test_model", audio="test_audio.wav")
    assert voice.model == "test_model"
    assert voice.audio == "test_audio.wav"


def test_target_voice_defaults():
    voice = TargetVoice()
    assert voice.model is None
    assert voice.audio is None


def test_item_type_enum():
    assert ItemType.SLIDE.value == "slide"
    assert ItemType.SCRIPT.value == "script"
    assert ItemType.VOICE.value == "voice"
    assert ItemType.VIDEO.value == "video"


@patch("src.slide_to_video.project.md5sum_of_file")
def test_item_init_with_md5(mock_md5):
    mock_md5.return_value = "abc123"

    item = Item(path="/test/path.txt", type=ItemType.SLIDE, md5sum="custom_hash")

    assert item.path == "/test/path.txt"
    assert item.type == ItemType.SLIDE
    assert item.md5sum == "custom_hash"  # Should use provided hash
    assert item.cached is False
    assert item.extra is None
    assert item.force_reset is False

    # md5sum_of_file should not be called when md5sum is provided
    mock_md5.assert_not_called()


@patch("src.slide_to_video.project.md5sum_of_file")
def test_item_init_without_md5(mock_md5):
    mock_md5.return_value = "computed_hash"

    item = Item(path="/test/path.txt", type=ItemType.SLIDE)

    assert item.md5sum == "computed_hash"
    mock_md5.assert_called_once_with("/test/path.txt")


def test_item_init_with_extra():
    extra_data = {"duration": 5.0, "format": "png"}
    item = Item(
        path="/test/path.txt",
        type=ItemType.SLIDE,
        md5sum="hash123",
        extra=extra_data,
        cached=True,
        force_reset=True,
    )

    assert item.extra == extra_data
    assert item.cached is True
    assert item.force_reset is True


def test_item_reset():
    item = Item(
        path="/test/path.txt", type=ItemType.SLIDE, md5sum="hash123", cached=True
    )

    item.reset()

    assert item.cached is False


@patch("builtins.open", new_callable=lambda: Mock())
def test_item_content_property(mock_open):
    mock_file = Mock()
    mock_file.read.return_value = "file content"
    mock_open.return_value.__enter__ = Mock(return_value=mock_file)
    mock_open.return_value.__exit__ = Mock(return_value=None)

    item = Item(path="/test/path.txt", type=ItemType.SLIDE, md5sum="hash123")

    content = item.content

    assert content == "file content"
    mock_open.assert_called_once_with("/test/path.txt", "r", encoding="utf-8")
    mock_file.read.assert_called_once()


def test_item_equality():
    item1 = Item(path="/path1.txt", type=ItemType.SLIDE, md5sum="hash123")
    item2 = Item(
        path="/path2.txt", type=ItemType.SCRIPT, md5sum="hash123"
    )  # Different path/type
    item3 = Item(
        path="/path3.txt", type=ItemType.SLIDE, md5sum="hash456"
    )  # Different hash
    item4 = Item(path="/path4.txt", type=ItemType.SLIDE, md5sum="hash123")  # Same hash

    assert item1 == item2  # Same hash and extra (None)
    assert item1 != item3  # Different hash
    assert item1 == item4  # Same hash and extra
    assert item1 != "not_an_item"  # Different type


def test_item_equality_with_extra():
    item1 = Item(
        path="/path1.txt", type=ItemType.SLIDE, md5sum="hash123", extra={"key": "value"}
    )
    item2 = Item(
        path="/path2.txt", type=ItemType.SLIDE, md5sum="hash123", extra={"key": "value"}
    )
    item3 = Item(
        path="/path3.txt", type=ItemType.SLIDE, md5sum="hash123", extra={"key": "other"}
    )
    item4 = Item(path="/path4.txt", type=ItemType.SLIDE, md5sum="hash123")  # No extra

    assert item1 == item2  # Same hash and extra
    assert item1 != item3  # Same hash, different extra
    assert item1 != item4  # Same hash, one has extra, other doesn't


def test_item_cache():
    item = Item(
        path="/test/path.txt", type=ItemType.SLIDE, md5sum="hash123", cached=False
    )

    item.cache()

    assert item.cached is True


def test_item_from_yaml():
    yaml_data = {
        "path": "/test/path.txt",
        "type": "slide",
        "cached": True,
        "md5sum": "yaml_hash",
        "force_reset": True,
        "extra": {"duration": 3.0},
    }

    item = Item.from_yaml(yaml_data)

    assert item.path == "/test/path.txt"
    assert item.type == ItemType.SLIDE
    assert item.cached is True
    assert item.md5sum == "yaml_hash"
    assert item.force_reset is True
    assert item.extra == {"duration": 3.0}


def test_item_from_yaml_minimal():
    yaml_data = {
        "path": "/test/path.txt",
        "type": "script",
        "cached": False,
        "md5sum": "yaml_hash",
    }

    item = Item.from_yaml(yaml_data)

    assert item.path == "/test/path.txt"
    assert item.type == ItemType.SCRIPT
    assert item.cached is False
    assert item.md5sum == "yaml_hash"
    assert item.force_reset is False  # Default value
    assert item.extra is None  # Default value


def test_item_to_yaml():
    item = Item(
        path="/test/path.txt",
        type=ItemType.VOICE,
        md5sum="hash123",
        cached=True,
        force_reset=True,
        extra={"format": "wav"},
    )

    yaml_data = item.to_yaml()

    expected = {
        "path": "/test/path.txt",
        "type": "voice",
        "cached": True,
        "md5sum": "hash123",
        "force_reset": True,
        "extra": {"format": "wav"},
    }

    assert yaml_data == expected


def test_item_to_yaml_minimal():
    item = Item(
        path="/test/path.txt",
        type=ItemType.VIDEO,
        md5sum="hash123",
        cached=False,
        force_reset=False,
    )

    yaml_data = item.to_yaml()

    expected = {
        "path": "/test/path.txt",
        "type": "video",
        "cached": False,
        "md5sum": "hash123",
        "force_reset": False,
    }

    assert yaml_data == expected
    # extra should not be present when it's None


class MockTTSEngine(TTSEngine):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        pass

    def parallizable(self) -> bool:
        return True


def test_task_init():
    slide_item = Item(path="/slide.pdf", type=ItemType.SLIDE, md5sum="slide_hash")
    script_item = Item(path="/script.txt", type=ItemType.SCRIPT, md5sum="script_hash")
    tts_engine = MockTTSEngine()

    task = Task(
        id="task_1",
        slide=slide_item,
        script=script_item,
        output_dir="/output",
        tts_engine=tts_engine,
        delay=2.5,
        lock=None,
    )

    assert task.id == "task_1"
    assert task.slide == slide_item
    assert task.script == script_item
    assert task.output_dir == "/output"
    assert task.tts_engine == tts_engine
    assert task.delay == 2.5
    assert task.lock is None


def test_task_init_with_lock():
    from multiprocessing import Manager

    manager = Manager()
    lock = manager.Lock()

    slide_item = Item(path="/slide.pdf", type=ItemType.SLIDE, md5sum="slide_hash")
    script_item = Item(path="/script.txt", type=ItemType.SCRIPT, md5sum="script_hash")
    tts_engine = MockTTSEngine()

    task = Task(
        id="task_1",
        slide=slide_item,
        script=script_item,
        output_dir="/output",
        tts_engine=tts_engine,
        delay=1.0,
        lock=lock,
    )

    assert task.lock == lock
