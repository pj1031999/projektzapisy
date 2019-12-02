from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Thesis, Remark, MAX_THESIS_TITLE_LEN
from .enums import ThesisKind
from apps.users.models import Employee, Student

class ThesisForm(forms.ModelForm):

    class Meta:
        model = Thesis
        fields = ('title', 'advisor', 'supporting_advisor', 'kind',
                  'reserved_until', 'description')

    title = forms.CharField(label="Tytuł pracy", max_length=MAX_THESIS_TITLE_LEN)
    advisor = forms.ModelChoiceField(Employee.objects,label="Promotor", required=False)
    supporting_advisor = forms.ModelChoiceField(Employee.objects, label="Promotor wspierający", required=False)
    kind = forms.ChoiceField(choices=ThesisKind.choices(), label="Typ")
    reserved_until = forms.DateTimeField(input_formats=['%d/%m/%Y %H:%M'], label="Zarezerwowana do",required=False)
    description = forms.CharField(label="Opis", widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Zapisz'))

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
