import random
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from book.models import Author, Book
from book.tests.factories import AuthorFactory, BookFactory


class Command(BaseCommand):
    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                'admin', 'admin@example.com', 'password')

        Author.objects.all().delete()
        Book.objects.all().delete()

        AuthorFactory.create_batch(10)
        author_list = list(Author.objects.all())
        for _ in range(50):
            authors = random.sample(author_list, random.randrange(1, 4))
            BookFactory(authors=authors)
