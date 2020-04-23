from copy import deepcopy

import docker
import logging
from power_shovel.task import Task, VirtualTarget
from power_shovel.config import CONFIG
from power_shovel.modules.filesystem.file_hash import FileHash
from power_shovel.utils.process import execute
from power_shovel_docker.modules.docker.checker import DockerImageExists
from power_shovel_docker.modules.docker.utils.compose import run
from power_shovel_docker.modules.docker.utils.images import (
    build_image_if_needed,
    pull_image,
    push_image,
)
from power_shovel_docker.modules.docker.utils.client import docker_client
from power_shovel_docker.modules.docker import utils


logger = logging.getLogger(__name__)


class CleanDocker(Task):
    """
    Clean Docker:
        - kill and remove all containers
    """

    name = "clean_docker"
    category = "docker"

    def execute(self):
        execute("docker-compose kill")
        execute("docker-compose rm -f -v")


class BuildDockerfile(Task):
    """
    Build dockerfile from configured modules and settings.

    This compiles a dockerfile based on the settings for the project. Each
    module may provide a jinja template snippet. The snippets are passed to
    a base template that renders them.

    The base template is read from {{DOCKER.DOCKERFILE_TEMPLATE}}. The base
    template is passed CONFIG and MODULES in the context.

    Each module may have template snippet to include.

    The compiled Dockerfile is written to {{CONFIG.DOCKER.DOCKER_FILE}}.

    Config:
        - DOCKER.DOCKERFILE_TEMPLATE:  Jinja2 base template.
        - DOCKER.DOCKER_FILE:          Dockerfile output.
    """

    name = "build_dockerfile"
    category = "build"
    check = FileHash("{POWER_SHOVEL}", "shovel.py")
    short_description = "build app's dockerfile"

    def execute(self):
        text = utils.build_dockerfile()
        with open(CONFIG.DOCKER.DOCKER_FILE, "w") as dockerfile:
            dockerfile.write(text)


def remove_image():
    try:
        image = docker_client().images.get(CONFIG.DOCKER.IMAGE)
    except docker.errors.NotFound:
        pass
    else:
        image.remove(True)


class BuildImage(Task):
    """Builds a docker image using CONFIG.DOCKER_FILE"""

    name = "build_image"
    category = "build"
    check = [
        FileHash(
            "{DOCKER.DOCKERFILE}",
            # TODO: FileHash should recursively expand and format list values
            # *CONFIG.format('{DOCKER.BASE_IMAGE_FILES}')
        ),
        DockerImageExists("{DOCKER.IMAGE}"),
    ]
    clean = remove_image
    short_description = "Build app image"

    def execute(self, pull=True):
        build_image_if_needed(
            repository=CONFIG.DOCKER.REPOSITORY,
            tag=CONFIG.DOCKER.IMAGE_TAG,
            dockerfile=CONFIG.DOCKER.DOCKERFILE,
            force=self.__task__.force,
            pull=pull,
            buildargs={
                "PYTHON_IMAGE": CONFIG.PYTHON.IMAGE,
                "COMPILED_STATIC_IMAGE": CONFIG.WEBPACK.IMAGE,
                "BOWER_IMAGE": CONFIG.BOWER.IMAGE,
            },
        )
        # TODO: this is why All is needed, to encapsulate running a list of checkers
        # recheck=self.check.check)


class BuildBaseImage(Task):
    """Builds the docker app image using CONFIG.DOCKER_FILE"""

    name = "build_base_image"
    category = "build"
    parent = "build_image"
    check = [
        FileHash(
            "{DOCKER.DOCKERFILE_BASE}", *CONFIG.resolve("DOCKER.BASE_IMAGE_FILES")
        ),
        DockerImageExists("{DOCKER.BASE_IMAGE}"),
    ]
    clean = remove_image
    short_description = "Build app image"

    def execute(self, pull=True):
        build_image_if_needed(
            repository=CONFIG.DOCKER.REPOSITORY,
            tag=CONFIG.DOCKER.BASE_IMAGE_TAG,
            dockerfile=CONFIG.DOCKER.DOCKERFILE_BASE,
            force=self.__task__.force,
            pull=pull,
        )
        # TODO: this is why All is needed, to encapsulate running a list of checkers
        # recheck=self.check.check)


class PullImage(Task):
    """
    Pull the Image as specified by {DOCKER.IMAGE}
    """

    name = "pull"
    short_description = "Pull the image"

    def execute(self):
        pull_image(CONFIG.DOCKER.IMAGE)


class PushImage(Task):
    """
    Push the Image as specified by {DOCKER.IMAGE}
    """

    name = "push"
    short_description = "Push the image"

    def execute(self):
        logger.info(f"pushing docker image {CONFIG.DOCKER.IMAGE}")
        push_image(CONFIG.DOCKER.REPOSITORY, CONFIG.DOCKER.IMAGE_TAG)


class PushBaseImage(Task):
    """
    Push the Image as specified by {DOCKER.IMAGE}
    """

    name = "push_base_image"
    short_description = "Push the base image"

    def execute(self):
        logger.info(f"pushing docker image {CONFIG.DOCKER.BASE_IMAGE}")
        push_image(CONFIG.DOCKER.REPOSITORY, CONFIG.DOCKER.BASE_IMAGE_TAG)


class ComposeRuntime(VirtualTarget):
    name = "compose_runtime"
    category = "docker"
    short_description = "Build development image & volumes for docker-compose "


# TODO: TaskRunner/Shim doesn't support multiple args or kwargs. fix that.
class Compose(Task):
    """
    Docker compose run a command in `app`

    :param command: command and args as single string.
    :param app: docker-compose app to run, default is {DOCKER.DEFAULT_APP}
    :param flags: docker-compose flags
    :param env: ENV variables to set.
    :param volumes: volumes to set.
    :return:
    """

    name = "compose"
    category = "docker"
    short_description = "Docker compose command"
    depends = ["compose_runtime"]

    def execute(self, command=None, *args, **kwargs):
        run(command, *args, **kwargs)


# =============================================================================
#  Container modules
# =============================================================================


class Bash(Task):
    """Open a bash shell in container"""

    name = "bash"
    category = "Docker"
    short_description = "Bash shell in docker container"
    depends = ["compose_runtime"]

    def execute(self, *args):
        return run("/bin/bash", *args)


class Up(Task):
    """Start app container"""

    name = "up"
    category = "Docker"
    short_description = "Start docker container"
    depends = ["compose_runtime"]

    def execute(self):
        return run("up -d app")


class Down(Task):
    """Stop app container"""

    name = "task"
    category = "Docker"
    short_description = "Stop docker container"
    depends = ["compose_runtime"]

    def execute(self):
        return compose("down")


# =============================================================================
#  Cleanup
# =============================================================================


def docker_full_teardown():
    # TODO this doesn't work yet because can't pipe commands
    # TODO split these into individual tasks kill_containers|clean_containers|clean_images
    # TODO add clean_volumes
    # TODO --force should be passed to docker commands where appropriate.
    execute("docker ps -q | xargs docker kill")
    execute("docker ps -q -a | xargs docker rm -v")
    execute("docker images -q | xargs docker rmi")
