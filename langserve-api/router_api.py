from fastapi import APIRouter
from starlette.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import AIMessageChunk,HumanMessage
from chain_wrapper import chat as chat_chain
from chain_wrapper import chat_reason as chat_chain_reason
from chain_wrapper import resume_evaluation as resume_chain
from chain_wrapper import resume_maker as resume_maker_chain
import time
import uuid

class Item(BaseModel):
    content: str
    session_id: str = None  # 添加可选的会话ID参数

router = APIRouter()

async def generate_response(content, type, session_id=None):
    # 如果没有提供session_id，生成一个新的
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # 为每个请求创建独立的配置
    request_config = {
        "configurable": {
            "session_id": session_id,
            "thread_id": session_id  # 使用相同的ID确保会话一致性
        }
    }
    
    print(f"使用会话ID: {session_id}")
    
    if type == "standard":
        app = chat_chain.app
    elif type == "reason":
        app = chat_chain_reason.app
    elif type == "resume":
        app = resume_chain.app
    elif type == "resume_maker":
        app = resume_maker_chain.app

    input_messages = [HumanMessage(content)]
    async for message_chunk, metadata in app.astream(
        {"messages": input_messages},
        config=request_config,  # 使用独立的配置
        stream_mode="messages",
    ):
        if isinstance(metadata, AIMessageChunk):
            message_str = str(message_chunk.content)
        else:
            message_str = message_chunk.content
        
        yield message_str.encode('utf-8')

@router.post("/api/chat")
async def chat(item: Item):
    print(f"传输的参数为：{item.content}, 会话ID: {item.session_id}")
    return StreamingResponse(
        generate_response(item.content, "standard", item.session_id),
        media_type="text/event-stream"
    )

@router.post("/api/chat_reason")
async def chat_reason(item: Item):
    print(f"传输的参数为：{item.content}, 会话ID: {item.session_id}")
    return StreamingResponse(
        generate_response(item.content, "reason", item.session_id),
        media_type="text/event-stream"
    )

@router.post("/api/chat_resume")
async def chat_resume(item: Item):
    print(f"传输的参数为：{item.content}, 会话ID: {item.session_id}")
    return StreamingResponse(
        generate_response(item.content, "resume", item.session_id),
        media_type="text/event-stream"
    )

@router.post("/api/chat_resume_maker")
async def chat_resume_maker(item: Item):
    print(f"传输的参数为：{item.content}, 会话ID: {item.session_id}")
    return StreamingResponse(
        generate_response(item.content, "resume_maker", item.session_id),
        media_type="text/event-stream"
    )
