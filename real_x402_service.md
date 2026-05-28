# 真实 x402 服务调研记录

本文档用于记录当前可用于工程验证的真实 x402 / agent payment 方向。结论先行：目前最适合本地项目优先接入的是 **Coinbase x402 Bazaar discovery**，其次是 **Coinbase CDP SQL API x402** 和 **CoinStats x402**；AWS AgentCore Payments 与 Cloudflare x402 更适合作为架构参考或服务端部署方向。

## 1. AI Agent 支付基础设施

### AWS AgentCore Payments

- **真实性：真实。**
- **定位：托管式 Agent 支付基础设施。**
- **核心内容：** Amazon Bedrock AgentCore Payments 预览版支持 AI Agent 对 API、MCP Server、Web 内容和其他 Agent 进行支付。其底层支付路径集成 Coinbase x402 / CDP 钱包能力，并与 Stripe、Privy 等钱包连接能力结合。
- **工程价值：** 证明 x402 已进入 AWS 级别的托管 Agent 支付基础设施阶段；其 PaymentSession、预算上限、支出控制、支付证明和重试流程，对本项目的支付策略设计有直接参考价值。
- **当前项目可用性：中等。** 需要 AWS 账号、AgentCore、钱包配置和云端资源。短期不建议作为本地最小验证首选。
- **参考：**
  - https://aws.amazon.com/blogs/machine-learning/agents-that-transact-introducing-amazon-bedrock-agentcore-payments-built-with-coinbase-and-stripe/
  - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/payments.html
  - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/payments-connect-bazaar.html

### Cloudflare x402 内容网关

- **真实性：真实。**
- **定位：服务端内容/API 付费网关。**
- **核心内容：** Cloudflare 提供 x402 相关能力，可用于给 HTTP 内容或 Worker 服务加上付费访问层。
- **工程价值：** 适合把本项目的 Mock x402 Service 升级成一个公网可访问的真实 x402 服务端。
- **当前项目可用性：中高。** 更适合“部署自己的 x402 服务”，不是“消费现成第三方服务”。
- **参考：**
  - https://developers.cloudflare.com/agents/agentic-payments/x402/
  - https://developers.cloudflare.com/agents/agentic-payments/x402/charge-for-http-content/

## 2. 真实 x402 服务发现与 API 市场

### Coinbase x402 Bazaar

- **真实性：真实。**
- **定位：x402 资源发现层 / API 目录。**
- **核心内容：** Coinbase 提供 x402 discovery API 和 MCP Server，用于发现支持 x402 微支付的资源与工具。AWS AgentCore 文档中也引用了 Coinbase x402 Bazaar MCP Server。
- **工程价值：最高。** 可以先不支付，只做真实服务发现，把搜索结果返回给 Agent；这非常适合本地项目第一阶段接入。
- **当前项目可用性：高。**
- **建议先接入：**
  - `GET https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources`
  - `GET https://api.cdp.coinbase.com/platform/v2/x402/discovery/search?query=...`
  - `https://api.cdp.coinbase.com/platform/v2/x402/discovery/mcp`
- **参考：**
  - https://docs.cdp.coinbase.com/x402/bazaar
  - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/payments-connect-bazaar.html

### Coinbase CDP SQL API x402

- **真实性：真实。**
- **定位：真实 x402 付费 API。**
- **核心内容：** Coinbase CDP SQL API 支持 x402 付费查询，官方示例中每次查询价格约为 0.10 USDC，并使用 Base 网络上的 USDC 支付。
- **工程价值：高。** 适合作为本项目从 Mock x402 服务迁移到真实服务的验证目标。
- **当前项目可用性：高，但会涉及真实钱包和 USDC。**
- **参考：**
  - https://www.coinbase.com/developer-platform/discover/launches/sql-api-x402

### CoinStats x402 API

- **真实性：真实。**
- **定位：加密资产行情与数据 API。**
- **核心内容：** CoinStats 公开说明其部分 read-only API endpoint 支持 x402 支付，价格较低，适合小额验证。
- **工程价值：高。** 如果需要低成本真实服务验证，可优先调研。
- **当前项目可用性：中高。** 需要确认具体端点、网络和支付要求。
- **参考：**
  - https://coinstats.app/blog/openapi-x402/

## 3. 容易混淆的条目

### Gloria AI 与 Kite AI

- **修正：** 之前记录中的“Kite 实时新闻平台 / $GLORIA”表述不准确，应该拆开理解。
- **Gloria AI：** 是面向市场新闻和实时资讯的 AI 新闻终端，公开材料提到支持 Coinbase x402 framework。
- **Kite AI：** 更偏向 AI payment chain / agentic economy 基础设施，不等同于实时新闻 API 平台。
- **当前项目建议：** 先不作为核心工程验证目标，保留为后续调研项。

## 4. 本项目接入优先级

1. **Coinbase x402 Bazaar discovery**  
   先做服务发现，不涉及真实支付，风险最低。

2. **真实 x402 request 探测工具**  
   输入 URL，只请求一次，解析 HTTP 402 payment requirements，不签名、不付款。

3. **Coinbase CDP SQL API / CoinStats x402**  
   在确认钱包、网络和预算策略后，再尝试真实支付闭环。

4. **Cloudflare x402 proxy**  
   作为“部署自己的真实 x402 服务端”的方向。

5. **AWS AgentCore Payments**  
   作为大厂架构参考和后续云端托管支付方向，不作为本地最小实现第一步。
