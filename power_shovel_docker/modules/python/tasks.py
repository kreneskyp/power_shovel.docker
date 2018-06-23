from power_shovel.config import CONFIG
from power_shovel.modules.filesystem.file_hash import FileHash
from power_shovel.task import task
from power_shovel_docker.modules.docker.checker import DockerVolumeExists
from power_shovel_docker.modules.docker.tasks import compose
from power_shovel_docker.modules.docker.utils import docker_client


def python_local_package_mount_flags():
    return []


@task(
    category='testing',
    short_description='Run all test tasks'
)
def test():
    """Virtual target for testing"""


@task(
    category='testing',
    short_description='Run all python test tasks'
)
def test_python():
    """Virtual target for python tests"""


@task(
    category='libraries',
    short_description='PipEnv environment manager'
)
def pipenv(*args):
    """
    Run a pipenv command.

    This runs in the builder container with volumes mounted.
    """
    compose('pipenv', *args)


def clean_pipenv():
    """
    Remove pipenv volume
    """
    print('clean pipenv')
    volume = docker_client().volumes.get(CONFIG.PYTHON.VIRTUAL_ENV_VOLUME)
    volume.remove(True)


@task(
    category='build',
    clean=clean_pipenv,
    short_description='Install python packages with pipenv',
    parent='build_app',
    check=[
        FileHash('Pipfile', 'Pipfile.lock'),
        DockerVolumeExists('{PYTHON.VIRTUAL_ENV_VOLUME}')
    ]
)
def build_pipenv(*args):
    """Run pipenv install"""
    pass
    #compose('pipenv install', flags=['--dev'], *args)
