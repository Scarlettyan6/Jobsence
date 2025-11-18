const express = require("express")
const app = express()
const bodyParser = require("body-parser")
const sqlite3 = require("sqlite3").verbose()
const bcrypt = require("bcryptjs") // 使用 bcryptjs 而不是 bcrypt
const cors = require("cors")
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const pdfParse = require('pdf-parse');

// 配置文件上传
const fileStorage = multer.diskStorage({
    destination: function (req, file, cb) {
        // 根据文件类型决定存储位置
        let uploadPath = path.join(__dirname, 'uploads');
        if (file.fieldname === 'image') {
            uploadPath = path.join(__dirname, 'static/assets/images/templates');
        } else if (file.fieldname === 'template') {
            uploadPath = path.join(__dirname, 'static/assets/downloads');
        }
        cb(null, uploadPath);
    },
    filename: function (req, file, cb) {
        // 生成唯一文件名
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        const ext = path.extname(file.originalname);
        cb(null, file.fieldname + '-' + uniqueSuffix + ext);
    }
});

const upload = multer({ storage: fileStorage });

const port = 3000

// 中间件
app.use(cors())
app.use(bodyParser.json())
app.use("/", express.static("static"))

// 创建数据库连接
const db = new sqlite3.Database("./users.db", (err) => {
  if (err) {
    console.error("数据库连接失败：", err.message)
  } else {
    console.log("已连接到 SQLite 数据库")
    // 创建用户表
    db.run(`CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`, (err) => {
      if (err) {
        console.error("创建用户表失败：", err.message)
      } else {
        console.log("用户表已创建或已存在")
      }
    })
  }
})

// 注册 API
app.post("/api/register", (req, res) => {
  const { username, password } = req.body
  
  // 验证输入
  if (!username || !password) {
    return res.status(400).json({ success: false, message: "用户名和密码不能为空" })
  }
  
  // 检查用户名是否已存在
  db.get("SELECT * FROM users WHERE username = ?", [username], (err, row) => {
    if (err) {
      return res.status(500).json({ success: false, message: "服务器错误" })
    }
    
    if (row) {
      return res.status(400).json({ success: false, message: "用户名已存在" })
    }
    
    // 加密密码
    bcrypt.hash(password, 10, (err, hash) => {
      if (err) {
        return res.status(500).json({ success: false, message: "密码加密失败" })
      }
      
      // 插入新用户
      db.run("INSERT INTO users (username, password) VALUES (?, ?)", [username, hash], function(err) {
        if (err) {
          return res.status(500).json({ success: false, message: "注册失败" })
        }
        
        res.json({ success: true, message: "注册成功" })
      })
    })
  })
})

// 登录 API
app.post("/api/login", (req, res) => {
  const { username, password } = req.body
  
  // 验证输入
  if (!username || !password) {
    return res.status(400).json({ success: false, message: "用户名和密码不能为空" })
  }
  
  // 查找用户
  db.get("SELECT * FROM users WHERE username = ?", [username], (err, user) => {
    if (err) {
      return res.status(500).json({ success: false, message: "服务器错误" })
    }
    
    if (!user) {
      return res.status(400).json({ success: false, message: "用户名或密码错误" })
    }
    
    // 验证密码
    bcrypt.compare(password, user.password, (err, result) => {
      if (err) {
        return res.status(500).json({ success: false, message: "密码验证失败" })
      }
      
      if (!result) {
        return res.status(400).json({ success: false, message: "用户名或密码错误" })
      }
      
      // 登录成功
      res.json({
        success: true,
        message: "登录成功",
        user: {
          id: user.id,
          username: user.username,
          created_at: user.created_at
        }
      })
    })
  })
})

// 在现有代码的基础上添加以下路由（主界面路由）
app.get("/", (req, res) => {
  res.redirect("/home.html");
});

app.listen(port, () => {
  console.log(`web server app listening on port ${port}`)
})

// 添加简历模板API
app.get('/api/resume-templates', (req, res) => {
    // 这里可以从数据库获取模板数据
    // 现在返回一些示例数据
    const templates = [
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
        // 其他模板数据...
    ];
    
    res.json(templates);
});

