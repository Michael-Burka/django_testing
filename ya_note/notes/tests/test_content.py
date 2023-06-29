from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

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

    def test_notes_list_for_different_users(self):
        clients = (
            (self.author, True),
            (self.reader, False),
        )
        url = reverse('notes:list')

        for user, note_in_list in clients:
            client = Client()
            client.force_login(user)
            with self.subTest(user=user, note_in_list=note_in_list):
                response = client.get(url)
                object_list = response.context['object_list']
                self.assertEqual((self.note in object_list), note_in_list)

    def test_pages_contains_form(self):
        pages = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        author_client = Client()
        author_client.force_login(self.author)

        for name, args in pages:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                response = author_client.get(url)
                self.assertIn('form', response.context)
