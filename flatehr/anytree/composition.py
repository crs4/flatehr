import logging
from dataclasses import dataclass
from typing import List, Union, cast

import anytree

from flatehr.anytree._node import Node, NodeNotFound
from flatehr.composition import Composition
from flatehr.composition import CompositionNode as BaseCompositionNode
from flatehr.composition import NotaLeaf
from flatehr.data_types import DataValue
from flatehr.factory import composition_factory
from flatehr.template import Template, TemplateNode, remove_cardinality

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
    def __init__(self, template: TemplateNode):
        Node.__init__(self, _id=template._id)
        BaseCompositionNode.__init__(self, template)

    def __setitem__(self, path, value: DataValue):
        try:
            node = self[path]
        except NodeNotFound as ex:
            last_node = cast(BaseCompositionNode, ex.node)
            missing_child_template = last_node.template[ex.child]
            missing_child = CompositionNode(missing_child_template)
            missing_child.parent = last_node
            remaining_path = path.replace(
                missing_child.path.replace(self.path, "").strip(self.separator), ""
            ).strip(self.separator)
            missing_child[remaining_path] = value
        else:
            if not node.template.is_leaf:
                raise NotaLeaf(f"{path} is not a leaf")
            node.value = value

    def _set_parent(self, value: "CompositionNode"):
        self.parent = value

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

    def set_defaults(self):
        raise NotImplementedError()

    def as_flat(self):
        flat = {}
        if self.template.is_leaf:

            value = self.value or self.null_flavour
            if value is None:
                raise AttributeError(f"value and null_flavour of {self} not set")

            flat.update(value.to_flat(f"{self.path.strip('/')}"))
        else:
            for leaf in self.leaves:
                flat.update(leaf.as_flat())
        return flat
