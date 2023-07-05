from book.models import Book, Publisher
from django.contrib.auth import get_user_model
from django_csv.model_csv import ValidationError, columns
from django_csv.model_csv.csv.django import DjangoCsv

User = get_user_model()


class PublisherCsv(DjangoCsv):
    pk = columns.AttributeColumn(header='id', attr_name='id')
    name = columns.AttributeColumn(header='Publisher Name')
    country = columns.MethodColumn(header='Country')
    city = columns.MethodColumn(header='City')
    registered_by = columns.MethodColumn(header='Registered BY')

    class Meta:
        model = Publisher
        auto_assign = True

    def column_country(self, instance: Publisher, **kwargs) -> str:
        return instance.headquarter.split(',')[1].strip()

    def column_city(self, instance: Publisher, **kwargs) -> str:
        return instance.headquarter.split(',')[0].strip()

    def column_registered_by(self, instance: Publisher, **kwargs) -> str:
        return instance.registered_by.username

    def field_headquarter(self, values: dict, **kwargs) -> dict:
        city = values['city'].strip()
        country = values['country'].strip()
        if not city or not country:
            raise ValidationError('`City` and `Country` are required', label='Headquarter')

        return city + ', ' + country

    def field_registered_by(self, values: dict, **kwargs):
        user, _ = User.objects.get_or_create(username=values['registered_by'])
        return user

    def get_publisher(self, values: dict, static: dict, **kwargs) -> Publisher:
        """
        callback method when used as a part.
        """
        values = self.remove_extra_values(values)
        if not static.get('only_exists'):
            return Publisher.objects.get_or_create(**values)[0]

        try:
            return Publisher.objects.get(**values)
        except (Publisher.DoesNotExist, Publisher.MultipleObjectsReturned) as e:
            raise ValidationError(str(e), label='Publisher', column_index=0)


class BookCsv(DjangoCsv):

    class Meta:
        model = Book
        fields = '__all__'


class BookWithPublisherCsv(DjangoCsv):
    pbl = PublisherCsv.as_part(
        related_name='publisher', callback='get_publisher'
    )

    pbl_name = pbl.AttributeColumn(header='Publisher', attr_name='name')
    pbl_country = pbl.MethodColumn(
        header='Country', method_suffix='country', value_name='country')
    pbl_city = pbl.MethodColumn(
        header='City', method_suffix='city', value_name='city')
    pbl_registered_by = pbl.MethodColumn(
        header='Registered By', method_suffix='registered_by',
        value_name='registered_by'
    )

    class Meta:
        model = Book
        fields = '__all__'
        auto_assign = True
