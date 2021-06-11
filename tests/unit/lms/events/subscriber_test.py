import pytest
from h_matchers import Any

from lms.events import FilesDiscoveredEvent
from lms.events.subscriber import files_discovered
from lms.models import File
from tests import factories


class TestFilesDiscovered:
    @pytest.mark.parametrize("extras", ({}, {"name": "new"}, {"course_id": "cid_1"}))
    def test_it_can_add_new_values(
        self, pyramid_request, db_session, application_instance, extras
    ):
        attrs = dict(type="new", lms_id="id_1", **extras)

        files_discovered(
            # Use a dict call here again to prevent SQLAlchemy from messing
            # with our dict in place
            event=FilesDiscoveredEvent(request=pyramid_request, values=[dict(attrs)])
        )

        assert db_session.query(File).all() == [
            Any.instance_of(File).with_attrs(
                dict(application_instance_id=application_instance.id, **attrs)
            )
        ]

    @pytest.mark.usefixtures("existing_file")
    def test_it_can_update_old_values(
        self,
        pyramid_request,
        db_session,
        existing_attrs,
    ):
        new_attrs = dict(existing_attrs, name="new")

        files_discovered(
            # Use a dict call here again to prevent SQLAlchemy from messing
            # with our dict in place
            event=FilesDiscoveredEvent(request=pyramid_request, values=[new_attrs])
        )

        assert db_session.query(File).all() == [
            Any.instance_of(File).with_attrs(new_attrs)
        ]

    # We don't cover the application instance id here 'cos it's annoying
    @pytest.mark.parametrize("field", ("type", "lms_id", "course_id"))
    @pytest.mark.usefixtures("existing_file")
    def test_old_values_are_only_updated_for_exact_matches(
        self, db_session, field, pyramid_request, existing_attrs
    ):
        new_attrs = dict(existing_attrs)
        new_attrs[field] = "different"

        files_discovered(
            # Use a dict call here again to prevent SQLAlchemy from messing
            # with our dict in place
            event=FilesDiscoveredEvent(
                request=pyramid_request, values=[dict(new_attrs)]
            )
        )

        assert (
            db_session.query(File).all()
            == Any.list.containing(
                [
                    Any.instance_of(File).with_attrs(existing_attrs),
                    Any.instance_of(File).with_attrs(new_attrs),
                ]
            ).only()
        )

    @pytest.fixture
    def existing_attrs(self, application_instance):
        return {
            "application_instance_id": application_instance.id,
            "type": "existing_type",
            "lms_id": "existing_lms_id",
            "course_id": "existing_course_id",
        }

    @pytest.fixture
    def existing_file(self, db_session, existing_attrs):
        file = File(**existing_attrs)
        db_session.add(file)
        db_session.flush()

        return file

    @pytest.fixture(autouse=True)
    def application_instance(self, db_session, application_instance_service):
        application_instance = factories.ApplicationInstance(id=1234)
        db_session.add(application_instance)
        db_session.flush()
        application_instance_service.get.return_value = application_instance

        return application_instance
