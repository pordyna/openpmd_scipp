"""Tests for DataLoader construction."""

import openpmd_scipp.loader as loader


def test_data_loader_uses_read_only_access_by_default(monkeypatch):
    """A path-only call preserves the read-only Series construction behavior."""
    created_series = object()
    calls = []

    def create_series(*args, **kwargs):
        calls.append((args, kwargs))
        return created_series

    iterations = object()
    monkeypatch.setattr(loader.pmd, "Series", create_series)
    monkeypatch.setattr(loader, "get_iterations", lambda series: iterations)

    data_loader = loader.DataLoader("data%T.h5")

    assert calls == [(("data%T.h5", loader.pmd.Access.read_only), {})]
    assert data_loader.series is created_series
    assert data_loader.iterations is iterations


def test_data_loader_forwards_access_and_extra_series_arguments(monkeypatch):
    """An explicit access mode and extra Series arguments are forwarded unchanged."""
    created_series = object()
    calls = []

    def create_series(*args, **kwargs):
        calls.append((args, kwargs))
        return created_series

    monkeypatch.setattr(loader.pmd, "Series", create_series)
    monkeypatch.setattr(loader, "get_iterations", lambda series: object())
    access = loader.pmd.Access.create
    options = '{"backend": "adios2"}'
    communicator = object()

    loader.DataLoader(
        "data%T.bp", access, options, communicator=communicator, defer_iteration_parsing=True
    )

    assert calls == [
        (
            ("data%T.bp", access, options),
            {"communicator": communicator, "defer_iteration_parsing": True},
        )
    ]
