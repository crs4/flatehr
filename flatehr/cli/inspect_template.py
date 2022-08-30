import json

from anytree import RenderTree

from flatehr.factory import template_factory


def main(template_file: str, *, aql_path: bool = False, inputs: bool = False):
    """Shows the template tree, with info about type, cardinality,
    requiredness and optionally aql path and expected inputs.

    :param template_file: path to the web template (json)
    :param aql_path: flag, if true shows the aql path for each node
    :param inputs: flag, if true shows the inputs for each node
    """
    with open(template_file, "r") as f_obj:
        template_dict = json.load(f_obj)

    template = template_factory("anytree", template_dict).get()

    for pre, _, node in RenderTree(template.root):
        cardinality = f"[{'0' if not node.required else '1'}..{'1' if not node.inf_cardinality else '-1'}]"
        ctx = " , CTX" if node.in_context else ""
        _aql_path = ", " + node.aql_path if aql_path else ""
        _inputs = ", " + json.dumps(node.inputs) if inputs and node.inputs else ""
        print(
            f"{pre}{str(node)} ({node.rm_type}, {cardinality}{ctx}{_aql_path}{_inputs})"
        )
