// 登录和注册模态框功能
const loginModal = document.getElementById("login-modal");
const registerModal = document.getElementById("register-modal");
const btnLogin = document.getElementById("btn-login");
const btnRegister = document.getElementById("btn-register");
const closeBtns = document.getElementsByClassName("close");

// 打开登录模态框
btnLogin.addEventListener("click", () => {
    loginModal.style.display = "block";
});

// 打开注册模态框
btnRegister.addEventListener("click", () => {
    registerModal.style.display = "block";
});

// 关闭模态框
for (let i = 0; i < closeBtns.length; i++) {
    closeBtns[i].addEventListener("click", function() {
        loginModal.style.display = "none";
        registerModal.style.display = "none";
    });
}

// 点击模态框外部关闭
window.addEventListener("click", (event) => {
    if (event.target === loginModal) {
        loginModal.style.display = "none";
    }
    if (event.target === registerModal) {
        registerModal.style.display = "none";
    }
});

// 登录表单提交
document.getElementById("login-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;
    
    // 发送登录请求
    fetch("http://127.0.0.1:3000/api/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("登录成功！");
            loginModal.style.display = "none";
            // 保存登录状态
            localStorage.setItem("user", JSON.stringify(data.user));
            updateAuthUI();
        } else {
            alert("登录失败：" + data.message);
        }
    })
    .catch(error => {
        console.error("登录请求出错：", error);
        alert("登录请求出错，请稍后再试");
    });
});

// 注册表单提交
document.getElementById("register-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const username = document.getElementById("register-username").value;
    const password = document.getElementById("register-password").value;
    const confirmPassword = document.getElementById("register-confirm-password").value;
    
    if (password !== confirmPassword) {
        alert("两次输入的密码不一致！");
        return;
    }
    
    // 发送注册请求
    fetch("http://127.0.0.1:3000/api/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("注册成功！请登录");
            registerModal.style.display = "none";
            loginModal.style.display = "block";
        } else {
            alert("注册失败：" + data.message);
        }
    })
    .catch(error => {
        console.error("注册请求出错：", error);
        alert("注册请求出错，请稍后再试");
    });
});

// 更新认证UI
function updateAuthUI() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (user) {
        // 用户已登录
        btnLogin.style.display = "none";
        btnRegister.style.display = "none";
        
        // 创建用户信息和退出按钮
        const authButtons = document.querySelector(".auth-buttons");
        if (!document.getElementById("user-info")) {
            const userInfo = document.createElement("div");
            userInfo.id = "user-info";
            userInfo.innerHTML = `
                <span>欢迎，${user.username}</span>
                <button id="btn-logout">退出</button>
            `;
            authButtons.appendChild(userInfo);
            
            // 添加退出按钮事件
            document.getElementById("btn-logout").addEventListener("click", () => {
                localStorage.removeItem("user");
                location.reload();
            });
        }
    }
}



document.getElementById("resume-analysis").addEventListener("click", () => {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
        alert("请先登录后使用相关功能");
        loginModal.style.display = "block";
    } else {
        window.location.href = "resume-evaluation.html";
    }
});

document.getElementById("resume-matching").addEventListener("click", () => {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
        alert("请先登录后使用相关功能");
        loginModal.style.display = "block";
    } else {
        window.location.href = "chat.html";
    }
});

document.getElementById("resume-creation").addEventListener("click", () => {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
        alert(`请先登录后使用相关功能`);
        loginModal.style.display = "block";
    } else {
        window.location.href = "resume-maker.html";
    }
});

// 功能卡片点击事件
// 修改简历模板库点击事件，直接跳转到模板库页面
document.getElementById("sentiment-analysis").addEventListener("click", () => {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
        alert(`请先登录后使用相关功能`);
        loginModal.style.display = "block";
    } else {
        window.location.href = "resume-templates.html";
    }
});

// 检查登录状态
function checkLoginStatus(featureName) {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
        alert(`请先登录后使用相关功能`);
        loginModal.style.display = "block";
    } else {
        alert(`${featureName}功能正在开发中，敬请期待！`);
    }
}

// 移除搜索按钮点击事件
// document.getElementById("search-button").addEventListener("click", () => {
//     const searchInput = document.getElementById("search-input").value;
//     if (searchInput.trim() === "") {
//         alert("请输入搜索内容");
//         return;
//     }
//     alert(`正在搜索: ${searchInput}\n该功能正在开发中，敬请期待！`);
// });

// 页面加载时检查登录状态
document.addEventListener("DOMContentLoaded", () => {
    updateAuthUI();
});