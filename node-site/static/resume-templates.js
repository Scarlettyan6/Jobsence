// 返回主页按钮事件
document.getElementById("btn-back").addEventListener("click", () => {
    window.location.href = "home.html";
});

// 模板数据 - 这里将来可以从服务器获取
let templates = [];

// 模板预览模态框
const templatePreviewModal = document.getElementById("template-preview-modal");
const closeBtn = templatePreviewModal.querySelector(".close");

// 关闭模态框
closeBtn.addEventListener("click", () => {
    templatePreviewModal.style.display = "none";
});

// 点击模态框外部关闭
window.addEventListener("click", (event) => {
    if (event.target === templatePreviewModal) {
        templatePreviewModal.style.display = "none";
    }
});

// 获取模板数据
function fetchTemplates() {
    // 直接使用默认模板数据
    return Promise.resolve(defaultTemplates);
}

// 渲染模板列表
function renderTemplates(templates) {
    const container = document.getElementById("templates-container");
    container.innerHTML = '';
    
    templates.forEach(template => {
        const card = document.createElement("div");
        card.className = "template-card";
        card.dataset.id = template.id;
        
        card.innerHTML = `
            <img class="template-image" src="${template.imageUrl}" alt="${template.name}">
            <div class="template-info">
                <h3>${template.name}</h3>
                <p>${template.shortDescription}</p>
                <div class="template-tags">
                    ${template.tags.map(tag => `<span class="template-tag">${tag}</span>`).join('')}
                </div>
            </div>
        `;
        
        // 点击卡片打开预览
        card.addEventListener("click", () => {
            openTemplatePreview(template);
        });
        
        container.appendChild(card);
    });
}

// 打开模板预览
function openTemplatePreview(template) {
    const previewImage = document.getElementById("preview-image");
    const previewTitle = document.getElementById("preview-title");
    const previewDescription = document.getElementById("preview-description");
    const btnDownload = document.getElementById("btn-download");
    
    previewImage.src = template.imageUrl;
    previewTitle.textContent = template.name;
    previewDescription.textContent = template.fullDescription;
    
    // 设置下载按钮链接
    btnDownload.onclick = () => {
        window.location.href = template.downloadUrl;
    };
    
    // 设置使用按钮事件
    document.getElementById("btn-use").onclick = () => {
        // 这里可以跳转到简历编辑页面，并传入模板ID
        alert(`即将使用模板：${template.name}\n该功能正在开发中，敬请期待！`);
    };
    
    templatePreviewModal.style.display = "block";
}

// 筛选模板
function filterTemplates() {
    const styleFilter = document.getElementById("style-filter").value;
    const industryFilter = document.getElementById("industry-filter").value;
    
    let filtered = [...templates];
    
    if (styleFilter !== 'all') {
        filtered = filtered.filter(template => template.style === styleFilter);
    }
    
    if (industryFilter !== 'all') {
        filtered = filtered.filter(template => template.industry === industryFilter);
    }
    
    renderTemplates(filtered);
}

// 添加筛选器事件监听
document.getElementById("style-filter").addEventListener("change", filterTemplates);
document.getElementById("industry-filter").addEventListener("change", filterTemplates);

// 默认模板数据（当API不可用时使用）
const defaultTemplates = [
    {
        id: 1,
        name: "专业商务简历",
        shortDescription: "适合商务和管理岗位的专业简历模板",
        fullDescription: "这是一个专为商务和管理岗位设计的专业简历模板。简洁大方的布局，突出您的专业经验和管理能力，适合金融、咨询、管理等领域的求职者。",
        imageUrl: "./assets/images/templates/template1.jpg",
        downloadUrl: "./assets/downloads/template1.docx",
        tags: ["专业", "商务", "管理"],
        style: "professional",
        industry: "finance"
    },
    {
        id: 2,
        name: "创意设计简历",
        shortDescription: "展示创意和设计能力的现代简历",
        fullDescription: "这是一个为设计师和创意工作者打造的现代简历模板。独特的布局和视觉元素，帮助您展示个人风格和创意能力，适合设计、广告、媒体等创意行业的求职者。",
        imageUrl: "./assets/images/templates/template2.jpg",
        downloadUrl: "./assets/downloads/template2.docx",
        tags: ["创意", "设计", "现代"],
        style: "creative",
        industry: "marketing"
    },
    {
        id: 3,
        name: "IT技术简历",
        shortDescription: "突出技术能力的程序员简历模板",
        fullDescription: "这是一个为IT专业人士设计的技术简历模板。清晰展示您的技术栈和项目经验，突出问题解决能力和技术成就，适合软件开发、数据科学、网络安全等技术岗位的求职者。",
        imageUrl: "./assets/images/templates/template3.jpg",
        downloadUrl: "./assets/downloads/template3.docx",
        tags: ["技术", "IT", "程序员"],
        style: "professional",
        industry: "it"
    },
    {
        id: 4,
        name: "学术研究简历",
        shortDescription: "适合学术和研究岗位的专业简历",
        fullDescription: "这是一个为学术和研究人员设计的专业简历模板。强调您的研究成果、发表论文和学术贡献，适合高校教师、科研人员、博士后等学术岗位的求职者。",
        imageUrl: "./assets/images/templates/template4.jpg",
        downloadUrl: "./assets/downloads/template4.docx",
        tags: ["学术", "研究", "教育"],
        style: "academic",
        industry: "education"
    },
    {
        id: 5,
        name: "简约风格简历",
        shortDescription: "干净整洁的通用型简历模板",
        fullDescription: "这是一个简约风格的通用型简历模板。干净整洁的布局，突出重点信息，适合各行各业的求职者，特别是喜欢简约风格的应聘者。",
        imageUrl: "./assets/images/templates/template5.jpg",
        downloadUrl: "./assets/downloads/template5.docx",
        tags: ["简约", "通用", "清晰"],
        style: "simple",
        industry: "all"
    },
    {
        id: 6,
        name: "医疗健康简历",
        shortDescription: "适合医疗和健康行业的专业简历",
        fullDescription: "这是一个为医疗和健康行业专业人士设计的简历模板。突出您的专业资质、临床经验和专业技能，适合医生、护士、治疗师等医疗健康领域的求职者。",
        imageUrl: "./assets/images/templates/template6.jpg",
        downloadUrl: "./assets/downloads/template6.docx",
        tags: ["医疗", "健康", "专业"],
        style: "professional",
        industry: "medical"
    }
];

// 页面加载时初始化
document.addEventListener("DOMContentLoaded", () => {
    // 获取并渲染模板
    fetchTemplates().then(data => {
        templates = data;
        renderTemplates(templates);
    });
});