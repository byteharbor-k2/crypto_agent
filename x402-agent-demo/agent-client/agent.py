"""
AI Agent Client with x402 Payment Capability
Uses Anthropic Claude API with MCP tools
"""

import asyncio
import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

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

    def _simulate_mcp_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        """
        Simulate MCP tool calls
        In production, this would communicate with the MCP server via stdio
        For demo, we implement the tools directly
        """
        if tool_name == "http_request":
            return self._tool_http_request(tool_input)
        elif tool_name == "web3_payment":
            return self._tool_web3_payment(tool_input)
        elif tool_name == "get_wallet_balance":
            return self._tool_get_balance(tool_input)
        elif tool_name == "check_payment_policy":
            return self._tool_check_policy(tool_input)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def _tool_http_request(self, args: dict) -> dict:
        """HTTP request tool implementation"""
        import requests

        url = args["url"]
        method = args.get("method", "GET")
        headers = args.get("headers", {})
        body = args.get("body")
        payment_proof = args.get("payment_proof")

        if payment_proof:
            headers["X-Payment-Proof"] = json.dumps(payment_proof)

        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=body, headers=headers)
            else:
                response = requests.request(method, url, json=body, headers=headers)

            if response.status_code == 402:
                return {
                    "status": "payment_required",
                    "payment_amount": response.headers.get("X-Payment-Amount"),
                    "payment_currency": response.headers.get("X-Payment-Currency"),
                    "payment_address": response.headers.get("X-Payment-Address"),
                    "payment_challenge": response.headers.get("X-Payment-Challenge"),
                    "payment_description": response.headers.get(
                        "X-Payment-Description"
                    ),
                    "url": url,
                    "method": method,
                    "body": body,
                }

            return {
                "status": "success",
                "status_code": response.status_code,
                "content": response.json()
                if "application/json" in response.headers.get("Content-Type", "")
                else response.text,
            }
        except Exception as e:
            return {"error": str(e)}

    def _tool_web3_payment(self, args: dict) -> dict:
        """Web3 payment tool implementation"""
        from web3 import Web3

        recipient = args["recipient"]
        amount = float(args["amount"])
        challenge = args["challenge"]

        # Simulate transaction (in production, actually sign and broadcast)
        tx_data = f"{AGENT_WALLET}:{recipient}:{amount}:{challenge}"
        simulated_tx_hash = Web3.keccak(text=tx_data).hex()

        print(f"\n✅ Payment executed: {amount} USDC to {recipient}")
        print(f"📝 TX Hash: {simulated_tx_hash}")

        return {
            "status": "success",
            "tx_hash": simulated_tx_hash,
            "from": AGENT_WALLET,
            "to": recipient,
            "amount": amount,
            "note": "Simulated transaction for demo",
        }

    def _tool_get_balance(self, args: dict) -> dict:
        """Get wallet balance"""
        return {
            "address": AGENT_WALLET,
            "balances": {"ETH": "0.1", "USDC": "100.0"},
            "note": "Simulated balance",
        }

    def _tool_check_policy(self, args: dict) -> dict:
        """Check payment policy"""
        amount = float(args["amount"])
        requires_approval = amount > MAX_AUTO_APPROVE_AMOUNT

        return {
            "amount": amount,
            "max_auto_approve": MAX_AUTO_APPROVE_AMOUNT,
            "requires_approval": requires_approval,
            "decision": "request_user_approval"
            if requires_approval
            else "auto_approve",
        }

    def chat(self, user_message: str) -> str:
        """Send a message and get response"""

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Define tools for Claude
        tools = [
            {
                "name": "http_request",
                "description": "Make HTTP request to a URL. Automatically detects x402 payment requirements.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to request"},
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST"],
                            "default": "GET",
                        },
                        "headers": {
                            "type": "object",
                            "description": "Optional HTTP headers",
                        },
                        "body": {
                            "type": "object",
                            "description": "Optional request body",
                        },
                        "payment_proof": {
                            "type": "object",
                            "description": "Payment proof if already paid",
                        },
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "web3_payment",
                "description": "Execute a Web3 payment transaction.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "recipient": {
                            "type": "string",
                            "description": "Recipient address",
                        },
                        "amount": {"type": "number", "description": "Amount in USDC"},
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
            },
            {
                "name": "get_wallet_balance",
                "description": "Get wallet balance",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "Wallet address (optional)",
                        }
                    },
                },
            },
            {
                "name": "check_payment_policy",
                "description": "Check if payment requires approval",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number", "description": "Payment amount"}
                    },
                    "required": ["amount"],
                },
            },
        ]

        # Call Claude API with tools
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=self._create_system_prompt(),
            tools=tools,
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

                    # Execute tool
                    tool_result = self._simulate_mcp_tool_call(tool_name, tool_input)
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
                tools=tools,
                messages=self.conversation_history,
            )

        # Final response
        final_text = ""
        for block in response.content:
            if block.type == "text":
                final_text += block.text

        self.conversation_history.append({"role": "assistant", "content": final_text})

        return final_text


def main():
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

    print("\nType 'quit' to exit\n")

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break

            if not user_input:
                continue

            response = agent.chat(user_input)
            print(f"\n🤖 Agent: {response}")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
