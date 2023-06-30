from http import HTTPStatus

import pytest

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news, form_data):
    url = reverse('news:detail', args=(news.id,))

    response = client.post(url, data=form_data)
    comments_count = Comment.objects.count()

    assert response.status_code == HTTPStatus.FOUND
    assert comments_count == 0


@pytest.mark.django_db
def test_auth_user_can_create_comment(author, author_client, news, form_data):
    url = reverse('news:detail', args=(news.id,))

    response = author_client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    comment = Comment.objects.first()

    assert response.status_code == HTTPStatus.FOUND
    assert comments_count == 1
    assert comment.news == news
    assert comment.author == author
    assert comment.text == form_data['text']


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, news):
    url = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}

    response = author_client.post(url, data=bad_words_data)
    comments_count = Comment.objects.count()

    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context
    assert response.context['form'].errors['text'][0] == WARNING
    assert comments_count == 0


@pytest.mark.django_db
def test_author_can_edit_comment(author_client, comment):
    edit_url = reverse('news:edit', args=(comment.id,))
    form_data = {'text': 'Обновленный комментарий'}

    response = author_client.post(edit_url, data=form_data)
    comment.refresh_from_db()

    assert response.status_code == HTTPStatus.FOUND
    assert comment.text == form_data['text']


@pytest.mark.django_db
def test_author_can_delete_comment(author_client, comment):
    delete_url = reverse('news:delete', args=(comment.id,))
    response = author_client.post(delete_url)
    comment_exists = Comment.objects.filter(pk=comment.id).exists()

    assert response.status_code == HTTPStatus.FOUND
    assert not comment_exists


@pytest.mark.django_db
@pytest.mark.parametrize(
    'author_client, comment_text, expected_text',
    [
        ('author_client', 'Comment Text', 'Comment Text'),
        ('author_client', 'Comment Text by User2', 'Comment Text by User2'),
    ],
    indirect=['author_client']
)
def test_auth_user_cannot_edit_or_delete_other_users_comments(
    author_client, comment, comment_text, expected_text
):

    User = get_user_model()
    user2 = User.objects.create(username='User2')
    client2 = Client()
    client2.force_login(user2)

    comment2 = Comment.objects.create(
        news=comment.news, author=user2, text=comment_text
    )

    edit_url = reverse('news:edit', args=(comment2.id,))
    form_data = {'text': 'Updated Comment'}
    response = author_client.post(edit_url, data=form_data)
    comment2.refresh_from_db()

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert comment2.text == expected_text

    delete_url = reverse('news:delete', args=(comment2.id,))
    response = author_client.post(delete_url)
    comment2_exists = Comment.objects.filter(pk=comment2.id).exists()
    assert comment2_exists
