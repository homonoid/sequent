from lark import v_args, Lark, Token, LarkError, Transformer
from lark.indenter import Indenter

from .node import SequentNode


@v_args(inline=True, meta=True)
class SequentTransformer(Transformer):
  """The machinery that transforms Lark's parse tree into the corresponding
     tree of Sequent AST nodes."""

  def _issue(self, node, meta, **kwargs):
    return SequentNode(node, kwargs, line=meta.line)

  def entry(self, _, *nodes):
    return list(nodes)

  # --- Top-level -------------------------------

  def function(self, _, name, matcher, body=None):
    return self._issue('Function', _,
      name=name.value,
      matcher=matcher,
      body=self._issue('Pass', _) if body is None else body)
  
  def object(self, _, name, *rest):
    *fields, guard, block = (*rest, []) if rest[-1] is None else rest
    return self._issue('Object', _,
      name=name.value,
      fields=[field.value for field in fields],
      guard=guard or False,
      body=block)
  
  def set_field(self, _, field, value):
    return self._issue('ObjectSetField', _, field=field.value, value=value)
  
  def needs(self, _, module):
    return self._issue('Needs', _, module=module.value)
  
  def bind(self, _, name, value):
    return self._issue('Bind', _, name=name.value, value=value)
  
  def case(self, _, cond, cases, alt=[]):
    return self._issue('Case', _, cond=cond, cases=cases, alt=alt)

  def case_block(self, _, *nodes):
    return {k: v for k, v in nodes}

  def variant(self, _, expr, conseq):
    return expr, conseq

  # ---------------------------------------------

  def block(self, _, *nodes):
    return list(nodes)

  def object_block(self, _, *nodes):
    return list(nodes)
  
  # --- Patterns --------------------------------
  
  def p_list_items(self, _, consume, *item_patterns):
    return self._issue('P_MatchItems', _,
      consume=consume is not None,
      item_patterns=list(item_patterns))
  
  def p_one_or_more(self, _, pattern):
    return self._issue('P_OneOrMoreItems', _, pattern=pattern)
  
  def p_zero_or_more(self, _, pattern):
    return self._issue('P_ZeroOrMoreItems', _, pattern=pattern)

  def p_guard(self, _, param, *rest):
    # XXX: Dirty but works (?) Rewrite?
    op, *other = rest
    if type(other[0]) is Token:
      op = f'{op.value}_{other[0].value}'
      other = other[1:]
    main = self._issue('P_Guard', _,
      param=param.value,
      cond=self._issue('Infix', _,
        lhs=self._issue('Req', _, name=param.value),
        rhs=other[0],
        op=op.upper()))
    if other[1] is None:
      return main
    return other[2].set('lhs', main)
  
  def p_req(self, _, name):
    return self._issue('P_Req', _, name=name.value)

  def p_in_range(self, _, low, high):
    if low.type == 'STR':
      return self._issue('P_InRange', _,
        subset='str',
        low=low.value[1:-1], high=high.value[1:-1]) # strip off the quotes
    return self._issue('P_InRange', _,
      subset='num',
      low=low.value, high=high.value)

  def p_regex(self, _, regex):
    return self._issue('P_Regex', _, regex=regex.value[1:-1]) # strip off the quotes

  def p_instanceof(self, _, obj):
    return self._issue('P_InstanceOf', _, obj=obj.value)

  def p_unpack(self, _, obj, *values):
    return self._issue('P_Unpack', _, 
      obj=obj.value,
      values=[x.value for x in values if type(x) is Token])

  def p_compare(self, _, value):
    return self._issue('P_Compare', _, value=value)

  def p_discard(self, _):
    return self._issue('P_Discard', _)
  
  def p_discard_many(self, _):
    return self._issue('P_DiscardMany', _)
  
  def p_remember_whole(self, _, name, pattern):
    return self._issue('P_RememberWhole', _, name=name.value, pattern=pattern)
  
  def p_remember_whole_expr(self, _, lhs, rhs):
    return self._issue('P_RememberWholeExpr', _,
      lhs=lhs.value if type(lhs) is Token else lhs,
      rhs=rhs)
  
  # --- Call-like -------------------------------

  def call(self, _, callee, arg):
    return self._issue('Call', _, callee=callee, arg=arg)
  
  def instance(self, _, name, *values):
    return self._issue('Instance', _, name=name.value, values=list(values))

  # --- Expressions -----------------------------

  def prefix(self, _, operator, operand):
    return self._issue('Prefix', _, operator=operator.value, operand=operand)

  def cmpfix(self, _, lhs, *rest):
    # E.g., 2 < 3 < 5 > 4 --> 2 < 3 and 3 < 5 and 5 > 4
    result = None
    for (op, rhs) in zip(*[iter(rest)]*2): # chunk by 2
      result = self._issue('Infix', _,
        lhs=result,
        rhs=self._issue('Infix', _, lhs=lhs, rhs=rhs, op=op.value),
        op='AND')
      lhs = rhs
    return result

  def infix(self, _, lhs, *rest):
    # Multi-word infixes like `is not`, `not of`, etc. -- take extra care of them.
    *op, rhs = rest
    return self._issue('Infix', _,
      lhs=lhs, rhs=rhs,
      op='_'.join([x.value.upper() for x in op]))

  # --- Data types etc. -------------------------

  def contextual(self, _):
    return self._issue('Contextual', _)
  
  def field(self, _, path, name):
    return self._issue('Field', _, path=path, name=name.value)

  def vec(self, _, *items):
    return self._issue('Vec', _, items=list(items))

  def req(self, _, token):
    return self._issue('Req', _, name=token.value)
  
  def str(self, _, token):
    return self._issue('Str', _, value=token.value)

  def num(self, _, token):
    return self._issue('Num', _, value=token.value)


class SequentIndenter(Indenter):
  NL_type = '_NL'
  OPEN_PAREN_types = 'LPAR', 'LSQB'
  CLOSE_PAREN_types = 'RPAR', 'RSQB'
  INDENT_type = '_INDENT'
  DEDENT_type = '_DEDENT'
  tab_len = 8


_parser = Lark.open('syntax/sequent.lark',
  rel_to=__file__,
  parser='lalr',
  lexer='standard',
  start='entry',
  postlex=SequentIndenter(),
  maybe_placeholders=True,
  propagate_positions=True,
  debug=True,
)


def parse(filename, source, pure=False):
  """Given a source, ask Lark to parse it against the Sequent grammar. If successful
     (and `pure` is not False), transform the parse tree into a tree of Sequent AST nodes.
     If there was a syntax error, raise generic SequentException with the given filename."""
  # TODO: error handling?
  tree = _parser.parse(source)
  return tree if pure else SequentTransformer().transform(tree)
