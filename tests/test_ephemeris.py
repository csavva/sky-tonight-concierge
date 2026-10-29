from sky_tonight.tools import ephemeris


def test_cache_dir_respects_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SKY_TONIGHT_CACHE", str(tmp_path / "eph"))
    assert ephemeris.cache_dir() == tmp_path / "eph"
    assert (tmp_path / "eph").is_dir()


def test_ephemeris_has_planets():
    eph = ephemeris.ephemeris()
    for body in ("sun", "moon", "earth", "mars", "jupiter barycenter"):
        assert body in eph
