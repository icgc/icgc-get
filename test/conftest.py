import pytest
import os


@pytest.fixture(scope="session")
def config():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    conf = path + "/config_dev.yaml"
    return conf


@pytest.fixture(scope="session")
def data_dir():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    dir = path + '/mnt/downloads/'
    return dir

@pytest.fixture(scope="session")
def manifest_dir():
    manifest_directory = os.path.abspath(os.path.dirname(__file__))
    return manifest_directory


def file_test(file_info, size):
    return file_info.st_size == size and oct(file_info.st_mode & 755)


def get_info(data, filename):
    if os.path.isfile(data + filename):
        file_info = os.stat(data + filename)
        return file_info
    else:
        assert 0  # file not found
