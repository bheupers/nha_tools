from lxml import etree

#file = 'examples/NL-HlmNHA_test.wav.metadata'

# file = '/Users/bart/tmp/NHA/Eerste overdracht 1875 - 1900.sidecar/0CD1B556-27B2-4BBE-8023-EE153CA0C70C.metadata'
# file = '/Users/bart/tmp/NHA/Eerste overdracht 1875 - 1900.sidecar/0CD1B556-27B2-4BBE-8023-EE153CA0C70C/0A2DE623-9AAD-4188-B1E7-B380BF2C3500.metadata'

# file = "examples/1498.metadata"
file = '/Users/bart/tmp/NHA/Eerste overdracht 1875 - 1900.sidecar/0CD1B556-27B2-4BBE-8023-EE153CA0C70C/0A2DE623-9AAD-4188-B1E7-B380BF2C3500/05e99f58-80d3-4d42-8248-d7b879ee4e59.tif.metadata'

# file = '/Users/bart/Development/nha/nha_tools/export_edepot/src/topx/templates/ToPX-2.3_Bestand_max.xml'
schema_root = etree.parse("xsd/topx-2.3_1.xsd")
schema = etree.XMLSchema(schema_root)

parser = etree.XMLParser(schema = schema)
root = etree.parse(file, parser)
print(len(parser.error_log))
print(root)

