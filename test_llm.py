import asyncio
import sys
sys.path.append('.')
from backend.llm.llm_service import LLMServiceManager

async def test():
    manager = LLMServiceManager()
    print('Available services:', manager.get_available_services())
    
    # 尝试调用process_text方法
    try:
        result = await manager.process_text("测试文本", "fix_typos")
        print("Result:", result)
    except Exception as e:
        print(f"Error calling process_text: {e}")

if __name__ == "__main__":
    asyncio.run(test())
