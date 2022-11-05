from django.test import TestCase

from book.models import Book
from django_csv.mcsv.metaclasses import ModelOptions


class ModelCsvOptionTest(TestCase):
    def test_model_csv_options(self):
        meta = type('Meta', (), {'model': Book, 'fields': '__all__'})
        opt = ModelOptions(meta=meta, columns={}, parts=[])
        self.assertEqual(len(opt.columns), 6)
        self.assertSetEqual(
            set(col.get_w_index(original=True) for col in opt.columns),
            set(i for i in range(6))
        )

        # check if the order of auto created columns is always same.
        FIELDS = [
            'title',
            'price',
            'is_on_sale',
            'description',
            'created_at',
            'updated_at',
        ]
        for i, field_name in enumerate(FIELDS):
            with self.subTest(field_name):
                col = opt.get_column(field_name)
                self.assertEqual(col.get_w_index(original=True), i)
                self.assertEqual(col.get_w_index(), i)

        # ModelOptions for Part does not have columns.
        part_meta = type('Meta', (), {'model': Book, 'as_part': True})
        part_opt = ModelOptions(meta=part_meta, columns={}, parts=[])
        self.assertEqual(len(part_opt.columns), 0)
