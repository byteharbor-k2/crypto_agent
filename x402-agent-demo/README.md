# x402 Agent Demo

**基于 x402 协议与 MCP 架构的自主经济 AI Agent**

*Design and Implementation of an Autonomous Economic AI Agent Based on x402 Protocol and MCP Architecture*

---

## 🎯 项目简介

这是一个创新的 AI Agent 演示项目，展示了如何让 AI 自主地发现付费服务、评估价格、执行加密货币支付并获取内容。项目结合了三个前沿技术：

- **x402 协议** - 基于 HTTP 402 状态码的 Web3 支付标准
- **MCP (Model Context Protocol)** - Anthropic 推出的 AI 工具调用协议
- **Claude AI** - 强大的大语言模型，具备工具调用能力

### 核心能力

✅ 自动检测 HTTP 402 付费墙  
✅ 解析支付需求（金额、地址、描述）  
✅ 基于策略自主决策是否支付  
✅ 执行 Web3 加密货币交易  
✅ 获取付费内容并呈现给用户  

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────┐
│   AI Agent Client (Claude API)     │
│   - 任务理解                         │
│   - 支付决策                         │
│   - 用户交互                         │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   MCP Server (stdio 工具层)           │
│   ├─ http_request                   │
│   ├─ web3_payment                   │
│   ├─ get_wallet_balance             │
│   └─ check_payment_policy           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Mock x402 Service (Flask)         │
│   ├─ Premium Article API (0.5 USDC) │
│   ├─ Image Generation (0.8 USDC)    │
│   └─ Video Generation (5.0 USDC)    │
└─────────────────────────────────────┘
```

---

## 📦 项目结构

```
x402-agent-demo/
├── src/x402_agent_demo/     # 主包
├── mock-service/             # Mock x402 付费服务
│   └── app.py               # Flask API
├── mcp-server/              # MCP Server (工具提供者)
│   └── server.py            # MCP 工具实现
├── agent-client/            # AI Agent 客户端
│   └── agent.py             # Claude Agent
├── setup.py                 # 快速设置脚本
├── run_mock_service.py      # 启动 Mock 服务
├── run_agent.py             # 启动 Agent
├── .env.example             # 环境变量模板
├── pyproject.toml           # 项目配置
└── README.md                # 本文档
```

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js v22+ (如需使用 MCP)
- uv (Python 包管理器)
- Anthropic API Key

### 1. 安装依赖

```bash
# 克隆项目后进入目录
cd x402-agent-demo

# 使用 uv 同步依赖
uv sync
```

### 2. 配置环境

```bash
# 运行设置脚本（会自动生成测试钱包和 .env 文件）
python setup.py
```

或者手动创建 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 Anthropic API Key：

```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 3. 启动服务

**终端 1 - 启动 Mock x402 服务**

```bash
python run_mock_service.py
```

服务将运行在 `http://localhost:5000`

**终端 2 - 启动 AI Agent**

```bash
python run_agent.py
```

---

## 💡 使用示例

### 场景 1: 自动支付（小额）

```
👤 You: 帮我获取这篇文章 http://localhost:5000/api/article/quantum-2026

🔧 Tool Call: http_request
   检测到 HTTP 402 付费墙
   价格: 0.5 USDC (低于 1.0 USDC 自动批准额度)

🔧 Tool Call: web3_payment
   ✅ 自动批准支付 0.5 USDC

🤖 Agent: 已为您获取这篇关于量子计算的付费文章...
```

### 场景 2: 需要用户确认（大额）

```
👤 You: 生成一段 4K 风景视频

🔧 Tool Call: http_request
   检测到需要 5.0 USDC

🔧 Tool Call: check_payment_policy
   超过自动批准额度，需要用户确认

💰 PAYMENT APPROVAL REQUIRED
Amount: 5.0 USDC
Description: AI-Generated 10s 4K Video
Recipient: 0x742d35Cc...

Approve payment? (yes/no): yes

✅ Payment executed
🤖 Agent: 视频生成完成！
```

---

## 🔧 可用的 API 端点

### Mock x402 Service

| 端点 | 方法 | 价格 | 描述 |
|------|------|------|------|
| `/api/article/<id>` | GET | 0.5 USDC | 高级研究文章 |
| `/api/generate/image` | POST | 0.8 USDC | AI 图片生成 |
| `/api/generate/video` | POST | 5.0 USDC | AI 视频生成 |
| `/health` | GET | 免费 | 健康检查 |

### 测试请求

```bash
# 测试付费墙
curl http://localhost:5000/api/article/test-123

# 带支付凭证的请求
curl http://localhost:5000/api/article/test-123 \
  -H 'X-Payment-Proof: {"tx_hash": "0x1234567890abcdef"}'
```

---

