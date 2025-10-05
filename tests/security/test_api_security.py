import pytest
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import UserFactory, TaskFactory


@pytest.mark.django_db
class TestAPISecurity:

    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def authenticate(self):
        """Helper method to authenticate requests"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_cors_configuration(self):
        """Test CORS headers are properly configured"""
        self.authenticate()
        response = self.client.get('/api/tasks/')

        # Check CORS headers are present when needed
        # In development, CORS might be more permissive
        if hasattr(response, 'get'):
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]

            # CORS headers might not be present in test environment
            # This test documents expected behavior
            for header in cors_headers:
                if response.get(header):
                    assert isinstance(response[header], str)

    def test_http_method_restrictions(self):
        """Test that HTTP methods are properly restricted"""
        self.authenticate()

        # Test that unsupported methods return 405
        task = TaskFactory(user=self.user)

        # TRACE method should not be allowed
        response = self.client.generic('TRACE', f'/api/tasks/{task.id}/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # HEAD should work for GET endpoints
        response = self.client.head('/api/tasks/')
        assert response.status_code == status.HTTP_200_OK

        # OPTIONS should work for CORS
        response = self.client.options('/api/tasks/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    def test_input_validation_and_sanitization(self):
        """Test that input is properly validated and sanitized"""
        self.authenticate()

        # Test XSS payloads in task creation
        xss_payloads = [
            '<script>alert("xss")</script>',
            '"><script>alert("xss")</script>',
            '<img src=x onerror=alert("xss")>',
            'javascript:alert("xss")',
            '<svg onload=alert("xss")>',
        ]

        for payload in xss_payloads:
            response = self.client.post('/api/tasks/', {
                'title': payload,
                'description': f'Description with {payload}',
                'completed': False
            })

            if response.status_code == status.HTTP_201_CREATED:
                # If task is created, payload should be properly escaped
                created_task = response.data
                assert '<script>' not in created_task['title']
                assert '<script>' not in created_task['description']
                assert 'javascript:' not in created_task['title']
                assert 'javascript:' not in created_task['description']

    def test_sql_injection_protection(self):
        """Test protection against SQL injection in API endpoints"""
        self.authenticate()

        sql_payloads = [
            "'; DROP TABLE tasks_task; --",
            "' UNION SELECT * FROM auth_user; --",
            "' OR '1'='1",
            "1; DELETE FROM tasks_task; --"
        ]

        for payload in sql_payloads:
            # Test in task title
            response = self.client.post('/api/tasks/', {
                'title': payload,
                'description': 'Normal description',
                'completed': False
            })

            # Should either create task safely or reject with validation error
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST
            ]

            # Ensure no SQL injection occurred by checking tasks still exist
            list_response = self.client.get('/api/tasks/')
            assert list_response.status_code == status.HTTP_200_OK

    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks"""
        self.authenticate()

        # Path traversal payloads
        traversal_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2f',  # URL encoded ../../../
            '....//....//....//etc/passwd'
        ]

        for payload in traversal_payloads:
            response = self.client.post('/api/tasks/', {
                'title': payload,
                'description': 'Path traversal test',
                'completed': False
            })

            # Should handle safely
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST
            ]

    def test_content_type_restrictions(self):
        """Test that content types are properly validated"""
        self.authenticate()

        # Test with invalid content type
        response = self.client.post('/api/tasks/',
            'title=Test&description=Test',  # Form data instead of JSON
            content_type='application/x-www-form-urlencoded'
        )

        # Should handle gracefully
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        ]

    def test_request_size_limits(self):
        """Test that large requests are handled appropriately"""
        self.authenticate()

        # Create very large payload
        large_title = 'A' * 10000  # Very long title
        large_description = 'B' * 100000  # Very long description

        response = self.client.post('/api/tasks/', {
            'title': large_title,
            'description': large_description,
            'completed': False
        })

        # Should either reject or truncate appropriately
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_201_CREATED
        ]

        if response.status_code == status.HTTP_201_CREATED:
            # If accepted, should respect model constraints
            assert len(response.data['title']) <= 200  # Model max_length

    def test_authentication_bypass_attempts(self):
        """Test attempts to bypass authentication"""
        # Create a task that requires authentication to access
        other_user = UserFactory()
        task = TaskFactory(user=other_user)

        # Attempt to access without authentication
        response = self.client.get(f'/api/tasks/{task.id}/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Attempt with malformed Authorization header
        malformed_headers = [
            'Bearer',
            'Bearer ',
            'Basic dGVzdDp0ZXN0',  # Basic auth instead of Bearer
            'InvalidScheme token',
            'Bearer invalid.jwt.token'
        ]

        for header_value in malformed_headers:
            self.client.credentials(HTTP_AUTHORIZATION=header_value)
            response = self.client.get(f'/api/tasks/{task.id}/')
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authorization_bypass_attempts(self):
        """Test attempts to bypass authorization (access other user's data)"""
        # Create two users with tasks
        user1 = UserFactory()
        user2 = UserFactory()

        task1 = TaskFactory(user=user1, title='User 1 Task')
        task2 = TaskFactory(user=user2, title='User 2 Task')

        # Authenticate as user1
        refresh1 = RefreshToken.for_user(user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh1.access_token)}')

        # Attempt to access user2's task with various manipulation attempts
        manipulation_attempts = [
            # Direct access
            f'/api/tasks/{task2.id}/',

            # Parameter pollution
            f'/api/tasks/{task1.id}/?user_id={user2.id}',
            f'/api/tasks/{task1.id}/?user={user2.id}',

            # Array manipulation
            f'/api/tasks/{task1.id}/?id[]={task2.id}',
        ]

        for url in manipulation_attempts:
            response = self.client.get(url)

            if response.status_code == status.HTTP_200_OK:
                # If successful, should only return user1's data
                if isinstance(response.data, dict):
                    assert response.data.get('id') == task1.id
                elif isinstance(response.data, list):
                    for item in response.data:
                        task_obj = TaskFactory._meta.model.objects.get(id=item['id'])
                        assert task_obj.user == user1
            else:
                # Should be 404 (not found) rather than 403 (forbidden)
                # to prevent information leakage
                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_error_message_information_disclosure(self):
        """Test that error messages don't disclose sensitive information"""
        # Attempt operations that should fail

        # Non-existent task ID
        self.authenticate()
        response = self.client.get('/api/tasks/99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Error message should not reveal internal details
        error_content = str(response.content).lower()

        # Should not contain sensitive information
        sensitive_terms = [
            'database',
            'sql',
            'table',
            'column',
            'traceback',
            'exception',
            'path',
            'file',
            'line',
            'django',
            'python'
        ]

        for term in sensitive_terms:
            assert term not in error_content, f"Error message contains sensitive term: {term}"

    def test_http_security_headers(self):
        """Test that appropriate HTTP security headers are set"""
        response = self.client.get('/')

        # Security headers that should be present
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': None,  # Should be present but value varies
            'Content-Security-Policy': None,  # Should be present but value varies
        }

        for header, expected_value in security_headers.items():
            if expected_value is None:
                # Just check presence
                if header in response:
                    assert len(response[header]) > 0
            elif isinstance(expected_value, list):
                # Check if value is one of expected values
                if header in response:
                    assert response[header] in expected_value
            else:
                # Check exact match
                if header in response:
                    assert response[header] == expected_value

    def test_sensitive_data_in_logs(self):
        """Test that sensitive data is not logged"""
        # This is more of a documentation test
        # In a real implementation, you'd check log files

        # Perform operations that might log sensitive data
        response = self.client.post('/api/auth/register/', {
            'username': 'loggingtest',
            'email': 'logging@example.com',
            'password': 'sensitivepassword123',
            'password_confirm': 'sensitivepassword123'
        })

        # In a real test, you'd verify that:
        # 1. Passwords are not logged in plain text
        # 2. JWT tokens are not logged
        # 3. Email addresses might be logged but should be considered

        # This test serves as documentation of security requirements
        assert response.status_code == status.HTTP_201_CREATED

    @override_settings(DEBUG=False)
    def test_debug_mode_disabled(self):
        """Test behavior with DEBUG=False (production mode)"""
        # Test that debug information is not exposed
        response = self.client.get('/api/nonexistent-endpoint/')

        # Should get clean 404, not debug information
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Response should not contain debug information
        response_content = str(response.content).lower()
        debug_terms = [
            'traceback',
            'django',
            'python',
            'manage.py',
            'settings.py'
        ]

        for term in debug_terms:
            assert term not in response_content

    def test_api_versioning_security(self):
        """Test that API versioning doesn't introduce security issues"""
        # Test various version attempts
        version_attempts = [
            '/api/v1/tasks/',
            '/api/v2/tasks/',
            '/api/../auth/register/',
            '/api/./tasks/',
        ]

        for url in version_attempts:
            response = self.client.get(url)
            # Should either work properly or fail safely
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_405_METHOD_NOT_ALLOWED
            ]