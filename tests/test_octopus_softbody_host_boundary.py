"""The isolated physical fixture must reject an artist GUI before any work."""

import importlib
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("operation", ["probe", "fit", "inspect"])
def test_artist_gui_rejected_before_case_io_or_host_mutation(monkeypatch, tmp_path, operation):
    examples = Path(__file__).resolve().parents[1] / "examples" / "showcase"
    monkeypatch.syspath_prepend(str(examples))
    # Any further host call would fail: the GUI must be rejected first.
    monkeypatch.setitem(sys.modules, "hou", SimpleNamespace(isUIAvailable=lambda: True))
    softbody = importlib.import_module("houdini_octopus_softbody")
    absent_case = tmp_path / "unprepared-case"
    with pytest.raises(ValueError, match="isolated headless Houdini"):
        getattr(softbody, operation)(absent_case)
    assert not absent_case.exists()
