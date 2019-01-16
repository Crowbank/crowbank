import pytest
from pypa.env import Environment, log


@pytest.fixture(scope="session")
def env():
    the_env = Environment('Testing', 'test')
    the_env.configure_logger(log)

    yield the_env
    the_env.connection.rollback()


@pytest.fixture(scope="session")
def pa(env):
    from pypa.petadmin import PetAdmin

    print("creating PetAdmin object")
    pa = PetAdmin(env)
    yield pa
    print("Rolling Back")
    pa.env.connection.rollback()


@pytest.fixture(scope="session")
def loaded_pa(pa):
    pa.load()

    yield pa
