from django_csv import ModelCsv, columns
from book.models import Book, Publisher


class PublisherCsv(ModelCsv):
    pk = columns.AttributeColumn(header='id', attr_name='id')
    name = columns.AttributeColumn(header='Publisher Name')
    country = columns.MethodColumn(header='Country')
    city = columns.MethodColumn(header='City')

    class Meta:
        auto_assign = True

    def column_country(self, instance: Publisher, **kwargs) -> str:
        return instance.headquarter.split(',')[1]

    def column_city(self, instance: Publisher, **kwargs) -> str:
        return instance.headquarter.split(',')[0]

    def field_headquarter(self, values: dict, **kwargs) -> dict:
        return values['country'] + ',' + values['city']


class BookCsv(ModelCsv):

    class Meta:
        model = Book
        fields = '__all__'


class BookWithPublisherCsv(ModelCsv):
    publisher = PublisherCsv.as_part(
        field_name='publisher', callback='get_or_create_object'
    )

    name = publisher.AttributeColumn(header='name', attr_name='name')
    country = publisher.MethodColumn(header='country', attr_name='country')
    city = publisher.MethodColumn(header='city', attr_name='city')

    class Meta:
        model = Book
        fields = '__all__'
        auto_assign = True

    def field_publisher__headquarter(self, values: dict, **kwargs) -> dict:
        """
        This method DOES NOT WORK.
        Do not try to modify foreign data in field_* method.
        Instead use field() method.
        """
