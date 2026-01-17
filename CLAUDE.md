# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**基于 x402 协议与 MCP 架构的自主经济 AI Agent 设计与实现**
Design and Implementation of an Autonomous Economic AI Agent Based on x402 Protocol and MCP Architecture

This is a graduation project that combines:
- **MCP (Model Context Protocol)**: Standardized protocol for AI models to call tools
- **x402 Protocol**: HTTP 402 Payment Required status code for Web3 payments
- **AI Agent**: Autonomous agent capable of detecting payment requirements and executing cryptocurrency transactions

## System Architecture

The system follows a three-layer architecture:

### 1. Frontend/Interaction Layer
- Chat interface for user task input
- User configuration for payment thresholds and whitelisted services

### 2. Core Agent Layer (Local LLM)
- Deploys open-source models (Llama 3 or Qwen) via Ollama
- Connects to MCP Server through MCP Client
- Interprets user intents and orchestrates tool calls

### 3. MCP Server Layer (Core Innovation)
Custom MCP Server providing two main tool categories:

**Web Browsing Tool**:
- Intercepts HTTP 402 responses
- Parses payment headers (price, recipient address, challenge data)
- Determines whether to proceed with payment based on budget policies

**Web3 Wallet Tool**:
- Manages private keys or integrates with OKX Wallet SDK
- Performs EIP-712 signatures for transaction intents
- Broadcasts transactions to blockchain
- Verifies transaction confirmations

### 4. Resource Service Layer (Mock Environment)
Test APIs supporting x402 protocol:
- Paid text/article API (simulates NYTimes paywall)
- Paid image generation API
- Returns 402 status with payment headers when unpaid
- Returns 200 with content after valid payment proof

## Functional Flow

1. User submits request → Agent attempts to access resource
2. Service returns HTTP 402 with payment requirements
3. Agent parses headers, checks wallet balance, evaluates price
4. If within budget threshold: auto-approve and sign transaction
5. If exceeds threshold: request user confirmation
6. After payment: retry request with payment proof
7. Service validates proof and returns content

## Payment Policy System

- **Free Payment Limit**: Small amounts auto-approved (e.g., < 1.0 USDC)
- **Budget Control**: Overall session budget limit
- **Service Whitelist**: Pre-approved service providers
- **Manual Approval**: Required for high-value transactions

## Technology Stack

### Backend
- **Python** or **TypeScript**: Primary languages
- **MCP SDK**: For building MCP client/server
- **Web3.py** or **Ethers.js**: Blockchain interaction
- **Flask/FastAPI**: Mock x402 service implementation

### AI/ML
- **Ollama**: Local LLM inference
- **Llama 3 / Qwen**: Base models with function calling capability

### Blockchain
- **EIP-712**: Typed structured data signing
- **USDT/USDC**: Stablecoin payment tokens
- **OKX Wallet SDK** (optional): For production wallet integration

## Development Timeline

- **Week 1-2**: Research x402 & MCP specifications, setup Ollama
- **Week 3-5**: Build mock x402 service (Flask/FastAPI)
- **Week 6-8**: Develop MCP Server with HTTP and wallet tools
- **Week 9-11**: System integration, prompt engineering, frontend
- **Week 12-14**: Testing scenarios (small/large amounts, insufficient balance)
- **Week 15-16**: Thesis writing and defense

## Key Implementation Notes

### For MCP Server Development
- Focus on clear tool definitions that LLMs can understand
- Implement robust error handling for network and blockchain failures
- Add detailed logging for all payment decisions
- Consider rate limiting and circuit breakers for external calls

### For Security
- **DO NOT** hardcode private keys in code - use environment variables
- Implement transaction amount validation before signing
- Add user confirmation prompts for high-value payments
- Log all payment attempts with timestamps and transaction hashes

### For Testing
- Create comprehensive test cases:
  - Small auto-approved payments
  - Large payments requiring confirmation
  - Insufficient balance scenarios
  - Invalid payment proofs
  - Network timeout handling
- Record all test interactions for thesis documentation

### Mock Service Design
- Start with simple mock services rather than trying to integrate real APIs
- Implement realistic x402 header format based on specifications
- Include various pricing tiers to test decision logic
- Simulate both instant and delayed transaction confirmations

## Important References

- **x402 Protocol**: https://docs.cdp.coinbase.com/x402/welcome
- **MCP Specification**: Anthropic's Model Context Protocol documentation
- **Google AP2**: https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol
- **Cloudflare x402**: https://blog.cloudflare.com/x402/
- **OKX x402 Guide**: https://web3.okx.com/learn/wallet-x402-how-to-trade-it

## Agent Behavior Examples

### Scenario 1: Auto-Approved Payment
```
User: "查看这篇关于量子计算的付费研报 [URL]"
Agent: 检测到付费内容，价格 0.5 USDC (低于免密额度)
      自动完成支付 (TxHash: 0x123...)
      [返回研报摘要内容]
```

### Scenario 2: Requires Confirmation
```
User: "生成一段4K风景视频"
Agent: 服务商报价 5.0 USDC (超过免密额度 1.0)
      当前余额 20 USDC，是否批准支付?
User: "批准"
Agent: 支付成功，正在处理... [返回视频]
```

## Project Success Criteria

1. Successfully intercept and parse HTTP 402 responses
2. Demonstrate autonomous payment decision-making
3. Complete end-to-end payment flow (detection → signing → verification)
4. Show different payment strategies (auto vs. manual approval)
5. Handle edge cases (insufficient funds, timeout, failed transactions)
6. Provide comprehensive documentation of architecture and security considerations
