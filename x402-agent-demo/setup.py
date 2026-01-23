#!/usr/bin/env python3
"""
Quick start script for x402 Agent Demo
Generates a test wallet and creates .env file
"""

from eth_account import Account
import os


def generate_wallet():
    """Generate a new Ethereum wallet for testing"""
    account = Account.create()
    return {"address": account.address, "private_key": account.key.hex()}


def create_env_file():
    """Create .env file with generated wallet"""

    if os.path.exists(".env"):
        print(
            "⚠️  .env file already exists. Please edit it manually or delete it first."
        )
        return

    print("🔑 Generating test wallet...")
    wallet = generate_wallet()

    print("\n" + "=" * 60)
    print("Generated Test Wallet:")
    print("=" * 60)
    print(f"Address: {wallet['address']}")
    print(f"Private Key: {wallet['private_key']}")
    print("\n⚠️  This is a TEST wallet for demo purposes only!")
    print("⚠️  Do NOT send real funds to this address!")
    print("=" * 60)

    # Read .env.example
    with open(".env.example", "r") as f:
        env_template = f.read()

    # Replace placeholders
    env_content = env_template.replace("your_private_key_here", wallet["private_key"])
    env_content = env_content.replace("your_wallet_address_here", wallet["address"])
    env_content = env_content.replace("your_anthropic_api_key_here", "")

    # Write .env
    with open(".env", "w") as f:
        f.write(env_content)

    print("\n✅ Created .env file")
    print("\n📝 Next steps:")
    print("1. Edit .env and add your ANTHROPIC_API_KEY")
    print("   Get one at: https://console.anthropic.com/")
    print("2. Run 'python run_mock_service.py' to start the mock service")
    print("3. Run 'python run_agent.py' to start the agent")


if __name__ == "__main__":
    create_env_file()
