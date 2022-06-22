from django import forms

from django_csv import readers

READER = {
    'csv': readers.CsvReader,
    'tsv': readers.TsvReader,
    'xlsx': readers.XlsxReader,
    'xls': readers.XlsReader,
}


class UploadForm(forms.Form):
    file = forms.FileField(required=True)

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data['file']
        expansion = file.name.split('.')[-1]

        try:
            cleaned_data['reader'] = READER[expansion.lower()]
        except KeyError:
            raise forms.ValidationError(f'`{expansion}` is not supported')

        return cleaned_data
