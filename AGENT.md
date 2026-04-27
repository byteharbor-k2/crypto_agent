# AGENT.md

This file provides guidance to coding agents when working with code in this repository.

## Project Overview

**基于 x402 协议与 MCP 架构的自主经济 AI Agent 设计与实现**
Design and Implementation of an Autonomous Economic AI Agent Based on x402 Protocol and MCP Architecture

This is a graduation project that combines:
- **MCP (Model Context Protocol)**: Standardized protocol for AI models to call tools
- **x402 Protocol**: HTTP 402 Payment Required status code for Web3 payments
- **AI Agent**: Autonomous agent capable of detecting payment requirements and executing cryptocurrency transactions

## Project Structure

```
crypto_agent/
├── AGENT.md                  # This file - project development guidelines
├── LICENSE                   # MIT License
├── README.md                 # Main documentation
│
└── x402-agent-demo/          # Demo implementation
    ├── .env                  # Environment configuration (local, git-ignored)
    ├── .env.example          # Configuration template
    ├── pyproject.toml        # Dependencies and metadata
    │
    ├── agent-client/         # AI Agent client
    │   └── agent.py          # Claude-based agent (406 lines)
    │
    ├── mcp-server/           # MCP server implementation
    │   └── server.py         # MCP tool definitions (337 lines)
    │
    ├── mock-service/         # Mock x402 payment service
    │   └── app.py            # Flask API (221 lines)
    │
    ├── setup.py              # Wallet generation & .env setup
    ├── run_mock_service.py   # Launch mock service
    ├── run_agent.py          # Launch agent CLI
    └── test_system.py        # Integration tests
```

## System Architecture

The system implements a three-layer architecture:

### 1. Interaction Layer
- CLI-based chat interface for user task input
- User configuration via environment variables
- Payment threshold and approval prompts

### 2. Core Agent Layer (Claude API)
- **AI Model**: Claude 3.5 Sonnet (via Anthropic API)
- **Tool Calling**: Uses Claude's native function calling capabilities
- **Decision Making**: Autonomous payment approval based on policies
- **Conversation Management**: Multi-turn chat with history
- **Implementation**: `agent-client/agent.py`

### 3. MCP Server Layer
Custom MCP Server providing four main tools:

**HTTP Request Tool**:
- Makes HTTP requests to services
- Intercepts HTTP 402 responses
- Parses payment headers (amount, currency, recipient, challenge)
- Returns payment requirements to agent

**Web3 Payment Tool**:
- Simulates cryptocurrency payments
- Generates transaction hashes
- (Infrastructure ready for real blockchain integration)

**Balance Query Tool**:
- Checks wallet balance
- Returns simulated ETH/USDC balances

**Payment Policy Tool**:
- Evaluates if payment needs user approval
- Checks against `MAX_AUTO_APPROVE_AMOUNT` threshold
- Returns approval recommendation

### 4. Resource Service Layer (Mock Environment)
Flask-based test APIs supporting x402 protocol:

1. **Article API** (`GET /api/article/<id>`):
   - Price: 0.5 USDC
   - Returns premium article content

2. **Image Generation API** (`POST /api/generate/image`):
   - Price: 0.8 USDC
   - Returns AI-generated image data

3. **Video Generation API** (`POST /api/generate/video`):
   - Price: 5.0 USDC (tests user confirmation flow)
   - Returns video generation result

All endpoints:
- Return HTTP 402 with x402 headers when unpaid
- Return HTTP 200 with content when valid `X-Payment-Proof` header provided

## Functional Flow

1. **User Request**: User submits task via CLI chat
2. **Agent Processing**: Claude agent analyzes request and makes HTTP call
3. **402 Detection**: Service returns HTTP 402 with x402 payment headers:
   - `X-Payment-Amount`: e.g., "0.5"
   - `X-Payment-Currency`: e.g., "USDC"
   - `X-Payment-Address`: Recipient wallet
   - `X-Payment-Challenge`: Unique request ID
   - `X-Payment-Description`: Payment purpose
4. **Policy Check**: Agent evaluates payment against threshold
5. **Decision Path**:
   - **Auto-Approve** (< 1.0 USDC): Execute payment automatically
   - **User Confirmation** (≥ 1.0 USDC): Prompt user for approval
6. **Payment Execution**: Generate transaction hash (simulated)
7. **Retry Request**: Send request with `X-Payment-Proof: <tx_hash>` header
8. **Content Delivery**: Service validates proof and returns content

## Payment Policy System

Current implementation includes:

