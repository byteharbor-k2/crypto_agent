"""
MCP Server for x402 Agent
Provides tools for HTTP requests with x402 detection and Web3 wallet operations
"""

import json
import logging
from typing import Any, Optional
from urllib.parse import urlencode
import requests
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data
import os
from pathlib import Path
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

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
X402_BAZAAR_BASE_URL = os.getenv(
    "X402_BAZAAR_BASE_URL",
    "https://api.cdp.coinbase.com/platform/v2/x402/discovery",
)
ALLOW_REAL_X402_PAYMENT = (
    os.getenv("ALLOW_REAL_X402_PAYMENT", "false").strip().lower() == "true"
)
DEFAULT_REQUEST_TIMEOUT = float(os.getenv("X402_REQUEST_TIMEOUT", "15"))


class PaymentAdapter:
    """Base class for payment execution strategies."""

    name = "base"

    def execute(self, arguments: dict) -> dict:
        raise NotImplementedError


class MockPaymentAdapter(PaymentAdapter):
    """Simulated payment adapter used by the local demo."""

    name = "mock"

    def execute(self, arguments: dict) -> dict:
        recipient = arguments["recipient"]
        amount = float(arguments["amount"])
        currency = arguments.get("currency", "USDC")
        challenge = arguments["challenge"]
        description = arguments.get("description", "")

        tx_data = f"{agent_account.address}:{recipient}:{amount}:{challenge}"
        simulated_tx_hash = Web3.keccak(text=tx_data).hex()

        logger.info(f"💸 Payment simulated: {amount} {currency} to {recipient}")
        logger.info(f"📝 Transaction hash: {simulated_tx_hash}")

        return {
            "status": "success",
            "adapter": self.name,
            "tx_hash": simulated_tx_hash,
            "from": agent_account.address,
            "to": recipient,
            "amount": amount,
            "currency": currency,
            "challenge": challenge,
            "description": description,
            "note": "⚠️ This is a simulated transaction for demo purposes",
        }


class RealX402DryRunAdapter(PaymentAdapter):
    """Dry-run adapter for real x402 services. It never signs or pays."""

    name = "real_x402_dry_run"

    def execute(self, arguments: dict) -> dict:
        return {
            "status": "dry_run_only",
            "adapter": self.name,
            "allow_real_payment": ALLOW_REAL_X402_PAYMENT,
            "message": (
                "Real x402 payment signing is intentionally disabled. "
                "Use real_x402_request to inspect payment requirements first."
            ),
            "payment_request": arguments,
        }


mock_payment_adapter = MockPaymentAdapter()
real_x402_dry_run_adapter = RealX402DryRunAdapter()


def json_response(payload: dict) -> list[TextContent]:
    """Return an MCP text content JSON response."""
    return [TextContent(type="text", text=json.dumps(payload, indent=2))]


def truncate_text(text: str, limit: int = 4000) -> str:
    """Avoid returning very large HTTP response bodies to the model."""
    if len(text) <= limit:
        return text
    return text[:limit] + f"... <truncated {len(text) - limit} chars>"


def parse_json_body(response: requests.Response) -> Any:
    """Best-effort JSON parser for HTTP responses."""
    content_type = response.headers.get("Content-Type", "")
    if "json" not in content_type.lower():
        return None
    try:
        return response.json()
    except ValueError:
        return None


def extract_x402_payment_requirements(response: requests.Response) -> dict:
    """
    Extract payment requirements from common x402-style responses.

    The local mock service uses X-Payment-* headers, while real x402 services
    usually return structured JSON bodies with accepts/paymentRequirements-like
    fields and may include x402-related response headers.
    """
    headers = dict(response.headers)
    lower_headers = {k.lower(): v for k, v in headers.items()}
    json_body = parse_json_body(response)

    header_payment = {
        "payment_required": lower_headers.get("x-payment-required"),
        "amount": lower_headers.get("x-payment-amount"),
        "currency": lower_headers.get("x-payment-currency"),
        "address": lower_headers.get("x-payment-address"),
        "challenge": lower_headers.get("x-payment-challenge"),
        "description": lower_headers.get("x-payment-description"),
    }
    header_payment = {k: v for k, v in header_payment.items() if v is not None}

    x402_headers = {
        k: v
        for k, v in headers.items()
        if k.lower().startswith(("x-payment", "x-402", "x402", "payment"))
    }

    body_requirements = {}
    if isinstance(json_body, dict):
        for key in (
            "accepts",
            "paymentRequirements",
            "payment_requirements",
            "payment",
            "x402",
            "error",
            "message",
        ):
            if key in json_body:
                body_requirements[key] = json_body[key]

    return {
        "status": "payment_required",
        "status_code": response.status_code,
        "headers": x402_headers,
        "legacy_header_requirements": header_payment,
        "body_requirements": body_requirements,
        "raw_body": truncate_text(response.text),
    }


def make_http_request(arguments: dict) -> requests.Response:
    """Execute a bounded HTTP request from MCP tools."""
    url = arguments["url"]
    method = arguments.get("method", "GET").upper()
    headers = arguments.get("headers") or {}
    body = arguments.get("body")
    timeout = float(arguments.get("timeout", DEFAULT_REQUEST_TIMEOUT))

    if method == "GET":
        return requests.get(url, headers=headers, timeout=timeout)
    if method == "POST":
        return requests.post(url, json=body, headers=headers, timeout=timeout)
    return requests.request(method, url, json=body, headers=headers, timeout=timeout)


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


