from dotenv import load_dotenv, find_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import Tool
import time
import os
import re
import json

# 尝试导入SerpAPI，如果失败则提供备选方案
try:
    from langchain_community.utilities import SerpAPIWrapper
    SERPAPI_AVAILABLE = True
except ImportError:
    print("⚠️ SerpAPI不可用，将使用内置知识回答问题")
    SERPAPI_AVAILABLE = False

_ = load_dotenv(find_dotenv())

# 配置API密钥
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

model = ChatTongyi(
    dashscope_api_key="sk-375ffc601cd642598f0cfead988f50ca",
    streaming=True,
    model_name="qwen-turbo"
)

# 联网搜索功能 - 增强版，返回详细的搜索来源信息
def web_search(query: str) -> dict:
    """使用SerpAPI进行网络搜索，返回详细的搜索结果和来源信息"""
    try:
        print(f"[日志] 🔍 网络搜索被调用，搜索内容：{query}")
        
        if not SERPAPI_AVAILABLE:
            return {
                "success": False,
                "content": "网络搜索功能暂不可用，请检查SerpAPI配置",
                "sources": [],
                "total_results": 0
            }
            
        if not SERPAPI_API_KEY:
            return {
                "success": False,
                "content": "SerpAPI密钥未配置，无法进行网络搜索",
                "sources": [],
                "total_results": 0
            }
            
        search = SerpAPIWrapper()
        # 获取原始搜索结果
        raw_result = search.results(query)
        
        # 解析搜索结果，提取详细信息
        sources = []
        content_parts = []
        
        if "organic_results" in raw_result:
            for i, result in enumerate(raw_result["organic_results"][:8]):  # 限制前8个结果
                source = {
                    "id": i + 1,
                    "title": result.get("title", "未知标题"),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", "无摘要"),
                    "displayed_link": result.get("displayed_link", ""),
                    "favicon": result.get("favicon", ""),
                    "position": result.get("position", i + 1)
                }
                sources.append(source)
                content_parts.append(f"[{i+1}] {result.get('title', '')}: {result.get('snippet', '')}")
        
        # 如果有知识图谱结果，也包含进来
        if "knowledge_graph" in raw_result:
            kg = raw_result["knowledge_graph"]
            if "description" in kg:
                content_parts.insert(0, f"知识图谱: {kg['description']}")
        
        content = "\n\n".join(content_parts)
        
        print(f"[日志] ✅ 搜索完成，找到 {len(sources)} 个结果")
        
        return {
            "success": True,
            "content": content,
            "sources": sources,
            "total_results": len(sources),
            "query": query
        }
        
    except Exception as e:
        error_msg = f"网络搜索失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "content": error_msg,
            "sources": [],
            "total_results": 0
        }

# 本地资源文件查询功能
def query_local_files(query: str) -> dict:
    """查询本地文件，返回结构化结果"""
    try:
        print(f"\n[日志] 📚 本地文件查询，关键词：{query}")
        
        # 定义专业的IT咨询数据文件路径
        possible_files = [
            # 职位和薪资数据
            "data/bytedance/bytedance_jobs_clean.json",
            "data/bytedance/company_profiles.txt", 
            "data/bytedance/data_statistics.json",
            "data/bytedance/tech_stack_trends.txt",
            
            # 简历优化资源
            "data/Tencent/tencent_jobs.txt",
            "resources/resume_keywords.txt",
            "resources/project_descriptions.txt",
            "resources/soft_skills_guide.txt",
            
            # 技术知识库
            "knowledge/programming_languages.txt",
            "knowledge/frameworks_libraries.txt",
            "knowledge/cloud_technologies.txt",
            "knowledge/devops_tools.txt",
            "knowledge/ai_ml_technologies.txt",
            
            # 面试指导
            "interview/interview_questions.txt",
            "interview/behavioral_questions.txt",
            "interview/code_challenges.txt",
            "interview/negotiation_tips.txt",
            
            # 职业发展
            "career/career_paths.txt",
            "career/skill_roadmaps.txt",
            "career/certifications.txt",
            "career/learning_resources.txt",
        ]
        
        found_content = []
        file_sources = []
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 简单的相关性匹配
                    paragraphs = content.split('\n\n')  # 按段落分割
                    relevant_info = []
                    
                    for para in paragraphs:
                        # 检查段落是否包含查询关键词
                        if any(keyword in para.lower() for keyword in query.lower().split()):
                            relevant_info.append(para.strip())
                    
                    if relevant_info:
                        found_content.extend(relevant_info)
                        file_sources.append({
                            "file_path": file_path,
                            "file_name": os.path.basename(file_path),
                            "matches": len(relevant_info)
                        })
                        print(f"[日志] ✅ 在 {file_path} 中找到相关信息")
                        
                except Exception as e:
                    print(f"[日志] ⚠️ 读取文件 {file_path} 时出错: {str(e)}")
                    continue
        
        if found_content:
            result_content = "\n\n".join(found_content)
            return {
                "success": True,
                "content": f"从本地文件中找到以下相关信息：\n\n{result_content}",
                "sources": file_sources,
                "total_results": len(file_sources)
            }
        else:
            return {
                "success": False,
                "content": "在本地文件中未找到相关信息。可能的原因：\n1. 本地文件不存在\n2. 文件中没有包含相关关键词的内容",
                "sources": [],
                "total_results": 0
            }
            
    except Exception as e:
        error_msg = f"本地文件查询失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "content": error_msg,
            "sources": [],
            "total_results": 0
        }

