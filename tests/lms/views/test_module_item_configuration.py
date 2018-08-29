from lms.views.module_item_configurations import create_module_item_configuration
from lms.models import ModuleItemConfiguration


class TestModuleItemConfiguration:
    def test_it_creates_a_module_item_configuration(self,
                                                    authenticated_request):
        initial_count = authenticated_request.db.query(
            ModuleItemConfiguration).count()
        authenticated_request.params['document_url'] = 'https://www.example.com'
        authenticated_request.params['resource_link_id'] = 'test'
        authenticated_request.params['tool_consumer_instance_guid'] = 'test'
        create_module_item_configuration(authenticated_request)
        new_count = authenticated_request.db.query(
            ModuleItemConfiguration).count()
        assert new_count == initial_count + 1

    def test_bad_jwt_fails_authentication(self, authenticated_request):
        initial_count = authenticated_request.db.query(
            ModuleItemConfiguration).count()
        authenticated_request.params['document_url'] = 'https://www.example.com'
        authenticated_request.params['resource_link_id'] = 'test'
        authenticated_request.params['tool_consumer_instance_guid'] = 'test'
        authenticated_request.params['jwt_token'] = 'wrongjwttoken'

        response = create_module_item_configuration(authenticated_request)

        new_count = authenticated_request.db.query(
            ModuleItemConfiguration).count()
        assert new_count == initial_count
        assert 'Unauthenticated Request' in str(response.body)

    def test_missing_jwt_fails_authentication(self, authenticated_request):
        initial_count = authenticated_request.db.query(
            ModuleItemConfiguration).count()
        authenticated_request.params['document_url'] = 'https://www.example.com'
        authenticated_request.params['resource_link_id'] = 'test'
        authenticated_request.params['tool_consumer_instance_guid'] = 'test'
        authenticated_request.params['jwt_token'] = 'wrongjwttoken'
        authenticated_request.params.pop('jwt_token')

        response = create_module_item_configuration(authenticated_request)

        new_count = authenticated_request.db.query(
            ModuleItemConfiguration).count()
        assert new_count == initial_count
        assert 'Unauthenticated Request' in str(response.body)
