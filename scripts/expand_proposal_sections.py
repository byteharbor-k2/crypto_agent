import copy
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

W = f"{{{NS['w']}}}"
DOCX_PATH = Path("5.毕业设计方案.docx")


BACKGROUND = [
    "随着大语言模型由文本生成工具逐步发展为能够规划任务、调用工具并完成外部操作的 AI Agent，智能体与网络服务之间的交互方式正在发生变化。传统 API 调用依赖预先注册、API Key、套餐订阅或人工支付，难以满足 Agent 按任务即时发现服务、按次计费、自动结算和跨平台调用的需求。当 Agent 需要购买数据、调用模型服务或获取付费内容时，必须具备安全、可控、可审计的机器支付能力。",
    "x402 协议以 HTTP 402 Payment Required 状态码为基础，将价格、币种、收款地址、挑战信息等支付需求嵌入标准 HTTP 流程。客户端完成支付后携带支付凭证重新请求资源，从而形成“请求—付费—验证—返回内容”的闭环。MCP（Model Context Protocol）则为大模型连接外部工具和数据源提供统一接口，使 Agent 能以标准化方式调用 HTTP 请求、钱包、策略检查等能力。二者结合后，可以为自主经济 Agent 提供清晰的工程实现路径。",
    "目前国外在 Agent 工具调用、MCP 协议、稳定币微支付和 x402 付费 API 方面已有较多探索，Coinbase、Cloudflare 等机构正在推动基于 HTTP 的机器支付实践；国内研究更多集中在智能体应用、区块链支付、API 网关计费和数字内容付费等方向。将 x402 支付协议与 MCP 工具架构结合，构建可运行的 AI Agent 原型，仍具有较强的实践价值。",
    "本课题的意义在于通过工程化原型验证 AI Agent 自动识别付费墙、解析支付需求、执行支付策略、生成支付凭证并获取付费资源的完整流程。课题重点是支付流程与工具调用架构的集成，难点在于支付额度控制、人工确认、安全边界、异常处理和后续真实链上环境扩展。该研究可为未来按次计费 API、去中心化 AI 服务市场和自动交易 Agent 应用提供参考。",
]

DESIGN_CONTENT = [
    "本设计拟完成一个基于 x402 协议与 MCP 架构的自主经济 AI Agent 演示系统。系统面向用户提出的资源获取、内容生成或服务调用任务，能够访问支持 x402 机制的付费服务，在遇到 HTTP 402 响应后解析支付需求，并依据预设策略判断是否自动支付或请求用户确认，最终携带支付凭证重新请求服务并返回结果。",
    "系统主要分为三层。第一层为 Agent 客户端，负责理解用户输入、维护上下文、组织工具调用和展示结果；第二层为 MCP 工具层，封装 HTTP 请求、402 检测、x402 Header 解析、钱包余额查询、支付策略检查和 Web3 支付执行等能力；第三层为资源服务层，使用 Flask 构建 Mock x402 服务，模拟文章获取、图像生成、视频生成等不同价格等级的付费接口。",
    "系统需要实现两类典型支付流程：一是小额自动支付，即当服务价格低于自动批准阈值时，Agent 自动完成余额检查、支付模拟和凭证重试；二是超额人工确认，即当价格超过阈值时，系统向用户展示金额、币种、收款地址和服务说明，得到确认后再执行支付。通过这两类流程验证 Agent 自主决策与用户安全控制之间的平衡。",
    "预期成果包括：可运行的 Python 原型系统；Agent 客户端、MCP 工具服务和 Mock 付费服务代码；自动支付与人工确认演示场景；关键流程测试用例、运行截图和说明文档；毕业设计说明书、中期检查材料、外文资料翻译等配套文档。后续可进一步探索本地部署模型替换云端 API Key，以及接入真实支持 x402 的互联网服务。",
]

