from django.contrib import admin

from book.mcsv import PublisherCsv, BookWithPublisherCsv
from book.models import Book, Publisher
from django_csv.admin.mixins import ModelCsvAdminMixin


@admin.register(Book)
class BookAdmin(ModelCsvAdminMixin, admin.ModelAdmin):
    csv_class = BookWithPublisherCsv
    file_name = 'book'


@admin.register(Publisher)
class PublisherAdmin(ModelCsvAdminMixin, admin.ModelAdmin):
    csv_class = PublisherCsv
    file_name = 'publisher'
