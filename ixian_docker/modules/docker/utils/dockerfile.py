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

import jinja2
import os

from ixian.build import write_file
from ixian.config import CONFIG


def get_dockerfile(path: str, render_to: str = None):
    """
    Get the dockerfile for `path`. If the path ends in .jinja it will be rendered to `render_to`.
    :param path: original path of dockerfile
    :param render_to: render to this file if
    :return: path to dockerfile
    """
    if path.endswith(".jinja"):
        dockerfile = render_to
        write_file(dockerfile, build_dockerfile(path))
    else:
        dockerfile = path
    return dockerfile


def build_dockerfile(template_path=None, context=None):
    """Build dockerfile from configured modules and settings.

    :param template_path: base template to use for rendering Dockerfile
    :return: DockerFile as a string.
    """

    # build loader that includes files from:
    #  - directory for base template
    #  - directories for each of the module's template snippets.
    path, filename = os.path.split(template_path or CONFIG.DOCKER.DOCKERFILE_TEMPLATE)
    prefixes = {"base": jinja2.FileSystemLoader(path)}
    loader = jinja2.PrefixLoader(prefixes)

    # render template
    environment = jinja2.Environment(loader=loader)
    template = environment.get_template("base/%s" % filename)
    return template.render({"CONFIG": CONFIG})
