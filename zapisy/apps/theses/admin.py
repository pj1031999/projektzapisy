from django.contrib import admin
from django import forms

from apps.theses.forms import ThesisFormAdmin, RemarkFormAdmin
from apps.theses.models import Thesis, Remark


class ThesisAdmin(admin.ModelAdmin):
    autocomplete_fields = []
    list_display = ('title', 'kind', 'status', 'added')
    form = ThesisFormAdmin


class RemarkAdmin(admin.ModelAdmin):
    autocomplete_fields = []
    form = RemarkFormAdmin


admin.site.register(Thesis, ThesisAdmin)
admin.site.register(Remark, RemarkAdmin)
