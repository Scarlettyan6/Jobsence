document.addEventListener('DOMContentLoaded', function() {
    // 工作经历相关
    const addExperienceBtn = document.getElementById('add-experience');
    const experiencesContainer = document.getElementById('experiences-container');
    
    // 项目经验相关
    const addProjectBtn = document.getElementById('add-project');
    const projectsContainer = document.getElementById('projects-container');
    
    // 生成简历按钮
    const generateResumeBtn = document.getElementById('generate-resume');
    
    // 模板选择器
    let templateSelect = null;
    
    // 初始化函数
    function init() {

        if (!checkContainer()) return;

        // 添加工作经历（只绑定一次）
        addExperienceBtn.addEventListener('click', function() {
            const count = experiencesContainer.querySelectorAll('.experience-item').length;
            const newExperience = createExperienceItem(count);
            experiencesContainer.appendChild(newExperience);
        });
        
        // 添加项目经验（只绑定一次）
        addProjectBtn.addEventListener('click', function() {
            const count = projectsContainer.querySelectorAll('.project-item').length;
            const newProject = createProjectItem(count);
            projectsContainer.appendChild(newProject);
        });
        
        // 生成简历按钮事件
        generateResumeBtn.addEventListener('click', generateResume);
        
        // 初始化模板选择器
        initTemplateSelector();
    }
    function initTemplateSelector() {
        fetch('/api/resume-templates')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP错误: ${response.status}`);
                return response.json();
            })
            .then(templates => {
                const container = document.querySelector('.questionnaire');
                const generateBtn = document.getElementById('generate-resume');
                
                // 强化节点关系验证
                if (!container || !generateBtn || !container.contains(generateBtn)) {
                    throw new Error('DOM节点关系无效');
                }
    
                const select = document.createElement('select');
                select.id = 'template-select';
                select.className = 'template-select';
                select.innerHTML = '<option value="">选择简历模板</option>' + 
                    templates.map(t => 
                        `<option value="${t.id}">${t.name}</option>`
                    ).join('');
    
                // 安全插入
                generateBtn.parentNode.insertBefore(select, generateBtn);
                templateSelect = select;
            })
            .catch(error => {
                console.error('加载模板失败:', error);
                createFallbackTemplateSelector();
            });
    }
    function initTemplateSelector() {
        fetch('/api/resume-templates')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP错误: ${response.status}`);
                return response.json();
            })
            .then(templates => {
                const container = document.querySelector('.questionnaire');
                const generateBtn = document.getElementById('generate-resume');
                
                // 强化节点关系验证
                if (!container || !generateBtn || !container.contains(generateBtn)) {
                    throw new Error('DOM节点关系无效');
                }
    
                const select = document.createElement('select');
                select.id = 'template-select';
                select.className = 'template-select';
                select.innerHTML = '<option value="">选择简历模板</option>' + 
                    templates.map(t => 
                        `<option value="${t.id}">${t.name}</option>`
                    ).join('');
    
                // 安全插入
                generateBtn.parentNode.insertBefore(select, generateBtn);
                templateSelect = select;
            })
            .catch(error => {
                console.error('加载模板失败:', error);
                createFallbackTemplateSelector();
            });
    }
    // 创建工作经历项
    function createExperienceItem(index) {
        const div = document.createElement('div');
        div.className = 'experience-item';
        div.dataset.index = index;
        div.innerHTML = `
            <span class="remove-experience" onclick="removeExperience(${index})">×</span>
            <div class="form-group">
                <label for="company-${index}">公司名称</label>
                <input type="text" id="company-${index}" name="company-${index}" required>
            </div>
            <div class="form-group">
                <label for="position-${index}">职位</label>
                <input type="text" id="position-${index}" name="position-${index}" required>
            </div>
            <div class="form-group">
                <label for="work-period-${index}">工作时间</label>
                <input type="text" id="work-period-${index}" name="work-period-${index}" 
                       placeholder="例如: 2019.07-2022.05" required>
            </div>
            <div class="form-group">
                <label for="work-description-${index}">工作内容</label>
                <textarea id="work-description-${index}" name="work-description-${index}" 
                          placeholder="描述你的工作职责和成就..." required></textarea>
            </div>
        `;
        return div;
    }
    
    // 创建项目经验项
    function createProjectItem(index) {
        const div = document.createElement('div');
        div.className = 'project-item';
        div.dataset.index = index;
        div.innerHTML = `
            <span class="remove-project" onclick="removeProject(${index})">×</span>
            <div class="form-group">
                <label for="project-name-${index}">项目名称</label>
                <input type="text" id="project-name-${index}" name="project-name-${index}" required>
            </div>
            <div class="form-group">
                <label for="project-description-${index}">项目描述</label>
                <textarea id="project-description-${index}" name="project-description-${index}" 
                          placeholder="描述项目目标、你的角色和成果..." required></textarea>
            </div>
        `;
        return div;
    }
    
    // 全局删除函数
    window.removeExperience = function(index) {
        const item = document.querySelector(`.experience-item[data-index="${index}"]`);
        if (item) {
            item.remove();
            reindexItems('experience');
        }
    };
    
    window.removeProject = function(index) {
        const item = document.querySelector(`.project-item[data-index="${index}"]`);
        if (item) {
            item.remove();
            reindexItems('project');
        }
    };
    
    // 重新索引项目
    function reindexItems(type) {
        const container = type === 'experience' ? experiencesContainer : projectsContainer;
        const items = container.querySelectorAll(`.${type}-item`);
        const className = `.remove-${type}`;
        const funcName = `remove${type.charAt(0).toUpperCase() + type.slice(1)}`;
        
        items.forEach((item, newIndex) => {
            item.dataset.index = newIndex;
            
            // 更新删除按钮的onclick
            const removeBtn = item.querySelector(className);
            if (removeBtn) {
                removeBtn.setAttribute('onclick', `${funcName}(${newIndex})`);
            }
            
            // 更新所有输入字段的ID和name
            item.querySelectorAll('input, textarea, select, label').forEach(element => {
                if (element.tagName === 'LABEL') {
                    const oldFor = element.htmlFor;
                    if (oldFor) {
                        const parts = oldFor.split('-');
                        if (parts.length > 1) {
                            element.htmlFor = `${parts[0]}-${newIndex}`;
                        }
                    }
                } else {
                    const oldId = element.id;
                    const oldName = element.name;
                    if (oldId) {
                        const parts = oldId.split('-');
                        if (parts.length > 1) {
                            element.id = `${parts[0]}-${newIndex}`;
                        }
                    }
                    if (oldName) {
                        const parts = oldName.split('-');
                        if (parts.length > 1) {
                            element.name = `${parts[0]}-${newIndex}`;
                        }
                    }
                }
            });
        });
    }

