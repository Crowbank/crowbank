import pytest


@pytest.fixture(scope="module")
def pa():
    from pypa.petadmin.petadmin import PetAdmin
    from pypa.petadmin.env import Environment, clean_html, log, ENVIRONMENT

    env = Environment('dev')
    env.configure_logger(log)

    print("creating PetAdmin object")
    pa = PetAdmin(env)
    yield pa

    print ("All done")

def test_petadmin(pa):
    print("starting test_petadmin")
    pa.load()

    customer_count = len(pa.customers.customers)
    pet_count = len(pa.pets.pets)
    booking_count = len(pa.bookings.bookings)

    assert(customer_count == 2647)
    assert(pet_count == 3305)
    assert(booking_count == 6709)
