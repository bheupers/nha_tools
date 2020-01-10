from lxml import etree

schema_root = etree.parse("xsd/topx-2.3_1.xsd")
schema = etree.XMLSchema(schema_root)

parser = etree.XMLParser(schema = schema)
root = etree.parse("examples/1498.metadata", parser)
print(len(parser.error_log))
print(root)

