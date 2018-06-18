from power_shovel import task
from power_shovel.config import CONFIG
from power_shovel.modules.filesystem.file_hash import FileHash
from power_shovel.utils.process import execute
from power_shovel_docker.modules.docker.utils import build_image
from power_shovel_docker.modules.docker.utils import convert_volume_flags
from power_shovel_docker.modules.docker import utils


@task(
    category='Docker',
    check=FileHash(
        '{POWER_SHOVEL}',
        '{DOCKER.ROOT_MODULE_DIR}'
    ),
    short_description='build app\'s dockerfile',
)
def build_dockerfile():
    text = utils.build_dockerfile()
    with open(CONFIG.DOCKER.DOCKER_FILE, 'w') as dockerfile:
        dockerfile.write(text)


@task(
    category='docker',
    check=FileHash(
        'Dockerfile'
    ),
    depends=[build_dockerfile],
    short_description='Build app image'
)
def build_app():
    """Builds the docker app using CONFIG.DOCKER_FILE"""
    build_image(CONFIG.PROJECT_NAME, CONFIG.DOCKER.DOCKER_FILE)


@task(
    category='docker',
    short_description='Docker compose command'
)
def compose(*args, **kwargs):
    """
    Docker compose run a command in `app`
    :param args:
    :param kwargs:
    :return:
    """
    args_str = CONFIG.format(' '.join(args))
    flags = ' '.join(kwargs.pop('flags', []))

    # convert volume configs provided by modules into flags to pass to compose
    volumes = ' '.join(convert_volume_flags(
        CONFIG.DOCKER.DEV_VOLUMES +
        CONFIG.DOCKER.VOLUMES))

    execute(CONFIG.format(
        'docker-compose run {volumes} '
        '-e APP_DIR={DOCKER.APP_DIR} '
        '-e ROOT_MODULE_PATH={PYTHON.ROOT_MODULE_PATH} '
        ' --rm {flags} app {args}',
        args=args_str,
        volumes=volumes,
        flags=flags
    ))


# =============================================================================
#  Container modules
# =============================================================================


@task(
    category='Docker',
    short_description='Bash shell in docker container'
)
def bash(*args):
    """Open a bash shell in container"""
    compose('/bin/bash', *args)


@task(
    category='Docker',
    short_description='Start docker container'
)
def up():
    """Start app in test-container"""
    compose('up -d app')


@task(
    category='Docker',
    short_description='Stop docker container'
)
def down():
    compose('down')


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

