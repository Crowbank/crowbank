import pytest


def test_server(pa):
    server_name = pa.env.get_server()
    assert(server_name.upper() == 'HP-SERVER\\SQLEXPRESS_DEV')


def test_petadmin(loaded_pa):
    customer_count = len(loaded_pa.customers.customers)
    pet_count = len(loaded_pa.pets.pets)
    booking_count = len(loaded_pa.bookings.bookings)

    assert(customer_count == 2642)
    assert(pet_count == 3291)
    assert(booking_count == 6665)


def test_create_customer(loaded_pa):
    from pypa.customer import Customer
    new_customer = Customer(-1)

    new_customer.surname = 'Smith'
    new_customer.forename = 'John'
    new_customer.addr1 = '1 Main Street'
    new_customer.addr3 = 'Cumbernauld'
    new_customer.postcode = 'G67 1XX'
    new_customer.email = 'test1@crowbank.co.uk'
    new_customer.telno_mobile = '07777555555'

    new_customer.write(loaded_pa.env)

    loaded_pa.load(force=True)

    customer_count = len(loaded_pa.customers.customers)
    assert(customer_count == 2643)
