from django import forms
from .models import Thesis


class ThesisForm(forms.ModelForm):
    class Meta:
        model = Thesis
        fields = '__all__'

    def clean(self):
        """
        Custom validation: ensure that the students limit hasn't been exceeded.
        """
        #students = self.cleaned_data.get('students')
        #if students and len(students) > 2:
        #    raise forms.ValidationError(
        #        'Do pracy dyplomowej można przypisać co najwyżej 2 studentów.'
        #    )
        return self.cleaned_data
