from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column
from .models import Thesis, Remark, MAX_THESIS_TITLE_LEN
from .enums import ThesisKind
from apps.users.models import Employee, Student

class ThesisForm(forms.ModelForm):

    class Meta:
        model = Thesis
        fields = ('title', 'advisor', 'supporting_advisor', 'kind',
                  'reserved_until', 'description')

    title = forms.CharField(label="Tytuł pracy", max_length=MAX_THESIS_TITLE_LEN)
    advisor = forms.ModelChoiceField(queryset=Employee.objects.all(),label="Promotor", required=True)
    supporting_advisor = forms.ModelChoiceField(queryset=Employee.objects.all(), label="Promotor wspierający", required=False)
    kind = forms.ChoiceField(choices=ThesisKind.choices(), label="Typ")
    reserved_until = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}),
                                     input_formats=['%d/%m/%Y'], label="Zarezerwowana do", required=False)
    description = forms.CharField(label="Opis", widget=forms.Textarea, required=False)

    def __init__(self, default_advisor=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        if default_advisor:
            self.fields['advisor'].widget.attrs['disabled'] = True
        self.helper.layout = Layout(
            'title',
            Row(
                Column('advisor', css_class='form-group col-md-6 mb-0'),
                Column('supporting_advisor', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('kind', css_class='form-group col-md-6 mb-0'),
                Column('reserved_until', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'description',
            Submit('submit', 'Zapisz')
        )
        self.helper.form_method = 'post'

    def clean(self):
        """
        Custom validation: ensure that the students limit hasn't been exceeded.
        """
        students = self.cleaned_data.get('students')
        if students and len(students) > 2:
            raise forms.ValidationError(
                'Do pracy dyplomowej można przypisać co najwyżej 2 studentów.'
            )
        return self.cleaned_data


class RemarkForm(forms.ModelForm):
    class Meta:
        model = Remark
        fields = '__all__'
