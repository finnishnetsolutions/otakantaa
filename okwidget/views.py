# coding=utf-8

from __future__ import unicode_literals

from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import activate
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin

from content.models import Scheme, ParticipationDetails
from conversation.models import Comment

from .forms import WidgetForm, SchemeListWidgetForm


class WidgetView(FormMixin, TemplateView):
    """
    Base class.
    Draws the widget with <html>, etc.  Used in iframes.
    """
    http_method_names = ["get"]
    template_name = "widget/widget.html"
    content_template_name = None
    queryset = None
    form_class = WidgetForm

    def get_content_template_name(self):
        return self.content_template_name

    def get_context_data(self, **kwargs):
        context = super(WidgetView, self).get_context_data(**kwargs)
        context["content_template_name"] = self.get_content_template_name()
        return context

    def get_form_kwargs(self):
        kwargs = super(WidgetView, self).get_form_kwargs()
        if len(self.request.GET):
            kwargs["data"] = self.request.GET
        else:
            kwargs["data"] = {}
        return kwargs

    def get_queryset(self):
        return self.queryset

    def form_valid(self, form):
        object_list = form.filtrate(self.get_queryset())
        context = self.get_context_data(form=form, object_list=object_list)
        return self.render_to_response(context)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class WidgetModalView(WidgetView):
    """
    Base class.
    Modal in which the widget can be configured and previewed.
    """
    template_name = "widget/widget_modal.html"
    widget_help_text = None
    widget_url = None

    def get_widget_help_text(self):
        return self.widget_help_text

    def get_widget_url(self):
        return self.widget_url

    def append_get_to_url(self, url):
        if len(self.request.GET):
            return "{}?{}".format(url, self.request.GET.urlencode())
        return url

    def get_context_data(self, **kwargs):
        context = super(WidgetModalView, self).get_context_data(**kwargs)
        context["widget_help_text"] = self.get_widget_help_text()
        context["widget_url"] = self.append_get_to_url(self.get_widget_url())
        return context


class SchemeListWidgetView(WidgetView):
    content_template_name = "widget/scheme_list_widget_content.html"
    form_class = SchemeListWidgetForm
    queryset = Scheme.objects.filter(visibility=Scheme.VISIBILITY_PUBLIC).\
        order_by("-published").prefetch_related("owners")

    def get_form_kwargs(self):
        kwargs = super(SchemeListWidgetView, self).get_form_kwargs()
        kwargs['default_language'] = self.request.LANGUAGE_CODE
        return kwargs

    def form_valid(self, form):
        activate(form.get_language())
        return super(SchemeListWidgetView, self).form_valid(form)


class SchemeListWidgetModalView(SchemeListWidgetView, WidgetModalView):
    template_name = "widget/scheme_list_widget_modal.html"
    widget_help_text = _("Widget luodaan käyttämistäsi hakuehdoista.")
    widget_url = reverse_lazy("widget:scheme_list")


class SchemeWidgetView(WidgetView):
    content_template_name = "widget/scheme_widget_content.html"
    form_class = WidgetForm

    def get_queryset(self):
        conversation_ids = ParticipationDetails.objects \
            .conversations() \
            .filter(scheme_id=self.kwargs["scheme_id"]) \
            .values_list("object_id", flat=True)
        return Comment.objects \
            .comments() \
            .filter(conversation_id__in=conversation_ids) \
            .order_by("-pk")


class SchemeWidgetModalView(SchemeWidgetView, WidgetModalView):
    widget_help_text = _("Widgettiin listataan viimeisimmät kommentit.")

    def get_widget_url(self):
        return reverse("widget:scheme", kwargs={"scheme_id": self.kwargs["scheme_id"]})
