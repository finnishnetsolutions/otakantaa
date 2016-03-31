# conding: utf-8

from __future__ import unicode_literals
from nocaptcha_recaptcha.fields import NoReCaptchaField
from django import forms
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from conversation.models import Comment


class BaseCommentForm(forms.ModelForm):
    quote = forms.IntegerField(widget=forms.HiddenInput, required=False)
    honeypot = forms.CharField(
        widget=forms.HiddenInput,
        required=False,
        label=_('If you enter anything in this field your comment will be treated as '
                'spam')
    )

    def clean_quote(self):
        quote_id = self.cleaned_data['quote']
        if quote_id:
            return get_object_or_404(Comment, pk=quote_id)
        return None

    def clean_honeypot(self):
        #Check that nothing's been entered into the honeypot.
        value = self.cleaned_data['honeypot']
        if value:
            raise forms.ValidationError(self.fields['honeypot'].label)
        return value


class BaseCommentFormAnon(BaseCommentForm):
    captcha = NoReCaptchaField(label=_("Tarkistuskoodi"))

    def __init__(self, *args, **kwargs):
        super(BaseCommentFormAnon, self).__init__(*args, **kwargs)
        self.fields['user_name'].required = True


class CommentFormTitleRequiredMixin(object):
    def __init__(self, *args, **kwargs):
        super(CommentFormTitleRequiredMixin, self).__init__(*args, **kwargs)
        self.fields['title'].required = True


class CommentForm(CommentFormTitleRequiredMixin, BaseCommentForm):
    class Meta:
        model = Comment
        fields = ('title', 'comment', )


class CommentFormAnon(CommentFormTitleRequiredMixin, BaseCommentFormAnon):
    class Meta:
        model = Comment
        fields = ('user_name', 'title', 'comment', )


class CommentResponseForm(BaseCommentForm):
    class Meta:
        model = Comment
        fields = ('quote', 'comment', )
        labels = {'comment': _("Vastaus")}


class CommentResponseFormAnon(BaseCommentFormAnon):
    class Meta:
        model = Comment
        fields = ('user_name', 'quote', 'comment', )
        labels = {'comment': _("Vastaus")}


class EditCommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditCommentForm, self).__init__(*args, **kwargs)
        if self.instance.is_response():
            self.fields['comment'].label = _("Vastaus")

    class Meta:
        model = Comment
        fields = ('comment', )


class DeleteCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ()

