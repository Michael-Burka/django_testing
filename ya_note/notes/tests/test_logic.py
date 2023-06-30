from http import HTTPStatus

from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class NoteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author1')
        cls.reader = User.objects.create(username='Reader1')
        cls.note_data = {
            'title': 'Title',
            'text': 'Text',
            'slug': 'slug',
            'author': cls.author,
        }
        cls.form_data = {
            'title': 'New Title',
            'text': 'New Text',
            'slug': 'new-slug',
        }

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.author)

    def test_user_can_create_note(self):
        note_count = Note.objects.count()

        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), note_count + 1)

        new_note = Note.objects.latest('pk')
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        Note.objects.create(**self.note_data)
        client = Client()
        note_count = Note.objects.count()

        url = reverse('notes:add')
        response = client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse('users:login') + f'?next={url}')
        self.assertEqual(Note.objects.count(), note_count)

    def test_not_unique_slug(self):
        note = Note.objects.create(**self.note_data)
        url = reverse('notes:add')
        self.form_data['slug'] = note.slug
        response = self.client.post(url, data=self.form_data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFormError(
            response, 'form', 'slug', errors=(note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        note_count = Note.objects.count()

        url = reverse('notes:add')
        self.form_data.pop('slug')

        response = self.client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), note_count + 1)

        new_note = Note.objects.latest('pk')
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        note = Note.objects.create(**self.note_data)
        url = reverse('notes:edit', args=(note.slug,))

        response = self.client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse('notes:success'))

        note.refresh_from_db()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        note = Note.objects.create(**self.note_data)
        client = Client()
        client.force_login(self.reader)

        url = reverse('notes:edit', args=(note.slug,))
        response = client.post(url, data=self.form_data)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note.refresh_from_db()
        self.assertNotEqual(note.title, self.form_data['title'])
        self.assertNotEqual(note.text, self.form_data['text'])
        self.assertNotEqual(note.slug, self.form_data['slug'])