class DiscoverX402ServicesArgs(BaseModel):
    """Arguments for discovering real x402 services."""

    query: Optional[str] = Field(
        default=None,
        description="Optional semantic search query. Leave empty to list resources.",
    )
    limit: int = Field(default=10, description="Maximum number of resources to return")


class RealX402RequestArgs(BaseModel):
    """Arguments for probing a real x402 endpoint."""

    url: str = Field(description="The real x402 URL to request once")
    method: str = Field(default="GET", description="HTTP method")
    headers: Optional[dict] = Field(default=None, description="Optional HTTP headers")
    body: Optional[dict] = Field(default=None, description="Optional JSON request body")
    timeout: float = Field(default=15, description="HTTP timeout in seconds")


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
        Tool(
            name="discover_x402_services",
            description="Discover real x402 services from Coinbase x402 Bazaar discovery/search APIs. This does not make payments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional semantic search query, e.g. 'crypto price data' or 'news'. Empty lists resources.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum number of resources to return.",
                    },
                },
            },
        ),
        Tool(
            name="real_x402_request",
            description="Probe a real x402 URL once and parse HTTP 402 payment requirements. This is dry-run only and never signs or pays.",
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
                    "timeout": {
                        "type": "number",
                        "default": 15,
                        "description": "HTTP timeout in seconds",
                    },
                },
                "required": ["url"],
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
    elif name == "discover_x402_services":
        return await handle_discover_x402_services(arguments)
    elif name == "real_x402_request":
        return await handle_real_x402_request(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_http_request(arguments: dict) -> list[TextContent]:
    """Handle HTTP request with x402 detection"""
    try:
        headers = arguments.get("headers") or {}
        payment_proof = arguments.get("payment_proof")

        # Add payment proof if provided
        if payment_proof:
            headers["X-Payment-Proof"] = json.dumps(payment_proof)
        arguments = {**arguments, "headers": headers}

        response = make_http_request(arguments)

        # Check for x402 payment required
        if response.status_code == 402:
            payment_info = extract_x402_payment_requirements(response)
            payment_info.update(
                {
                    "url": arguments["url"],
                    "method": arguments.get("method", "GET"),
                    "body": arguments.get("body"),
                }
            )

            return json_response(payment_info)

        # Success response
        result = {
            "status": "success",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.json()
            if response.headers.get("Content-Type", "").startswith("application/json")
            else response.text,
        }

        return json_response(result)

    except Exception as e:
        logger.error(f"HTTP request error: {e}")
        return json_response({"error": str(e)})


async def handle_web3_payment(arguments: dict) -> list[TextContent]:
    """Handle Web3 payment transaction"""
    try:
        result = mock_payment_adapter.execute(arguments)
        return json_response(result)

    except Exception as e:
        logger.error(f"Payment error: {e}")
        return json_response({"error": str(e)})


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

        return json_response(balance_info)

    except Exception as e:
        return json_response({"error": str(e)})


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

        return json_response(policy_result)

    except Exception as e:
        return json_response({"error": str(e)})


async def handle_discover_x402_services(arguments: dict) -> list[TextContent]:
    """Discover real x402 services via Coinbase x402 Bazaar."""
    try:
        query = (arguments or {}).get("query")
        limit = int((arguments or {}).get("limit", 10))
        limit = max(1, min(limit, 50))

        if query:
            endpoint = f"{X402_BAZAAR_BASE_URL.rstrip('/')}/search"
            params = {"query": query, "limit": limit}
        else:
            endpoint = f"{X402_BAZAAR_BASE_URL.rstrip('/')}/resources"
            params = {"limit": limit}

        url = endpoint + "?" + urlencode(params)
        response = requests.get(url, timeout=DEFAULT_REQUEST_TIMEOUT)
        parsed = parse_json_body(response)

        result = {
            "status": "success" if response.ok else "error",
            "source": "coinbase_x402_bazaar",
            "query": query,
            "limit": limit,
            "request_url": url,
            "status_code": response.status_code,
            "content": parsed if parsed is not None else truncate_text(response.text),
            "note": "Discovery only. This tool does not make payments.",
        }
        return json_response(result)

    except Exception as e:
        logger.error(f"x402 discovery error: {e}")
        return json_response({"status": "error", "error": str(e)})


async def handle_real_x402_request(arguments: dict) -> list[TextContent]:
    """Probe a real x402 endpoint once without signing or paying."""
    try:
        response = make_http_request(arguments)

        if response.status_code == 402:
            payment_info = extract_x402_payment_requirements(response)
            payment_info.update(
                {
                    "url": arguments["url"],
                    "method": arguments.get("method", "GET"),
                    "dry_run": True,
                    "allow_real_payment": ALLOW_REAL_X402_PAYMENT,
                    "next_step": (
                        "Show these payment requirements to the user. "
                        "Do not sign or pay until a real payment adapter is implemented and explicitly enabled."
                    ),
                    "payment_adapter": real_x402_dry_run_adapter.name,
                }
            )
            return json_response(payment_info)

        result = {
            "status": "success",
            "status_code": response.status_code,
            "url": arguments["url"],
            "method": arguments.get("method", "GET"),
            "headers": dict(response.headers),
            "content": parse_json_body(response)
            if parse_json_body(response) is not None
            else truncate_text(response.text),
            "note": "The endpoint did not return HTTP 402 on this request.",
        }
        return json_response(result)

    except Exception as e:
        logger.error(f"real x402 request error: {e}")
        return json_response({"status": "error", "error": str(e)})


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
