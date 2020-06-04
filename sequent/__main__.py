from .parse import parse


with open('sample/calculator.seq') as file:
  source = file.read()
  tree = parse(file.name, source)
  print(tree.pretty())
