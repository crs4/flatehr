#!/usr/bin/env python
# -*- coding: utf-8 -*-

import defopt
from flatehr.cli import generate
from flatehr.cli import inspect_template


def main():
    defopt.run({"generate": generate.main, "inspect": inspect_template.main})
