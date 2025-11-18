from dotenv import load_dotenv, find_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.tools import Tool
import time
import os
import re
import json
import random

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
    streaming=True,
    model_name="qwen-turbo"
)

# 联网搜索功能 - 获取面试题目
def web_search(query: str) -> dict:
    """使用SerpAPI进行网络搜索，返回详细的搜索结果和来源信息"""
    try:
        print(f"[日志] 🔍 网络搜索面试题，关键词：{query}")
        
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
        raw_result = search.results(query + " 面试题")
        
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
        
        print(f"[日志] ✅ 搜索完成，找到 {len(sources)} 个面试题相关结果")
        
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

# 本地面试题库查询功能
def query_local_interview_questions(query: str) -> dict:
    """查询本地面试题库，返回结构化结果"""
    try:
        print(f"\n[日志] 📚 本地面试题库查询，关键词：{query}")
        
        # 模拟本地面试题库
        interview_questions = {
            "python": [
                "请解释Python中的GIL是什么，它对多线程编程有什么影响？",
                "Python中的装饰器是什么？请给出一个简单的例子。",
                "请描述Python中的列表推导式和生成器表达式的区别。",
                "如何在Python中处理异常？请解释try-except-finally的工作流程。",
                "Python中的深拷贝和浅拷贝有什么区别？"
            ],
            "java": [
                "Java中的接口和抽象类有什么区别？",
                "请解释Java中的垃圾回收机制。",
                "什么是Java中的线程安全？如何实现线程安全？",
                "Java中的HashMap和ConcurrentHashMap有什么区别？",
                "请解释Java中的反射机制及其应用场景。"
            ],
            "前端": [
                "请解释JavaScript中的闭包概念及其应用场景。",
                "React中的虚拟DOM是什么？它有什么优势？",
                "请描述CSS盒模型及其组成部分。",
                "Vue和React的主要区别是什么？",
                "什么是跨域问题？如何解决跨域问题？"
            ],
            "数据库": [
                "请解释SQL中的索引及其工作原理。",
                "什么是数据库事务？请解释ACID属性。",
                "NoSQL和关系型数据库有什么区别？",
                "如何优化一个慢查询SQL语句？",
                "请解释数据库范式及其作用。"
            ],
            "算法": [
                "请解释时间复杂度和空间复杂度的概念。",
                "什么是动态规划？请给出一个应用例子。",
                "请描述快速排序的工作原理及其时间复杂度。",
                "如何判断一个链表是否有环？",
                "请解释二叉树的前序、中序和后序遍历。"
            ],
            "系统设计": [
                "如何设计一个高并发的系统？",
                "微服务架构的优缺点是什么？",
                "如何保证分布式系统的一致性？",
                "请解释CAP定理及其在系统设计中的应用。",
                "如何设计一个可扩展的缓存系统？"
            ],
            "软技能": [
                "请描述一个你曾经解决的技术难题及其解决过程。",
                "如何与团队成员有效沟通和协作？",
                "你如何保持对新技术的学习和更新？",
                "请描述一个你参与的项目，以及你在其中的角色和贡献。",
                "你如何处理工作中的压力和挑战？"
            ]
        }
        
        # 根据查询关键词匹配相关题目
        matched_categories = []
        for category, questions in interview_questions.items():
            if category in query.lower() or any(keyword in query.lower() for keyword in category.lower().split()):
                matched_categories.append(category)
        
        # 如果没有匹配到特定类别，随机选择一个类别
        if not matched_categories:
            matched_categories = random.sample(list(interview_questions.keys()), 2)
        
        # 从匹配的类别中选择问题
        selected_questions = []
        for category in matched_categories:
            selected_questions.extend([(category, q) for q in interview_questions[category]])
        
        # 随机打乱问题顺序
        random.shuffle(selected_questions)
        
        # 构建结果
        if selected_questions:
            content_parts = []
            for i, (category, question) in enumerate(selected_questions[:10], 1):
                content_parts.append(f"[{category}] {question}")
            
            result_content = "\n\n".join(content_parts)
            
            return {
                "success": True,
                "content": f"从本地面试题库中找到以下相关问题：\n\n{result_content}",
                "sources": [{
                    "type": "local",
                    "file_name": "interview_questions_database",
                    "categories": matched_categories,
                    "question_count": len(content_parts)
                }],
                "total_results": len(content_parts)
            }
        else:
            return {
                "success": False,
                "content": "在本地面试题库中未找到相关问题。",
                "sources": [],
                "total_results": 0
            }
            
    except Exception as e:
        error_msg = f"本地面试题库查询失败: {str(e)}"
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
        description="用于搜索最新的IT面试题目和技术问题。当需要获取特定技术领域的面试题时使用此工具。输入：技术领域关键词"
    ),
    Tool(
        name="query_local_interview_questions", 
        func=query_local_interview_questions,
        description="用于查询本地面试题库中的问题。当需要获取常见IT面试题目时使用此工具。输入：技术领域关键词"
    )
]