- **Auto-Approval Threshold**: Payments < 1.0 USDC (configurable via `MAX_AUTO_APPROVE_AMOUNT`)
- **Manual Approval**: Payments ≥ 1.0 USDC require user confirmation
- **Balance Checking**: Agent verifies sufficient funds before payment
- **Transaction Logging**: All payments logged with timestamps and hashes

Future enhancements (infrastructure ready):
- Session budget limits
- Service whitelisting
- Spending history tracking
- Multiple approval strategies

## Technology Stack (Implemented)

### Core Dependencies
- **Python 3.11+**: Primary language
- **anthropic >= 0.39.0**: Claude API integration
- **mcp >= 1.0.0**: Model Context Protocol SDK
- **web3 >= 7.0.0**: Ethereum/Web3 interaction
- **eth-account >= 0.13.0**: Wallet management and signing
- **flask >= 3.0.0**: Mock service framework
- **flask-cors >= 4.0.0**: Cross-origin support
- **requests >= 2.31.0**: HTTP client
- **python-dotenv >= 1.0.0**: Environment configuration
- **pydantic >= 2.0.0**: Data validation
- **colorama >= 0.4.6**: CLI output formatting

### AI/ML
- **Claude 3.5 Sonnet**: via Anthropic API (claude-3-5-sonnet-20241022)
- **Function Calling**: Native tool use capabilities

### Blockchain
- **Simulated Payments**: Transaction hash generation (keccak256)
- **Wallet**: eth-account for key generation
- **EIP-712**: Infrastructure ready (not active in demo)
- **Network**: Sepolia testnet configuration (for future integration)

## Implementation Status

### ✅ Completed Features
- HTTP 402 detection and parsing
- x402 header extraction and processing
- Payment policy evaluation system
- Auto-approval for small payments (< 1.0 USDC)
- User confirmation prompts for large payments
- Simulated Web3 payment execution
- Mock service with multiple pricing tiers
- Claude API integration with tool calling
- MCP server infrastructure
- Multi-turn conversation support
- Balance checking system
- CLI chat interface

### 🔧 Simulated Components (Demo Mode)
- **Blockchain Transactions**: Uses keccak256 for mock tx hashes
- **Wallet Balances**: Hardcoded (0.1 ETH, 100 USDC)
- **Payment Verification**: Accepts any non-empty tx_hash
- **Tool Execution**: Local simulation instead of MCP stdio

### 🚀 Ready for Integration
- MCP server implementation (async tools defined)
- Web3.py blockchain interaction layer
- EIP-712 signing infrastructure
- Real wallet integration (via eth-account)
- Testnet deployment configuration

## Configuration

### Environment Variables

Create `.env` file in `x402-agent-demo/` directory:

```env
# Required: Claude API key
ANTHROPIC_API_KEY=sk-ant-api...

# Generated by setup.py
AGENT_PRIVATE_KEY=0x...
AGENT_WALLET_ADDRESS=0x...

# Payment Policy (optional)
MAX_AUTO_APPROVE_AMOUNT=1.0  # USDC threshold for auto-approval
SESSION_BUDGET=50.0          # Max spending per session (future)

# Network Configuration (optional)
WEB3_RPC_URL=https://sepolia.infura.io/v3/...
MOCK_SERVICE_PORT=5000
```

### Quick Start

1. **Install Dependencies**:
   ```bash
   cd x402-agent-demo
   pip install -e .
   ```

2. **Setup Environment**:
   ```bash
   python setup.py  # Generates wallet and .env file
   ```

3. **Run Mock Service** (Terminal 1):
   ```bash
   python run_mock_service.py
   ```

4. **Run Agent** (Terminal 2):
   ```bash
   python run_agent.py
   ```

5. **Test Scenarios**:
   - "查看文章ID 123" → Auto-approved (0.5 USDC)
   - "生成一张风景图片" → Auto-approved (0.8 USDC)
   - "生成一段视频" → Requires confirmation (5.0 USDC)

## Key Implementation Notes

### For Agent Development (`agent-client/agent.py`)
- Uses Claude's native function calling (tools parameter)
- Maintains conversation history for multi-turn interactions
- System prompt guides payment detection and decision-making
- Tool execution loop handles Claude's tool_use blocks
- Balance checking before payment attempts
- Colored CLI output for better UX

### For MCP Server (`mcp-server/server.py`)
- Four async tools defined with clear descriptions
- Pydantic models for type safety
- HTTP client with 402 detection logic
- Web3 payment simulation ready for real integration
- Balance query with mock data structure
- Policy evaluation based on configurable thresholds

### For Mock Service (`mock-service/app.py`)
- Three endpoints with varying price points:
  - Article: 0.5 USDC (tests auto-approval)
  - Image: 0.8 USDC (tests auto-approval)
  - Video: 5.0 USDC (tests user confirmation)
