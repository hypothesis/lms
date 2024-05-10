from unittest.mock import Mock, create_autospec, sentinel

import pytest

from lms.models import ApplicationInstance
from lms.services.exceptions import ExternalRequestError
from lms.services.moodle import MoodleAPIClient


class TestMoodleAPIClient:
    def test_failed_request(self, svc, http_service):
        http_service.post.return_value.json.return_value = {
            "errorcode": "ERROR_CODE",
            "message": "MESSAGE",
        }

        with pytest.raises(ExternalRequestError) as exc:
            svc.course_group_sets("COURSE_ID")

        exc.validation_errors = {
            "errorcode": "ERROR_CODE",
            "message": "MESSAGE",
        }

    def test_course_group_sets(self, svc, http_service, group_sets):
        http_service.post.return_value.json.return_value = group_sets

        api_group_sets = svc.course_group_sets("COURSE_ID")

        http_service.post.assert_called_once_with(
            f"sentinel.lms_url/{svc.API_PATH}?wstoken=sentinel.token&moodlewsrestformat=json&wsfunction=core_group_get_course_groupings",
            params={"courseid": "COURSE_ID"},
        )
        assert api_group_sets == group_sets

    def test_group_set_groups(self, svc, http_service, groups):
        http_service.post.return_value.json.return_value = [{"groups": groups}]

        api_groups = svc.group_set_groups(100, "GROUP_SET")

        http_service.post.assert_called_once_with(
            "sentinel.lms_url/webservice/rest/server.php?wstoken=sentinel.token&moodlewsrestformat=json&wsfunction=core_group_get_groupings&groupingids[0]=GROUP_SET&returngroups=1",
            params=None,
        )
        assert api_groups == [
            {"id": g["id"], "name": g["name"], "group_set_id": "GROUP_SET"}
            for g in groups
        ]

    def test_groups_for_user(self, svc, http_service, groups):
        http_service.post.return_value.json.return_value = {"groups": groups}

        api_groups = svc.groups_for_user("COURSE_ID", "GROUP_SET", "USER_ID")

        http_service.post.assert_called_once_with(
            "sentinel.lms_url/webservice/rest/server.php?wstoken=sentinel.token&moodlewsrestformat=json&wsfunction=core_group_get_course_user_groups&groupingid=GROUP_SET&userid=USER_ID&courseid=COURSE_ID",
            params=None,
        )
        assert api_groups == [
            {"id": g["id"], "name": g["name"], "group_set_id": "GROUP_SET"}
            for g in groups
        ]

    def test_course_contents(self, svc, http_service):
        http_service.post.return_value.json.return_value = sentinel.contents

        api_contents = svc.course_contents("COURSE_ID")

        http_service.post.assert_called_once_with(
            "sentinel.lms_url/webservice/rest/server.php?wstoken=sentinel.token&moodlewsrestformat=json&wsfunction=core_course_get_contents",
            params={"courseid": "COURSE_ID"},
        )
        assert api_contents == sentinel.contents

    def test_page_not_found(self, svc, http_service, pages):
        http_service.post.return_value.json.return_value = {"pages": pages}

        assert not svc.page("COURSE_ID", "100")

    def test_page(self, svc, http_service, pages):
        http_service.post.return_value.json.return_value = {"pages": pages}

        page = svc.page("COURSE_ID", "1")

        http_service.post.assert_called_once_with(
            "sentinel.lms_url/webservice/rest/server.php?wstoken=sentinel.token&moodlewsrestformat=json&wsfunction=mod_page_get_pages_by_courses&courseids[0]=COURSE_ID",
            params=None,
        )
        assert page == {
            "id": "ID 1",
            "course_module": "1",
            "title": "PAGE 1",
            "body": "HTML 1",
        }

    def test_list_files(self, svc, http_service, contents):
        http_service.post.return_value.json.return_value = contents

        api_files = svc.list_files("COURSE_ID")

        assert api_files == [
            {
                "type": "Folder",
                "display_name": "General",
                "id": "COURSE_ID-General",
                "lms_id": "COURSE_ID-General",
                "children": [
                    {
                        "type": "File",
                        "display_name": "dummy.pdf",
                        "mime_type": "application/pdf",
                        "id": "moodle://file/course/COURSE_ID/url/https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1046/mod_resource/content/1/dummy.pdf?forcedownload=1",
                        "lms_id": "https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1046/mod_resource/content/1/dummy.pdf?forcedownload=1",
                        "updated_at": 1707992547 * 1000,
                    },
                    {
                        "type": "Folder",
                        "display_name": "A Folder",
                        "id": "COURSE_ID-A Folder",
                        "lms_id": "COURSE_ID-A Folder",
                        "children": [
                            {
                                "type": "File",
                                "display_name": "dummy.pdf",
                                "mime_type": "application/pdf",
                                "id": "moodle://file/course/COURSE_ID/url/https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1134/mod_folder/content/3/dummy.pdf?forcedownload=1",
                                "lms_id": "https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1134/mod_folder/content/3/dummy.pdf?forcedownload=1",
                                "updated_at": 1708513742 * 1000,
                            },
                            {
                                "type": "Folder",
                                "display_name": "Nested folder",
                                "id": "COURSE_ID-Nested folder",
                                "lms_id": "COURSE_ID-Nested folder",
                                "children": [
                                    {
                                        "type": "File",
                                        "display_name": "FILE IN NESTED.pdf",
                                        "mime_type": "application/pdf",
                                        "id": "moodle://file/course/COURSE_ID/url/https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1134/mod_folder/content/3/Nested%20folder/FILE%20IN%20NESTED.pdf?forcedownload=1",
                                        "lms_id": "https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1134/mod_folder/content/3/Nested%20folder/FILE%20IN%20NESTED.pdf?forcedownload=1",
                                        "updated_at": 1708513801 * 1000,
                                    }
                                ],
                            },
                        ],
                    },
                ],
            }
        ]

    @pytest.mark.parametrize(
        "header,expected",
        [
            ("application/json", False),
            ("application/pdf", True),
        ],
    )
    def test_file_exists(self, svc, http_service, header, expected):
        http_service.request.return_value = Mock(headers={"content-type": header})

        assert svc.file_exists("URL") == expected

        http_service.request.assert_called_once_with("HEAD", "URL&token=sentinel.token")

    def test_list_pages(self, svc, http_service, contents):
        http_service.post.return_value.json.return_value = contents

        api_pages = svc.list_pages("COURSE_ID")

        assert api_pages == [
            {
                "type": "Folder",
                "display_name": "General",
                "id": "COURSE_ID-General",
                "lms_id": "COURSE_ID-General",
                "children": [
                    {
                        "type": "File",
                        "display_name": "A Page",
                        "mime_type": "text/html",
                        "lms_id": 860,
                        "id": "moodle://page/course/COURSE_ID/page_id/860",
                        "updated_at": 1708598607 * 1000,
                    },
                    {
                        "type": "File",
                        "display_name": "Another Page",
                        "mime_type": "text/html",
                        "lms_id": 1860,
                        "id": "moodle://page/course/COURSE_ID/page_id/1860",
                        "updated_at": 1708598607 * 1000,
                    },
                ],
            }
        ]

    def test_factory(
        self,
        http_service,
        aes_service,
        pyramid_request,
        file_service,
    ):
        ai = create_autospec(ApplicationInstance)
        pyramid_request.lti_user.application_instance = ai

        service = MoodleAPIClient.factory(sentinel.context, pyramid_request)

        ai.settings.get_secret.assert_called_once_with(
            aes_service, "moodle", "api_token"
        )

        assert service._lms_url == ai.lms_url  # noqa: SLF001
        assert service._http == http_service  # noqa: SLF001
        assert service._file_service == file_service  # noqa: SLF001
        assert service._token == ai.settings.get_secret.return_value  # noqa: SLF001

    @pytest.fixture
    def group_sets(self):
        return [
            {"id": 1, "name": "1"},
            {"id": 2, "name": "2"},
        ]

    @pytest.fixture
    def groups(self):
        return [
            {"id": 1, "name": "1", "courseid": 100},
            {"id": 2, "name": "2", "courseid": 100},
        ]

    @pytest.fixture
    def contents(self):
        return [
            {
                "id": 48,
                "name": "General",
                "visible": 1,
                "summary": "",
                "summaryformat": 1,
                "section": 0,
                "hiddenbynumsections": 0,
                "uservisible": True,
                "modules": [
                    {
                        "id": 130,
                        "url": "https://hypothesisuniversity.moodlecloud.com/mod/forum/view.php?id=130",
                        "name": "Announcements",
                        "instance": 12,
                        "contextid": 195,
                        "visible": 1,
                        "uservisible": True,
                        "visibleoncoursepage": 1,
                        "modicon": "https://hypothesisuniversity.moodlecloud.com/theme/image.php/boost/forum/1705160259/monologo?filtericon=1",
                        "modname": "forum",
                        "modplural": "Forums",
                        "availability": None,
                        "indent": 0,
                        "onclick": "",
                        "afterlink": None,
                        "activitybadge": [],
                        "customdata": '""',
                        "noviewlink": False,
                        "completion": 0,
                        "downloadcontent": 1,
                        "dates": [],
                        "groupmode": 0,
                    },
                    {
                        "id": 773,
                        "url": "https://hypothesisuniversity.moodlecloud.com/mod/resource/view.php?id=773",
                        "name": "A PDF",
                        "instance": 8,
                        "contextid": 1046,
                        "visible": 1,
                        "uservisible": True,
                        "visibleoncoursepage": 1,
                        "modicon": "https://hypothesisuniversity.moodlecloud.com/theme/image.php/boost/core/1705160259/f/pdf?filtericon=1",
                        "modname": "resource",
                        "modplural": "Files",
                        "availability": None,
                        "indent": 0,
                        "onclick": "",
                        "afterlink": None,
                        "activitybadge": [],
                        "customdata": '{"filtericon":true,"displayoptions":"a:1:{s:10:\\"printintro\\";i:1;}","display":5}',
                        "noviewlink": False,
                        "completion": 0,
                        "downloadcontent": 1,
                        "dates": [],
                        "groupmode": 0,
                        "contents": [
                            {
                                "type": "file",
                                "filename": "dummy.pdf",
                                "filepath": "/",
                                "filesize": 13264,
                                "fileurl": "https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1046/mod_resource/content/1/dummy.pdf?forcedownload=1",
                                "timecreated": 1707992536,
                                "timemodified": 1707992547,
                                "sortorder": 1,
                                "mimetype": "application/pdf",
                                "isexternalfile": False,
                                "userid": 5,
                                "author": "Professor Hypothesis",
                                "license": "allrightsreserved",
                            }
                        ],
                        "contentsinfo": {
                            "filescount": 1,
                            "filessize": 13264,
                            "lastmodified": 1707992547,
                            "mimetypes": ["application/pdf"],
                            "repositorytype": "",
                        },
                    },
                    {
                        "id": 859,
                        "url": "https://hypothesisuniversity.moodlecloud.com/mod/folder/view.php?id=859",
                        "name": "A Folder",
                        "instance": 2,
                        "contextid": 1134,
                        "visible": 1,
                        "uservisible": True,
                        "visibleoncoursepage": 1,
                        "modicon": "https://hypothesisuniversity.moodlecloud.com/theme/image.php/boost/folder/1705160259/monologo?filtericon=1",
                        "modname": "folder",
                        "modplural": "Folders",
                        "availability": None,
                        "indent": 0,
                        "onclick": "",
                        "afterlink": None,
                        "customdata": '""',
                        "noviewlink": False,
                        "completion": 0,
                        "downloadcontent": 1,
                        "dates": [],
                        "groupmode": 0,
                        "contents": [
                            {
                                "type": "file",
                                "filename": "dummy.pdf",
                                "filepath": "/",
                                "filesize": 13264,
                                "fileurl": "https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1134/mod_folder/content/3/dummy.pdf?forcedownload=1",
                                "timecreated": 1708513738,
                                "timemodified": 1708513742,
                                "sortorder": 0,
                                "mimetype": "application/pdf",
                                "isexternalfile": False,
                                "userid": 5,
                                "author": "Professor Hypothesis",
                                "license": "allrightsreserved",
                            },
                            {
                                "type": "file",
                                "filename": "An image.png",
                                "filepath": "/",
                                "filesize": 28060,
                                "fileurl": "https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1134/mod_folder/content/4/An%20image.png?forcedownload=1",
                                "timecreated": 1709296257,
                                "timemodified": 1709296260,
                                "sortorder": 0,
                                "mimetype": "image/png",
                                "isexternalfile": False,
                                "userid": 5,
                                "author": "Professor Hypothesis",
                                "license": "allrightsreserved",
                            },
                            {
                                "type": "file",
                                "filename": "FILE IN NESTED.pdf",
                                "filepath": "/Nested folder/",
                                "filesize": 1296644,
                                "fileurl": "https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1134/mod_folder/content/3/Nested%20folder/FILE%20IN%20NESTED.pdf?forcedownload=1",
                                "timecreated": 1708513795,
                                "timemodified": 1708513801,
                                "sortorder": 0,
                                "mimetype": "application/pdf",
                                "isexternalfile": False,
                                "userid": 5,
                                "author": "Professor Hypothesis",
                                "license": "allrightsreserved",
                            },
                        ],
                        "contentsinfo": {
                            "filescount": 2,
                            "filessize": 1309908,
                            "lastmodified": 1708513801,
                            "mimetypes": ["application/pdf"],
                            "repositorytype": "",
                        },
                    },
                    {
                        "id": 860,
                        "url": "https://hypothesisuniversity.moodlecloud.com/mod/page/view.php?id=860",
                        "name": "A Page",
                        "instance": 2,
                        "contextid": 1135,
                        "visible": 1,
                        "uservisible": True,
                        "visibleoncoursepage": 1,
                        "modicon": "https://hypothesisuniversity.moodlecloud.com/theme/image.php/boost/page/1705160259/monologo?filtericon=1",
                        "modname": "page",
                        "modplural": "Pages",
                        "availability": None,
                        "indent": 0,
                        "onclick": "",
                        "afterlink": None,
                        "customdata": '""',
                        "noviewlink": False,
                        "completion": 0,
                        "downloadcontent": 1,
                        "dates": [],
                        "groupmode": 0,
                        "contents": [
                            {
                                "type": "file",
                                "filename": "Screenshot from 2024-01-16 18-25-46.png",
                                "filepath": "/",
                                "filesize": 133458,
                                "fileurl": "https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1135/mod_page/content/1/Screenshot%20from%202024-01-16%2018-25-46.png?forcedownload=1",
                                "timecreated": 1708598585,
                                "timemodified": 1708598608,
                                "sortorder": 0,
                                "mimetype": "image/png",
                                "isexternalfile": False,
                                "userid": 5,
                                "author": "Professor Hypothesis",
                                "license": "allrightsreserved",
                            },
                            {
                                "type": "file",
                                "filename": "index.html",
                                "filepath": "/",
                                "filesize": 0,
                                "fileurl": "https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1135/mod_page/content/index.html?forcedownload=1",
                                "timecreated": None,
                                "timemodified": 1708598607,
                                "sortorder": 1,
                                "userid": None,
                                "author": None,
                                "license": None,
                            },
                        ],
                        "contentsinfo": {
                            "filescount": 2,
                            "filessize": 133458,
                            "lastmodified": 1708598608,
                            "mimetypes": ["image/png"],
                            "repositorytype": "",
                        },
                    },
                    {
                        "id": 1860,
                        "url": "https://hypothesisuniversity.moodlecloud.com/mod/page/view.php?id=1860",
                        "name": "Another Page",
                        "instance": 2,
                        "contextid": 1135,
                        "visible": 1,
                        "uservisible": True,
                        "visibleoncoursepage": 1,
                        "modicon": "https://hypothesisuniversity.moodlecloud.com/theme/image.php/boost/page/1705160259/monologo?filtericon=1",
                        "modname": "page",
                        "modplural": "Pages",
                        "availability": None,
                        "indent": 0,
                        "onclick": "",
                        "afterlink": None,
                        "customdata": '""',
                        "noviewlink": False,
                        "completion": 0,
                        "downloadcontent": 1,
                        "dates": [],
                        "groupmode": 0,
                        "contents": [
                            {
                                "type": "file",
                                "filename": "index.html",
                                "filepath": "/",
                                "filesize": 0,
                                "fileurl": "https://hypothesisuniversity.moodlecloud.com/webservice/pluginfile.php/1135/mod_page/content/index.html?forcedownload=1",
                                "timecreated": None,
                                "timemodified": 1708598607,
                                "sortorder": 1,
                                "userid": None,
                                "author": None,
                                "license": None,
                            },
                        ],
                    },
                ],
            },
            {
                "id": 49,
                "name": "localhost (make devdata) Test Assignments",
                "visible": 1,
                "summary": '<p>These work as long as you have run "make devdata"<br></p>',
                "summaryformat": 1,
                "section": 3,
                "hiddenbynumsections": 0,
                "uservisible": True,
                "modules": [
                    {
                        "id": 110,
                        "url": "https://hypothesisuniversity.moodlecloud.com/mod/lti/view.php?id=110",
                        "name": "localhost (make devdata) HTML Assignment",
                        "instance": 88,
                        "contextid": 173,
                        "visible": 1,
                        "uservisible": True,
                        "visibleoncoursepage": 1,
                        "modicon": "https://d242fdlp0qlcia.cloudfront.net/uploads/brand/HypothesisBlackboardIcon.png",
                        "modname": "lti",
                        "modplural": "External tools",
                        "availability": None,
                        "indent": 0,
                        "onclick": "",
                        "afterlink": None,
                        "customdata": '""',
                        "noviewlink": False,
                        "completion": 0,
                        "downloadcontent": 1,
                        "dates": [],
                        "groupmode": 0,
                    },
                ],
            },
        ]

    @pytest.fixture
    def pages(self):
        return [
            {
                "id": "ID 1",
                "coursemodule": "1",
                "name": "PAGE 1",
                "content": "HTML 1",
            },
            {
                "id": "ID 2",
                "coursemodule": "2",
                "name": "PAGE 2",
                "content": "HTML 2",
            },
        ]

    @pytest.fixture
    def svc(self, http_service, file_service):
        return MoodleAPIClient(
            sentinel.lms_url, sentinel.token, http_service, file_service
        )
