# coding=utf-8

from __future__ import unicode_literals

from importlib import import_module

from .conf import config


perms = import_module(config.perms_path)

CanEditSurvey = perms.CanEditSurvey
CanAnswerSurvey = perms.CanAnswerSurvey
ShowSurveyResults = perms.ShowSurveyResults
