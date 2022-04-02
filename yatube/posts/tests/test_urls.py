from http import HTTPStatus
from urllib import response

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='testslug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def test_public_pages(self):
        '''Проверка доступности страницы неавторизованного клиента'''
        url_address = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/'
        )
        for address in url_address:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_user_pages(self):
        """Проверка доступности страницы авторизованного клиента"""
        url_address = (
            f'/posts/{self.post.id}/edit/',
            '/create/'
        )
        for address in url_address:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_not_author(self):
        """Проверка страницы доступной только автору поста"""
        testuser = User.objects.create_user(username='TestUser')
        auth_client = Client()
        auth_client.force_login(testuser)
        response = auth_client.get(f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_redirect_non_auth(self):
        """Проверка доступности страницы неавторизованному пользователю"""
        response=self.client.get(f'/posts/{self.post.id}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page(self):
        '''Проверка несуществующей страницы'''
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
        templates_url_names_non_auth = {
            f'/posts/{self.post.id}/edit/': 'users/login.html',
            '/create/': 'users/login.html',
            f'/posts/{self.post.id}/comment/': 'users/login.html',
        }
        for address, template in templates_url_names_non_auth.items():
            with self.subTest(address=address):
                response = self.client.get(address, follow=True)
                self.assertTemplateUsed(response, template)
