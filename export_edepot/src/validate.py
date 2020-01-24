from lxml import etree

file = 'examples/NL-HlmNHA_test.wav.metadata'
# file = "examples/1498.metadata"

schema_root = etree.parse("xsd/topx-2.3_1.xsd")
schema = etree.XMLSchema(schema_root)

parser = etree.XMLParser(schema = schema)
root = etree.parse(file, parser)
print(len(parser.error_log))
print(root)

