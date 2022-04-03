import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def make_image(self, image_name):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name=f'{image_name}.gif',
            content=small_gif,
            content_type='image/gif'
        )
        return uploaded

    def check_post(self, post, form_data):
        with self.subTest(post=post):
            self.assertEqual(post.text, form_data['text'])
            self.assertEqual(post.author, self.user)
            self.assertEqual(
                post.image.name, 'posts/' + form_data['image'].name
            )
            self.assertEqual(post.group.id, form_data['group'])

    def test_post_create(self):
        """Проверка формы создания поста"""
        uploaded = self.make_image('post_create_image')
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.check_post(Post.objects.latest('id'), form_data)

    def test_post_edit(self):
        """Проверка формы редактирования поста"""
        posts_count = Post.objects.count()
        uploaded = self.make_image('post_edit_image')
        new_group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_new_group_slug',
            description='Тестовое описание'
        )
        form_data = {
            'text': 'Тестовый текст 2',
            'group': new_group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.check_post(
            Post.objects.filter(id=self.post.id).first(), form_data
        )

    def test_add_comment(self):
        """Проверка формы создания комментария"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        comment = Comment.objects.latest('id')
        self.assertEqual(comment.post.id, self.post.id)
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.text, form_data['text'])
