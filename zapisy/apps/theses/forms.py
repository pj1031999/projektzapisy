from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column
from .models import Thesis, Remark, MAX_THESIS_TITLE_LEN
from .enums import ThesisKind, ThesisStatus
from apps.users.models import Employee, Student


class ThesisFormAdmin(forms.ModelForm):
    class Meta:
        model = Thesis
        fields = '__all__'


class RemarkFormAdmin(forms.ModelForm):
    class Meta:
        model = Remark
        fields = '__all__'


class ThesisFormBase(forms.ModelForm):
    class Meta:
        model = Thesis
        fields = '__all__'

    title = forms.CharField(label="Tytuł pracy",
                            max_length=MAX_THESIS_TITLE_LEN)
    advisor = forms.ModelChoiceField(
        queryset=Employee.objects.none(), label="Promotor", required=True)
    supporting_advisor = forms.ModelChoiceField(queryset=Employee.objects.none(),
                                                label="Promotor wspierający", required=False)
    kind = forms.ChoiceField(choices=ThesisKind.choices(), label="Typ")
    reserved_until = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}),
                                     label="Zarezerwowana do", required=False)
    description = forms.CharField(
        label="Opis", widget=forms.Textarea, required=False)

    def __init__(self, user, *args, **kwargs):
        super(ThesisFormBase, self).__init__(*args, **kwargs)
        if user.is_staff:
            self.fields['advisor'].queryset = Employee.objects.all()
        else:
            self.fields['advisor'].queryset = Employee.objects.filter(
                pk=user.employee.pk)
            self.fields['advisor'].initial = user.employee
            self.fields['advisor'].widget.attrs['readonly'] = True
        self.fields['supporting_advisor'].queryset = Employee.objects.exclude(
            pk=user.employee.pk)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'


class ThesisForm(ThesisFormBase):
    def __init__(self, user, *args, **kwargs):
        super(ThesisForm, self).__init__(user, *args, **kwargs)
        self.helper.layout = Layout(
            'title',
            Row(
                Column('advisor', css_class='form-group col-md-6 mb-0'),
                Column('supporting_advisor',
                       css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('kind', css_class='form-group col-md-6 mb-0'),
                Column('reserved_until', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'description'
        )
        self.helper.add_input(Submit('submit', 'Dodaj', css_class='btn-primary'))


class EditThesisForm(ThesisFormBase):
    students = forms.ModelMultipleChoiceField(queryset=Student.objects.all(), required=False,
                                              widget=forms.SelectMultiple(attrs={'size': '10'}))

    def __init__(self, user, *args, **kwargs):
        super(EditThesisForm, self).__init__(user, *args, **kwargs)
        self.helper.layout = Layout(
            'title',
            Row(
                Column('advisor', css_class='form-group col-md-6 mb-0'),
                Column('supporting_advisor',
                       css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('kind', css_class='form-group col-md-6 mb-0'),
                Column('reserved_until', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'students',
            'description'
        )
        self.helper.add_input(Submit('submit', 'Edytuj', css_class='btn-primary'))

    def clean_students(self):
        students = self.cleaned_data['students']
        if len(students) > 2:
            raise forms.ValidationError("Możesz przypisać maksymalnie 2 studentów")
        return students


class RemarkForm(forms.ModelForm):
    class Meta:
        model = Remark
        fields = ['text']

    text = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': '5'}))

    def __init__(self, *args, **kwargs):
        super(RemarkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_method = 'POST'
        self.helper.add_input(Submit('submit', 'Edytuj', css_class='btn-primary'))
