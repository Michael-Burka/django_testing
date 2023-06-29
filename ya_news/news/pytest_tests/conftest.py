import datetime

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from news.models import Comment, News


@pytest.fixture
def author():
    User = get_user_model()
    return User.objects.create(username='Author')


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def create_user():
    def _create_user(username):
        User = get_user_model()
        return User.objects.create(username=username)
    return _create_user


@pytest.fixture
def news(author):
    return News.objects.create(
        title='Test news',
        text='Test news text',
        date=datetime.datetime.today()
    )


@pytest.fixture
def create_news(author):
    def create_news(title, text, date):
        return News.objects.create(title=title, text=text, date=date)
    return create_news


@pytest.fixture
def comment(author, news):
    return Comment.objects.create(
        news=news,
        author=author,
        text='Test comment',
    )


@pytest.fixture
def comment_id(comment):
    return comment.id,


@pytest.fixture
def form_data():
    return {
        'title': 'Test title',
        'text': 'Test text',
    }