# 工具调用函数
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

# 面试状态跟踪
class InterviewState(MessagesState):
    """跟踪面试状态的类"""
    question_count: int = 0  # 已提问的问题数量
    current_topic: str = ""  # 当前面试主题
    asked_questions: list = []  # 已提问的问题列表
    candidate_responses: list = []  # 候选人的回答列表
    interview_feedback: list = []  # 面试官的反馈列表
    interview_complete: bool = False  # 面试是否完成

# 智能工具选择函数
def select_and_call_tool(state):
    """智能选择工具并调用"""
    print(f"[日志] 📊 当前状态: {state}")
    
    # 获取状态信息
    question_count = state.get("question_count", 0)
    current_topic = state.get("current_topic", "")
    asked_questions = state.get("asked_questions", [])
    interview_complete = state.get("interview_complete", False)
    messages = state.get("messages", [])
    
    # 检查是否刚刚生成了问题（避免重复生成）
    if messages and "【面试官】" in messages[-1].content:
        print("[日志] ⏸️ 已生成问题，等待用户回答")
        return state  # 不生成新问题，保持当前状态
    
    # 检查面试是否已完成
    if question_count >= 8 or interview_complete:
        print("[日志] ✅ 面试已完成")
        completion_message = HumanMessage(
            content="【面试官】面试已结束，感谢您的参与！我们会尽快给您反馈。",
            additional_kwargs={"interview_complete": True}
        )
        return {
            "messages": [completion_message],
            "question_count": question_count,
            "current_topic": current_topic,
            "asked_questions": asked_questions,
            "interview_complete": True
        }
    
  # 生成新问题的逻辑（保持原有逻辑）
def evaluate_response(state):
        """评估候选人回答"""
        print(f"[日志] 🔍 评估候选人回答")
        
        # 获取状态信息
        messages = state.get("messages", [])
        question_count = state.get("question_count", 0)
        current_topic = state.get("current_topic", "")
        asked_questions = state.get("asked_questions", [])
        
        # ✅ 关键修改：只评估真实的用户回答
        if not messages:
            print("[日志] ⚠️ 没有消息需要评估")
            return state
        
        last_message = messages[-1]
        
        # 检查最后一条消息是否是用户回答（不是面试官问题）
        if "【面试官】" in last_message.content:
            print("[日志] ⚠️ 最后一条消息是面试官问题，无需评估")
            return state
        
        # 获取用户的真实回答
        candidate_answer = last_message.content
        current_question = asked_questions[-1] if asked_questions else "未知问题"
        
        # 构建评估提示
        evaluation_prompt = f"""
        面试问题：{current_question}
        候选人回答：{candidate_answer}
        
        请对候选人的回答进行专业评估，包括：
        1. 技术准确性
        2. 深度理解
        3. 实践经验
        4. 解决问题能力
        5. 表达能力
        
        给出简洁的评估反馈。
        """
        
        # 生成评估
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是专业的IT技术面试官，请对候选人的回答进行客观评估。"),
            ("human", evaluation_prompt)
        ])
        
        response = model.invoke(prompt.format_messages())
        
        # 返回评估结果
        return {
            "messages": [response],
            "question_count": question_count,
            "current_topic": current_topic,
            "asked_questions": asked_questions,
            "interview_complete": question_count >= 8
        }
        # 在文件末尾添加


