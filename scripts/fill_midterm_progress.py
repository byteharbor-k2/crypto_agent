import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

W = f"{{{NS['w']}}}"
DOCX_PATH = Path("7.毕业设计中期检查表.docx")

PROGRESS = (
    "实际工作进展状况：已完成课题调研、需求分析和原型系统搭建，当前采用模型 API Key "
    "方式实现 Agent 对话与工具调用，完成 HTTP 402 检测、x402 支付信息解析、支付策略判断、"
    "模拟支付和付费资源获取流程。后续计划使用本地部署 AI 替换云端模型，并继续寻找真实支持 "
    "x402 的互联网服务，探索 Polymarket 等自动交易 Agent 应用方向，完善测试、安全控制和论文材料。"
)

TITLE = "基于x402协议与MCP架构的自主经济AI Agent设计与实现"


def qn(name: str) -> str:
    return f"{W}{name}"


def set_paragraph_text(p: ET.Element, text: str) -> None:
    ppr = p.find(qn("pPr"))
    if ppr is None:
        ppr = ET.Element(qn("pPr"))
        p.insert(0, ppr)

    spacing = ppr.find(qn("spacing"))
    if spacing is None:
        spacing = ET.SubElement(ppr, qn("spacing"))
    spacing.set(qn("line"), "300")
    spacing.set(qn("lineRule"), "auto")

    jc = ppr.find(qn("jc"))
    if jc is None:
        jc = ET.SubElement(ppr, qn("jc"))
    jc.set(qn("val"), "left")

    ind = ppr.find(qn("ind"))
    if ind is None:
        ind = ET.SubElement(ppr, qn("ind"))
    ind.set(qn("firstLine"), "420")

    for child in list(p):
        if child.tag != qn("pPr"):
            p.remove(child)

    run = ET.SubElement(p, qn("r"))
    rpr = ET.SubElement(run, qn("rPr"))
    fonts = ET.SubElement(rpr, qn("rFonts"))
    fonts.set(qn("ascii"), "Times New Roman")
    fonts.set(qn("hAnsi"), "Times New Roman")
    fonts.set(qn("eastAsia"), "SimSun")
    ET.SubElement(rpr, qn("sz")).set(qn("val"), "21")
    ET.SubElement(rpr, qn("szCs")).set(qn("val"), "21")
    t = ET.SubElement(run, qn("t"))
    t.text = text


def make_p(text: str, *, size: str = "24", bold: bool = False, align: str = "left") -> ET.Element:
    p = ET.Element(qn("p"))
    ppr = ET.SubElement(p, qn("pPr"))
    jc = ET.SubElement(ppr, qn("jc"))
    jc.set(qn("val"), align)
    spacing = ET.SubElement(ppr, qn("spacing"))
    spacing.set(qn("line"), "300")
    spacing.set(qn("lineRule"), "auto")

    r = ET.SubElement(p, qn("r"))
    rpr = ET.SubElement(r, qn("rPr"))
    fonts = ET.SubElement(rpr, qn("rFonts"))
    fonts.set(qn("ascii"), "Times New Roman")
    fonts.set(qn("hAnsi"), "Times New Roman")
    fonts.set(qn("eastAsia"), "SimSun")
    if bold:
        ET.SubElement(rpr, qn("b"))
    ET.SubElement(rpr, qn("sz")).set(qn("val"), size)
    ET.SubElement(rpr, qn("szCs")).set(qn("val"), size)
    t = ET.SubElement(r, qn("t"))
    t.text = text
    return p


def make_cell(text: str, width: int, *, span: int = 1, bold: bool = False, align: str = "left") -> ET.Element:
    tc = ET.Element(qn("tc"))
    tcpr = ET.SubElement(tc, qn("tcPr"))
    tcw = ET.SubElement(tcpr, qn("tcW"))
    tcw.set(qn("w"), str(width))
    tcw.set(qn("type"), "dxa")
    if span > 1:
        grid_span = ET.SubElement(tcpr, qn("gridSpan"))
        grid_span.set(qn("val"), str(span))
    borders = ET.SubElement(tcpr, qn("tcBorders"))
    for side in ("top", "left", "bottom", "right"):
        border = ET.SubElement(borders, qn(side))
        border.set(qn("val"), "single")
        border.set(qn("sz"), "4")
        border.set(qn("space"), "0")
        border.set(qn("color"), "auto")
    v_align = ET.SubElement(tcpr, qn("vAlign"))
    v_align.set(qn("val"), "center")
    tc.append(make_p(text, size="21", bold=bold, align=align))
    return tc


