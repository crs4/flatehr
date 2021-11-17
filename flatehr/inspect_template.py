import json
import logging
import re
from typing import Dict

import clize
from anytree import RenderTree

from flatehr.flat import WebTemplateNode

logger = logging.getLogger()


def convert_aql_path_to_flat_id(
    web_template: WebTemplateNode, aql_path: str
) -> WebTemplateNode:
    path = aql_path.replace("]", "\]")
    path = path.replace("[", "\[")
    path = re.sub(r"\\]", "[,\\\w\\\s']*\\\]", path)

    for node in web_template.leaves:
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
    ancestors: (bool, "a") = False,
):
    with open(template, "r") as f_obj:
        template_dict = json.load(f_obj)

    web_template = WebTemplateNode.create(template_dict)
    if aql_path:
        web_template_node = convert_aql_path_to_flat_id(web_template, node_id)
    else:
        web_template_node = web_template.get_descendant(node_id)
    if ancestors:
        for ancestor in web_template_node.ancestors:
            print(ancestor)
    print(web_template_node)
    #  _node = WebTemplateNode(row.node)
    #  print("%s%s (required %s)" % (row.pre, _node.path, _node.required))


if __name__ == "__main__":
    clize.run(main)
