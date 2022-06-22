from django.contrib import admin
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from book.admin.forms import UploadForm
from book.mcsv import PublisherCsv, BookWithPublisherCsv
from book.models import Book, Publisher
from django_csv.writers import CsvWriter, TsvWriter, XlsxWriter, XlsWriter


class DownloadActionMixin:
    actions = ['download_csv', 'download_tsv', 'download_xlsx', 'download_xls']
    _csv_name: str = 'CsvFile'

    @admin.action(description='download (.csv)')
    def download_csv(self, request, queryset):
        mcsv = self._csv_class.for_write(queryset=queryset)
        return mcsv.get_response(CsvWriter(filename=f'{self._csv_name}.csv'))

    @admin.action(description='download (.tsv)')
    def download_tsv(self, request, queryset):
        mcsv = self._csv_class.for_write(queryset=queryset)
        return mcsv.get_response(TsvWriter(filename=f'{self._csv_name}.tsv'))

    @admin.action(description='download (.xlsx)')
    def download_xlsx(self, request, queryset):
        mcsv = self._csv_class.for_write(queryset=queryset)
        return mcsv.get_response(XlsxWriter(filename=f'{self._csv_name}.xlsx'))

    @admin.action(description='download (.xls)')
    def download_xls(self, request, queryset):
        mcsv = self._csv_class.for_write(queryset=queryset)
        return mcsv.get_response(XlsWriter(filename=f'{self._csv_name}.xls'))


@admin.register(Book)
class BookAdmin(DownloadActionMixin, admin.ModelAdmin):
    _csv_class = BookWithPublisherCsv
    _csv_name = 'book'

    def get_urls(self):
        urls = super().get_urls()
        new_url = [
            path('upload/',
                 self.admin_site.admin_view(self.upload_csv), name='upload_csv'
                 ),
        ]
        return new_url + urls

    def upload_csv(self, request):
        if request.method == 'GET':
            return TemplateResponse(
                request, 'admin/book/upload_csv.html', {'form': UploadForm()})
        else:
            form = UploadForm(request.POST, request.FILES)
            if not form.is_valid():
                return TemplateResponse(
                    request, 'admin/book/upload_csv.html', {'form': form})

            READER = form.cleaned_data['reader']
            reader = READER(file=form.cleaned_data['file'], table_start_from=1)

            mcsv = self._csv_class.for_read(table=reader.get_table())
            mcsv.bulk_create()

            return redirect(reverse('admin:book'))


@admin.register(Publisher)
class PublisherAdmin(DownloadActionMixin, admin.ModelAdmin):
    _csv_class = PublisherCsv
    _csv_name = 'publisher'
