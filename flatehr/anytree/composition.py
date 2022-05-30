import logging
import re

import anytree

from flatehr.anytree._node import Node
from flatehr.composition import CompositionNode as BaseCompositionNode
from flatehr.data_types import DataValue, Factory, NullFlavour
from flatehr.template import TemplateNode

logger = logging.getLogger(__name__)


class CompositionNode(BaseCompositionNode):
    def __init__(
        self,
        node: Node,
        template_node: TemplateNode,
        value: DataValue = None,
        null_flavour: NullFlavour = None,
    ):
        self._node = node
        self._node.attrs["template"] = template_node
        self._template_node = template_node
        self._resolver = anytree.Resolver("name")
        self._node.value = value
        self._node.attrs["null_flavour"] = null_flavour

    @property
    def value(self) -> DataValue:
        return self._node.value

    @value.setter
    def value(self, value: DataValue):
        self._node.value = value

    @property
    def null_flavour(self):
        return self._node.attrs["null_flavour"]

    @property
    def template_node(self):
        return self._template_node

    def add_child(
        self,
        name: str,
        value: DataValue = None,
        increment_cardinality: bool = True,
        null_flavour: NullFlavour = None,
    ):
        template_node = self._template_node.get_descendant(name)
        if template_node.inf_cardinality:
            n_siblings = len(self._resolver.glob(self._node, f"{name}:*"))
            logger.debug(
                "create new sibling %s for path %s/%s", n_siblings, self.path, name
            )
            increment_cardinality = increment_cardinality or n_siblings == 0
            if increment_cardinality:
                name = f"{name}:{n_siblings}"
                node = anytree.Node(name, parent=self._node)
            else:
                node = self._resolver.get(self._node, f"{name}:{n_siblings -1}")
        else:
            try:
                node = self._resolver.get(self._node, name)
            except anytree.ChildResolverError:
                node = anytree.Node(name, parent=self._node)
        return CompositionNode(node, template_node, value, null_flavour)

    def create_node(
        self,
        path: str,
        increment_cardinality: bool = True,
        null_flavour: NullFlavour = None,
        **kwargs,
    ) -> "CompositionNode":
        logger.debug("create node: parent %s, path %s", self.path, path)

        def _add_descendant(root, path_, **kwargs):
            try:
                node = self._resolver.get(root, path_)
            except anytree.ChildResolverError as ex:
                last_node = ex.node
                missing_child = ex.child
                logger.debug("last_node %s, missing_child %s", last_node, missing_child)
                web_template_node = last_node.web_template
                missing_path = os.path.join(root.web_template.path, path_).replace(
                    web_template_node.path, ""
                )
                is_last = len(missing_path.strip("/").split("/")) == 1
                node = CompositionNode(last_node, web_template_node).add_child(
                    missing_child,
                    increment_cardinality=is_last and increment_cardinality,
                    null_flavour=null_flavour if is_last else None,
                )

                path_to_remove = [n.name for n in last_node.path] + [missing_child]

                for el in path_to_remove:
                    path_ = re.sub(r"^" + el + "(/|$)", "", path_, 1)

                path_ = path_.lstrip(root.separator)

                return _add_descendant(node._node, path_, **kwargs)
            else:
                web_template_node = node.web_template
                if kwargs:
                    value = Factory(node.web_template).create(**kwargs)
                else:
                    value = None
                return CompositionNode(
                    node,
                    web_template_node,
                    value,
                    null_flavour,
                )

        try:
            self.get_descendant(path)
        except NodeNotFound:
            return _add_descendant(self._node, path, **kwargs)
        else:
            raise NodeAlreadyExists(f"node {self.path}, path {path}")

    def _get_web_template(self):
        path = re.sub(r"\[\d+\]", "", self.path)
        return self._resolver.get(self._web_template_node, path)

    @property
    def leaves(self):
        for leaf in self._node.leaves:
            yield CompositionNode(
                leaf,
                leaf.web_template,
                leaf.value,
                null_flavour=leaf.null_flavour,
            )

    def get_descendant(self, path: str):
        #  path = path if path.startswith("/") else f"/{path}"
        resolver = anytree.Resolver("name")
        try:
            node = resolver.get(self._node, path)
        except anytree.resolver.ChildResolverError as ex:
            raise NodeNotFound(f"{path} not found") from ex
        return type(self)(node, node.web_template, value=node.value)

    @property
    def parent(self):
        parent = self._node.parent
        return CompositionNode(
            parent, parent.web_template, parent.value, parent.null_flavour
        )

    @property
    def children(self):
        return [
            CompositionNode(
                child,
                child.web_template,
                child.value,
                child.null_flavour,
            )
            for child in self._node.children
        ]

    def set_defaults(self):
        self.value = Factory(self.template_node).create()

    def as_flat(self):
        flat = {}
        if self.template_node.is_leaf:

            value = self.value or self.null_flavour
            if value is None:
                raise AttributeError(f"value and null_flavour of {self} not set")

            flat.update(value.to_flat(f"{self.path.strip(self.separator)}"))
        else:
            for leaf in self.leaves:
                flat.update(leaf.as_flat())
        return flat


class NodeNotFound(Exception):
    ...


class NodeAlreadyExists(Exception):
    ...
