"""
AI Agent Client with x402 Payment Capability
Uses Anthropic Claude API with MCP tools
"""

import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Agent configuration
MAX_AUTO_APPROVE_AMOUNT = float(os.getenv("MAX_AUTO_APPROVE_AMOUNT", "1.0"))
AGENT_WALLET = os.getenv("AGENT_WALLET_ADDRESS", "Not configured")


def get_user_approval(amount: float, description: str, recipient: str) -> bool:
    """Request user approval for payment"""
    print("\n" + "=" * 60)
    print("💰 PAYMENT APPROVAL REQUIRED")
    print("=" * 60)
    print(f"Amount: {amount} USDC")
    print(f"Description: {description}")
    print(f"Recipient: {recipient}")
    print(f"Max auto-approve limit: {MAX_AUTO_APPROVE_AMOUNT} USDC")
    print("=" * 60)

    while True:
        response = input("\nApprove payment? (yes/no): ").strip().lower()
        if response in ["yes", "y"]:
            return True
        elif response in ["no", "n"]:
            return False
        else:
            print("Please enter 'yes' or 'no'")


class X402Agent:
    """AI Agent with x402 payment capability"""

    def __init__(self):
        self.conversation_history = []
        self.pending_payment = None
        self.exit_stack = AsyncExitStack()
        self.mcp_session = None
        self.tools = []

    async def connect_mcp_server(self):
        """Start the MCP server process and load its tool definitions."""
        server_script = PROJECT_ROOT / "mcp-server" / "server.py"

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(server_script)],
            env=os.environ.copy(),
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = stdio_transport

        self.mcp_session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self.mcp_session.initialize()

        tools_result = await self.mcp_session.list_tools()
        self.tools = [self._to_anthropic_tool(tool) for tool in tools_result.tools]

        print(f"\n🔌 Connected to MCP server: {server_script}")
        print("🧰 MCP tools loaded: " + ", ".join(tool["name"] for tool in self.tools))

    async def close(self):
        """Stop the MCP server process and release streams."""
        await self.exit_stack.aclose()

    def _to_anthropic_tool(self, tool) -> dict:
        """Convert an MCP Tool object to Anthropic's tool schema."""
        input_schema = getattr(tool, "inputSchema", None)
        if input_schema is None and isinstance(tool, dict):
            input_schema = tool.get("inputSchema", {})

        return {
            "name": getattr(tool, "name", None)
            if not isinstance(tool, dict)
            else tool["name"],
            "description": getattr(tool, "description", "")
            if not isinstance(tool, dict)
            else tool.get("description", ""),
            "input_schema": input_schema or {"type": "object", "properties": {}},
        }

    def _parse_mcp_result(self, result) -> dict:
        """Return a JSON-friendly payload from an MCP tool result."""
        content_blocks = []

        for content in getattr(result, "content", []):
            if getattr(content, "type", None) == "text":
                text = content.text
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    content_blocks.append({"type": "text", "text": text})
            else:
                content_blocks.append(
                    {
                        "type": getattr(content, "type", "unknown"),
                        "data": str(content),
                    }
                )

        parsed = {"content": content_blocks}
        if getattr(result, "isError", False):
            parsed["error"] = True
        return parsed

    async def _call_mcp_tool(self, tool_name: str, tool_input: dict) -> dict:
        """Call a tool through the MCP session."""
        if self.mcp_session is None:
            raise RuntimeError("MCP server is not connected")

        result = await self.mcp_session.call_tool(tool_name, tool_input)
        return self._parse_mcp_result(result)

    def _create_system_prompt(self) -> str:
        """Create system prompt for the agent"""
        return """You are an AI assistant with the ability to autonomously access paid content and services using cryptocurrency payments.

You have access to the following tools:
1. http_request - Make HTTP requests to any URL. This tool will automatically detect if a service requires payment (HTTP 402 status).
2. web3_payment - Execute cryptocurrency payments to unlock paid content.
3. get_wallet_balance - Check your wallet balance.
4. check_payment_policy - Check if a payment requires user approval.

Payment Policy:
- Payments under {max_auto} USDC are automatically approved
- Payments above {max_auto} USDC require user confirmation
- Always check payment policy before making payments

When you encounter a 402 Payment Required response:
1. Parse the payment information (amount, recipient, description)
2. Check the payment policy to see if approval is needed
3. If auto-approved: proceed with payment automatically
4. If approval needed: explain the situation and ask the user
5. After payment, retry the request with payment proof

Always be transparent about payments and explain what you're paying for.

Your wallet address: {wallet}
""".format(max_auto=MAX_AUTO_APPROVE_AMOUNT, wallet=AGENT_WALLET)

    async def chat(self, user_message: str) -> str:
        """Send a message and get response"""

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Call Claude API with tools
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=self._create_system_prompt(),
            tools=self.tools,
            messages=self.conversation_history,
        )

        # Process response
        while response.stop_reason == "tool_use":
            # Extract tool calls
            tool_results = []
            assistant_content = []

            for block in response.content:
                if block.type == "text":
                    assistant_content.append(block)
                    if block.text:
                        print(f"\n🤖 Agent: {block.text}")

                elif block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    print(f"\n🔧 Tool Call: {tool_name}")
                    print(f"   Input: {json.dumps(tool_input, indent=2)}")

                    # Handle payment approval if needed
                    if tool_name == "web3_payment":
                        amount = float(tool_input["amount"])
                        if amount > MAX_AUTO_APPROVE_AMOUNT:
                            approved = get_user_approval(
                                amount,
                                tool_input.get("description", "Payment"),
                                tool_input["recipient"],
                            )
                            if not approved:
                                tool_result = {"error": "Payment rejected by user"}
                                tool_results.append(
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": json.dumps(tool_result),
                                    }
                                )
                                continue

                    # Execute tool through MCP
                    tool_result = await self._call_mcp_tool(tool_name, tool_input)
                    print(f"   Result: {json.dumps(tool_result, indent=2)}")

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(tool_result),
                        }
                    )

            # Add assistant message to history
            self.conversation_history.append(
                {"role": "assistant", "content": response.content}
            )

            # Add tool results
            self.conversation_history.append({"role": "user", "content": tool_results})

            # Continue conversation
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=self._create_system_prompt(),
                tools=self.tools,
                messages=self.conversation_history,
            )

        # Final response
        final_text = ""
        for block in response.content:
            if block.type == "text":
                final_text += block.text

        self.conversation_history.append({"role": "assistant", "content": final_text})

        return final_text


async def run_agent():
    """Run the agent"""
    print("=" * 60)
    print("🤖 x402 AI Agent - Autonomous Economic Agent")
    print("=" * 60)
    print(f"Wallet: {AGENT_WALLET}")
    print(f"Auto-approve limit: {MAX_AUTO_APPROVE_AMOUNT} USDC")
    print("\nThe agent can autonomously pay for content and services.")
    print(
        "Try: 'Get the premium article at http://localhost:5000/api/article/quantum-2026'"
    )
    print("=" * 60)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("Please set it in .env file")
        sys.exit(1)

    agent = X402Agent()
    try:
        await agent.connect_mcp_server()

        print("\nType 'quit' to exit\n")

        while True:
            try:
                user_input = input("\n👤 You: ").strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("\n👋 Goodbye!")
                    break

                if not user_input:
                    continue

                response = await agent.chat(user_input)
                print(f"\n🤖 Agent: {response}")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    finally:
        await agent.close()


def main():
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()
