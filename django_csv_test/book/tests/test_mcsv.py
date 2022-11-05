import random
from datetime import datetime, timezone, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from book.models import Book, Author, Publisher
from book.tests.factories import AuthorFactory, BookFactory
from django_csv import ModelCsv, columns
from django_csv.columns import ColumnValidationError


class ModelCsvForWriteTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        User.objects.create_user(username='admin', password='password')

        AuthorFactory.create_batch(10)
        author_list = list(Author.objects.all())
        for _ in range(50):
            authors = random.sample(author_list, random.randrange(1, 4))
            BookFactory(authors=authors)

    def setUp(self) -> None:
        self.all_queryset = Book.objects.order_by('id').all()

    def test_model_csv_default_use(self):
        class BookCsv(ModelCsv):
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

    def test_customize_column(self):
        class CustomizeBookCsv(ModelCsv):
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
        class OnlyTitleBookCsv(ModelCsv):
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
        class BookCsv(ModelCsv):
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
        class PublisherCsv(ModelCsv):

            class Meta:
                model = Publisher

            def column_city(self, instance: Publisher, **kwargs) -> str:
                return instance.headquarter.split(',')[0]

            def column_country(self, instance: Publisher, **kwargs) -> str:
                return instance.headquarter.split(',')[1]

            def field_headquarter(self, values: dict, **kwargs) -> str:
                return values['city'] + ',' + values['country']

        class BookCsv(ModelCsv):
            title = columns.AttributeColumn()

            prt = PublisherCsv.as_part(field_name='publisher')
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
        pbl_cnt = Publisher.objects.count()
        with self.subTest():
            for obj, d in zip(self.all_queryset, for_read.get_as_dict()):
                self.assertSetEqual(set(d.keys()), {'title', 'publisher'})
                self.assertEqual(obj.publisher, d['publisher'])

        # default is 'get_or_create' so the count of publishers doesn't change.
        self.assertEqual(pbl_cnt, Publisher.objects.count())

    def test_part_column_validation(self):
        class PublisherCsv(ModelCsv):
            class Meta:
                model = Publisher

        class MethodColumnInvalidCsv(ModelCsv):
            part = PublisherCsv.as_part(field_name='publisher')
            pbl_name = part.AttributeColumn(attr_name='name')
            pbl_country = part.MethodColumn()  # ColumnValidationError

            class Meta:
                model = Book
                auto_assign = True

        with self.assertRaises(ColumnValidationError):
            MethodColumnInvalidCsv.for_read(table=[['', '']])

        with self.assertRaises(ColumnValidationError):
            MethodColumnInvalidCsv.for_write(instances=self.all_queryset)

        class MethodColumnValidCsv(ModelCsv):
            part = PublisherCsv.as_part(field_name='publisher')
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

        class StaticColumnInvalidCsv(ModelCsv):
            part = PublisherCsv.as_part(field_name='publisher')
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

        class StaticColumnValidCsv(ModelCsv):
            part = PublisherCsv.as_part(field_name='publisher')
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
        class PublisherPart(ModelCsv):
            class Meta:
                model = Publisher

            def column_name(self, instance: Publisher, **kwargs):
                # column_<attr_name> is called. Not column_<var name>
                return 'pbl:' + instance.name

            def column_suffix(self, instance: Publisher, **kwargs):
                return 'suffix:' + instance.name

        class BookCsv(ModelCsv):
            book_name = columns.AttributeColumn(attr_name='name')
            # columns which have same attr_name ↑↓ does not cause conflict.
            part = PublisherPart.as_part(field_name='publisher')
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
        class JSTTimeZoneCsv(ModelCsv):
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

        class UTCTimeZoneCsv(ModelCsv):
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
