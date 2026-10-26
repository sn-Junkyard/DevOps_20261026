"""B02: a symlink input must fail before invoking Docker or writing output."""
from unittest.mock import patch

import pytest

from draft.autobuild import auto_build


def test_symlink_fixture_rejected_before_docker(tmp_path):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    source = tmp_path / "outside.c"
    source.write_text("int main(void) { return 0; }\n")
    (fixture / "main.c").symlink_to(source)
    candidate = tmp_path / "Dockerfile"
    candidate.write_text("FROM placeholder\n")
    output = tmp_path / "output"

    with patch("draft.autobuild.execute") as docker:
        with pytest.raises(ValueError, match="Symlink fixtures are unsupported"):
            auto_build(fixture, candidate, output, "hello E3")
        docker.assert_not_called()
    assert not output.exists()
