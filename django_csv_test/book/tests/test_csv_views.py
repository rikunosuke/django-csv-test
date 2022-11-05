import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from book.models import Book, Publisher

User = get_user_model()

TEST_DATA_DIR = Path(os.path.dirname(__file__)) / 'test_data'


class ViewTest(TestCase):
    url = reverse('admin:book_book_upload_csv')
    redirect_to = reverse('admin:book_book_changelist')

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_superuser(username='admin')

    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(user=self.user)

    def test_upload_csv(self):
        self.assertEqual(Book.objects.count(), 0)
        self.assertEqual(Publisher.objects.count(), 0)

        with open(TEST_DATA_DIR / 'book.csv', 'br') as f:
            resp = self.client.post(self.url, {'file': f})
        self.assertRedirects(resp, expected_url=self.redirect_to)

        self.assertEqual(Book.objects.count(), 50)
        self.assertGreater(Publisher.objects.count(), 0)

    def test_upload_tsv(self):
        self.assertEqual(Book.objects.count(), 0)
        self.assertEqual(Publisher.objects.count(), 0)

        with open(TEST_DATA_DIR / 'book.tsv', 'br') as f:
            resp = self.client.post(self.url, {'file': f})
        self.assertRedirects(resp, expected_url=self.redirect_to)

        self.assertEqual(Book.objects.count(), 50)
        self.assertGreater(Publisher.objects.count(), 0)

    def test_upload_xlsx(self):
        self.assertEqual(Book.objects.count(), 0)
        self.assertEqual(Publisher.objects.count(), 0)

        with open(TEST_DATA_DIR / 'book.xlsx', 'br') as f:
            resp = self.client.post(self.url, {'file': f})
        self.assertRedirects(resp, expected_url=self.redirect_to)

        self.assertEqual(Book.objects.count(), 50)
        self.assertGreater(Publisher.objects.count(), 0)

    def test_upload_xls(self):
        self.assertEqual(Book.objects.count(), 0)
        self.assertEqual(Publisher.objects.count(), 0)

        with open(TEST_DATA_DIR / 'book.xls', 'br') as f:
            resp = self.client.post(self.url, {'file': f})
        self.assertRedirects(resp, expected_url=self.redirect_to)

        self.assertEqual(Book.objects.count(), 50)
        self.assertGreater(Publisher.objects.count(), 0)
