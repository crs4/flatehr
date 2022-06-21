import logging
import os
from typing import List, Optional, Union, cast

import anytree
from pipe import chain, map, traverse

from flatehr import data_types
from flatehr.anytree._node import Node, NodeNotFound
from flatehr.composition import Composition
from flatehr.composition import CompositionNode as BaseCompositionNode
from flatehr.composition import IncompatibleDataType, NotaLeaf
from flatehr.data_types import DATA_VALUE
from flatehr.factory import composition_factory
from flatehr.rm import get_model_class, models
from flatehr.template import Template, TemplateNode, to_string

logger = logging.getLogger(__name__)


@composition_factory.register("anytree")
class CompositionFactory:
    def __init__(self, template: Template):
        self._template = template

    def get(self) -> Composition:
        template_root = self._template.root
        composition_root = CompositionNode(template_root)
        return Composition(self._template, composition_root)


class CompositionNode(Node, BaseCompositionNode):
    def __init__(
        self, template: TemplateNode, parent: Optional["CompositionNode"] = None
    ):
        if parent and template.inf_cardinality:
            cardinality = len(cast(list, parent.get(f"{template._id}:*")))
            _id = f"{template._id}:{cardinality}"
        else:
            _id = template._id

        Node.__init__(self, _id=_id)
        BaseCompositionNode.__init__(self, template)
        Node.parent.fset(self, parent)

    def get(self, path) -> "CompositionNode":
        return cast(CompositionNode, Node.get(self, path))

    def __getitem__(self, path: str) -> Union[List[DATA_VALUE], DATA_VALUE]:
        nodes = self.get(path)
        return (
            [node.value for node in nodes] if isinstance(nodes, list) else nodes.value
        )

    def get_required_leaves(self, _id: Optional[str] = None) -> List[str]:
        not_leaves = anytree.iterators.preorderiter.PreOrderIter(
            self,
            filter_=lambda node: not node.template.is_leaf,
        )
        missing_required = (
            not_leaves
            | map(
                lambda node: anytree.iterators.preorderiter.PreOrderIter(
                    node.template,
                    stop=lambda n: not n.required if n != node.template else False,
                    filter_=lambda n: n.is_leaf
                    and n.required
                    and (n._id == _id if _id else True),
                )
            )
            | chain
        )
        missing_required_leaves = (
            missing_required
            | map(
                lambda template: os.path.relpath(
                    to_string(template, wildcard=True), self._id
                )
            )
            | traverse
        )
        return list(missing_required_leaves)

    def __setitem__(self, path, value: DATA_VALUE):

        if path.startswith("**"):
            _id = os.path.basename(path)

            missing_required_parents = (
                self.get_required_leaves(_id)
                | map(lambda path: self._get_or_create_node(os.path.dirname(path)))
            ) | traverse
            list(
                missing_required_parents
                | map(lambda node: node.__setitem__(os.path.basename(path), value))
            )
            return

        nodes = self._get_or_create_node(path)
        if not isinstance(nodes, list):
            nodes = [nodes]
        for node in nodes:
            if not node.template.is_leaf:
                raise NotaLeaf(f"{path} is not a leaf")
            # @fixme: not work in case of abstract classes
            # if not isinstance(value, get_model_class(node.template.rm_type)):
            #     raise IncompatibleDataType(
            #         f"Expected value as instance of {node.template.rm_type}, found {type(value)} instead"
            #     )
            node.value = value

    def _get_or_create_node(self, path: str) -> "CompositionNode":
        if not path:
            return self
        try:
            return cast("CompositionNode", self.get(path))
        except NodeNotFound as ex:
            last_node = cast(CompositionNode, ex.node)
            missing_child_template = last_node.template.get(ex.child)

            if missing_child_template.inf_cardinality:
                cardinality = (
                    len(cast(list, last_node.get(f"{missing_child_template._id}:*")))
                    - 1
                )
                if cardinality < 0:
                    missing_child = CompositionNode(missing_child_template, last_node)
                else:
                    missing_child = last_node.get(
                        f"{missing_child_template._id}:{cardinality}"
                    )
            else:
                missing_child = CompositionNode(missing_child_template, last_node)

            remaining_path = path.replace(
                to_string(missing_child_template, relative_to=self.template),
                "",
                1,
            ).strip(self.separator)
            return missing_child._get_or_create_node(remaining_path)

    @property
    def parent(self) -> "CompositionNode":
        return cast("CompositionNode", Node.parent.fget(self))

    def add(self, path: str) -> str:
        parent = cast(
            "CompositionNode",
            self._get_or_create_node(os.path.dirname(path.rstrip("/"))),
        )
        node = CompositionNode(self.template.get(path), parent)
        return str(node)

    #      try:
    #          self[path].value = value
    #      except NodeNotFound as ex:
    #          last_template_node = cast("CompositionNode", ex.node).template
    #          missing_template_nodes last_template_node.walk_to()
    #
    #  def add_child(
    #      self,
    #      name: str,
    #      value: Optional[None] = None,
    #      increment_cardinality: bool = True,
    #      null_flavour: Optional[NullFlavour] = None,
    #  ):
    #      resolver = anytree.Resolver("_id")
    #      template_node = self.template.get_descendant(name)
    #      if template_node.inf_cardinality:
    #          n_siblings = len(resolver.glob(self, f"{name}:*"))
    #          logger.debug(
    #              "create new sibling %s for path %s/%s", n_siblings, self.path, name
    #          )
    #          increment_cardinality = increment_cardinality or n_siblings == 0
    #          if increment_cardinality:
    #              name = f"{name}:{n_siblings}"
    #              child = CompositionNode(
    #                  name,
    #                  template_node,
    #              )
    #              child.parent = self
    #          else:
    #              child = resolver.get(self, f"{name}:{n_siblings -1}")
    #      else:
    #          try:
    #              child = resolver.get(self, name)
    #          except anytree.ChildResolverError:
    #              child = CompositionNode(name, template_node)
    #
    #              child.parent = self
    #      return child
    #
    #  def create_node(
    #      self,
    #      path: str,
    #      increment_cardinality: bool = True,
    #      null_flavour: Optional[NullFlavour] = None,
    #      **kwargs,
    #  ) -> "CompositionNode":
    #      logger.debug("create node: parent %s, path %s", self.path, path)
    #
    #      def _add_descendant(root, path_, **kwargs):
    #          resolver = anytree.Resolver("_id")
    #          try:
    #              node = resolver.get(root, path_)
    #          except anytree.ChildResolverError as ex:
    #              last_node = ex.node
    #              missing_child = ex.child
    #              logger.debug("last_node %s, missing_child %s", last_node, missing_child)
    #              template_node = last_node.template
    #              missing_path = os.path.join(root.template.path, path_).replace(
    #                  template_node.path, ""
    #              )
    #              is_last = len(missing_path.strip("/").split("/")) == 1
    #              node = CompositionNode(last_node._id, template_node).add_child(
    #                  missing_child,
    #                  increment_cardinality=is_last and increment_cardinality,
    #                  null_flavour=null_flavour if is_last else None,
    #              )
    #              node.parent = root
    #
    #              path_to_remove = [n.name for n in last_node.path] + [missing_child]
    #
    #              for el in path_to_remove:
    #                  path_ = re.sub(r"^" + el + "(/|$)", "", path_, 1)
    #
    #              path_ = path_.lstrip(root.separator)
    #
    #              return _add_descendant(node, path_, **kwargs)
    #          else:
    #              template_node = node.template
    #              if kwargs:
    #                  value = Factory(node.web_template).create(**kwargs)
    #              else:
    #                  value = None
    #              return node
    #
    #      try:
    #          self.get_descendant(path)
    #      except NodeNotFound:
    #          return _add_descendant(self, path, **kwargs)
    #      else:
    #          raise NodeAlreadyExists(f"node {self.path}, path {path}")
    #
    #  def _get_web_template(self):
    #      path = re.sub(r"\[\d+\]", "", self.path)
    #      resolver = anytree.Resolver("_id")
    #      return resolver.get(self.template, path)

    def as_flat(self):
        flat = {}
        if self.template.is_leaf:

            value = self.value or self.null_flavour
            if value is None:
                raise AttributeError(f"value and null_flavour of {self} not set")

            flat.update(value.to_flat(f"{str(self).strip('/')}"))
        else:
            for leaf in self.leaves:
                flat.update(leaf.as_flat())
        return flat
