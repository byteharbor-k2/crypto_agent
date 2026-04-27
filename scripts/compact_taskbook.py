import copy
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
DOCX_PATH = Path("4.毕业设计任务书.docx")


CONTENT = (
    "本课题设计并实现基于 x402 协议与 MCP 架构的自主经济 AI Agent。系统包括 Agent 客户端、"
    "MCP 工具层和 Mock x402 服务，完成 HTTP 402 付费墙检测、支付需求解析、支付策略判断、"
    "模拟 Web3 支付、支付凭证重试及付费内容获取等功能。"
)

REQUIREMENTS = [
    "1. 完成 x402、MCP、AI Agent 与 Web3 支付相关资料调研，明确需求与技术路线。",
    "2. 完成系统架构、模块划分、接口流程、支付策略和异常处理设计。",
    "3. 实现 Agent 客户端、MCP 工具、Mock 付费服务、余额查询和模拟支付功能。",
    "4. 完成系统测试、中期材料、毕业设计说明书和外文资料翻译，保证文档与实现一致。",
]

SCHEDULE = [
    ("1", "调研、需求分析、总体设计与环境搭建", "2026.03.02-03.29"),
    ("2", "核心模块实现、Mock 服务联调与中期检查", "2026.03.30-04.30"),
    ("3", "系统测试完善、论文撰写、外文翻译与答辩准备", "2026.05.01-06.12"),
]

LITERATURE = (
    "围绕 AI Agent 工具调用、MCP 协议、HTTP 402/x402 支付协议、Web3 钱包、稳定币支付、"
    "交易签名和 API 付费访问控制等方向查阅资料。主要来源包括 CNKI、万方、IEEE Xplore、"
    "ACM Digital Library、Google Scholar、arXiv 以及 Coinbase、Anthropic、Ethereum、Web3.py 等官方文档。"
)


def qn(name: str) -> str:
    return f"{W}{name}"


def make_para(text: str, *, size="21", bold=False, align="left", first_line=True, font="SimSun") -> ET.Element:
    p = ET.Element(qn("p"))
    ppr = ET.SubElement(p, qn("pPr"))
    spacing = ET.SubElement(ppr, qn("spacing"))
    spacing.set(qn("line"), "300")
    spacing.set(qn("lineRule"), "auto")
    jc = ET.SubElement(ppr, qn("jc"))
    jc.set(qn("val"), align)
    if first_line:
        ind = ET.SubElement(ppr, qn("ind"))
        ind.set(qn("firstLine"), "420")

    r = ET.SubElement(p, qn("r"))
    rpr = ET.SubElement(r, qn("rPr"))
    fonts = ET.SubElement(rpr, qn("rFonts"))
    fonts.set(qn("ascii"), "Times New Roman")
    fonts.set(qn("hAnsi"), "Times New Roman")
    fonts.set(qn("eastAsia"), font)
    if bold:
        ET.SubElement(rpr, qn("b"))
    ET.SubElement(rpr, qn("sz")).set(qn("val"), size)
    ET.SubElement(rpr, qn("szCs")).set(qn("val"), size)
    t = ET.SubElement(r, qn("t"))
    t.text = text
    return p


def set_para_text(p: ET.Element, text: str, *, size="21", bold=False, align="left", first_line=True, font="SimSun") -> None:
    for child in list(p):
        p.remove(child)
    new_p = make_para(text, size=size, bold=bold, align=align, first_line=first_line, font=font)
    for child in list(new_p):
        p.append(copy.deepcopy(child))


def make_cell(text: str, width: int, *, bold=False, align="center") -> ET.Element:
    tc = ET.Element(qn("tc"))
    tcpr = ET.SubElement(tc, qn("tcPr"))
    tcw = ET.SubElement(tcpr, qn("tcW"))
    tcw.set(qn("w"), str(width))
    tcw.set(qn("type"), "dxa")
    borders = ET.SubElement(tcpr, qn("tcBorders"))
    for side in ("top", "left", "bottom", "right"):
        border = ET.SubElement(borders, qn(side))
        border.set(qn("val"), "single")
        border.set(qn("sz"), "4")
        border.set(qn("space"), "0")
        border.set(qn("color"), "auto")
    valign = ET.SubElement(tcpr, qn("vAlign"))
    valign.set(qn("val"), "center")
    tc.append(make_para(text, size="18", bold=bold, align=align, first_line=False))
    return tc


def make_row(values, widths, *, header=False) -> ET.Element:
    tr = ET.Element(qn("tr"))
    trpr = ET.SubElement(tr, qn("trPr"))
    trh = ET.SubElement(trpr, qn("trHeight"))
    trh.set(qn("val"), "340")
    trh.set(qn("hRule"), "atLeast")
    for text, width in zip(values, widths):
        tr.append(make_cell(text, width, bold=header, align="center" if header or width < 1800 else "left"))
    return tr


def make_schedule_table() -> ET.Element:
    widths = [700, 5200, 2200]
    tbl = ET.Element(qn("tbl"))
    tblpr = ET.SubElement(tbl, qn("tblPr"))
    tblw = ET.SubElement(tblpr, qn("tblW"))
    tblw.set(qn("w"), str(sum(widths)))
    tblw.set(qn("type"), "dxa")
    layout = ET.SubElement(tblpr, qn("tblLayout"))
    layout.set(qn("type"), "fixed")
    margins = ET.SubElement(tblpr, qn("tblCellMar"))
    for side in ("top", "left", "bottom", "right"):
        mar = ET.SubElement(margins, qn(side))
        mar.set(qn("w"), "80")
        mar.set(qn("type"), "dxa")
    grid = ET.SubElement(tbl, qn("tblGrid"))
    for width in widths:
        col = ET.SubElement(grid, qn("gridCol"))
        col.set(qn("w"), str(width))
    tbl.append(make_row(("序号", "阶段任务", "日期"), widths, header=True))
    for row in SCHEDULE:
        tbl.append(make_row(row, widths))
    return tbl


def main() -> None:
    with zipfile.ZipFile(DOCX_PATH, "r") as zin:
        root = ET.fromstring(zin.read("word/document.xml"))
        body = root.find(qn("body"))
        sect = list(body)[-1]

        keep = list(body)[:3]
        for child in list(body):
            body.remove(child)
        for child in keep:
            body.append(child)

        body.append(make_para("一、毕业设计的内容", size="28", bold=True, first_line=False, font="SimHei"))
        body.append(make_para(CONTENT, size="21"))
        body.append(make_para("二、毕业设计的要求", size="28", bold=True, first_line=False, font="SimHei"))
        for item in REQUIREMENTS:
            body.append(make_para(item, size="21", first_line=False))
        body.append(make_para("三、毕业设计进程安排", size="28", bold=True, first_line=False, font="SimHei"))
        for no, task, date in SCHEDULE:
            body.append(make_para(f"{no}. {task}：{date}", size="21", first_line=False))
        body.append(make_para("四、文献查询方向及范围", size="28", bold=True, first_line=False, font="SimHei"))
        body.append(make_para(LITERATURE, size="21"))
        body.append(make_para("毕业设计起止时间: 2026年 3月 2日——2026年 6月 12日", size="21", first_line=False))
        body.append(make_para("指导教师（签字）  曹毅            系 主 任（签字）", size="21", first_line=False, align="center"))
        body.append(make_para("2026年  月  日", size="21", first_line=False, align="center", bold=True))
        body.append(sect)

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
