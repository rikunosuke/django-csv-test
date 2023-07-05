from django.contrib import admin

from book.mcsv import PublisherCsv, BookWithPublisherCsv
from book.models import Book, Publisher
from django_csv.model_csv.csv.django.admin import DjangoCsvAdminMixin


@admin.register(Book)
class BookAdmin(DjangoCsvAdminMixin, admin.ModelAdmin):
    csv_class = BookWithPublisherCsv
    file_name = 'book'


@admin.register(Publisher)
class PublisherAdmin(DjangoCsvAdminMixin, admin.ModelAdmin):
    csv_class = PublisherCsv
    file_name = 'publisher'
