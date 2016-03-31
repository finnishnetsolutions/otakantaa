# coding=utf-8

from __future__ import unicode_literals

import factory

from .models import Instruction


class InstructionFactory(factory.DjangoModelFactory):
    title = factory.Sequence(lambda x: "Written instruction {}".format(x))
    description = "You can use this site."

    class Meta:
        model = Instruction
