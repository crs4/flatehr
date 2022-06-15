#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
from pathlib import Path

from datamodel_code_generator import InputFileType, generate

filename = "./openehr_rm_1.1.0_all.json"
schema = open(filename, "r").read()


def rename_class(name: str):
    splitted = name.split("_")
    return "".join([n.capitalize() if n != "DV" else n for n in splitted])


template_dir = Path(os.path.dirname(os.path.realpath(__file__))) / Path("templates")
output = Path("rm.py")
generate(
    schema,
    input_file_type=InputFileType.JsonSchema,
    output=output,
    custom_class_name_generator=rename_class,
)

#  subprocess.check_call(
#      ["sed", "-i", "7s/^/from pydantic.dataclasses import dataclass\\n/", "rm.py"]
#  )
subprocess.check_call(["sed", "-i", "s/min_items=/minItems=/g", "rm.py"])
