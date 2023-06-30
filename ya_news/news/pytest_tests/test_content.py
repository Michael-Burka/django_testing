import datetime
from http import HTTPStatus

import pytest
from django.conf import settings
from django.urls import reverse
from news.models import Comment


@pytest.mark.django_db
@pytest.mark.parametrize('num_news', [5, 10, 15])
def test_home_page_max_news_count(client, create_news, num_news):

    for i in range(num_news):
        create_news(f'Title {i}', f'Text {i}', datetime.datetime.now())

    response = client.get(reverse('news:home'))
    assert response.status_code == HTTPStatus.OK
    assert len(
        response.context['news_list']
    ) <= settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_home_page_news_order(client, create_news):

    # Create 3 news objects with different dates
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    two_days_ago = today - datetime.timedelta(days=2)
    create_news('Title 1', 'Text 1', today)
    create_news('Title 2', 'Text 2', yesterday)
    create_news('Title 3', 'Text 3', two_days_ago)

    response = client.get(reverse('news:home'))
    assert response.status_code == HTTPStatus.OK
    news_list = response.context['news_list']
    assert len(news_list) == 3
    assert news_list[0].date > news_list[1].date > news_list[2].date


@pytest.mark.django_db
def test_news_detail_comment_order(client, author, author_client, news):

    # Create 3 comments with different created dates
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    two_days_ago = today - datetime.timedelta(days=2)
    Comment.objects.create(
        news=news,
        author=author,
        text='Comment 1',
        created=two_days_ago
    )
    Comment.objects.create(
        news=news,
        author=author,
        text='Comment 2',
        created=today
    )
    Comment.objects.create(
        news=news,
        author=author,
        text='Comment 3',
        created=yesterday
    )

    # Test for anonymous user
    response = client.get(reverse('news:detail', kwargs={'pk': news.pk}))
    assert response.status_code == HTTPStatus.OK
    context = response.context
    assert 'object' in context
    assert len(context['object'].comment_set.all()) == 3
    comment_list = context['object'].comment_set.all()
    assert (comment_list[0].created
            < comment_list[1].created
            < comment_list[2].created)

    # Test for author user
    response = author_client.get(
        reverse('news:detail', kwargs={'pk': news.pk}))
    assert response.status_code == HTTPStatus.OK
    context = response.context
    assert 'object' in context
    assert len(context['object'].comment_set.all()) == 3
    comment_form = context['form']
    assert comment_form is not None


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, create_news):
    news = create_news('Title', 'Text', datetime.datetime.now())

    # Test for anonymous client
    response = client.get(reverse('news:detail', kwargs={'pk': news.pk}))
    assert response.status_code == HTTPStatus.OK
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(author_client, create_news, author):
    news = create_news('Title', 'Text', datetime.datetime.now())

    # Test for authorized client
    response = author_client.get(reverse(
        'news:detail', kwargs={'pk': news.pk}))
    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context
