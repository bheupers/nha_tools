from lxml import etree

#file = 'examples/NL-HlmNHA_test.wav.metadata'

file = '/Users/bart/tmp/NHA/Eerste overdracht 1875 - 1900.sidecar/0CD1B556-27B2-4BBE-8023-EE153CA0C70C.xml'
# file = "examples/1498.metadata"

schema_root = etree.parse("xsd/topx-2.3_1.xsd")
schema = etree.XMLSchema(schema_root)

parser = etree.XMLParser(schema = schema)
root = etree.parse(file, parser)
print(len(parser.error_log))
print(root)

