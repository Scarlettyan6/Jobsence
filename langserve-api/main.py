#!/usr/bin/env python
from fastapi import FastAPI
from langchain.prompts import ChatPromptTemplate
from langserve import add_routes
from dotenv import load_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from router_api import router
from chain_wrapper import tagging,tagging_pure

# 1. Create prompt template
system_template = "Translate the following into {language}:"
prompt_template = ChatPromptTemplate.from_messages([
    ("system",system_template),
    ("user","{text}")
])

# 2 获取你的 API Key
load_dotenv()

# 3. Create model
model = ChatTongyi(
    streaming=True,
)

# 5. Create chain
chain = prompt_template | model 

# 6. App definition
app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple api server using Langchain's Runnable interfaces",
)

# 7. Adding chain route
add_routes(
    app,
    chain,
    path="/chain",
)

add_routes(
    app,
    tagging_pure.tagging_chain,
    path="/chain/tagging_pure",
)

add_routes(
    app,
    tagging.tagging_chain,
    path="/chain/tagging",
)


# 8. cors跨域
from fastapi.middleware.cors import CORSMiddleware
# 允许所有来源访问，允许所有方法和标头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    # allow_headers=["*"],
)

#9 加载自定义路由
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)   


"""
python serve.py

每个 LangServe 服务都带有一个简单的内置 UI，用于配置和调用应用程序，并提供流式输出和中间步骤的可见性。
前往 http://localhost:8000/chain/playground/ 试用！
传入与之前相同的输入 - {"language": "chinese", "text": "hi"} - 它应该会像以前一样做出响应。
"""