DESIGN_PLAN = [
    "系统采用 Python 作为主要开发语言，使用 Flask 构建 Mock x402 资源服务，使用 Web3.py 与 eth-account 实现钱包地址、交易哈希和支付凭证的模拟，使用 MCP 工具接口思想封装外部能力。当前阶段以模型 API Key 完成 Agent 推理与工具调用，后续计划尝试部署本地大模型，以降低外部 API 依赖并提高系统可控性。",
    "总体流程为：用户输入任务后，Agent 调用 HTTP 工具访问目标服务；若服务返回普通 200 响应，则直接处理内容；若返回 402 响应，则工具层提取金额、币种、收款地址、挑战值和服务描述；随后 Agent 调用支付策略模块判断是否低于自动批准额度，并在必要时请求用户确认；支付完成后生成交易凭证，再次请求资源服务，服务端校验凭证并返回内容。",
    "模块设计方面，Agent 客户端负责自然语言交互、任务理解、工具调度和结果解释；HTTP 工具负责请求发送、状态码识别和 x402 信息提取；支付工具负责余额检查、交易模拟和凭证生成；策略模块负责自动批准阈值、人工确认和余额校验；Mock 服务负责付费墙响应、凭证校验和不同服务价格配置；测试模块覆盖自动支付、人工确认、余额不足、异常响应和凭证重试等场景。",
    "进度安排为：第一阶段完成文献调研、需求分析、总体架构设计和开发环境搭建；第二阶段完成 HTTP 402 检测、x402 解析、支付策略、模拟支付和 Mock 服务联调，并整理中期检查材料；第三阶段完成系统测试、功能完善、论文撰写、外文资料翻译和答辩材料准备。后续还将持续寻找真实支持 x402 的服务场景，并关注 Polymarket 等自动交易 Agent 方向的应用可行性。",
]

REFERENCES = [
    "[1] Coinbase Developer Platform. Welcome to x402[EB/OL]. https://docs.cdp.coinbase.com/x402/docs/http-402.",
    "[2] Model Context Protocol. Specification: Protocol Revision 2025-11-25[EB/OL]. https://modelcontextprotocol.io/specification/2025-11-25/basic/index.",
    "[3] Anthropic. Model Context Protocol Documentation[EB/OL]. https://modelcontextprotocol.io/.",
    "[4] Ethereum Improvement Proposals. EIP-712: Typed structured data hashing and signing[EB/OL]. https://eips.ethereum.org/EIPS/eip-712.",
    "[5] Web3.py Project. Web3.py Documentation[EB/OL]. https://web3py.readthedocs.io/.",
    "[6] Pallets Projects. Flask Documentation[EB/OL]. https://flask.palletsprojects.com/.",
    "[7] JSON-RPC Working Group. JSON-RPC 2.0 Specification[EB/OL]. https://www.jsonrpc.org/specification.",
    "[8] Antonopoulos A M, Wood G. Mastering Ethereum: Building Smart Contracts and DApps[M]. Sebastopol: O'Reilly Media, 2018.",
    "[9] Brown T B, Mann B, Ryder N, et al. Language Models are Few-Shot Learners[C]//Advances in Neural Information Processing Systems. 2020.",
    "[10] Yao S, Zhao J, Yu D, et al. ReAct: Synergizing Reasoning and Acting in Language Models[C]//International Conference on Learning Representations. 2023.",
    "[11] Schick T, Dwivedi-Yu J, Dessì R, et al. Toolformer: Language Models Can Teach Themselves to Use Tools[C]//Advances in Neural Information Processing Systems. 2023.",
    "[12] Nakano R, Hilton J, Balaji S, et al. WebGPT: Browser-assisted Question-answering with Human Feedback[EB/OL]. arXiv:2112.09332, 2021.",
    "[13] Fielding R T. Architectural Styles and the Design of Network-based Software Architectures[D]. University of California, Irvine, 2000.",
    "[14] Wood G. Ethereum: A Secure Decentralised Generalised Transaction Ledger[EB/OL]. https://ethereum.github.io/yellowpaper/paper.pdf.",
]


def qn(name: str) -> str:
    return f"{W}{name}"


def get_text(elem: ET.Element) -> str:
    return "".join(t.text or "" for t in elem.findall(f".//{qn('t')}"))


def set_para_text(p: ET.Element, text: str, *, size: str = "21", align: str = "left", first_line: bool = True) -> None:
    for child in list(p):
        if child.tag != qn("pPr"):
            p.remove(child)

    ppr = p.find(qn("pPr"))
    if ppr is None:
        ppr = ET.Element(qn("pPr"))
        p.insert(0, ppr)

    pstyle = ppr.find(qn("pStyle"))
    if pstyle is not None:
        ppr.remove(pstyle)
    rpr = ppr.find(qn("rPr"))
    if rpr is not None:
        ppr.remove(rpr)

    spacing = ppr.find(qn("spacing"))
    if spacing is None:
        spacing = ET.SubElement(ppr, qn("spacing"))
    spacing.set(qn("line"), "300")
    spacing.set(qn("lineRule"), "auto")

    jc = ppr.find(qn("jc"))
    if jc is None:
        jc = ET.SubElement(ppr, qn("jc"))
    jc.set(qn("val"), align)

    ind = ppr.find(qn("ind"))
    if ind is None:
        ind = ET.SubElement(ppr, qn("ind"))
    if first_line:
        ind.set(qn("firstLine"), "420")
    else:
        ind.attrib.pop(qn("firstLine"), None)

    r = ET.SubElement(p, qn("r"))
    run_pr = ET.SubElement(r, qn("rPr"))
    fonts = ET.SubElement(run_pr, qn("rFonts"))
    fonts.set(qn("ascii"), "Times New Roman")
    fonts.set(qn("hAnsi"), "Times New Roman")
    fonts.set(qn("eastAsia"), "SimSun")
    ET.SubElement(run_pr, qn("sz")).set(qn("val"), size)
    ET.SubElement(run_pr, qn("szCs")).set(qn("val"), size)
    t = ET.SubElement(r, qn("t"))
    t.text = text


