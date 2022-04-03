import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.new_user = User.objects.create_user(username='Testname')
        cls.new_authorized_client = Client()
        cls.new_authorized_client.force_login(cls.new_user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='testslug',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_post_equal(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.image, self.post.image)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.id, self.post.id)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts:index': 'posts/index.html',
            'posts:post_create': 'posts/post_create.html',
        }
        templates_pages_names_params = {
            'posts:profile': ['posts/profile.html', {
                'username': self.user.username}
            ],
            'posts:post_edit': ['posts/post_create.html', {
                'post_id': self.post.id}
            ],
            'posts:post_detail': ['posts/post_detail.html', {
                'post_id': self.post.id}
            ],
            'posts:group_list': ['posts/group_list.html', {
                'slug': self.group.slug}
            ]
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse(reverse_name))
                self.assertTemplateUsed(response, template)
        for reverse_name, templateset in templates_pages_names_params.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse(reverse_name, kwargs=templateset[1])
                )
                self.assertTemplateUsed(response, templateset[0])

    def test_index_group_profile_correct_context(self):
        """Проверка контекста шаблонов index, group_list, profile"""
        reverse_params = {
            'posts:index': None,
            'posts:group_list': {'slug': self.group.slug},
            'posts:profile': {'username': self.user.username}
        }
        for template, kwargs_value in reverse_params.items():
            response = self.authorized_client.get(
                reverse(template, kwargs=kwargs_value)
            )
            self.check_post_equal(response.context.get('page_obj')[0])

    def test_index_cached(self):
        """Хранится ли index в кэше"""
        response = self.client.get(reverse('posts:index'))
        cached_content = response.content
        Post.objects.all().delete()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(cached_content, response.content)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotEqual(cached_content, response.content)

    def test_post_detail_context(self):
        """Проверка контекста post_detail"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.check_post_equal(response.context.get('post'))

    def test_post_create_context(self):
        """Проверка контекста post_create"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        """Проверка контекста post_edit"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_in_another_group(self):
        """Не попал ли пост в другую группу"""
        secondgroup = Group.objects.create(
            title='Заголовок 2 группы',
            slug='second',
            description='Тест описание',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': secondgroup.slug})
        )
        self.assertNotIn(self.post, response.context.get('page_obj'))

    def test_add_comment(self):
        """Проверка добавления комментария"""
        comments_count = Comment.objects.count()
        new_comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='test2'
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(comments_count, Comment.objects.count() - 1)
        self.assertIn(new_comment, response.context.get('comments'))

    def test_follow(self):
        """Пользователь может подписаться"""
        response = self.new_authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}
        ))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Follow.objects.filter(
            user=self.new_user, author=self.user
        ).exists())

    def test_unfollow(self):
        """Подписчик может отписаться"""
        response = self.new_authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user.username}
        ))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Follow.objects.filter(
            user=self.new_user, author=self.user
        ).exists())

    def test_follow_unfollow_line(self):
        """Новая запись не появляется в ленте неподписанного/
        появляется у подписчика"""
        user = User.objects.create_user(username='NoFollow')
        unfollowed_client = Client()
        unfollowed_client.force_login(user)
        Follow.objects.create(user=self.new_user, author=self.user)
        response = unfollowed_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['posts']), 0)
        response = self.new_authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotEqual(len(response.context['posts']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Kirill')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.post = []
        for i in range(settings.POST_PER_PAGE + 3):
            cls.post.append(Post(
                text=f'Тестовый пост №{i}',
                author=cls.user,
                group=cls.group
            ))
        Post.objects.bulk_create(cls.post)

    def test_first_page_contains_ten_records(self):
        """Проверка первой страницы paginator"""
        templates_pages_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), settings.POST_PER_PAGE
                )

    def test_second_page_contains_three_records(self):
        """Проверка второй(последней) страницы paginator"""
        templates_pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
