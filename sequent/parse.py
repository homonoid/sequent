from lark import v_args, Lark, LarkError, Transformer
from lark.indenter import Indenter


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


def parse(filename, source):
  """Given a source, ask Lark to parse it against the Sequent grammar. If successful,
     transform the parse tree into a tree of Sequent AST nodes. If not, raise 
     generic SequentException with the given filename."""
  return _parser.parse(source)
