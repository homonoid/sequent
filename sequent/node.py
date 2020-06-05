from textwrap import indent


class SequentNode:
  """Sequent has only one actual AST node class -- the generic SequentNode."""

  INDENT = 2

  def __init__(self, kind, attrs, line=1):
    self.kind = kind
    self.line = line
    self.attrs = attrs

  def set(self, attr, value):
    """Set node's attribute attr to the given value and return self."""
    self.attrs[attr] = value
    return self

  def __repr__(self):
    def _iter():
      yield f'<{self.kind}:{self.line}>'
      for attr, value in self.attrs.items():
        if isinstance(value, SequentNode):
          yield indent(f'{attr}:', ' ' * self.INDENT)
          yield indent(repr(value), ' ' * (self.INDENT * 2))
        elif type(value) is dict and value:
          # XXX: dictionaries are too rare and too hard to format?
          yield indent(f'{attr}: (dict ...)', ' ' * self.INDENT)
        elif type(value) is list and value:
          yield indent(f'{attr}', ' ' * self.INDENT)
          for item in value:
            yield indent(repr(item), ' ' * (self.INDENT * 2))
        else:
          yield indent(f'{attr}: {repr(value)}', ' ' * self.INDENT)
    return '\n'.join(_iter())
