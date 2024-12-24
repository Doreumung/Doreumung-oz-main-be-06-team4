import pytest


@pytest.fixture
def sample_data() -> list[int]:
    return [1, 2, 3, 4, 5]


def test_data(sample_data: list[int]) -> None:
    assert len(sample_data) == 5
