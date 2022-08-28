from django_csv import ModelCsv, columns
from book.models import Book, Publisher


class PublisherCsv(ModelCsv):
    pk = columns.AttributeColumn(header='id', attr_name='id')
    name = columns.AttributeColumn(header='Publisher Name')
    country = columns.MethodColumn(header='Country')
    city = columns.MethodColumn(header='City')

    class Meta:
        auto_assign = True
        model = Publisher

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

    pbl_name = publisher.AttributeColumn(header='Publisher', attr_name='name')
    pbl_country = publisher.MethodColumn(header='Country', attr_name='country')
    pbl_city = publisher.MethodColumn(header='City', attr_name='city')

    class Meta:
        model = Book
        fields = '__all__'
        auto_assign = True
