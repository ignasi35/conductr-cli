import os

DEFAULT_DOCKER_MACHINE_NAME = 'default'
DEFAULT_DOCKER_MACHINE_RAM_SIZE = '2048'


def vm_name():
    return os.getenv('DOCKER_MACHINE_NAME', DEFAULT_DOCKER_MACHINE_NAME)