## ⚙️ 支付策略配置

在 `.env` 文件中配置：

```env
# 免密支付额度（USDC）
MAX_AUTO_APPROVE_AMOUNT=1.0

# 钱包配置
AGENT_WALLET_ADDRESS=0x...
AGENT_PRIVATE_KEY=0x...

# Web3 RPC (Sepolia 测试网)
WEB3_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/demo
```

---

## 🔐 安全说明

⚠️ **重要提示**：

1. **本项目仅用于演示和研究**
2. 所有支付交易都是**模拟的**，不会产生真实链上交易
3. 不要在测试钱包中存入真实资金
4. 不要将私钥提交到代码仓库
5. 生产环境需要：
   - 真实的区块链交易验证
   - 安全的私钥管理（硬件钱包、KMS）
   - 完善的错误处理和重试机制
   - 交易金额和频率限制

---

## 📚 技术栈

**后端**
- Python 3.11+
- Flask - Web 框架
- Web3.py - 以太坊交互
- eth-account - 钱包和签名

**AI/LLM**
- Anthropic Claude API
- MCP (Model Context Protocol)

**开发工具**
- uv - Python 包管理
- python-dotenv - 环境变量管理

---

## 🛠️ 开发指南

### 添加新的付费服务

编辑 `mock-service/app.py`，添加新的端点：

```python
@app.route('/api/your-service', methods=['GET'])
def your_service():
    # 检查支付
    payment_proof = request.headers.get('X-Payment-Proof')
    
    if not payment_proof:
        # 返回 402
        response = jsonify({"error": "payment_required"})
        response.headers['X-Payment-Amount'] = '0.3'
        response.headers['X-Payment-Currency'] = 'USDC'
        # ... 其他 x402 headers
        return response, 402
    
    # 验证支付后返回内容
    return jsonify({"content": "Your paid content"})
```

### 调整支付策略

修改 `mcp-server/server.py` 中的 `handle_check_policy()` 逻辑。Agent 会通过 MCP 调用该工具，而不是在客户端内部直接判断策略：

```python
async def handle_check_policy(arguments: dict) -> list[TextContent]:
    amount = float(arguments["amount"])
    
    # 自定义策略
    if amount < 0.5:
        result = {"decision": "auto_approve"}
    elif amount < 2.0:
        result = {"decision": "request_approval"}
    else:
        result = {"decision": "reject", "reason": "exceeds limit"}

    return [TextContent(type="text", text=json.dumps(result))]
```

---

## 🔄 MCP Server 集成

当前版本中，`run_agent.py` 会启动 Agent 客户端，Agent 再通过 stdio 自动拉起并连接 `mcp-server/server.py`。Claude 只看到从 MCP Server 动态加载的工具定义，具体的 HTTP 请求、x402 检测、支付模拟、余额查询和支付策略判断都在 MCP Server 中执行。

运行时链路：

1. Agent 初始化 MCP ClientSession
2. MCP Client 通过 stdio 启动 `mcp-server/server.py`
3. Agent 调用 `list_tools()` 加载工具 schema
4. Claude 发起 tool_use 后，Agent 将参数转发到 MCP Server 的 `call_tool()`
5. MCP Server 执行工具并把 JSON 结果返回给 Agent

参考 MCP 官方文档：https://github.com/anthropics/mcp

---

## 📖 相关资源

- **x402 协议**: https://docs.cdp.coinbase.com/x402/welcome
- **MCP 规范**: https://github.com/anthropics/mcp
- **Google AP2**: https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol
- **Cloudflare x402**: https://blog.cloudflare.com/x402/

---

## 🎓 毕业设计相关

本项目是毕业设计"基于 x402 协议与 MCP 架构的自主经济 AI Agent 设计与实现"的最小可执行 Demo。

### 核心创新点

1. **自主经济行为** - Agent 能独立完成"发现→评估→支付→获取"全流程
2. **标准化工具调用** - 使用 MCP 协议连接 AI 与工具层
3. **Web3 支付集成** - 展示加密货币在 AI Agent 场景的应用

### 后续扩展方向

- [ ] 集成本地 LLM (Ollama + Llama 3)
- [ ] 真实区块链交易（Sepolia 测试网）
- [ ] 服务商白名单和黑名单
- [ ] 会话级预算管理
- [ ] 交易历史记录和审计
- [ ] Web UI 界面
- [ ] 多币种支持（ETH, USDT, USDC）

---

## 📄 许可证

MIT License - 仅供学习和研究使用

---

## 👤 作者

牛稼豪 (202231235035)

---

## 🙏 致谢

- Anthropic - Claude API 和 MCP 协议
- Coinbase - x402 协议规范
- OKX - x402 实践指南

---

**⚡ 开始探索 AI Agent 的自主经济能力吧！**