// 添加简历模板上传API
app.post('/api/upload-template', upload.fields([
    { name: 'image', maxCount: 1 },
    { name: 'template', maxCount: 1 }
]), (req, res) => {
    try {
        if (!req.files || !req.files.image || !req.files.template) {
            return res.status(400).json({ success: false, message: '请上传模板图片和文件' });
        }
        
        const imageFile = req.files.image[0];
        const templateFile = req.files.template[0];
        
        // 保存文件信息到数据库
        // 这里需要实现数据库存储逻辑
        
        // 返回成功信息
        res.json({
            success: true,
            message: '模板上传成功',
            template: {
                id: Date.now(), // 临时ID
                name: req.body.name,
                imageUrl: `/uploads/${imageFile.filename}`,
                downloadUrl: `/uploads/${templateFile.filename}`
            }
        });
    } catch (error) {
        console.error('上传模板失败:', error);
        res.status(500).json({ success: false, message: '服务器错误' });
    }
});

// 添加简历生成API
app.post('/api/resumes', async (req, res) => {
    try {
        const formData = req.body;
        
        // 将表单数据转换为简历内容字符串
        const resumeContent = generateResumeContent(formData.formData);
        
        // 调用LangServe API生成简历 - 修改这里的URL
        const response = await fetch('http://localhost:8000/api/chat_resume_maker', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: resumeContent })
        });
        
        if (!response.ok) {
            throw new Error('调用AI服务失败');
        }
        
        // 获取AI生成的简历内容
        const aiResponse = await response.text();
        
        // 根据选择的模板生成HTML
        const html = applyTemplate(aiResponse, formData.templateId || 1, formData.formData);
        
        res.json({
            success: true,
            resume: {
                html: html,
                text: aiResponse
            }
        });
    } catch (error) {
        console.error('生成简历失败:', error);
        res.status(500).json({ success: false, message: error.message || '生成简历失败' });
    }
});

// 生成简历内容字符串函数
function generateResumeContent(formData) {
    // 将表单数据转换为文本格式，供AI模型处理
    let content = `姓名: ${formData.basicInfo.name}\n`;
    content += `求职意向: ${formData.basicInfo.jobTitle}\n`;
    content += `联系方式: ${formData.basicInfo.phone} | ${formData.basicInfo.email}\n`;
    if (formData.basicInfo.address) {
        content += `现居地: ${formData.basicInfo.address}\n`;
    }
    
    content += `\n教育背景:\n`;
    content += `${formData.education.school} | ${formData.education.degree} | ${formData.education.major} | ${formData.education.period}\n`;
    
    if (formData.experiences && formData.experiences.length > 0) {
        content += `\n工作经历:\n`;
        formData.experiences.forEach(exp => {
            content += `${exp.company} | ${exp.position} | ${exp.period}\n`;
            content += `工作内容: ${exp.description}\n`;
        });
    }
    
    if (formData.skills && formData.skills.length > 0) {
        content += `\n技能专长:\n${formData.skills.join(', ')}\n`;
    }
    
    if (formData.projects && formData.projects.length > 0) {
        content += `\n项目经验:\n`;
        formData.projects.forEach(project => {
            content += `${project.name}\n`;
            content += `项目描述: ${project.description}\n`;
        });
    }
    
    return content;
}

// 应用模板函数
function applyTemplate(aiContent, templateId, formData) {
    // 这里可以根据不同的模板ID应用不同的HTML样式
    // 简单示例：将AI内容包装在基本HTML中
    const basicInfo = formData.basicInfo;
    
    let html = `
    <div class="resume-container template-${templateId}">
        <div class="resume-header">
            <h1>${basicInfo.name}</h1>
            <p class="job-title">${basicInfo.jobTitle}</p>
            <p class="contact-info">${basicInfo.phone} | ${basicInfo.email}</p>
            ${basicInfo.address ? `<p class="address">${basicInfo.address}</p>` : ''}
        </div>
        <div class="resume-content">
            <div id="formatted-content"></div>
        </div>
    </div>
    `;
    
    return html;
}

// 添加PDF解析API
app.post('/api/extract-pdf', upload.single('resume'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ success: false, message: '请上传PDF文件' });
        }

        // 检查文件类型
        if (req.file.mimetype !== 'application/pdf') {
            return res.status(400).json({ success: false, message: '请上传PDF格式的文件' });
        }

        const dataBuffer = fs.readFileSync(req.file.path);
        
        // 解析PDF文件
        const pdfData = await pdfParse(dataBuffer);
        
        // 返回提取的文本
        res.json({
            success: true,
            text: pdfData.text,
            filename: req.file.originalname
        });
    } catch (error) {
        console.error('PDF解析失败:', error);
        res.status(500).json({ success: false, message: '解析PDF失败' });
    }
});


