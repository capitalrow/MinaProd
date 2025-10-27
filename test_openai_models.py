#!/usr/bin/env python3
"""Test which OpenAI models are available for this API key."""

import os
from openai import OpenAI

api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    print("❌ OPENAI_API_KEY not set")
    exit(1)

print(f"✅ API key: {api_key[:20]}...")
print()

client = OpenAI(api_key=api_key)

print("📋 Listing all available models...")
print("=" * 80)

try:
    models = client.models.list()
    model_list = [m.id for m in models.data]
    model_list.sort()
    
    print(f"Found {len(model_list)} models:")
    print()
    
    # Filter for chat models
    chat_models = [m for m in model_list if 'gpt' in m.lower()]
    
    if chat_models:
        print("🤖 Available GPT/Chat models:")
        for model in chat_models:
            print(f"  - {model}")
    else:
        print("⚠️  No GPT/chat models found!")
        print()
        print("All models:")
        for model in model_list[:20]:  # Show first 20
            print(f"  - {model}")
    
except Exception as e:
    print(f"❌ Failed to list models: {e}")
