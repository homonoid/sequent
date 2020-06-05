"""
  Usage:
    sequent [options] [SCRIPT]

  Options:
    -h --help             show this screen
    -v --version          show the language's version
    --dump=(ast|lark)     specify which stage of interpretation to dump [default: ast]
"""
import os
import sys
import readline

from docopt import docopt


def _dump(stage, filename, source):
  """Dumps the tree of the source at a given stage."""
  tree = parse(filename, source + '\n', pure=(stage == 'lark'))
  if stage == 'lark':
    print(tree.pretty())
  else:
    print(*tree, sep='\n')


def _validate(args):
  """Check if the arguments have correct values."""
  if args['--dump'] and args['--dump'] not in ('ast', 'lark'):
    sys.exit(f'argument error: there is no interpretation stage "{args["--dump"]}"')
  elif args['SCRIPT'] and not os.path.exists(args['SCRIPT']):
    sys.exit(f'argument error: file "{args["SCRIPT"]}" not found')
  return args


args = _validate(docopt(__doc__, version='0.0.1', options_first=True))
JUST_DUMP = args['--dump']


# What is this import doing here? We delayed it for as long as possible, since
# it takes rather long time for it to initialize. Waiting 100ms to see that
# the file you gave does not exists is a pretty unpleasant expirience, isn't it?
from .parse import parse


if args['SCRIPT']:
  with open(args['SCRIPT'], 'r') as file:
    source = file.read()
    if JUST_DUMP:
      _dump(args['--dump'], file.name, source)
else:
  while True:
    line = input(' * ')
    if JUST_DUMP:
      _dump(args['--dump'], '<interactive>', line)
