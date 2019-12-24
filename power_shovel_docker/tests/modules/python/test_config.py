import pytest

from power_shovel.config import CONFIG


EXPECTED_FIELDS = [
    "BIN",
    "DOCKERFILE",
    "HOST_ROOT_MODULE_PATH",
    "IMAGE",
    "IMAGE_HASH",
    "IMAGE_TAG",
    "MODULE_DIR",
    "REPOSITORY",
    "REQUIREMENTS",
    "ROOT_MODULE",
    "ROOT_MODULE_PATH",
    "VIRTUAL_ENV",
    "VIRTUAL_ENV_DIR",
    "VIRTUAL_ENV_RUN",
]


class TestPythonConfig:
    @pytest.mark.parametrize("field", EXPECTED_FIELDS)
    def test_read(self, field, mock_python_environment, snapshot):
        """
        Test reading default config values and testing property getter functions.
        """
        snapshot.assert_match(getattr(CONFIG.PYTHON, field))
