import random
from datetime import datetime, timezone, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from book.models import Book, Author, Publisher
from book.tests.factories import AuthorFactory, BookFactory
from django_csv.model_csv import ValidationError
from django_csv.model_csv import columns
from django_csv.model_csv.columns import ColumnValidationError
from django_csv.model_csv.csv.django import DjangoCsv

User = get_user_model()


class DjangoCsvForWriteTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='admin', password='password')

        AuthorFactory.create_batch(10)
        author_list = list(Author.objects.all())
        for _ in range(50):
            authors = random.sample(author_list, random.randrange(1, 4))
            BookFactory(authors=authors)

    def setUp(self) -> None:
        self.all_queryset = Book.objects.order_by('id').all()

    def test_model_csv_default_use(self):
        class BookCsv(DjangoCsv):
            class Meta:
                model = Book
                fields = '__all__'

        for_write = BookCsv.for_write(self.all_queryset)
        table = for_write.get_table(header=True)
        self.assertEqual(len(table), 51)  # 50 main row + 1 header

        FIELDS = [
            'title',
            'price',
            'is_on_sale',
            'description',
            'created_at',
            'updated_at',
        ]

        # check header
        for header, field_name in zip(table[0], FIELDS):
            with self.subTest(field_name):
                verbose_name = Book._meta.get_field(field_name).verbose_name
                self.assertEqual(verbose_name, header)

        for row, obj in zip(table[1:], self.all_queryset):
            for x, field_name in enumerate(FIELDS):
                val = getattr(obj, field_name)
                if isinstance(val, bool):
                    val = 'yes' if val else 'no'
                if isinstance(val, datetime):
                    val = val.astimezone(
                        BookCsv._meta.tzinfo).strftime(
                        BookCsv._meta.datetime_format)
                else:
                    val = str(val)

                self.assertEqual(val, row[x])

    def test_headers(self):
        class BookCsv(DjangoCsv):
            class Meta:
                model = Book
                fields = ['title', 'price']
                headers = {'title': 'Book Title', 'price': 'Book Price'}

        for_write = BookCsv.for_write(instances=[[0]])
        headers = for_write._meta.get_headers(for_write=True)
        self.assertEqual(headers, ['Book Title', 'Book Price'])

    def test_customize_column(self):
        class CustomizeBookCsv(DjangoCsv):
            pk = columns.AttributeColumn(header='primary key')
            is_on_sale = columns.AttributeColumn(header='now on sale', to=bool)
            title = columns.AttributeColumn(header='custom title')

            class Meta:
                model = Book
                auto_assign = True

        for_write = CustomizeBookCsv.for_write(
            instances=self.all_queryset)
        table = for_write.get_table()
        self.assertListEqual(table[0], ['primary key', 'now on sale', 'custom title'])

        for row, obj in zip(table[1:], self.all_queryset):
            self.assertListEqual(
                row, [str(obj.pk), 'yes' if obj.is_on_sale else 'no', obj.title])

    def test_override_model_csv(self):
        class OnlyTitleBookCsv(DjangoCsv):
            title = columns.AttributeColumn(header='custom title')

            class Meta:
                model = Book
                auto_assign = True

        only_title_for_write = OnlyTitleBookCsv.for_write(
            instances=self.all_queryset)

        for obj, row in zip(self.all_queryset,
                            only_title_for_write.get_table(header=False)):
            self.assertListEqual([obj.title], row)

        class TitleAndPriceBookCsv(OnlyTitleBookCsv):
            price = columns.AttributeColumn(index=1)

            class Meta:
                model = Book
                auto_assign = True

        for_write = TitleAndPriceBookCsv.for_write(instances=self.all_queryset)
        for row, obj in zip(for_write.get_table(header=False),
                            self.all_queryset):
            self.assertListEqual(row, [obj.title, str(obj.price)])

        class BookCsv(TitleAndPriceBookCsv):
            class Meta:
                model = Book
                fields = ['title', 'price', 'is_on_sale']
                auto_assign = True

        self.assertEqual(len(BookCsv._meta.columns), 3)

        self.assertSetEqual(
            {col.get_r_index() for col in BookCsv._meta.columns}, {0, 1, 2}
        )
        self.assertSetEqual(
            {col.get_w_index() for col in BookCsv._meta.columns}, {0, 1, 2}
        )

        price_column = BookCsv._meta.get_column('price')
        self.assertEqual(price_column.get_r_index(), 1)
        self.assertEqual(price_column.get_r_index(original=True), 1)

        for_write = BookCsv.for_write(instances=self.all_queryset)
        for row, obj in zip(for_write.get_table(header=False),
                            self.all_queryset):
            self.assertListEqual(
                row, ['yes' if obj.is_on_sale else 'no', str(obj.price), obj.title])

    def test_foreign_key_only_write(self):
        class BookCsv(DjangoCsv):
            title = columns.AttributeColumn()
            publisher__name = columns.AttributeColumn()
            publisher__headquarter = columns.AttributeColumn()

            class Meta:
                model = Book
                auto_assign = True

        for_write = BookCsv.for_write(instances=self.all_queryset)
        table = for_write.get_table(header=False)
        for obj, row in zip(self.all_queryset, table):
            with self.subTest():
                self.assertListEqual(
                    row,
                    [obj.title, obj.publisher.name, obj.publisher.headquarter]
                )

    def test_part_default_use(self, **kwargs):
        class PublisherCsv(DjangoCsv):

            class Meta:
                model = Publisher

            def column_city(self, instance: Publisher, **kwargs) -> str:
                return instance.headquarter.split(',')[0]

            def column_country(self, instance: Publisher, **kwargs) -> str:
                return instance.headquarter.split(',')[1]

            def field_headquarter(self, values: dict, **kwargs) -> str:
                return values['city'] + ',' + values['country']

        class BookCsv(DjangoCsv):
            title = columns.AttributeColumn()

            prt = PublisherCsv.as_part(related_name='publisher')
            pbl_name = prt.AttributeColumn(attr_name='name')
            pbl_city = prt.MethodColumn(
                method_suffix='city', value_name='city')
            pbl_country = prt.MethodColumn(
                method_suffix='country', value_name='country')
            pbl_registered_by_id = prt.StaticColumn(
                static_value=1, value_name='registered_by_id', to=int)

            class Meta:
                model = Book
                auto_assign = True

        for_write = BookCsv.for_write(instances=self.all_queryset)
        table = for_write.get_table(header=False)
        for obj, row in zip(self.all_queryset, table):
            city, country = obj.publisher.headquarter.split(',')
            self.assertListEqual(
                row, [obj.title, obj.publisher.name, city, country, '1']
            )

        for_read = BookCsv.for_read(table=table)
        self.assertTrue(for_read.is_valid())
        pbl_cnt = Publisher.objects.count()
        with self.subTest():
            for obj, d in zip(self.all_queryset, for_read.cleaned_rows):
                self.assertSetEqual(set(d.keys()), {'title', 'publisher'})
                self.assertEqual(obj.publisher, d['publisher'])

        # default is 'get_or_create' so the count of publishers doesn't change.
        self.assertEqual(pbl_cnt, Publisher.objects.count())

    def test_part_column_validation(self):
        class PublisherCsv(DjangoCsv):
            class Meta:
                model = Publisher

        class MethodColumnInvalidCsv(DjangoCsv):
            part = PublisherCsv.as_part(related_name='publisher')
            pbl_name = part.AttributeColumn(attr_name='name')
            pbl_country = part.MethodColumn()  # ColumnValidationError

            class Meta:
                model = Book
                auto_assign = True

        with self.assertRaises(ColumnValidationError):
            MethodColumnInvalidCsv.for_read(table=[['', '']])

        with self.assertRaises(ColumnValidationError):
            MethodColumnInvalidCsv.for_write(instances=self.all_queryset)

        class MethodColumnValidCsv(DjangoCsv):
            part = PublisherCsv.as_part(related_name='publisher')
            pbl_name = part.AttributeColumn(attr_name='name')
            pbl_count = part.MethodColumn(
                value_name='country', method_suffix='country')

            class Meta:
                model = Book
                auto_assign = True

        try:
            MethodColumnValidCsv.for_read(table=[['', '']])
        except ColumnValidationError as e:
            self.fail(
                '`ColumnValidationError` is raised unexpectedly. ' + str(e))

        try:
            MethodColumnValidCsv.for_write(instances=self.all_queryset)
        except ColumnValidationError as e:
            self.fail(
                '`ColumnValidationError` is raised unexpectedly. ' + str(e))

        class StaticColumnInvalidCsv(DjangoCsv):
            part = PublisherCsv.as_part(related_name='publisher')
            pbl_name = part.AttributeColumn(attr_name='name')
            pbl_created_by = part.StaticColumn()

            class Meta:
                model = Book
                auto_assign = True

        with self.assertRaises(ColumnValidationError):
            StaticColumnInvalidCsv.for_read(table=[['', '']])

        try:
            StaticColumnInvalidCsv.for_write(instances=self.all_queryset)
        except ColumnValidationError as e:
            self.fail('`ColumnValidationError` is raised unexpectedly. ' + str(e))

        class StaticColumnValidCsv(DjangoCsv):
            part = PublisherCsv.as_part(related_name='publisher')
            pbl_name = part.AttributeColumn(attr_name='name')
            pbl_created_by = part.StaticColumn(value_name='created_by')

            class Meta:
                model = Book
                auto_assign = True

        try:
            StaticColumnValidCsv.for_read(table=[['', '']])
        except ColumnValidationError as e:
            self.fail(
                '`ColumnValidationError` is raised unexpectedly. ' + str(e))

        try:
            StaticColumnValidCsv.for_write(instances=self.all_queryset)
        except ColumnValidationError as e:
            self.fail(
                '`ColumnValidationError` is raised unexpectedly. ' + str(e))

    def test_method_suffix(self):
        class PublisherPart(DjangoCsv):
            class Meta:
                model = Publisher

            def column_name(self, instance: Publisher, **kwargs):
                # column_<attr_name> is called. Not column_<var name>
                return 'pbl:' + instance.name

            def column_suffix(self, instance: Publisher, **kwargs):
                return 'suffix:' + instance.name

        class BookCsv(DjangoCsv):
            book_name = columns.AttributeColumn(attr_name='name')
            # columns which have same attr_name ↑↓ does not cause conflict.
            part = PublisherPart.as_part(related_name='publisher')
            pbl_name = part.AttributeColumn(attr_name='name')
            suffix_test = part.MethodColumn(method_suffix='suffix')

            class Meta:
                model = Book
                auto_assign = True
                read_mode = False

        for_write = BookCsv.for_write(instances=self.all_queryset)
        table = for_write.get_table()
        self.assertListEqual(['book_name', 'pbl_name', 'suffix_test'], table[0])
        for obj, row in zip(self.all_queryset, table[1:]):
            with self.subTest():
                self.assertListEqual(
                    [obj.name, f'pbl:{obj.publisher.name}', f'suffix:{obj.publisher.name}'],
                    row
                )

    def test_tz_meta_option(self):
        settings.TIME_ZONE = 'Asia/Tokyo'

        class JSTTimeZoneCsv(DjangoCsv):
            class Meta:
                model = Book
                fields = ['created_at']

        for_write = JSTTimeZoneCsv.for_write(instances=self.all_queryset)
        table = for_write.get_table(header=False)
        for obj, row in zip(self.all_queryset, table):
            with self.subTest():
                # timezone is jst
                jst_created_at = obj.created_at + timedelta(hours=9)
                self.assertEqual(
                    jst_created_at.strftime(for_write._meta.datetime_format),
                    row[0]
                )

        for_read = JSTTimeZoneCsv.for_read(table=[['2022-10-01 00:00:00']])
        self.assertTrue(for_read.is_valid())
        row = list(for_read.cleaned_rows)[0]
        self.assertEqual(
            row['created_at'], datetime(2022, 9, 30, 15, tzinfo=timezone.utc)
        )

        class UTCTimeZoneCsv(DjangoCsv):
            class Meta:
                model = Book
                fields = ['created_at']
                tzinfo = timezone.utc

        for_write = UTCTimeZoneCsv.for_write(instances=self.all_queryset)
        table = for_write.get_table(header=False)
        for obj, row in zip(self.all_queryset, table):
            self.assertEqual(
                obj.created_at.strftime(for_write._meta.datetime_format),
                row[0]
            )

        for_read = UTCTimeZoneCsv.for_read(table=[['2022-10-01 00:00:00']])
        self.assertTrue(for_read.is_valid())
        row = list(for_read.cleaned_rows)[0]
        self.assertEqual(
            row['created_at'], datetime(2022, 10, 1, tzinfo=timezone.utc)
        )

    def test_decorator(self):
        class PublisherCsv(DjangoCsv):
            pk = columns.AttributeColumn(header='id', attr_name='id')
            name = columns.AttributeColumn(header='Publisher Name')

            class Meta:
                model = Publisher
                auto_assign = True

            @columns.as_column(header='Country')
            def country(self, instance: Publisher, **kwargs) -> str:
                return instance.headquarter.split(',')[0]

            @columns.as_column(header='City')
            def city(self, instance: Publisher, **kwargs):
                return instance.headquarter.split(',')[1]

            @columns.as_column(header='registered_by')
            def registered_by(self, instance: Publisher, **kwargs) -> str:
                return instance.registered_by.username

        publishers = Publisher.objects.all()
        mcsv = PublisherCsv.for_write(instances=publishers)
        for publisher, row in zip(publishers, mcsv.get_table(header=False)):
            self.assertEqual(str(publisher.pk), row[0])
            self.assertEqual(publisher.name, row[1])
            country, city = publisher.headquarter.split(',')
            self.assertEqual(country, row[2])
            self.assertEqual(city, row[3])
            self.assertEqual(publisher.registered_by.username, row[4])

    def test_validation(self):
        HEADQUARTER_CHOICES = [
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
        ]

        class MustNotBeRaisedError(Exception):
            pass

        class PublisherCsv(DjangoCsv):
            class Meta:
                model = Publisher

            def field_headquarter(self, values: dict, **kwargs) -> str:
                headquarter = ', '.join([values['city'], values['country']])
                if headquarter not in HEADQUARTER_CHOICES:
                    raise ValidationError(f'{headquarter} is not in choices.')
                return headquarter

            def field(self, values: dict, **kwargs) -> dict:
                if values['city'] == 'osaka':
                    raise MustNotBeRaisedError('`field` must not be called')
                return values

        class BookCsv(DjangoCsv):
            prt = PublisherCsv.as_part(related_name='publisher')
            prt_name = prt.AttributeColumn(attr_name='name')
            prt_city = prt.MethodColumn(value_name='city')
            prt_country = prt.MethodColumn(value_name='country')

            class Meta:
                model = Book
                auto_assign = True

        publishers = Publisher.objects.all()
        table = [[pbl.name, pbl.city, pbl.country] for pbl in publishers]

        mcsv = BookCsv.for_read(table=table)
        self.assertTrue(mcsv.is_valid())
        for row in mcsv.cleaned_rows:
            self.assertIn('publisher', row)

        invalid_table = table + [['SHUEISHA', 'osaka', 'Japan']]
        mcsv = BookCsv.for_read(table=invalid_table)
        try:
            self.assertFalse(mcsv.is_valid())
        except MustNotBeRaisedError as e:
            self.fail(str(e))

        self.assertEqual(len(mcsv.cleaned_rows), publishers.count() + 1)
        for i, row in enumerate(mcsv.cleaned_rows):
            if row.is_valid:
                continue

            self.assertEqual(row.number, i)
            self.assertEqual(len(row.errors), 1)
            self.assertEqual(row.errors[0].name, 'publisher__headquarter')
            self.assertEqual(
                row.errors[0].message, 'osaka, Japan is not in choices.')