def clone_para(template: ET.Element, text: str, *, size: str = "21", first_line: bool = True) -> ET.Element:
    new_p = copy.deepcopy(template)
    set_para_text(new_p, text, size=size, first_line=first_line)
    return new_p


def find_idx(body: ET.Element, heading: str) -> int:
    for i, child in enumerate(list(body)):
        if child.tag == qn("p") and get_text(child) == heading:
            return i
    raise ValueError(heading)


def replace_between(body: ET.Element, start_heading: str, end_heading: str, texts: list[str], *, refs: bool = False) -> None:
    children = list(body)
    start = find_idx(body, start_heading) + 1
    end = find_idx(body, end_heading)
    template = children[start] if start < end else children[start - 1]
    new_nodes = [
        clone_para(template, text, size="20" if refs else "21", first_line=not refs)
        for text in texts
    ]
    for _ in range(end - start):
        body.remove(list(body)[start])
    for offset, node in enumerate(new_nodes):
        body.insert(start + offset, node)


def add_page_break_before(body: ET.Element, heading: str) -> None:
    p = list(body)[find_idx(body, heading)]
    ppr = p.find(qn("pPr"))
    if ppr is None:
        ppr = ET.Element(qn("pPr"))
        p.insert(0, ppr)
    if ppr.find(qn("pageBreakBefore")) is None:
        ET.SubElement(ppr, qn("pageBreakBefore"))


def fix_tail_tables(body: ET.Element) -> None:
    for tbl in body.findall(qn("tbl")):
        tbl_pr = tbl.find(qn("tblPr"))
        if tbl_pr is None:
            tbl_pr = ET.Element(qn("tblPr"))
            tbl.insert(0, tbl_pr)

        tbl_w = tbl_pr.find(qn("tblW"))
        if tbl_w is None:
            tbl_w = ET.SubElement(tbl_pr, qn("tblW"))
        tbl_w.set(qn("w"), "9003")
        tbl_w.set(qn("type"), "dxa")

        tbl_layout = tbl_pr.find(qn("tblLayout"))
        if tbl_layout is None:
            tbl_layout = ET.SubElement(tbl_pr, qn("tblLayout"))
        tbl_layout.set(qn("type"), "fixed")

        tbl_grid = tbl.find(qn("tblGrid"))
        if tbl_grid is None:
            tbl_grid = ET.Element(qn("tblGrid"))
            tbl.insert(1 if tbl.find(qn("tblPr")) is not None else 0, tbl_grid)
        for child in list(tbl_grid):
            tbl_grid.remove(child)
        ET.SubElement(tbl_grid, qn("gridCol")).set(qn("w"), "9003")

        for tc in tbl.findall(f".//{qn('tc')}"):
            tc_pr = tc.find(qn("tcPr"))
            if tc_pr is None:
                tc_pr = ET.Element(qn("tcPr"))
                tc.insert(0, tc_pr)
            tc_w = tc_pr.find(qn("tcW"))
            if tc_w is None:
                tc_w = ET.SubElement(tc_pr, qn("tcW"))
            tc_w.set(qn("w"), "9003")
            tc_w.set(qn("type"), "dxa")
            text_direction = tc_pr.find(qn("textDirection"))
            if text_direction is None:
                text_direction = ET.SubElement(tc_pr, qn("textDirection"))
            text_direction.set(qn("val"), "lrTb")


def main() -> None:
    with zipfile.ZipFile(DOCX_PATH, "r") as zin:
        root = ET.fromstring(zin.read("word/document.xml"))
        body = root.find(qn("body"))

        replace_between(body, "一、选题背景与意义", "二、设计内容", BACKGROUND)
        replace_between(body, "二、设计内容", "三、设计方案", DESIGN_CONTENT)
        replace_between(body, "三、设计方案", "四、参考文献", DESIGN_PLAN)
        replace_between(body, "四、参考文献", "五、指导教师评语", REFERENCES, refs=True)
        add_page_break_before(body, "五、指导教师评语")
        fix_tail_tables(body)

        new_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp_path = Path(tmp.name)
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = new_xml
                zout.writestr(item, data)

    tmp_path.replace(DOCX_PATH)


if __name__ == "__main__":
    main()
