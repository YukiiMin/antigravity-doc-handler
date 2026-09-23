import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

NS_W = nsdecls('w')
DOC_PATH = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\src\Report3_Software Requirement Specification.docx'

doc = docx.Document(DOC_PATH)

for t in doc.tables:
    for idx, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr()
        if trPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cantSplit') is None:
            trPr.append(parse_xml(f'<w:cantSplit {NS_W}/>'))
        if idx == 0:
            if trPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblHeader') is None:
                trPr.append(parse_xml(f'<w:tblHeader {NS_W}/>'))
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            if tcPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}vAlign') is None:
                tcPr.append(parse_xml(f'<w:vAlign {NS_W} w:val="center"/>'))

doc.save(DOC_PATH)
print("Enforced table OpenXML invariants successfully on all tables!")
