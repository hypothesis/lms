import os
import os.path
from unittest import mock

import pytest

from lms.assets import _CachedFile


class Test_CachedFile:
    ASSET_INI_CONTENTS = "assets.ini contents"
    DOCKER_FILE_CONTENTS = "Dockerfile contents"

    def test_it_calculates_the_root_directory_correctly(self):
        # We don't know where we are or where the root is necessarily, but we
        # know where we are relative to the root path
        rel_path = os.path.relpath(__file__, _CachedFile.ROOT_DIR)

        assert rel_path == "tests/unit/lms/assets_test.py"

    def test_we_can_load_a_file(self, CachedFile, assets_ini, loader):
        cached = CachedFile(assets_ini, loader)
        contents = cached.load()

        assert contents == self.ASSET_INI_CONTENTS

    def test_we_can_load_a_file_outside_of_our_package(
        self, CachedFile, dockerfile, loader
    ):
        cached = CachedFile(dockerfile, loader)
        contents = cached.load()

        assert contents == self.DOCKER_FILE_CONTENTS

    def test_we_check_paths_when_created(self, loader):
        with pytest.raises(FileNotFoundError):
            _CachedFile("not_a_file.txt", loader)

    def test_we_cache_files(self, CachedFile, assets_ini, loader):
        cached = CachedFile(assets_ini, loader)
        cached.load()
        contents = cached.load()

        loader.assert_called_once()
        assert contents == self.ASSET_INI_CONTENTS

    def test_we_read_from_the_cache_if_the_mtime_changes(
        self, CachedFile, assets_ini, loader, tmpdir
    ):
        cached = CachedFile(assets_ini, loader, auto_reload=False)

        cached.load()
        self.age_file(tmpdir / assets_ini, -2000)  # 2 seconds into the future
        cached.load()

        assert loader.call_count == 1

    def test_we_auto_reload_if_the_mtime_changes_aith_auto_reload_True(
        self, CachedFile, assets_ini, loader, tmpdir
    ):
        cached = CachedFile(assets_ini, loader, auto_reload=True)

        cached.load()
        self.age_file(tmpdir / assets_ini, -2000)  # 2 seconds into the future
        cached.load()

        assert loader.call_count == 2

    @classmethod
    def age_file(cls, filename, age):
        info = os.stat(filename)

        os.utime(filename, (info.st_atime - age, info.st_mtime - age))

    @pytest.fixture
    def CachedFile(self, tmpdir):
        class CachedFile(_CachedFile):
            ROOT_DIR = tmpdir

        return CachedFile

    @pytest.fixture
    def loader(self):
        def reader(handle):
            return handle.read()

        loader = mock.create_autospec(spec=reader)
        loader.side_effect = reader
        return loader

    @pytest.fixture
    def lms_dir(self, tmp_path):
        lms_dir = tmp_path / "lms"
        lms_dir.mkdir()

        return lms_dir

    @pytest.fixture
    def dockerfile(self, tmp_path):
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text(self.DOCKER_FILE_CONTENTS)

        # Files are relative to root
        return "Dockerfile"

    @pytest.fixture
    def assets_ini(self, lms_dir):
        assets_ini = lms_dir / "assets.ini"
        assets_ini.write_text(self.ASSET_INI_CONTENTS)

        # Files are relative to root
        return "lms/assets.ini"
