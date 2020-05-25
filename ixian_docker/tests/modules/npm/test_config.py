# Copyright [2018-2020] Peter Krenesky
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from ixian.config import CONFIG


EXPECTED_FIELDS = [
    "BIN",
    "DOCKERFILE",
    "IMAGE",
    "IMAGE_FILES",
    "IMAGE_TAG",
    "MODULE_DIR",
    "NODE_MODULES_DIR",
    "PACKAGE_JSON",
    "REPOSITORY",
    "VOLUME",
]


class TestNPMConfig:
    @pytest.mark.parametrize("field", EXPECTED_FIELDS)
    def test_read(self, field, mock_npm_environment, snapshot):
        """
        Test reading default config values and testing property getter functions.
        """
        snapshot.assert_match(getattr(CONFIG.NPM, field))

    def test_task_hash(self, mock_npm_environment, snapshot):
        snapshot.assert_match(CONFIG.TASKS.BUILD_NPM_IMAGE)
