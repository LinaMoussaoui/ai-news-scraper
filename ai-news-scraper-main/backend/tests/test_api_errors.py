import pytest

from backend.utils.api_errors import require_callable, structured_http_exception


def test_structured_http_exception_payload_shape():
    exc = structured_http_exception(
        500,
        "TEST_ERROR",
        "Something failed",
        "Fix the failing dependency",
        details={"path": "/demo"},
    )

    assert exc.status_code == 500
    assert exc.detail["error_code"] == "TEST_ERROR"
    assert exc.detail["error_message"] == "Something failed"
    assert exc.detail["suggested_fix"] == "Fix the failing dependency"
    assert exc.detail["details"]["path"] == "/demo"


def test_require_callable_raises_for_missing_method():
    class Dummy:
        pass

    with pytest.raises(Exception) as err:
        require_callable(Dummy(), "missing", "MISSING_METHOD", "Implement it")

    assert getattr(err.value, "status_code", None) == 500
    assert err.value.detail["error_code"] == "MISSING_METHOD"