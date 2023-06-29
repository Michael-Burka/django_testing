from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note
from pytils.translit import slugify

User = get_user_model()


class NoteTestCase(TestCase):
    def setUp(self):
        self.author = User.objects.create(username='Author1')
        self.reader = User.objects.create(username='Reader1')
        self.note = Note.objects.create(
            title='Title',
            text='Text',
            slug='slug',
            author=self.author,
        )
        self.form_data = {
            'title': 'New Title',
            'text': 'New Text',
            'slug': 'new-slug',
        }

    def test_user_can_create_note(self):
        client = Client()
        client.force_login(self.author)
        url = reverse('notes:add')
        response = client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.latest('pk')
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        client = Client()
        url = reverse('notes:add')
        response = client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse('users:login') + f'?next={url}')
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        client = Client()
        client.force_login(self.author)
        url = reverse('notes:add')
        self.form_data['slug'] = self.note.slug
        response = client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        client = Client()
        client.force_login(self.author)
        url = reverse('notes:add')
        self.form_data.pop('slug')
        response = client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.latest('pk')
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        client = Client()
        client.force_login(self.author)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        client = Client()
        client.force_login(self.reader)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)