# 定义工具列表
tools = [
    Tool(
        name="web_search",
        func=web_search,
        description="用于搜索最新信息、新闻和实时数据。当需要获取最新信息或网络上的资料时使用此工具。输入：搜索关键词"
    ),
    Tool(
        name="query_local_files", 
        func=query_local_files,
        description="用于查询本地资源文件中的信息。当问题涉及本地存储的知识、数据或文档时使用此工具。输入：查询关键词"
    )
]

# 修改工具调用函数，返回结构化结果
def call_tools(query: str, tool_name: str) -> dict:
    """根据工具名称调用相应的工具，返回结构化结果"""
    for tool in tools:
        if tool.name == tool_name:
            return tool.func(query)  # 直接返回字典结果
    return {
        "success": False,
        "content": f"未找到工具: {tool_name}",
        "sources": [],
        "total_results": 0
    }

# 修改智能工具选择函数，简化输出
def select_and_call_tool(state: MessagesState) -> dict:
    last_message = state["messages"][-1]
    user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # 扩展关键词匹配规则
    web_keywords = ["最新", "新闻", "实时", "当前", "今天", "现在", "搜索", "查找", "网上", "招聘", "岗位", "市场行情"]
    
    local_keywords = {
        "简历": ["简历", "CV", "resume", "模板", "优化", "修改"],
        "面试": ["面试", "interview", "题目", "问题", "准备"],
        "技术": ["技术栈", "编程", "开发", "框架", "语言", "工具"],
        "职业": ["职业", "发展", "规划", "路径", "晋升", "转行"],
        "薪资": ["薪资", "工资", "待遇", "薪酬", "谈判"],
        "职位": ["职位", "岗位", "招聘", "工作", "工作机会","字节跳动职位","腾讯职位"],
    }
    
    user_input_lower = user_input.lower()
    
    # 判断是否需要使用工具
    needs_web_search = any(keyword in user_input_lower for keyword in web_keywords)
    needs_local_search = any(any(kw in user_input_lower for kw in keywords) for keywords in local_keywords.values())
    
    tool_results = []
    all_sources = []  # 存储所有搜索来源
    web_count = 0  # 网页搜索数量
    local_count = 0  # 本地文件数量
    
    if needs_web_search:
        web_result = call_tools(user_input, "web_search")
        if web_result["success"]:
            web_count = web_result.get('total_results', 0)
            # 简化工具结果，只保留核心内容
            tool_results.append(f"网络搜索结果：\n{web_result['content']}")
            # 为网络搜索来源添加类型标识
            for source in web_result.get('sources', []):
                source['type'] = 'web'
                source['search_query'] = web_result.get('query', user_input)
            all_sources.extend(web_result.get('sources', []))
        else:
            tool_results.append(f"网络搜索失败：{web_result.get('content', '未知错误')}")
    
    if needs_local_search:
        local_result = call_tools(user_input, "query_local_files")
        if local_result["success"]:
            local_count = local_result.get('total_results', 0)
            tool_results.append(f"本地文件查询结果：\n{local_result['content']}")
            # 为本地文件来源添加类型标识
            for source in local_result.get('sources', []):
                source['type'] = 'local'
            all_sources.extend(local_result.get('sources', []))
    
    # 如果使用了工具，将结果添加到消息中
    if tool_results:
        # 构建搜索统计信息
        search_stats = []
        
        search_summary = "、".join(search_stats) if search_stats else "已完成搜索"
        
        # 简化消息内容，不包含用户问题和详细搜索过程
        tool_info = "\n\n".join(tool_results)
        # 修改第292行
        enhanced_message = f""
        # 将搜索来源信息添加到消息的additional_kwargs中
        enhanced_human_message = HumanMessage(
            content=enhanced_message,
            additional_kwargs={
                "search_sources": all_sources,
                "has_sources": len(all_sources) > 0,
                "source_count": len(all_sources),
                "web_count": web_count,
                "local_count": local_count,
                "search_summary": search_summary
            }
        )
        
        return {"messages": [enhanced_human_message]}
    
    return {"messages": [last_message]}

# Define a new graph
workflow = StateGraph(state_schema=MessagesState)

# 更新的系统提示词
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", """
你是一位专业的IT职位咨询和简历咨询助手，具备以下能力：

