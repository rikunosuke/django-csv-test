import factory
import random

from book.models import Book, Author, Publisher


class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author

    name = factory.Faker('name')


class PublisherFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Publisher

    name = factory.Faker('company')
    headquarter = factory.Iterator([
        'Tokyo, Japan',
        'Seoul, North Korea',
        'New York City, U.S',
        'Toronto, Canada',
        'Rio de Janeiro, Brasil',
        'Buenos Aires, Argentine',
        'Warsaw, Poland',
        'London, U.K',
        'Cape Town, South Africa',
        'Accra, Ghana',
        'Sydney, Australia',
        'Auckland, New Zealand',
    ])


def random_tf():
    return random.choices([True, False], weights=[9, 1], k=1)[0]


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Sequence(lambda i: f'title {i}')
    price = factory.LazyAttribute(lambda _: random.randrange(400, 10000))
    publisher = factory.SubFactory(PublisherFactory)
    is_on_sale = factory.LazyFunction(random_tf)
    description = factory.Faker('text')

    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for author in extracted:
                self.authors.add(author)