def make_row(cells: list[ET.Element], height: int | None = None) -> ET.Element:
    tr = ET.Element(qn("tr"))
    if height:
        trpr = ET.SubElement(tr, qn("trPr"))
        trh = ET.SubElement(trpr, qn("trHeight"))
        trh.set(qn("val"), str(height))
        trh.set(qn("hRule"), "atLeast")
    for cell in cells:
        tr.append(cell)
    return tr


def make_table() -> ET.Element:
    widths = [1500, 2550, 1200, 3250]
    tbl = ET.Element(qn("tbl"))
    tblpr = ET.SubElement(tbl, qn("tblPr"))
    tblw = ET.SubElement(tblpr, qn("tblW"))
    tblw.set(qn("w"), "8500")
    tblw.set(qn("type"), "dxa")
    borders = ET.SubElement(tblpr, qn("tblBorders"))
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = ET.SubElement(borders, qn(side))
        border.set(qn("val"), "single")
        border.set(qn("sz"), "4")
        border.set(qn("space"), "0")
        border.set(qn("color"), "auto")
    layout = ET.SubElement(tblpr, qn("tblLayout"))
    layout.set(qn("type"), "fixed")
    margins = ET.SubElement(tblpr, qn("tblCellMar"))
    for side in ("top", "left", "bottom", "right"):
        mar = ET.SubElement(margins, qn(side))
        mar.set(qn("w"), "120")
        mar.set(qn("type"), "dxa")

    grid = ET.SubElement(tbl, qn("tblGrid"))
    for width in widths:
        col = ET.SubElement(grid, qn("gridCol"))
        col.set(qn("w"), str(width))

    tbl.append(make_row([
        make_cell("论文（设计）题目", widths[0], bold=True, align="center"),
        make_cell(TITLE, sum(widths[1:]), span=3),
    ], 600))
    tbl.append(make_row([
        make_cell("学生姓名", widths[0], bold=True, align="center"),
        make_cell("牛稼豪", widths[1], align="center"),
        make_cell("学号", widths[2], bold=True, align="center"),
        make_cell("202231235035", widths[3], align="center"),
    ], 600))
    tbl.append(make_row([
        make_cell("指导教师", widths[0], bold=True, align="center"),
        make_cell("曹毅", widths[1], align="center"),
        make_cell("职称", widths[2], bold=True, align="center"),
        make_cell("", widths[3]),
    ], 600))
    tbl.append(make_row([
        make_cell(PROGRESS, sum(widths), span=4),
    ], 1800))
    tbl.append(make_row([
        make_cell("安排进度的完成情况", widths[0], bold=True),
        make_cell("□超额完成    □按计划完成    □部分完成    □未开展", sum(widths[1:]), span=3),
    ], 600))
    tbl.append(make_row([
        make_cell("工作态度情况", widths[0], bold=True),
        make_cell("□认真    □较认真    □一般    □不认真", sum(widths[1:]), span=3),
    ], 600))
    tbl.append(make_row([
        make_cell("质量评价", widths[0], bold=True),
        make_cell("□优    □良    □中    □差", sum(widths[1:]), span=3),
    ], 600))
    tbl.append(make_row([
        make_cell("存在的主要问题和解决方案：\n\n\n\n\n指导教师（签字）：                         年    月    日", sum(widths), span=4),
    ], 2400))
    return tbl


def make_form_paragraphs() -> list[ET.Element]:
    return [
        make_p(f"论文（设计）题目：{TITLE}", size="24"),
        make_p("学生姓名：牛稼豪        学号：202231235035", size="24"),
        make_p("指导教师：曹毅        职称：", size="24"),
        make_p(PROGRESS, size="21"),
        make_p("安排进度的完成情况：□超额完成    □按计划完成    □部分完成    □未开展", size="21"),
        make_p("工作态度情况：□认真    □较认真    □一般    □不认真", size="21"),
        make_p("质量评价：□优    □良    □中    □差", size="21"),
        make_p("存在的主要问题和解决方案：", size="21"),
        make_p("", size="21"),
        make_p("", size="21"),
        make_p("指导教师（签字）：                         年    月    日", size="21", align="right"),
    ]


def main() -> None:
    with zipfile.ZipFile(DOCX_PATH, "r") as zin:
        root = ET.fromstring(zin.read("word/document.xml"))
        body = root.find(qn("body"))
        children = list(body)
        for i, child in enumerate(children):
            if child.tag == qn("tbl"):
                body.remove(child)
                if i < len(list(body)) and list(body)[i].tag == qn("p"):
                    # Remove the red template note after the table.
                    body.remove(list(body)[i])
                for offset, p in enumerate(make_form_paragraphs()):
                    body.insert(i + offset, p)
                break

        new_document_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp_path = Path(tmp.name)
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = new_document_xml
                zout.writestr(item, data)

    tmp_path.replace(DOCX_PATH)


if __name__ == "__main__":
    main()