🎯 **核心专长**：
- IT职位分析与匹配
- 简历优化与技能提升建议  
- 技术栈规划与学习路径
- 面试指导与职业发展
- 薪资谈判与职场建议

🔧 **可用工具**：
- 网络搜索：获取最新的行业信息、技术趋势、招聘需求
- 本地资源：查询专业知识库、成功案例、模板资源

💡 **回答原则**：
1. 使用专业的IT术语和行业标准
2. 提供具体可行的建议和步骤
3. 结合最新的行业趋势和技术发展
4. 给出量化的改进建议
5. 提供相关的学习资源和工具推荐
6. 如果用户给出自己的毕业院校或地区，请着重查找这个地区及其附近的职位推荐
📊 **搜索结果处理**：
- 当使用网络搜索时，在回答开头简单显示："已为您搜索 X 个网页"
- 不要在回答中显示具体的搜索链接或来源详情
- 专注于基于搜索结果提供有价值的回答内容

请根据用户的具体需求，提供专业、简洁、实用的咨询建议。
        """),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# 修改call_model函数，传递搜索来源信息
def call_model(state: MessagesState):
    prompt = prompt_template.invoke(state)
    response = model.invoke(prompt)
    
    # 检查输入消息中是否有搜索来源信息
    search_sources = []
    has_sources = False
    web_count = 0
    local_count = 0
    search_summary = ""
    
    for message in state["messages"]:
        if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
            if 'search_sources' in message.additional_kwargs:
                search_sources.extend(message.additional_kwargs['search_sources'])
                has_sources = message.additional_kwargs.get('has_sources', False)
                web_count = message.additional_kwargs.get('web_count', 0)
                local_count = message.additional_kwargs.get('local_count', 0)
                search_summary = message.additional_kwargs.get('search_summary', '')
    
    # 将搜索来源信息添加到响应消息的additional_kwargs中
    if search_sources:
        if hasattr(response, 'additional_kwargs'):
            response.additional_kwargs.update({
                "search_sources": search_sources,
                "has_sources": has_sources,
                "source_count": len(search_sources),
                "web_count": web_count,
                "local_count": local_count,
                "search_summary": search_summary
            })
        else:
            response.additional_kwargs = {
                "search_sources": search_sources,
                "has_sources": has_sources,
                "source_count": len(search_sources),
                "web_count": web_count,
                "local_count": local_count,
                "search_summary": search_summary
            }
    
    return {"messages": response}

# 添加节点和边
workflow.add_node("tool_selector", select_and_call_tool)
workflow.add_node("model", call_model)

# 设置工作流程
workflow.add_edge(START, "tool_selector")
workflow.add_edge("tool_selector", "model")

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

config = {
    "configurable": {
        "session_id": time.time(),
        "thread_id": time.time()
    }
}

# 测试函数
# 测试函数
def test_chat_with_tools(question: str):
    """测试聊天功能"""
    print(f"\n📝 测试问题：{question}")
    print("="*50)
    
    try:
        response = app.invoke(
            {"messages": [HumanMessage(content=question)]},
            config=config
        )
        
        last_message = response["messages"][-1]
        answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
        print(f"\n🤖 回答：\n{answer}")
        
        # 显示搜索统计和来源信息
        if hasattr(last_message, 'additional_kwargs') and last_message.additional_kwargs:
            kwargs = last_message.additional_kwargs
            
            # 显示搜索统计
            if 'search_summary' in kwargs:
                print(f"\n📊 搜索统计：{kwargs['search_summary']}")
            
            # 显示详细来源
            if 'search_sources' in kwargs:
                sources = kwargs['search_sources']
                if sources:
                    print(f"\n📚 详细来源 ({len(sources)}个):")
                    web_sources = [s for s in sources if s.get('type') == 'web']
                    local_sources = [s for s in sources if s.get('type') == 'local']
                    
                    if web_sources:
                        print(f"\n🌐 网页来源 ({len(web_sources)}个):")
                        for i, source in enumerate(web_sources, 1):
                            print(f"  {i}. [{source.get('title', '未知标题')}]({source.get('url', '')})")
                            print(f"     摘要: {source.get('snippet', '无摘要')[:100]}...")
                    
                    if local_sources:
                        print(f"\n📁 本地文件 ({len(local_sources)}个):")
                        for i, source in enumerate(local_sources, 1):
                            print(f"  {i}. 文件: {source.get('file_name', '未知文件')}")
                            print(f"     匹配数: {source.get('matches', 0)}")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
    
    print("="*50)

if __name__ == "__main__":
    print("🚀 IT职位咨询助手已启动...")
    print("\n📌 开始测试...")
    
    # 测试问题
    test_questions = [
        "请搜索2024年Python开发工程师的最新招聘要求",
        "查询本地文件中关于简历优化的建议",
        "我想了解前端开发的技术栈发展趋势"
    ]
    
    for question in test_questions:
        test_chat_with_tools(question)
