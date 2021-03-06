from __future__ import unicode_literals

from mock import patch
from rest_framework_simplejwt.compat import reverse
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.state import User
from rest_framework_simplejwt.tokens import AccessToken, SlidingToken

from .utils import APIViewTestCase


class TestTestView(APIViewTestCase):
    view_name = 'test_view'

    def setUp(self):
        self.username = 'test_user'
        self.password = 'test_password'

        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )

    def test_no_authorization(self):
        res = self.view_get()

        self.assertEqual(res.status_code, 401)
        self.assertIn('credentials were not provided', res.data['detail'])

    def test_wrong_auth_type(self):
        res = self.client.post(
            reverse('token_obtain_sliding'),
            data={
                User.USERNAME_FIELD: self.username,
                'password': self.password,
            },
        )

        token = res.data['token']
        self.authenticate_with_token('Wrong', token)

        res = self.view_get()

        self.assertEqual(res.status_code, 401)
        self.assertIn('credentials were not provided', res.data['detail'])

    def test_user_can_get_sliding_token_and_use_it(self):
        res = self.client.post(
            reverse('token_obtain_sliding'),
            data={
                User.USERNAME_FIELD: self.username,
                'password': self.password,
            },
        )

        token = res.data['token']
        self.authenticate_with_token(api_settings.AUTH_HEADER_TYPE, token)

        with patch('rest_framework_simplejwt.authentication.AuthToken', SlidingToken):
            res = self.view_get()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['foo'], 'bar')

    def test_user_can_get_access_and_refresh_tokens_and_use_them(self):
        res = self.client.post(
            reverse('token_obtain_pair'),
            data={
                User.USERNAME_FIELD: self.username,
                'password': self.password,
            },
        )

        access = res.data['access']
        refresh = res.data['refresh']

        self.authenticate_with_token(api_settings.AUTH_HEADER_TYPE, access)

        with patch('rest_framework_simplejwt.authentication.AuthToken', AccessToken):
            res = self.view_get()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['foo'], 'bar')

        res = self.client.post(
            reverse('token_refresh'),
            data={'refresh': refresh},
        )

        access = res.data['access']

        self.authenticate_with_token(api_settings.AUTH_HEADER_TYPE, access)

        with patch('rest_framework_simplejwt.authentication.AuthToken', AccessToken):
            res = self.view_get()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['foo'], 'bar')
