import datetime
import os
from django.db import models
from django.template.defaultfilters import slugify
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.utils import timezone
from django.core.urlresolvers import reverse

ROLE_CHOICE = (
    ('Admin', 'Admin'),
    ('Publisher', 'Publisher'),
    ('Author', 'Author'),
)

STATUS_CHOICE = (
    ('Drafted', 'Drafted'),
    ('Published', 'Published'),
    ('Rejected', 'Rejected'),
    ('Trashed', 'Trashed'),
)


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # avatar = models.ImageField(upload_to='profile/', blank=True, null=True, default='profile/avatar-m.jpg')
    role = models.CharField(max_length=10, choices=STATUS_CHOICE)

    class Meta:
        ordering = ['-id']

    # def save(self, *args, **kwargs):
    #     super(UserRole, self).save(*args, **kwargs)


class Theme(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=500)
    enabled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Theme, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=500)
    is_active = models.BooleanField(default=False)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    meta_keywords = models.TextField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-id']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def category_posts(self):
        return Post.objects.filter(category=self).count()


class Tags(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        tempslug = slugify(self.name)
        if self.id:
            tag = Tags.objects.get(pk=self.id)
            if tag.name != self.name:
                self.slug = create_tag_slug(tempslug)
        else:
            self.slug = create_tag_slug(tempslug)
        super(Tags, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


def create_tag_slug(tempslug):
    slugcount = 0
    while True:
        try:
            Tags.objects.get(slug=tempslug)
            slugcount += 1
            tempslug = tempslug + '-' + str(slugcount)
        except ObjectDoesNotExist:
            return tempslug


class Post(models.Model):
    title = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tags, related_name='rel_posts')
    status = models.CharField(max_length=10, choices=STATUS_CHOICE, default='Drafted')
    keywords = models.TextField(max_length=500, blank=True)
    featured_image = models.ImageField(upload_to='uploads/%Y-%m-%d', blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateField(auto_now=True)
    published_on = models.DateField(auto_now_add=True, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        self.old_status = self.status

    class Meta:
        ordering = ['-updated_on']

    def save(self, *args, **kwargs):
        tempslug = slugify(self.title)
        if self.id:
            blogpost = Post.objects.get(pk=self.id)
            if blogpost.title != self.title and self.status != 'Published':
                self.slug = create_slug(tempslug)
        else:
            if not self.slug:
                self.slug = create_slug(tempslug)
            self.email_to_admins_on_post_create()

        if self.old_status != self.status and self.status == 'Published':
            self.published_on = datetime.date.today()
        super(Post, self).save(*args, **kwargs)

    def update(self, *args, **kwargs):
        if self.old_status != self.status and self.status == 'Published':
            self.published_on = datetime.date.today()
        super(Post, self).update(*args, **kwargs)

    def __str__(self):
        return self.title

    def is_deletable_by(self, user):
        if self.user == user or user.is_superuser:
            return True
        return False

    def create_activity(self, user, content):
        return PostHistory.objects.create(
            user=user, post=self, content=content
        )

    def create_activity_instance(self, user, content):
        return PostHistory(
            user=user, post=self, content=content
        )

    def remove_activity(self):
        self.history.all().delete()

    def email_to_admins_on_post_create(self):
        email = os.getenv("DEFAULT_EMAIL")
        if not self.id and email:
            admin_roles = UserRole.objects.select_related().filter(role="Admin")
            admin_emails = [admin_role.user.email for admin_role in admin_roles]
            user = self.user
            author_name = user.first_name + user.last_name if user.first_name else user.email
            text = "New blog post has been created by {0} with the name {1} in the category {2}.".format(author_name,
                                                                                                         self.title,
                                                                                                         self.category.name)
            send_mail(
                subject="New Blog Post created",
                message=text,
                from_email=email,
                recipient_list=admin_emails,
                fail_silently=False,
            )

    def store_old_slug(self, old_slug):
        query = Post_Slugs.objects.filter(blog=self, slug=old_slug).values_list("slug", flat=True)
        if not (query and old_slug != self.slug):
            old_slug, _ = Post_Slugs.objects.get_or_create(blog=self, slug=old_slug)
            old_slug.is_active = False
            old_slug.save()
        active_slug, _ = Post_Slugs.objects.get_or_create(blog=self, slug=self.slug)
        active_slug.is_active = True
        active_slug.save()

    def get_absolute_url(self):
        return reverse('blog_post_view', args=[self.slug])


def create_slug(tempslug):
    slugcount = 0
    while True:
        try:
            Post.objects.get(slug=tempslug)
            slugcount += 1
            tempslug = tempslug + '-' + str(slugcount)
        except ObjectDoesNotExist:
            return tempslug


class Post_Slugs(models.Model):
    blog = models.ForeignKey(Post, related_name='slugs', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.slug


class PostHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='history', on_delete=models.CASCADE)
    content = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{username} {content} {blog_title}'.format(
            username=str(self.user.get_username()),
            content=str(self.content),
            blog_title=str(self.post.title)
        )


class Image_File(models.Model):
    upload = models.FileField(upload_to="uploads/%Y-%m-%d")
    date_created = models.DateTimeField(default=timezone.now)
    is_image = models.BooleanField(default=True)
    thumbnail = models.FileField(upload_to="uploads/%Y-%m-%d", blank=True, null=True)

    def __str__(self):
        return self.date_created


class Page(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    slug = models.SlugField()
    is_active = models.BooleanField(default=True)
    meta_description = models.TextField()
    keywords = models.TextField()
    meta_title = models.TextField()
    is_home = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def save(self, *args, **kwargs):
        tempslug = slugify(self.title)
        if self.id:
            existed_page = Page.objects.get(pk=self.id)
            if existed_page.title != self.title:
                self.slug = create_slug(tempslug)
        else:
            self.slug = create_slug(tempslug)

        # if is_home is true update all other rows to 0
        if self.is_home:
            Page.objects.all().update(is_home=0)

        super(Page, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('page_view', args=[self.slug])


class Menu(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    status = models.BooleanField(default=True)
    lvl = models.IntegerField(blank=True)

    def __str__(self):
        return self.title

    def get_children(self):
        return self.menu_set.all()

    def has_children(self):
        if self.get_children():
            return True
        return False


class ContactUsSettings(models.Model):
    from_email = models.EmailField()
    reply_to_email = models.EmailField(blank=True, null=True)
    email_admin = models.EmailField()
    subject = models.CharField(max_length=500)
    body_user = models.TextField()
    body_admin = models.TextField()


class Google(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='google', on_delete=models.CASCADE)
    google_id = models.CharField(max_length=200, default='')
    google_url = models.CharField(max_length=1000, default='')
    verified_email = models.CharField(max_length=200, default='')
    family_name = models.CharField(max_length=200, default='')
    name = models.CharField(max_length=200, default='')
    picture = models.CharField(max_length=200, default='')
    gender = models.CharField(max_length=10, default='')
    dob = models.CharField(max_length=50, default='')
    given_name = models.CharField(max_length=200, default='')
    email = models.CharField(max_length=200, default='', db_index=True)

    def __str__(self):
        return self.email


class Facebook(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='facebook', on_delete=models.CASCADE)
    facebook_id = models.CharField(max_length=100)
    facebook_url = models.CharField(max_length=200, default='')
    first_name = models.CharField(max_length=200, default='')
    last_name = models.CharField(max_length=200, default='')
    verified = models.CharField(max_length=200, default='')
    name = models.CharField(max_length=200, default='')
    language = models.CharField(max_length=200, default='')
    hometown = models.CharField(max_length=200, default='')
    email = models.CharField(max_length=200, default='', db_index=True)
    gender = models.CharField(max_length=200, default='')
    dob = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, default='')
    timezone = models.CharField(max_length=200, default='')
    accesstoken = models.CharField(max_length=2000, default='')

    def __str__(self):
        return self.email


class UrlHit(models.Model):
    url = models.URLField()
    hits = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.url)

    def increase(self):
        self.hits += 1
        self.save()

    class Meta:
        db_table = 'url_hit'


class HitCount(models.Model):
    id = models.IntegerField(primary_key=True, auto_created=True)
    url_hit = models.ForeignKey(UrlHit, editable=False, on_delete=models.CASCADE)
    ip = models.CharField(max_length=40)
    session = models.CharField(max_length=40)
    user_agent = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hit_count'