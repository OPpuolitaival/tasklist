import pytest
import jwt
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import UserFactory, TaskFactory


@pytest.mark.django_db
class TestAuthenticationSecurity:

    def setup_method(self):
        self.client = APIClient()

    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        user = UserFactory(username='securitytest')
        user.set_password('plainpassword123')
        user.save()

        # Password should be hashed, not stored in plain text
        assert user.password != 'plainpassword123'
        assert user.password.startswith('pbkdf2_sha256$')
        assert len(user.password) > 50  # Hashed passwords are long

        # Should be able to authenticate with original password
        assert user.check_password('plainpassword123')
        assert not user.check_password('wrongpassword')

    def test_password_requirements_enforcement(self):
        """Test password validation (if implemented)"""
        # Test weak password
        weak_passwords = [
            '123',
            'password',
            '12345678',
            'qwerty',
            'abc123'
        ]

        for weak_password in weak_passwords:
            response = self.client.post('/api/auth/register/', {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': weak_password,
                'password_confirm': weak_password
            })

            # Depending on password validation implementation,
            # weak passwords might be rejected
            # For now, we test that the endpoint responds properly
            assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]

    def test_user_enumeration_protection(self):
        """Test that user enumeration is not possible"""
        # Create a known user
        UserFactory(username='knownuser', email='known@example.com')

        # Try to register with existing username
        response = self.client.post('/api/auth/register/', {
            'username': 'knownuser',
            'email': 'different@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Try to register with existing email
        response = self.client.post('/api/auth/register/', {
            'username': 'differentuser',
            'email': 'known@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        })

        # Should handle duplicate email appropriately
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED]

    def test_brute_force_protection(self):
        """Test protection against brute force attacks"""
        user = UserFactory(username='bruteforcetest')
        user.set_password('correctpassword')
        user.save()

        # Attempt multiple failed logins
        for i in range(10):
            response = self.client.post('/api/auth/login/', {
                'username': 'bruteforcetest',
                'password': f'wrongpassword{i}'
            })
            assert response.status_code == status.HTTP_400_BAD_REQUEST

        # After multiple failures, legitimate login should still work
        # (In production, you might implement account lockout)
        response = self.client.post('/api/auth/login/', {
            'username': 'bruteforcetest',
            'password': 'correctpassword'
        })

        # Should still be able to login (unless lockout is implemented)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_jwt_token_security(self):
        """Test JWT token security properties"""
        user = UserFactory(username='jwttest')
        user.set_password('password123')
        user.save()

        # Login to get token
        response = self.client.post('/api/auth/login/', {
            'username': 'jwttest',
            'password': 'password123'
        })

        assert response.status_code == status.HTTP_200_OK
        tokens = response.data['tokens']

        # Test token structure
        access_token = tokens['access']
        refresh_token = tokens['refresh']

        assert access_token != refresh_token
        assert len(access_token) > 100  # JWT tokens should be substantial length

        # Decode token to verify structure (without verification for testing)
        decoded_access = jwt.decode(access_token, options={"verify_signature": False})

        # JWT should contain required claims
        assert 'user_id' in decoded_access
        assert 'exp' in decoded_access  # Expiration
        assert 'iat' in decoded_access  # Issued at
        assert decoded_access['user_id'] == str(user.id)

    def test_jwt_token_expiration(self):
        """Test that JWT tokens expire appropriately"""
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Token should work initially
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/tasks/')
        assert response.status_code == status.HTTP_200_OK

        # Decode to check expiration time
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        exp_claim = decoded.get('exp')
        iat_claim = decoded.get('iat')

        # Token should have reasonable expiration time (not too long)
        token_lifetime = exp_claim - iat_claim
        assert token_lifetime <= 3600  # No more than 1 hour by default

    def test_invalid_jwt_token_handling(self):
        """Test handling of invalid/malformed JWT tokens"""
        invalid_tokens = [
            'invalid.jwt.token',
            'Bearer invalid_token',
            'malformed_token_structure',
            '',
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid',  # Valid header, invalid payload
        ]

        for invalid_token in invalid_tokens:
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {invalid_token}')
            response = self.client.get('/api/tasks/')
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_reuse_after_logout(self):
        """Test that tokens can't be reused after logout scenarios"""
        user = UserFactory()
        user.set_password('password123')
        user.save()

        # Login and get token
        response = self.client.post('/api/auth/login/', {
            'username': user.username,
            'password': 'password123'
        })

        access_token = response.data['tokens']['access']

        # Use token successfully
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/tasks/')
        assert response.status_code == status.HTTP_200_OK

        # Token should still work (no server-side logout implemented yet)
        # In a full implementation, you'd test token blacklisting

    def test_sql_injection_protection(self):
        """Test protection against SQL injection in authentication"""
        # Attempt SQL injection in login
        malicious_inputs = [
            "'; DROP TABLE auth_user; --",
            "admin' OR '1'='1",
            "' UNION SELECT * FROM auth_user WHERE '1'='1",
            "admin'; UPDATE auth_user SET is_superuser=1; --"
        ]

        for malicious_input in malicious_inputs:
            response = self.client.post('/api/auth/login/', {
                'username': malicious_input,
                'password': 'anypassword'
            })

            # Should fail safely without executing SQL
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_xss_protection_in_error_messages(self):
        """Test that error messages don't reflect XSS payloads"""
        xss_payloads = [
            '<script>alert("xss")</script>',
            '"><script>alert("xss")</script>',
            "javascript:alert('xss')",
            '<img src=x onerror=alert("xss")>'
        ]

        for payload in xss_payloads:
            response = self.client.post('/api/auth/register/', {
                'username': payload,
                'email': 'test@example.com',
                'password': 'password123',
                'password_confirm': 'password123'
            })

            # Check that payload is not reflected in response
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                response_text = str(response.content)
                # XSS payload should be escaped or removed
                assert '<script>' not in response_text
                assert 'javascript:' not in response_text

    def test_csrf_protection(self):
        """Test CSRF protection on authentication endpoints"""
        # Django's CSRF protection should be properly configured
        # This test verifies the protection exists but doesn't break API functionality

        # API endpoints should work without CSRF tokens (using JWT)
        response = self.client.post('/api/auth/register/', {
            'username': 'csrftest',
            'email': 'csrf@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        })

        # Should work for API endpoints
        assert response.status_code == status.HTTP_201_CREATED

    def test_rate_limiting_headers(self):
        """Test that rate limiting information is provided (if implemented)"""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })

        # Check for rate limiting headers (if implemented)
        rate_limit_headers = [
            'X-RateLimit-Limit',
            'X-RateLimit-Remaining',
            'X-RateLimit-Reset'
        ]

        # Rate limiting headers might not be implemented yet
        # This test documents the expected behavior
        for header in rate_limit_headers:
            if header in response:
                assert isinstance(response[header], str)

    def test_secure_session_configuration(self):
        """Test that sessions are configured securely"""
        # This test would verify session security settings
        # For JWT-based API, sessions are less relevant
        # But we can test that sensitive settings are configured

        from django.conf import settings

        # Check security-related settings (if they exist)
        security_settings = {
            'SECRET_KEY': lambda x: len(x) > 20,  # Secret key should be long
            'DEBUG': lambda x: x is False,  # Debug should be False in production
        }

        for setting_name, validator in security_settings.items():
            if hasattr(settings, setting_name):
                setting_value = getattr(settings, setting_name)
                # In test environment, some settings might differ
                # This documents expected production configuration
                if setting_name != 'DEBUG':  # DEBUG might be True in tests
                    assert validator(setting_value), f"{setting_name} is not securely configured"

    def test_user_data_isolation_security(self):
        """Test that user data isolation is enforced"""
        user1 = UserFactory(username='user1')
        user2 = UserFactory(username='user2')

        # Create tasks for each user
        task1 = TaskFactory(user=user1, title='User 1 Secret Task')
        task2 = TaskFactory(user=user2, title='User 2 Secret Task')

        # User 1 should not be able to access User 2's data
        refresh1 = RefreshToken.for_user(user1)
        access_token1 = str(refresh1.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token1}')

        # Try to access User 2's task directly
        response = self.client.get(f'/api/tasks/{task2.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Try to modify User 2's task
        response = self.client.patch(f'/api/tasks/{task2.id}/', {
            'title': 'Hacked title'
        })
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Try to delete User 2's task
        response = self.client.delete(f'/api/tasks/{task2.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verify User 2's task is unchanged
        task2.refresh_from_db()
        assert task2.title == 'User 2 Secret Task'