def analyze_resume(state):
    """分析用户简历并生成第一个问题"""
    print(f"[日志] 📄 分析用户简历")
    
    messages = state.get("messages", [])
    if not messages:
        return state
    
    # 获取用户输入的简历内容
    user_input = messages[-1].content
    
    # 重新创建分析提示词，确保没有隐藏字符
    analysis_text = "请分析以下简历内容，并根据简历信息生成一个面试问题：\n\n"
    analysis_text += f"简历内容：\n{user_input}\n\n"
    analysis_text += "请：\n"
    analysis_text += "1. 分析候选人的技术背景和经验\n"
    analysis_text += "2. 识别关键技能和项目经验\n"
    analysis_text += "3. 生成一个针对性的开场面试问题\n"
    analysis_text += "4. 问题应该基于简历内容，具有针对性\n\n"
    analysis_text += "直接输出面试问题，格式：【面试官】问题内容"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业的IT技术面试官，擅长根据简历内容提出针对性问题。"),
        ("human", analysis_text)
    ])
    
    response = model.invoke(prompt.format_messages())
    print(f"[日志] 分析结果: {response.content}")
    return {
        "messages": [response],
        "resume_content": user_input,
        "resume_analyzed": True,
        "question_count": 1,
        "current_topic": "简历相关",
        "asked_questions": [response.content],
        "candidate_responses": [],
        "interview_feedback": [],
        "interview_complete": False
    }
