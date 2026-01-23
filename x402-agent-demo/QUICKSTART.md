# x402 Agent Demo - 快速使用指南

## 第一次运行（完整流程）

### 1. 安装依赖

```bash
cd x402-agent-demo
uv sync
```

### 2. 生成配置文件

```bash
.venv/Scripts/python.exe setup.py
```

这将：
- 自动生成一个测试用的 ETH 钱包
- 创建 `.env` 配置文件

### 3. 配置 API Key

编辑 `.env` 文件，添加你的 Anthropic API Key：

```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

获取 API Key: https://console.anthropic.com/

### 4. 测试系统

```bash
# 先启动 Mock 服务（保持运行）
.venv/Scripts/python.exe run_mock_service.py
```

在另一个终端运行测试：

```bash
.venv/Scripts/python.exe test_system.py
```

如果所有测试通过，继续下一步。

### 5. 启动 Agent

```bash
.venv/Scripts/python.exe run_agent.py
```

## 使用示例

### 示例 1: 获取付费文章（自动支付）

```
👤 You: 帮我获取这篇文章 http://localhost:5000/api/article/quantum-2026

🤖 Agent 会：
1. 访问 URL
2. 检测到 402 付费墙 (0.5 USDC)
3. 检查支付策略（低于 1.0 自动批准）
4. 自动执行支付
5. 重新请求并返回内容
```

### 示例 2: 生成图片（自动支付）

```
👤 You: 用这个 API 生成一张赛博朋克风格的图片 http://localhost:5000/api/generate/image

请求体: {"prompt": "cyberpunk city"}

🤖 Agent 会自动支付 0.8 USDC 并返回生成的图片 URL
```

### 示例 3: 生成视频（需要确认）

```
👤 You: 生成一段 4K 风景视频 http://localhost:5000/api/generate/video

请求体: {"prompt": "mountain landscape"}

💰 PAYMENT APPROVAL REQUIRED
Amount: 5.0 USDC
Description: AI-Generated 10s 4K Video
Recipient: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0

Approve payment? (yes/no): yes

✅ Payment executed
🤖 Agent: 视频已生成
```

## 常见问题

### Q: Mock 服务无法启动？

确保端口 5000 没有被占用：

```bash
# Windows
netstat -ano | findstr :5000

# 如果被占用，修改 .env 中的端口
MOCK_SERVICE_PORT=5001
```

### Q: Agent 不执行支付？

检查：
1. `.env` 中的 `MAX_AUTO_APPROVE_AMOUNT` 设置
2. 服务价格是否超过限额
3. API Key 是否正确配置

### Q: 如何调整自动支付额度？

编辑 `.env`:

```env
# 提高到 2.0 USDC
MAX_AUTO_APPROVE_AMOUNT=2.0
```

### Q: 如何添加新的付费服务？

编辑 `mock-service/app.py`，参考现有端点添加新的路由。

## 目录结构说明

```
x402-agent-demo/
├── .env                    # 你的配置（不要提交到 Git）
├── .env.example            # 配置模板
├── setup.py                # 初始化脚本
├── run_mock_service.py     # 启动 Mock 服务
├── run_agent.py            # 启动 Agent
├── test_system.py          # 系统测试
│
├── mock-service/           # 模拟的 x402 付费服务
│   └── app.py             # Flask API
│
├── mcp-server/            # MCP 工具服务器（暂未使用）
│   └── server.py          # MCP 工具实现
│
└── agent-client/          # AI Agent 客户端
    └── agent.py           # Claude Agent 实现
```

## 下一步

1. **理解代码**: 阅读 `agent-client/agent.py` 了解 Agent 如何处理支付
2. **自定义服务**: 在 `mock-service/app.py` 添加你的付费 API
3. **调整策略**: 修改支付决策逻辑
4. **集成真实链**: 参考 `mcp-server/server.py` 集成真实区块链

## 注意事项

⚠️ **这是演示项目，所有支付都是模拟的！**

- 不会产生真实的区块链交易
- 测试钱包不要存入真实资金
- 生产环境需要真实的交易验证

## 获取帮助

遇到问题？查看：
- `README.md` - 完整文档
- `CLAUDE.md` - 项目设计文档
- 或直接查看代码注释
