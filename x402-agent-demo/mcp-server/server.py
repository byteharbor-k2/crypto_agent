"""
MCP Server for x402 Agent
Provides tools for HTTP requests with x402 detection and Web3 wallet operations
"""

import json
import logging
from typing import Any, Optional
import requests
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data
import os
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Web3 (using a test network for demo)
# For production, use actual RPC endpoint
w3 = Web3(
    Web3.HTTPProvider(
        os.getenv("WEB3_RPC_URL", "https://eth-sepolia.g.alchemy.com/v2/demo")
    )
)

# Agent's wallet (loaded from env)
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY", "")
if AGENT_PRIVATE_KEY:
    agent_account = Account.from_key(AGENT_PRIVATE_KEY)
else:
    # Generate a temporary account for demo
    agent_account = Account.create()
    logger.warning(f"⚠️  Generated temporary wallet: {agent_account.address}")
    logger.warning(f"⚠️  Private key: {agent_account.key.hex()}")

# Payment policy
MAX_AUTO_APPROVE_AMOUNT = float(os.getenv("MAX_AUTO_APPROVE_AMOUNT", "1.0"))  # USDC


class HttpRequestArgs(BaseModel):
    """Arguments for HTTP request tool"""

    url: str = Field(description="The URL to request")
    method: str = Field(default="GET", description="HTTP method (GET, POST, etc.)")
    headers: Optional[dict] = Field(default=None, description="Optional HTTP headers")
    body: Optional[dict] = Field(
        default=None, description="Optional request body for POST/PUT"
    )
    payment_proof: Optional[dict] = Field(
        default=None, description="Payment proof if already paid"
    )


class Web3PaymentArgs(BaseModel):
    """Arguments for Web3 payment tool"""

    recipient: str = Field(description="Recipient wallet address")
    amount: float = Field(description="Amount to pay in USDC")
    currency: str = Field(default="USDC", description="Currency (USDC, USDT, etc.)")
    challenge: str = Field(description="Challenge string from service")
    description: str = Field(default="", description="Payment description")


class GetBalanceArgs(BaseModel):
    """Arguments for getting wallet balance"""

    address: Optional[str] = Field(
        default=None, description="Wallet address (defaults to agent's wallet)"
    )


# Create MCP server
server = Server("x402-agent-mcp-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="http_request",
            description="Make HTTP request to a URL. Automatically detects x402 payment requirements and returns payment info.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to request"},
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE"],
                        "default": "GET",
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional HTTP headers",
                    },
                    "body": {"type": "object", "description": "Optional request body"},
                    "payment_proof": {
                        "type": "object",
                        "description": "Payment proof if already paid",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="web3_payment",
            description="Execute a Web3 payment transaction. Signs and broadcasts payment to blockchain.",
            inputSchema={
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "Recipient wallet address",
                    },
                    "amount": {"type": "number", "description": "Amount in USDC"},
                    "currency": {"type": "string", "default": "USDC"},
                    "challenge": {
                        "type": "string",
                        "description": "Challenge from service",
                    },
                    "description": {
                        "type": "string",
                        "description": "Payment description",
                    },
                },
                "required": ["recipient", "amount", "challenge"],
            },
        ),
        Tool(
            name="get_wallet_balance",
            description="Get wallet balance in ETH and USDC",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Wallet address (optional, defaults to agent wallet)",
                    }
                },
            },
        ),
        Tool(
            name="check_payment_policy",
            description="Check if a payment amount requires user approval based on policy",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Payment amount in USDC",
                    }
                },
                "required": ["amount"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    if name == "http_request":
        return await handle_http_request(arguments)
    elif name == "web3_payment":
        return await handle_web3_payment(arguments)
    elif name == "get_wallet_balance":
        return await handle_get_balance(arguments)
    elif name == "check_payment_policy":
        return await handle_check_policy(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_http_request(arguments: dict) -> list[TextContent]:
    """Handle HTTP request with x402 detection"""
    try:
        url = arguments["url"]
        method = arguments.get("method", "GET")
        headers = arguments.get("headers", {})
        body = arguments.get("body")
        payment_proof = arguments.get("payment_proof")

        # Add payment proof if provided
        if payment_proof:
            headers["X-Payment-Proof"] = json.dumps(payment_proof)

        # Make request
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=body, headers=headers)
        else:
            response = requests.request(method, url, json=body, headers=headers)

        # Check for x402 payment required
        if response.status_code == 402:
            payment_info = {
                "status": "payment_required",
                "payment_amount": response.headers.get("X-Payment-Amount"),
                "payment_currency": response.headers.get("X-Payment-Currency"),
                "payment_address": response.headers.get("X-Payment-Address"),
                "payment_challenge": response.headers.get("X-Payment-Challenge"),
                "payment_description": response.headers.get("X-Payment-Description"),
                "url": url,
                "method": method,
                "body": body,
            }

            return [TextContent(type="text", text=json.dumps(payment_info, indent=2))]

        # Success response
        result = {
            "status": "success",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.json()
            if response.headers.get("Content-Type", "").startswith("application/json")
            else response.text,
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"HTTP request error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_web3_payment(arguments: dict) -> list[TextContent]:
    """Handle Web3 payment transaction"""
    try:
        recipient = arguments["recipient"]
        amount = float(arguments["amount"])
        currency = arguments.get("currency", "USDC")
        challenge = arguments["challenge"]
        description = arguments.get("description", "")

        # For demo purposes, we simulate the payment transaction
        # In production, this would:
        # 1. Build actual USDC transfer transaction
        # 2. Sign with EIP-712
        # 3. Broadcast to blockchain
        # 4. Wait for confirmation

        # Simulate transaction hash
        tx_data = f"{agent_account.address}:{recipient}:{amount}:{challenge}"
        simulated_tx_hash = Web3.keccak(text=tx_data).hex()

        logger.info(f"💸 Payment simulated: {amount} {currency} to {recipient}")
        logger.info(f"📝 Transaction hash: {simulated_tx_hash}")

        result = {
            "status": "success",
            "tx_hash": simulated_tx_hash,
            "from": agent_account.address,
            "to": recipient,
            "amount": amount,
            "currency": currency,
            "challenge": challenge,
            "description": description,
            "note": "⚠️ This is a simulated transaction for demo purposes",
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Payment error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_get_balance(arguments: dict) -> list[TextContent]:
    """Get wallet balance"""
    try:
        address = arguments.get("address", agent_account.address)

        # For demo, return simulated balances
        # In production, query actual blockchain
        balance_info = {
            "address": address,
            "balances": {
                "ETH": "0.1",  # Simulated
                "USDC": "100.0",  # Simulated
            },
            "note": "⚠️ Simulated balances for demo",
        }

        return [TextContent(type="text", text=json.dumps(balance_info, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_check_policy(arguments: dict) -> list[TextContent]:
    """Check if payment amount requires approval"""
    try:
        amount = float(arguments["amount"])

        requires_approval = amount > MAX_AUTO_APPROVE_AMOUNT

        policy_result = {
            "amount": amount,
            "max_auto_approve": MAX_AUTO_APPROVE_AMOUNT,
            "requires_approval": requires_approval,
            "decision": "request_user_approval"
            if requires_approval
            else "auto_approve",
        }

        return [TextContent(type="text", text=json.dumps(policy_result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server

    logger.info("🚀 Starting x402 Agent MCP Server")
    logger.info(f"🔑 Agent wallet: {agent_account.address}")
    logger.info(f"💰 Max auto-approve: {MAX_AUTO_APPROVE_AMOUNT} USDC")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