def generate_next_question(state):
    """根据简历、题库和用户回答生成下一个问题"""
    print(f"[日志] 🤔 生成下一个问题")
    
    # 获取状态信息
    messages = state.get("messages", [])
    resume_content = state.get("resume_content", "")
    question_count = state.get("question_count", 0)
    asked_questions = state.get("asked_questions", [])
    candidate_responses = state.get("candidate_responses", [])
    
    # 检查是否已完成面试
    if question_count > 8:
        completion_message = AIMessage(
            content="【面试官】面试已结束，感谢您的参与！我们会尽快给您反馈。"
        )
        return {
            "messages": [completion_message],
            "resume_content": resume_content,
            "resume_analyzed": True,
            "question_count": question_count,
            "current_topic": state.get("current_topic", ""),
            "asked_questions": asked_questions,
            "candidate_responses": candidate_responses,
            "interview_feedback": state.get("interview_feedback", []),
            "interview_complete": True
        }
    
    # 获取最新的用户回答
    latest_response = ""
    if messages:
        latest_response = messages[-1].content
        candidate_responses.append(latest_response)
    
    # 从简历中提取技术关键词
    def extract_tech_keywords(resume_text):
        """从简历中提取技术关键词"""
        tech_keywords = []
        common_techs = [
            "python", "java", "javascript", "react", "vue", "spring", "django", 
            "mysql", "redis", "mongodb", "docker", "kubernetes", "aws", "git",
            "linux", "算法", "数据结构", "机器学习", "深度学习", "微服务", "分布式"
        ]
        
        resume_lower = resume_text.lower()
        for tech in common_techs:
            if tech in resume_lower:
                tech_keywords.append(tech)
        return tech_keywords
    
    # 读取题库文件
    def load_question_bank():
        """从文件中加载面试题库"""
        import os
        
        question_bank = {
            "技术问题": [],
            "行为问题": []
        }
        
        try:
            # 读取技术面试问题
            tech_file_path = os.path.join(os.path.dirname(__file__), "interview", "interview_questions.txt")
            if os.path.exists(tech_file_path):
                with open(tech_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 解析文件内容，提取问题
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('- "') and line.endswith('"'):
                            # 提取引号内的问题
                            question = line[3:-1]  # 去掉 '- "' 和 '"'
                            question_bank["技术问题"].append(question)
            
            # 读取行为面试问题
            behavior_file_path = os.path.join(os.path.dirname(__file__), "interview", "behavioral_questions.txt")
            if os.path.exists(behavior_file_path):
                with open(behavior_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 解析文件内容，提取问题
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('- "') and line.endswith('"'):
                            # 提取引号内的问题
                            question = line[3:-1]  # 去掉 '- "' 和 '"'
                            question_bank["行为问题"].append(question)
                        elif line.startswith('- "') and '" (' in line:
                            # 处理带有说明的问题，如 '- "问题内容" (说明)'
                            question = line[3:line.find('" (')]  # 提取问题部分
                            question_bank["行为问题"].append(question)
            
            print(f"[日志] 📚 成功加载题库：技术问题 {len(question_bank['技术问题'])} 个，行为问题 {len(question_bank['行为问题'])} 个")
            
        except Exception as e:
            print(f"[错误] 📚 加载题库失败：{str(e)}")
            # 如果文件读取失败，使用默认题库
            question_bank = {
                "技术问题": [
                    "请解释一下快速排序的原理。",
                    "如何在二叉搜索树中找到第k大的元素？",
                    "LRU缓存淘汰算法如何实现？"
                ],
                "行为问题": [
                    "请描述一个你遇到的最困难的技术挑战，以及你是如何解决的？",
                    "请分享一次你和团队成员发生意见分歧的经历，你们是如何达成共识的？"
                ]
            }
        
        return question_bank
    
    # 判断问题生成模式
    def determine_question_mode(latest_response, question_count):
        """判断应该使用哪种问题生成模式"""
        # 模式1：基于题库生成新问题（前3个问题或回答较简短时）
        if question_count <= 3 or len(latest_response) < 100:
            return "question_bank_mode"
        # 模式2：基于回答追问技术细节
        else:
            return "follow_up_mode"
    
    # 提取技术关键词和加载题库
    tech_keywords = extract_tech_keywords(resume_content)
    question_bank = load_question_bank()
    question_mode = determine_question_mode(latest_response, question_count)
    
    if question_mode == "question_bank_mode":
        # 模式1：基于简历与面试题库生成新问题（题库权重更高）
        print(f"[日志] 📚 使用题库模式生成问题")
        
        # 从题库中选择相关问题
        all_questions = question_bank["技术问题"] + question_bank["行为问题"]
        
        # 过滤已问过的问题
        available_questions = []
        for q in all_questions:
            # 检查问题是否已经被问过（模糊匹配）
            is_asked = False
            for asked_q in asked_questions:
                if q in asked_q or asked_q in q:
                    is_asked = True
                    break
            if not is_asked:
                available_questions.append(q)
        
        if available_questions:
            # 从可用问题中选择一个与简历最相关的
            import random
            
            # 优先选择与技术关键词相关的问题
            relevant_questions = []
            for question in available_questions:
                for keyword in tech_keywords:
                    if keyword.lower() in question.lower():
                        relevant_questions.append(question)
                        break
            
            # 如果有相关问题就从中选择，否则随机选择
            if relevant_questions:
                selected_question = random.choice(relevant_questions)
            else:
                selected_question = random.choice(available_questions)
            
            question_prompt = f"""
            基于以下信息，请优化并个性化这个面试问题：
            
            题库问题：{selected_question}
            
            技术关键词：{', '.join(tech_keywords)}
            
            要求：
            1. 保持题库问题的核心技术点
            2. 确保问题具有针对性和适当的难度
            3. 避免与之前问题重复
            
            请直接输出优化后的面试问题，格式：【面试官】问题内容
            """
        else:
            # 如果题库问题都用完了，生成新问题
            question_prompt = f"""
            基于以下信息生成一个新的面试问题：
            
            简历内容：
            {resume_content}
            
            已提问的问题：
            {chr(10).join([f"{i+1}. {q}" for i, q in enumerate(asked_questions)])}
            
            技术关键词：{', '.join(tech_keywords)}
            
            请生成第{question_count + 1}个问题，要求：
            1. 基于简历中的技术栈和项目经验
            2. 具有一定的技术深度和挑战性
            3. 避免重复之前的问题
            4. 问题应该有针对性
            
            请直接输出面试问题，格式：【面试官】问题内容
            """
    
    else:
        # 模式2：基于用户回答追问技术细节
        print(f"[日志] 🔍 使用追问模式生成问题")
        
        question_prompt = f"""
        基于候选人的最新回答，请生成一个深入的追问问题：
        
        候选人的最新回答：
        {latest_response}
        
        简历内容：
        {resume_content}
        
        已提问的问题：
        {chr(10).join([f"{i+1}. {q}" for i, q in enumerate(asked_questions)])}
        
        所有候选人回答：
        {chr(10).join([f"{i+1}. {r}" for i, r in enumerate(candidate_responses)])}
        
        请生成一个追问问题，要求：
        1. 针对候选人回答中的关键技术点进行深入追问
        2. 挖掘更多技术细节和实际应用经验
        3. 测试候选人对相关技术的深度理解
        4. 可以询问具体的实现方案、遇到的问题、解决思路等
        5. 保持问题的专业性和挑战性
        
        请直接输出追问问题，格式：【面试官】问题内容
        """
    
    # 生成问题
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业的IT技术面试官，擅长根据简历、题库和候选人回答生成高质量的面试问题。"),
        ("human", question_prompt)
    ])
    
    response = model.invoke(prompt.format_messages())
    
    # 更新状态
    new_asked_questions = asked_questions + [response.content]
    
    return {
        "messages": [response],
        "resume_content": resume_content,
        "resume_analyzed": True,
        "question_count": question_count + 1,
        "current_topic": "技术深入" if question_mode == "follow_up_mode" else "题库问题",
        "asked_questions": new_asked_questions,
        "candidate_responses": candidate_responses,
        "interview_feedback": state.get("interview_feedback", []),
        "interview_complete": False
    }
