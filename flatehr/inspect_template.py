import json
import logging
import re
from typing import Dict

import clize
from anytree import RenderTree

from flatehr.core import TemplateNode
from flatehr.factory import template_factory

logger = logging.getLogger()


def convert_aql_path_to_flat_id(template: TemplateNode, aql_path: str) -> TemplateNode:
    path = aql_path.replace("]", "\]")
    path = path.replace("[", "\[")
    path = re.sub(r"\\]", "[,\\\w\\\s']*\\\]", path)

    for node in template.leaves:
        search = re.search(
            r"%s" % path,
            node.aql_path,
        )
        if search:
            return node
    raise PathNotFound(f" not flat id corresponding to aqlPath {aql_path}")


class PathNotFound(Exception):
    ...


def get_elements_by_id(composition: Dict, _id: str) -> Dict:
    pattern = _id.replace("/", "[:\d]*/")
    keys = [
        s.group()
        for key in composition.keys()
        if (s := re.search(r"%s" % pattern, key))
    ]
    return {k: composition[k] for k in keys}


def main(
    node_id,
    *,
    template: (str, "t"),
    aql_path: bool = False,
):
    with open(template, "r") as f_obj:
        template_dict = json.load(f_obj)

    template = template_factory("anytree", template_dict).get()
    #  if aql_path:
    #      nodes = convert_aql_path_to_flat_id(template.root, node_id)
    #  else:
    nodes = template.root.find(node_id)

    for n in nodes:
        path = "/".join([a._id for a in n.ancestors] + [node_id])
        print(path)


if __name__ == "__main__":
    clize.run(main)