- Returns x402 headers on unpaid requests
- Validates `X-Payment-Proof` header
- CORS enabled for future web frontend

### Security Considerations
- ✅ Private keys stored in `.env` (git-ignored)
- ✅ Transaction amount validation before signing
- ✅ User confirmation prompts for high-value payments
- ✅ Payment logging with timestamps
- ⚠️ Demo uses test wallets only (not for production)
- ⚠️ No real funds required (simulated transactions)

### Testing Coverage
Implemented test scenarios:
- ✅ Small auto-approved payments (< 1.0 USDC)
- ✅ Large payments requiring confirmation (≥ 1.0 USDC)
- ✅ Balance checking before payment
- ✅ HTTP 402 detection and parsing
- ✅ Payment proof validation
- ✅ Multi-turn conversation flow

Future test cases:
- Insufficient balance scenarios
- Network timeout handling
- Invalid payment proofs
- Concurrent payment requests

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

### ✅ Achieved
1. Successfully intercept and parse HTTP 402 responses
   - Implementation: `agent-client/agent.py:execute_http_request()`
2. Demonstrate autonomous payment decision-making
   - Implementation: `agent-client/agent.py:check_payment_policy()`
3. Complete end-to-end payment flow (detection → signing → verification)
   - Flow: HTTP request → 402 detection → policy check → payment → retry
4. Show different payment strategies (auto vs. manual approval)
   - Auto: < 1.0 USDC, Manual: ≥ 1.0 USDC
5. Comprehensive documentation
   - README.md, QUICKSTART.md, code comments

### 🎯 Future Enhancements
1. Real blockchain integration (Sepolia/Mainnet)
2. Actual EIP-712 transaction signing
3. MCP stdio communication (agent ↔ server)
4. Web-based frontend interface
5. Session budget tracking
6. Service whitelisting system
7. Advanced error handling and retry logic

## Code Architecture Details

### Main Entry Points
- **`run_agent.py`**: Launch interactive agent CLI
- **`run_mock_service.py`**: Start Flask service on port 5000
- **`setup.py`**: Generate wallet and environment configuration
- **`test_system.py`**: Run integration tests

### Core Classes and Functions

**Agent Client** (`agent-client/agent.py`):
- `X402Agent` class: Main agent orchestrator
- `.chat(message)`: Process user input with Claude API
- `.execute_http_request()`: HTTP client with 402 handling
- `.execute_web3_payment()`: Payment simulation
- `.get_wallet_balance()`: Balance query
- `.check_payment_policy()`: Approval logic

**MCP Server** (`mcp-server/server.py`):
- `handle_http_request()`: Async HTTP tool
- `handle_web3_payment()`: Async payment tool
- `handle_get_balance()`: Async balance tool
- `handle_check_policy()`: Async policy tool

**Mock Service** (`mock-service/app.py`):
- `/api/article/<id>`: Article endpoint (0.5 USDC)
- `/api/generate/image`: Image endpoint (0.8 USDC)
- `/api/generate/video`: Video endpoint (5.0 USDC)
- `require_payment()`: Decorator for 402 responses

## Working with This Codebase

### Local Agent Preferences
- MarkItDown is installed globally via `uv` and available as `markitdown` (`/Users/howienew/.local/bin/markitdown`).
- Prefer `markitdown` for converting supported input files (PDF, DOCX, XLSX, HTML, CSV/JSON/XML, etc.) into Markdown before analysis or summarization in this project.
- FFmpeg is installed globally via Homebrew and available as `ffmpeg` (`/opt/homebrew/bin/ffmpeg`) for audio/video handling.

### When Adding New Features
1. **New Payment Services**: Add endpoints in `mock-service/app.py`
2. **New Tools**: Define in `mcp-server/server.py` and `agent-client/agent.py`
3. **Policy Changes**: Modify `check_payment_policy()` logic
4. **Configuration**: Add to `.env.example` and document

### When Debugging
- Check `.env` configuration first
- Verify mock service is running (port 5000)
- Enable verbose logging in Claude API calls
- Review conversation history in agent
- Test tools individually before integration

### When Testing
- Use `test_system.py` for automated checks
- Test all three price tiers (0.5, 0.8, 5.0 USDC)
- Verify both auto and manual approval flows
- Check error messages are user-friendly

## Project Achievements

This implementation successfully demonstrates:
- AI agent autonomy in financial decisions
- x402 protocol integration for Web3 payments
- MCP architecture for extensible tool systems
- Practical balance between automation and user control
- Clean separation of concerns (agent, tools, services)
- Production-ready code structure and documentation
