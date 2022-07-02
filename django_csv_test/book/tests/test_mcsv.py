import random
from datetime import datetime
from django.test import TestCase

from book.models import Book, Author, Publisher
from book.tests.factories import AuthorFactory, BookFactory
from django_csv import ModelCsv, columns


class ModelCsvForWriteTest(TestCase):
    @classmethod
    def setUpTestData(cls):
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
                    val = val.strftime(BookCsv._meta.datetime_format)
                else:
                    val = str(val)

                self.assertEqual(val, row[x])

    def test_customize_column(self):
        class CustomizeBookCsv(ModelCsv):
            pk = columns.AttributeColumn(header='primary key')
            is_on_sale = columns.AttributeColumn(header='now on sale')
            title = columns.AttributeColumn(header='custom title')

            class Meta:
                model = Book
                auto_assign = True

        for_write = CustomizeBookCsv.for_write(
            queryset=self.all_queryset)
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
            queryset=self.all_queryset)

        for obj, row in zip(self.all_queryset,
                            only_title_for_write.get_table(header=False)):
            self.assertListEqual([obj.title], row)

        class TitleAndPriceBookCsv(OnlyTitleBookCsv):
            price = columns.AttributeColumn(index=1)

            class Meta:
                model = Book
                auto_assign = True

        for_write = TitleAndPriceBookCsv.for_write(queryset=self.all_queryset)
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

        for_write = BookCsv.for_write(queryset=self.all_queryset)
        for row, obj in zip(for_write.get_table(header=False),
                            self.all_queryset):
            self.assertListEqual(
                row, ['yes' if obj.is_on_sale else 'no', str(obj.price), obj.title])

    def test_foreign_part_without_part(self):
        class BookCsv(ModelCsv):
            title = columns.AttributeColumn()
            publisher__name = columns.AttributeColumn()
            publisher__headquarter = columns.AttributeColumn()

            class Meta:
                model = Book
                auto_assign = True

        for_write = BookCsv.for_write(queryset=self.all_queryset)
        table = for_write.get_table(header=False)
        for obj, row in zip(self.all_queryset, table):
            with self.subTest():
                self.assertListEqual(
                    row, [obj.title, obj.publisher.name, obj.publisher.headquarter])

    def test_part_default_use(self, **kwargs):
        class PublisherCsv(ModelCsv):
            name = columns.AttributeColumn()
            city = columns.MethodColumn()
            country = columns.MethodColumn()

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

            pbl_part = PublisherCsv.as_part(field_name='publisher')
            pbl_name = pbl_part.AttributeColumn(attr_name='name')
            pbl_city = pbl_part.MethodColumn(attr_name='city')
            pbl_country = pbl_part.MethodColumn(attr_name='country')

            class Meta:
                model = Book
                auto_assign = True

        for_write = BookCsv.for_write(queryset=self.all_queryset)
        table = for_write.get_table(header=False)
        for obj, row in zip(self.all_queryset, table):
            city, country = obj.publisher.headquarter.split(',')
            self.assertListEqual(
                row, [obj.title, obj.publisher.name, city, country])
