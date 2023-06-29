from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from http import HTTPStatus

from notes.models import Note


User = get_user_model()


class TestRoures(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

    def test_home_availability_for_anonymous_user(self):
        urls = ['notes:home', 'users:login', 'users:logout', 'users:signup']
        for name in urls:
            url = reverse(name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_home_availability_for_auth_user(self):
        self.client.force_login(self.reader)
        urls = ['notes:list', 'notes:add', 'notes:success']
        for name in urls:
            url = reverse(name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_user(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ['notes:detail', 'notes:edit', 'notes:delete']:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirects(self):
        redirect_urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        login_url = reverse('users:login')

        for name, args in redirect_urls:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args) if args else reverse(name)
                expected_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertEqual(response.url, expected_url)
