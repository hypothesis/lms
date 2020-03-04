import os
from unittest import mock

import pytest

from lms.assets import _CachedFile


class Test_CachedFile:
    ASSET_INI_CONTENTS = "assets.ini contents"
    DOCKER_FILE_CONTENTS = "Dockerfile contents"

    def test_we_can_load_a_file(self, assets_ini, loader):
        cached = _CachedFile(assets_ini, loader)
        contents = cached.load()

        assert contents == self.ASSET_INI_CONTENTS

    def test_we_can_load_a_file_outside_of_our_package(self, dockerfile, loader):
        cached = _CachedFile(dockerfile, loader)
        contents = cached.load()

        assert contents == self.DOCKER_FILE_CONTENTS

    def test_we_check_paths_when_created(self, loader):
        with pytest.raises(FileNotFoundError):
            _CachedFile("not_a_file.txt", loader)

    def test_we_cache_files(self, assets_ini, loader):
        cached = _CachedFile(assets_ini, loader)
        cached.load()
        contents = cached.load()

        loader.assert_called_once()
        assert contents == self.ASSET_INI_CONTENTS

    def test_we_read_from_the_cache_if_the_mtime_changes(self, assets_ini, loader):
        cached = _CachedFile(assets_ini, loader, auto_reload=False)

        cached.load()
        self.age_file(assets_ini, -2000)  # 2 seconds into the future
        cached.load()

        assert loader.call_count == 1

    def test_we_auto_reload_if_the_mtime_changes_aith_auto_reload_True(
        self, assets_ini, loader
    ):
        cached = _CachedFile(assets_ini, loader, auto_reload=True)

        cached.load()
        self.age_file(assets_ini, -2000)  # 2 seconds into the future
        cached.load()

        assert loader.call_count == 2

    @classmethod
    def age_file(cls, filename, age):
        info = os.stat(filename)

        os.utime(filename, (info.st_atime - age, info.st_mtime - age))

    @pytest.fixture(autouse=True)
    def resource_filename(self, patch, tmp_path):
        resource_filename = patch("lms.assets.resource_filename")

        resource_filename.return_value = tmp_path

        return resource_filename

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
        return dockerfile

    @pytest.fixture
    def assets_ini(self, lms_dir):
        old_file = lms_dir / "assets.ini"
        old_file.write_text(self.ASSET_INI_CONTENTS)

        return old_file
