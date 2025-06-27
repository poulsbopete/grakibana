#!/usr/bin/env python3
"""
Environment setup script for Grafana to Kibana Converter
"""

import os
import sys
from pathlib import Path


def create_env_file():
    """Create .env file from template"""
    template_path = Path("config.env.example")
    env_path = Path(".env")
    
    if env_path.exists():
        print("⚠️  .env file already exists. Skipping creation.")
        return
    
    if not template_path.exists():
        print("❌ config.env.example not found. Creating basic .env file...")
        create_basic_env()
        return
    
    print("📝 Creating .env file from template...")
    with open(template_path, 'r') as f:
        content = f.read()
    
    with open(env_path, 'w') as f:
        f.write(content)
    
    print("✅ .env file created successfully!")


def create_basic_env():
    """Create a basic .env file"""
    content = """# LLM Configuration (Optional)
# Uncomment and set your API keys to enable LLM features
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_AI_API_KEY=your_google_ai_api_key_here

# LLM Settings
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=info
DEBUG=false

# Server Settings
HOST=0.0.0.0
PORT=8000

# File Storage
UPLOAD_DIR=uploads
DOWNLOAD_DIR=downloads
MAX_FILE_SIZE=10485760

# Security
SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# LLM Features (set to true to enable)
ENABLE_LLM_CONVERSION=false
ENABLE_SMART_QUERY_TRANSLATION=false
ENABLE_INTELLIGENT_MAPPING=false
"""
    
    with open(".env", 'w') as f:
        f.write(content)
    
    print("✅ Basic .env file created successfully!")


def install_llm_dependencies():
    """Install LLM dependencies based on user choice"""
    print("\n🤖 LLM Integration Setup")
    print("=======================")
    print("Choose your LLM provider (or press Enter to skip):")
    print("1. OpenAI (GPT-4, GPT-3.5)")
    print("2. Anthropic (Claude)")
    print("3. Google AI (Gemini)")
    print("4. Skip LLM setup")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        print("📦 Installing OpenAI dependencies...")
        os.system("pip install openai")
        print("✅ OpenAI dependencies installed!")
        print("💡 Don't forget to set OPENAI_API_KEY in your .env file")
        
    elif choice == "2":
        print("📦 Installing Anthropic dependencies...")
        os.system("pip install anthropic")
        print("✅ Anthropic dependencies installed!")
        print("💡 Don't forget to set ANTHROPIC_API_KEY in your .env file")
        
    elif choice == "3":
        print("📦 Installing Google AI dependencies...")
        os.system("pip install google-generativeai")
        print("✅ Google AI dependencies installed!")
        print("💡 Don't forget to set GOOGLE_AI_API_KEY in your .env file")
        
    elif choice == "4":
        print("⏭️  Skipping LLM setup")
        
    else:
        print("❌ Invalid choice. Skipping LLM setup.")


def main():
    """Main setup function"""
    print("🚀 Grafana to Kibana Converter Setup")
    print("====================================")
    
    # Create .env file
    create_env_file()
    
    # Install LLM dependencies
    install_llm_dependencies()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file to configure your settings")
    print("2. Set your API keys if using LLM features")
    print("3. Run: python main.py")
    print("4. Open: http://localhost:8000")


if __name__ == "__main__":
    main() 