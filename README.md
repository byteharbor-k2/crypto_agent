# x402 Agent Demo

**基于 x402 协议与 MCP 架构的自主经济 AI Agent 设计与实现**

*Design and Implementation of an Autonomous Economic AI Agent Based on x402 Protocol and MCP Architecture*

---

## 项目简介

本项目是一个创新的 AI Agent 演示，展示了如何让 AI 自主地发现付费服务、评估价格、执行加密货币支付并获取内容。项目融合了三个前沿技术：

- **x402 协议** - 基于 HTTP 402 状态码的 Web3 支付标准
- **MCP (Model Context Protocol)** - Anthropic 推出的 AI 工具调用协议
- **AI Agent** - 具备自主经济行为能力的智能体

### 项目意义

随着大语言模型（LLM）从单纯的信息处理向自主智能体（Agent）演进，如何赋予 Agent 独立的经济行为能力成为构建"机器经济体"的关键挑战。目前的 AI Agent 大多受限于传统的 API Key 付费模式，缺乏自主发现服务、评估价格并完成支付的能力。

本项目旨在探索 Web3 支付在 AI 领域的应用落地，解决 Agent 跨平台、无许可支付的难题，为未来去中心化 AI 协作网络的构建提供实践参考。

---

## 系统架构

采用 **三层架构** 设计：

```
┌─────────────────────────────────────────┐
│   AI Agent Client (Claude API)          │
│   - 任务理解与意图识别                    │
│   - 支付决策                             │
│   - 用户交互                             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   MCP Tools Layer                       │
│   ├─ http_request      (HTTP 请求/402检测)│
│   ├─ web3_payment      (Web3 支付执行)    │
│   ├─ get_wallet_balance (钱包余额查询)    │
│   └─ check_payment_policy (策略检查)      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   Mock x402 Service (Flask)             │
│   ├─ Premium Article API   (0.5 USDC)   │
│   ├─ Image Generation API  (0.8 USDC)   │
│   └─ Video Generation API  (5.0 USDC)   │
└─────────────────────────────────────────┘
```

### 各层职责

1. **Agent 客户端层**：部署 AI 模型，负责理解用户意图、调用工具、做出支付决策
2. **MCP 工具层**：封装 HTTP 请求和 Web3 钱包功能，实现 x402 协议解析
3. **资源服务层**：模拟支持 x402 协议的付费 API，用于验证 Agent 支付能力

---

## 核心功能

- 自动检测 HTTP 402 付费墙
- 解析 x402 支付需求（金额、地址、挑战数据）
- 基于策略自主决策是否支付
- 执行 Web3 加密货币交易（模拟）
- 获取付费内容并呈现给用户

### 支付策略

- **免密支付额度**：低于阈值（默认 1.0 USDC）自动批准
- **超额确认**：超过阈值需要用户手动确认
- **余额检查**：支付前检查钱包余额

---

## 功能流程

```
用户下达指令
     ↓
Agent 访问资源 → 返回 HTTP 402 (Payment Required)
     ↓
解析 x402 Headers (价格、收款地址、挑战数据)
     ↓
检查支付策略 (金额是否在免密范围内?)
     ↓
┌─────────────┬─────────────────────┐
│ 免密范围内   │ 超过免密额度          │
│ 自动批准支付 │ 请求用户确认          │
└─────────────┴─────────────────────┘
     ↓
执行 Web3 支付，获取交易凭证
     ↓
携带支付凭证重新请求资源
     ↓
服务验证凭证，返回内容
```

---

## 用户交互示例

### 场景一：自动支付（预算内）

```
👤 用户: 帮我查看这篇关于"量子计算最新进展"的付费研报

🤖 Agent: 正在访问该链接...
   检测到付费内容，价格 0.5 USDC (低于免密额度 1.0)
   已自动完成支付 (TxHash: 0x123...)

   以下是研报的核心内容：...
```

### 场景二：需要用户确认（超额）

```
👤 用户: 生成一段 4K 风景视频

🤖 Agent: 已连接视频生成 API，服务商报价 5.0 USDC
   超过免密支付额度，需要您的确认

💰 PAYMENT APPROVAL REQUIRED
   Amount: 5.0 USDC
   Description: AI-Generated 10s 4K Video

   Approve payment? (yes/no): yes

✅ Payment executed
🤖 Agent: 视频生成完成！
```

---

## 项目结构

```
crypto_agent/
├── x402-agent-demo/             # Demo 实现
│   ├── agent-client/            # AI Agent 客户端
│   │   └── agent.py             # Claude Agent 实现
│   ├── mcp-server/              # MCP Server
│   │   └── server.py            # MCP 工具定义
│   ├── mock-service/            # Mock x402 服务
│   │   └── app.py               # Flask API
│   ├── setup.py                 # 环境配置脚本
│   ├── run_mock_service.py      # 启动 Mock 服务
│   ├── run_agent.py             # 启动 Agent
│   └── README.md                # Demo 详细文档
├── CLAUDE.md                    # 项目开发指引
└── README.md                    # 本文档
```

---

## 快速开始

```bash
# 进入 demo 目录
cd x402-agent-demo

# 安装依赖
uv sync

# 配置环境（生成测试钱包和 .env）
python setup.py

# 终端 1 - 启动 Mock x402 服务
python run_mock_service.py

# 终端 2 - 启动 AI Agent
python run_agent.py
```

详细说明请参考 `x402-agent-demo/README.md`

---

## 技术栈

| 类别 | 技术 |
|------|------|
| **后端** | Python 3.11+, Flask, Web3.py, eth-account |
| **AI/LLM** | Anthropic Claude API, MCP Protocol |
| **区块链** | EVM 兼容链 (Sepolia 测试网) |
| **开发工具** | uv, python-dotenv |

---

## 安全说明

- 本项目仅用于演示和研究
- 所有支付交易都是**模拟的**，不会产生真实链上交易
- 不要在测试钱包中存入真实资金
- 不要将私钥提交到代码仓库

---

## 后续扩展方向

- [ ] 集成本地 LLM (Ollama + Llama 3 / Qwen)
- [ ] 真实区块链交易（Sepolia/Base 测试网）
- [ ] EIP-712 签名实现
- [ ] 服务商白名单和黑名单
- [ ] 会话级预算管理
- [ ] 交易历史记录和审计
- [ ] Web UI 界面
- [ ] 多币种支持（ETH, USDT, USDC）

---

## 相关资源

### x402 协议

- [Coinbase x402 文档](https://docs.cdp.coinbase.com/x402/welcome)
- [Cloudflare x402 博客](https://blog.cloudflare.com/x402/)
- [OKX x402 指南](https://web3.okx.com/learn/wallet-x402-how-to-trade-it)

### AI Agent 支付

- [Google AP2 协议](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol)
- [MCP 协议规范](https://github.com/anthropics/mcp)

### Agent 开发

- [Advent of Agents](https://adventofagents.com/)
- [Claude Code Agent Skills](https://code.claude.com/docs/en/skills)

### Web3 基础设施

- [Questflow x402 Facilitator](https://next.questflow.ai/@santa)
- [Kite AI Payment Chain](https://gokite.ai/)

---

