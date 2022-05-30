import itertools
import logging
import os
import re
from functools import singledispatchmethod
from typing import Dict, List, Tuple

import anytree
from deepdiff import DeepDiff

from flatehr.data_types import DataValue, Factory, NullFlavour

logger = logging.getLogger("flatehr")


class Node:
    def __init__(self, node: anytree.Node):
        self._node = node

    def __str__(self):
        return str(self._node)

    def _set_value(self, value):
        self._node.value = value

    def _get_value(self):
        return self._node.value

    value = property(_get_value, _set_value)

    @property
    def is_leaf(self):
        return self._node.is_leaf

    @property
    def separator(self):
        return self._node.separator

    @property
    def name(self):
        return self._node.name

    @property
    def leaves(self):
        for leaf in self._node.leaves:
            yield type(self)(leaf)

    def walk_to(self, node: "Node") -> Tuple:
        walker = anytree.walker.Walker()
        return tuple(
            type(self)(node_) for node_ in walker.walk(self._node, node._node)[2]
        )

    @property
    def path(self):
        return (
            self._node.separator
            + self._node.separator.join([n.name for n in self._node.path])
            + self._node.separator
        )

    def get_descendant(self, path: str):
        resolver = anytree.Resolver("name")
        #  return type(self)(resolver.get(self._node, path))
        try:
            return type(self)(resolver.get(self._node, path))
        except anytree.ChildResolverError as ex:
            raise NodeNotFound(f"node: {self.path}, path {path}")

    @property
    def parent(self):
        parent = self._node.parent
        return type(self)(parent)

    def render(self) -> str:
        return anytree.RenderTree(self._node)


class WebTemplateNode(Node):
    @property
    def rm_type(self):
        return self._node.rm_type

    @property
    def _id(self):
        return self._node.name

    @property
    def aql_path(self):
        return self._node.aql_path

    @property
    def required(self):
        return self._node.required

    @property
    def inf_cardinality(self):
        return self._node.inf_cardinality

    @property
    def annotations(self):
        return self._node.annotations

    @property
    def children(self):
        return [WebTemplateNode(child) for child in self._node.children]

    @property
    def inputs(self):
        return self._node.inputs

    def __str__(self):
        return f"{self.path}, rm_type={self.rm_type}, cardinality={int(self.required)}:{ '*' if self.inf_cardinality else 1 }"

    def __repr__(self):
        return f"{self.__class__.__name__}({str(self)})"

    @property
    def parent(self):
        return WebTemplateNode(self._node.parent)

    @property
    def ancestors(self):
        for ancestor in self._node.ancestors:
            yield WebTemplateNode(ancestor)


class Composition:
    def __init__(self, web_template: WebTemplateNode):
        self._web_template = web_template
        self._root = CompositionNode(
            anytree.Node(web_template.path.strip(web_template.separator)), web_template
        )
        self.metadata = {}

    def __str__(self):
        return f"<template {self._web_template.name}, metadata {self.metadata}>"

    @property
    def web_template(self):
        return self._web_template

    @property
    def root(self):
        return self._root

    def create_node(
        self,
        path,
        increment_cardinality: bool = True,
        null_flavour: NullFlavour = None,
        **kwargs,
    ) -> "CompositionNode":
        path = path.replace(f"{self.root.path}", "")
        composition_node = self.root.create_node(
            path, increment_cardinality, null_flavour
        )
        # @fixme it should be on CompositionNode.create_node
        if composition_node.web_template.is_leaf and not null_flavour:
            value = Factory(composition_node.web_template).create(**kwargs)
            composition_node.value = value
        return composition_node

    def get(self, path) -> "CompositionNode":
        path = path.replace(self._root.name, "").strip("/")
        return self._root.get_descendant(path)

    def set_all(self, name: str, **kwargs) -> "CompositionNode":
        """
        if kwargs is not provided, defaultValue on inputs fields
        will be retrieved

        """

        def _set_default(existing_path: str, path_to_create: str, kwargs):
            if existing_path:
                try:
                    for node in resolver.glob(self._root._node, existing_path):
                        if not kwargs:
                            kwargs = {}
                            for input_ in node.web_template.get_descendant(name).inputs:
                                key = input_.get("suffix", "value")
                                kwargs[key] = input_["defaultValue"]
                        composition_node = CompositionNode(node, node.web_template)
                        child = node.web_template.get_descendant(
                            path_to_create.split("/")[0]
                        )
                        if child.required:
                            try:
                                composition_node.create_node(path_to_create, **kwargs)
                            except NodeAlreadyExists as ex:
                                logger.warning(ex)

                except (NodeNotFound, anytree.ChildResolverError):
                    nodes = existing_path.split("/")
                    last_node = nodes[-1]
                    existing_path = "/".join(nodes[: len(nodes) - 1])
                    path_to_create = last_node + "/" + path_to_create
                    _set_default(existing_path, path_to_create, kwargs)

        resolver = anytree.resolver.Resolver("name")
        leaves = [node for node in self._web_template.leaves if node.name == name]
        for target in leaves:
            descendants = self._web_template.walk_to(target)[:-1]
            if not descendants:
                try:
                    self._root.create_node(name, **kwargs)
                except NodeAlreadyExists as ex:
                    logger.warning(ex)
            else:
                path = self._root.separator.join(
                    [
                        descendant.name
                        if descendant.inf_cardinality is False
                        else f"{descendant.name}:*"
                        for descendant in descendants
                    ]
                )
                _set_default(path, name, kwargs)

    def as_flat(self):
        flat = {}
        for leaf in self._root.leaves:
            flat.update(leaf.as_flat())
        return flat

    def set_defaults(self):
        def _get_required_children(
            node: CompositionNode,
        ) -> Tuple[CompositionNode, List[WebTemplateNode]]:

            existing_children = {c.web_template.name for c in node.children}

            logger.debug(
                "existing_children for node %s, %s",
                node.name,
                existing_children,
            )
            required = [
                child
                for child in node.web_template.children
                if child.required and child.name not in existing_children
            ]
            logger.debug(
                "required for node %s, %s", node.name if node else None, required
            )
            return node, required

        def _set_default(node, web_template_nodes):
            for web_template_node in web_template_nodes:
                child = node.add_child(web_template_node.name)
                if web_template_node.is_leaf:
                    logger.debug(
                        "creating node %s and setting default", web_template_node
                    )
                    #  node = self.create_node(web_template_node.path)
                    child.set_defaults()
                else:
                    required_children = _get_required_children(child)
                    _set_default(*required_children)

        nodes = anytree.PreOrderIter(self.root)
        required_children = map(_get_required_children, nodes)
        #  list(map(_set_default, required_children))
        list(map(lambda x: _set_default(*x), required_children))