def final_evaluation(state):
    """生成最终面试评估报告"""
    print(f"[日志] 📊 生成最终面试评估报告")
    
    # 获取状态信息
    messages = state.get("messages", [])
    resume_content = state.get("resume_content", "")
    asked_questions = state.get("asked_questions", [])
    candidate_responses = state.get("candidate_responses", [])
    question_count = state.get("question_count", 0)
    
    # 构建完整的面试记录
    interview_record = ""
    for i, (question, response) in enumerate(zip(asked_questions, candidate_responses), 1):
        interview_record += f"\n问题{i}：{question}\n"
        interview_record += f"回答{i}：{response}\n"
        interview_record += "-" * 50 + "\n"
    
    # 构建评估提示词
    evaluation_prompt = f"""
    请对以下面试进行全面的专业评估：
    
    【简历信息】
    {resume_content}
    
    【面试记录】
    {interview_record}
    
    【评估要求】
    请从以下维度进行专业评估：
    
    1. **技术能力评估** (1-10分)
       - 技术知识的广度和深度
       - 对核心概念的理解程度
       - 实际项目经验的体现
    
    2. **问题解决能力** (1-10分)
       - 分析问题的逻辑性
       - 解决方案的合理性
       - 思维的清晰度
    
    3. **表达沟通能力** (1-10分)
       - 回答的条理性
       - 技术表达的准确性
       - 沟通的有效性
    
    4. **学习成长潜力** (1-10分)
       - 对新技术的接受度
       - 持续学习的意愿
       - 适应能力
    
    5. **项目经验匹配度** (1-10分)
       - 项目经验与岗位的匹配程度
       - 实际工作能力的体现
       - 团队协作经验
    
    【输出格式】
    请按以下格式输出评估结果：
    
    ## 🎯 面试评估报告
    
    ### 📊 综合评分
    - **技术能力**：X/10分 - 简要说明
    - **问题解决能力**：X/10分 - 简要说明
    - **表达沟通能力**：X/10分 - 简要说明
    - **学习成长潜力**：X/10分 - 简要说明
    - **项目经验匹配度**：X/10分 - 简要说明
    
    **总体评分：XX/50分**
    
    ### 💪 主要优势
    1. 优势点1的具体描述
    2. 优势点2的具体描述
    3. 优势点3的具体描述
    
    ### 📈 改进建议
    1. 具体的改进建议1
    2. 具体的改进建议2
    3. 具体的改进建议3
    
    ### 🎯 岗位匹配度
    **匹配度：XX%**
    
    匹配度分析：详细说明候选人与目标岗位的匹配情况
    
    ### 📝 面试官总结
    对候选人的整体印象和推荐意见
    
    ---
    
    **【面试官】感谢您参加本次技术面试！**
    
    本次面试已圆满结束。通过{question_count}轮问答，我们对您的技术能力和项目经验有了全面的了解。
    
    **面试表现总结：**
    - 面试时长：约{question_count * 3}分钟
    - 问题覆盖：技术基础、项目经验、问题解决多个维度
    - 整体表现：[根据评分给出简要评价]
    
    我们会在3-5个工作日内通过邮件或电话的方式给您反馈面试结果。如果您有任何疑问，欢迎随时联系我们。
    
    再次感谢您的时间和精彩表现，祝您工作顺利！
    """
    
    # 生成评估报告
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是资深的IT技术面试官和HR专家，具有丰富的人才评估经验。请客观、专业、详细地评估候选人的面试表现。"),
        ("human", evaluation_prompt)
    ])
    
    response = model.invoke(prompt.format_messages())
    
    print(f"[日志] ✅ 最终评估报告生成完成")
    
    # 返回最终状态
    return {
        "messages": [response],
        "resume_content": resume_content,
        "resume_analyzed": True,
        "question_count": question_count,
        "current_topic": "面试评估",
        "asked_questions": asked_questions,
        "candidate_responses": candidate_responses,
        "interview_feedback": state.get("interview_feedback", []) + [response.content],
        "interview_complete": True
    }