function checkContainer() {
    const container = document.querySelector('.questionnaire');
    const generateBtn = document.getElementById('generate-resume');
    
    if (!container || !generateBtn) {
      console.error('无法找到插入点');
      return false;
    }
    return true;
  }

    //container.insertBefore(select, generateBtn);
    
    // 收集表单数据
    function collectFormData() {
        // 获取当前登录用户ID（实际应用中应从登录状态获取）
        const userId = localStorage.getItem('userId') || 'guest';
        
        return {
            userId: userId,
            templateId: templateSelect ? templateSelect.value : null,
            formData: {
                basicInfo: {
                    name: document.getElementById('full-name').value,
                    jobTitle: document.getElementById('job-title').value,
                    phone: document.getElementById('phone').value,
                    email: document.getElementById('email').value,
                    address: document.getElementById('address').value || null
                },
                education: {
                    school: document.getElementById('school').value,
                    degree: document.getElementById('degree').value,
                    major: document.getElementById('major').value,
                    period: document.getElementById('education-period').value
                },
                experiences: Array.from(document.querySelectorAll('.experience-item')).map((item, index) => ({
                    company: document.getElementById(`company-${index}`).value,
                    position: document.getElementById(`position-${index}`).value,
                    period: document.getElementById(`work-period-${index}`).value,
                    description: document.getElementById(`work-description-${index}`).value
                })),
                skills: document.getElementById('skills').value.split(',').map(skill => skill.trim()),
                projects: Array.from(document.querySelectorAll('.project-item')).map((item, index) => ({
                    name: document.getElementById(`project-name-${index}`).value,
                    description: document.getElementById(`project-description-${index}`).value
                }))
            }
        };
    }
    
    // 验证表单数据
    function validateFormData(formData) {
        if (!formData.basicInfo.name || !formData.basicInfo.jobTitle) {
            return { isValid: false, message: '姓名和求职意向是必填项' };
        }
        
        if (!formData.education.school || !formData.education.degree) {
            return { isValid: false, message: '请填写完整教育信息' };
        }
        
        return { isValid: true };
    }
    
    // 生成简历
    async function generateResume() {
        const formData = collectFormData();
        const validation = validateFormData(formData.formData);
        
        if (!validation.isValid) {
            alert(validation.message);
            return;
        }
        
        // 显示加载状态
        const previewPlaceholder = document.querySelector('.preview-placeholder');
        const resumeOutput = document.getElementById('resume-output');
        
        previewPlaceholder.innerHTML = '<div class="loading-spinner"></div><p>正在生成简历，请稍候...</p>';
        previewPlaceholder.style.display = 'block';
        resumeOutput.style.display = 'none';
        
        try {
            const response = await fetch('/api/resumes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error(await response.text());
            }
            
            const result = await response.json();
            
            if (result.success) {
                // 显示生成的简历
                previewPlaceholder.style.display = 'none';
                // 使用formatResult函数处理结果
                formatResult(result.resume.text, resumeOutput);
                resumeOutput.style.display = 'block';
                
                // 添加下载按钮
                addDownloadButton(result.resume);
            } else {
                throw new Error(result.message || '生成简历失败');
            }
        } catch (error) {
            console.error('生成简历错误:', error);
            previewPlaceholder.innerHTML = `
                <div class="error-message">
                    <i class="iconfont icon-error"></i>
                    <p>生成简历时出错: ${error.message}</p>
                    <button onclick="generateResume()">重试</button>
                </div>
            `;
        }
    }
    
    // 添加格式化结果显示函数
    function formatResult(result, outputElement) {
        // 这里可以根据返回的结果格式进行自定义处理
        // 使用marked直接渲染markdown格式
        outputElement.innerHTML = marked.parse(result);
    }
    
    // 添加下载按钮
    function addDownloadButton(resumeData) {
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'download-btn';
        downloadBtn.innerHTML = '<i class="iconfont icon-download"></i> 下载简历';
        downloadBtn.onclick = () => downloadResume(resumeData);
        
        const resumeOutput = document.getElementById('resume-output');
        resumeOutput.prepend(downloadBtn);
    }
    
    // 下载简历
    function downloadResume(resumeData) {
        // 这里可以实现PDF或其他格式的下载功能
        // 示例: 下载HTML文件
        const blob = new Blob([resumeData.html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `简历_${new Date().toISOString().slice(0, 10)}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    // 初始化应用
    init();
    
    // 检查URL参数
    function checkUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        const templateId = urlParams.get('templateId');
        
        if (templateId) {
            // 如果URL中有模板ID参数，等待模板选择器加载完成后选择对应模板
            const checkTemplateSelect = setInterval(() => {
                if (templateSelect) {
                    templateSelect.value = templateId;
                    clearInterval(checkTemplateSelect);
                }
            }, 100);
            
            // 设置5秒超时，防止无限等待
            setTimeout(() => {
                clearInterval(checkTemplateSelect);
            }, 5000);
        }
    }
});

function createFallbackTemplateSelector() {
    const container = document.querySelector('.questionnaire');
    const generateBtn = document.getElementById('generate-resume');
    
    if (!container || !generateBtn) {
        console.error('无法找到插入点');
        return;
    }
    
    const select = document.createElement('select');
    select.id = 'template-select';
    select.className = 'template-select';
    select.innerHTML = `
        <option value="">选择简历模板</option>
        <option value="1">专业商务简历</option>
        <option value="2">创意设计简历</option>
        <option value="3">IT技术简历</option>
        <option value="4">学术研究简历</option>
        <option value="5">简约风格简历</option>
        <option value="6">医疗健康简历</option>
    `;
    
    // 安全插入
    generateBtn.parentNode.insertBefore(select, generateBtn);
    templateSelect = select;
    
    // 检查URL参数
    const urlParams = new URLSearchParams(window.location.search);
    const templateId = urlParams.get('templateId');
    if (templateId) {
        select.value = templateId;
    }
}