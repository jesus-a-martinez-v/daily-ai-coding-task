import logging

import pytest

from test_tools.stubber_factory import stubber_factory

logger = logging.getLogger(__name__)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integ: integration test that requires and uses AWS resources. " "",
    )


@pytest.fixture(name="make_stubber")
def fixture_make_stubber(request, monkeypatch):
    """
    Return a factory function that makes an object configured either
    to pass calls through to AWS or to use stubs.
    """

    def _make_stubber(service_client):
        """
        Create a class that wraps the botocore Stubber and implements a variety of
        stub functions that can be used in unit tests for the specified service client.

        After tests complete, the stubber checks that no more responses remain in its
        queue. This lets tests verify that all expected calls were actually made during
        the test.

        When tests are run against an actual AWS account, the stubber does not
        set up stubs and passes all calls through to the Boto 3 client.
        """
        fact = stubber_factory(service_client.meta.service_model.service_name)
        stubber = fact(service_client)

        def fin():
            stubber.assert_no_pending_responses()
            stubber.deactivate()

        request.addfinalizer(fin)
        stubber.activate()

        return stubber

    return _make_stubber