class CompositionNode(Node):
    def __init__(
        self,
        node: anytree.Node,
        web_template_node: WebTemplateNode,
        value: DataValue = None,
        null_flavour: NullFlavour = None,
    ):
        super().__init__(node)
        self._node.web_template = web_template_node
        self._web_template_node = web_template_node
        self._resolver = anytree.Resolver("name")
        self._node.value = value
        self._node.null_flavour = null_flavour

    def __repr__(self):
        return "<CompositionNode %s>" % self._node

    @property
    def null_flavour(self):
        return self._node.null_flavour

    @property
    def web_template(self):
        return self._web_template_node

    def add_child(
        self,
        name: str,
        value: DataValue = None,
        increment_cardinality: bool = True,
        null_flavour: NullFlavour = None,
    ):
        web_template_node = self._web_template_node.get_descendant(name)
        if web_template_node.inf_cardinality:
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
        return CompositionNode(node, web_template_node, value, null_flavour)

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
        self.value = Factory(self.web_template).create()

    def as_flat(self):
        flat = {}
        if self.web_template.is_leaf:

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


def diff(flat_1: Dict, flat_2: Dict):
    return DeepDiff(flat_1, flat_2, verbose_level=2)


class WebTemplateNodeFactory:
    @singledispatchmethod
    @staticmethod
    def create(*args) -> WebTemplateNode:
        ...

    @staticmethod
    @create.register
    def _create_from_dict(dct: dict) -> "WebTemplateNode":
        def _recursive_create(web_template_el):
            _node = anytree.Node(
                web_template_el["id"],
                rm_type=web_template_el["rmType"],
                required=web_template_el["min"] == 1,
                inf_cardinality=web_template_el["max"] == -1,
                annotations=web_template_el.get("annotations", {}),
                inputs=web_template_el.get("inputs"),
                aql_path=web_template_el.get("aqlPath"),
            )

            children = []
            for child in web_template_el.get("children", []):
                children.append(_recursive_create(child)._node)
            _node.children = children

            return WebTemplateNode(_node)

        tree = dct["tree"]
        node = _recursive_create(tree)
        return node

    @staticmethod
    @create.register
    def _create(
        _id: str,
        rm_type: str,
        required: bool,
        inf_cardinality: bool,
        aql_path: str,
        children: List["WebTemplateNode"] = None,
        inputs: Dict = None,
        annotations: Dict = None,
    ) -> "WebTemplateNode":
        _node = anytree.Node(
            _id,
            rm_type=rm_type,
            required=required,
            inf_cardinality=inf_cardinality,
            annotations=annotations or {},
            inputs=inputs or {},
            aql_path=aql_path,
        )

        children = children or []
        _node.children = [c._node for c in children]

        return WebTemplateNode(_node)
