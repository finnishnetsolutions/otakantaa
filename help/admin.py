# coding=utf-8

from __future__ import unicode_literals

from django.contrib import admin
from django import forms

from libs.attachtor.forms.fields import RedactorAttachtorField, UploadSignatureField
from libs.attachtor.forms.forms import RedactorAttachtorFormMixIn
from mptt.admin import MPTTModelAdmin

from .models import Instruction


class InstructionAdminForm(RedactorAttachtorFormMixIn, forms.ModelForm):
    description = RedactorAttachtorField()
    upload_ticket = UploadSignatureField()

    class Media:
        js = {
            "redactor/langs/fi.js",
            "redactor/langs/sv.js"
        }


@admin.register(Instruction)
class InstructionAdmin(MPTTModelAdmin):
    form = InstructionAdminForm
    mptt_level_indent = 20
    list_display = ('title', 'description', 'parent', 'connect_link_type', 'order', )
    list_editable = ('order', )
