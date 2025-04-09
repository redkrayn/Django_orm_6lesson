from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch


class TagQuerySet(models.QuerySet):
    def popular(self):
        popular_tags = (self.annotate(
            num_posts=Count('posts', distinct=True)
        ).order_by('-num_posts').prefetch_related('posts'))
        return popular_tags


class PostQuerySet(models.QuerySet):
    def year(self, year):
        posts_at_year = self.filter(published_at__year=year).order_by('published_at')
        return posts_at_year

    def popular(self):
        popular_posts = self.annotate(likes_count=Count('likes')).order_by('-likes_count')
        return popular_posts

    def with_prefetched_tags(self):
        return self.prefetch_related(Prefetch('tags', queryset=Tag.objects.order_by('title')))

    def fetch_with_comments_count(self):
        posts_with_comments = (
            self.model.objects
            .filter(id__in=self.values_list('id', flat=True))
            .annotate(comments_count=Count('comments'))
            .prefetch_related('author')
        )
        comments_count_dict = {post.id: post.comments_count for post in posts_with_comments}

        for post in self:
            post.comments_count = comments_count_dict.get(post.id, 0)

        return posts_with_comments


class Post(models.Model):

    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')
    objects = PostQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)
    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан',
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