def route_workflow(state):
    """路由决定下一步流程"""
    print(f"[日志] 🔄 工作流路由判断")
    
    resume_analyzed = state.get("resume_analyzed", False)
    interview_complete = state.get("interview_complete", False)
    question_count = state.get("question_count", 0)
    messages = state.get("messages", [])
    
    print(f"[日志] 📊 当前状态 - 简历已分析: {resume_analyzed}, 面试完成: {interview_complete}, 问题数: {question_count}")
    print(f"[调试] 消息数量: {len(messages)}")
    
    # 状态恢复逻辑
    if len(messages) > 1 and not resume_analyzed:
        print(f"[警告] 检测到状态丢失，尝试恢复...")
        for msg in messages:
            if hasattr(msg, 'content') and "【面试官】" in str(msg.content):
                print(f"[恢复] 发现历史面试问题，恢复状态")
                state["resume_analyzed"] = True
                state["question_count"] = len([m for m in messages if "【面试官】" in str(getattr(m, 'content', ''))])
                resume_analyzed = True
                question_count = state["question_count"]
                break
    
    # ✅ 关键修改：只有明确标记完成或用户回答了第8个问题才评估
    if interview_complete:
        print(f"[日志] ✅ 面试明确标记完成，开始最终评估")
        return "final_evaluation"
    
    # 如果简历未分析，先分析简历
    if not resume_analyzed:
        print(f"[日志] 📄 需要分析简历")
        return "analyze_resume"
    
    # 检查最后一条消息的类型
    if messages:
        last_message = messages[-1]
        last_content = getattr(last_message, 'content', str(last_message))
        
        # 如果最后一条消息是面试官问题，等待用户回答
        if "【面试官】" in last_content:
            print(f"[日志] ⏸️ 等待用户回答问题")
            return "END"  # 等待用户输入
        
        # ✅ 新增：如果已经问了8个问题且用户刚回答，进入评估
        elif question_count >= 8 and not "【面试官】" in last_content:
            print(f"[日志] ✅ 第8个问题已回答，开始最终评估")
            return "final_evaluation"
        
        # 如果最后一条消息是用户回答，生成下一个问题
        else:
            print(f"[日志] 🤔 用户已回答，生成下一个问题")
            return "generate_question"
    
    # 默认情况：生成问题
    print(f"[日志] 🔄 默认生成问题")
    return "generate_question"

# 修改工作流定义
workflow = StateGraph(state_schema=InterviewState)

# 添加节点
workflow.add_node("analyze_resume", analyze_resume)
workflow.add_node("generate_question", generate_next_question)
workflow.add_node("final_evaluation", final_evaluation) 
# ✅ 关键修改：使用条件边从START开始
workflow.add_conditional_edges(
    START,
    route_workflow,  # 让路由函数决定起始节点
    {
        "analyze_resume": "analyze_resume",
        "generate_question": "generate_question",
        "final_evaluation": "final_evaluation",  # 新增路由
        "END": END
    }
)

# 添加条件边：从分析简历节点出发
workflow.add_conditional_edges(
    "analyze_resume",
    route_workflow,
    {
        "generate_question": "generate_question",
        "final_evaluation": "final_evaluation",  # 新增路由
        "END": END
    }
)

# 添加条件边：从生成问题节点出发
workflow.add_conditional_edges(
    "generate_question",
    route_workflow,
    {
        "generate_question": "generate_question",
        "final_evaluation": "final_evaluation",  # 新增路由
        "END": END
    }
)
workflow.add_edge("final_evaluation", END)

# 编译工作流
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# 添加config配置
config = {
    "configurable": {
        "session_id": time.time(),
        "thread_id": time.time()
    }
}
