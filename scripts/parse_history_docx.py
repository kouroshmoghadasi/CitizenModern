# -*- coding: utf-8 -*-
"""Parse History of Canada1.docx — options are lines that do NOT end with ?"""
import zipfile
import xml.etree.ElementTree as ET

path = r"e:\OK Projects\Nemoneh Question Citizen CA\History of Canada1.docx"
with zipfile.ZipFile(path) as z:
    root = ET.fromstring(z.read("word/document.xml"))
paras = []
for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
    texts = []
    for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
        if t.text:
            texts.append(t.text)
        if t.tail:
            texts.append(t.tail)
    line = "".join(texts).strip()
    if line:
        paras.append(line)

blocks = paras[1:]
qs = []
i = 0
while i < len(blocks):
    q = blocks[i]
    if not q.endswith("?"):
        i += 1
        continue
    i += 1
    opts = []
    while i < len(blocks) and not blocks[i].endswith("?"):
        opts.append(blocks[i])
        i += 1
    qs.append((q, opts))

print("count", len(qs))
for j, (q, o) in enumerate(qs):
    print(j + 1, len(o), q[:72])
