from django.contrib import admin
from django import forms

from apps.theses.forms import ThesisForm
from apps.theses.models import Thesis


class ThesisAdmin(admin.ModelAdmin):
    autocomplete_fields = ['advisor', 'supporting_advisor']
    form = ThesisForm


admin.site.register(Thesis, ThesisAdmin)
