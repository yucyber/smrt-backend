-- 创建数据库
CREATE DATABASE IF NOT EXISTS smart_editor DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE smart_editor;

-- 删除表（如果存在）以确保干净的环境
DROP TABLE IF EXISTS verification_codes;
DROP TABLE IF EXISTS document_versions;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS users;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    email VARCHAR(64) NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME DEFAULT NULL,
    role VARCHAR(20) DEFAULT 'user' COMMENT '用户角色: admin, user'
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);

-- 创建文档表
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(64) NOT NULL,
    content MEDIUMTEXT NOT NULL COMMENT '文档内容，使用HTML格式存储',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_favorite BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    is_template BOOLEAN DEFAULT FALSE,
    category VARCHAR(32) DEFAULT 'general' COMMENT '文档分类',
    word_count INT DEFAULT 0 COMMENT '字数统计',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_is_template ON documents(is_template);
CREATE INDEX idx_documents_is_favorite ON documents(is_favorite);
CREATE INDEX idx_documents_is_deleted ON documents(is_deleted);
CREATE INDEX idx_documents_category ON documents(category);

-- 创建评论表
CREATE TABLE IF NOT EXISTS comments (
    id VARCHAR(36) PRIMARY KEY,
    document_id INT NOT NULL,
    user_id INT NOT NULL,
    text TEXT NOT NULL,
    selected_text TEXT,
    range_from INT NOT NULL,
    range_to INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建评论表索引
CREATE INDEX idx_comments_document_id ON comments(document_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_comments_is_deleted ON comments(is_deleted);

-- 创建文档版本历史表
CREATE TABLE IF NOT EXISTS document_versions (
    id VARCHAR(36) PRIMARY KEY,
    document_id INT NOT NULL,
    user_id INT NOT NULL,
    version_number INT NOT NULL,
    content MEDIUMTEXT NOT NULL COMMENT '版本内容，使用HTML格式存储',
    summary VARCHAR(255) DEFAULT '' COMMENT '版本摘要或备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_current BOOLEAN DEFAULT FALSE COMMENT '是否为当前版本',
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_document_version (document_id, version_number)
);

-- 创建文档版本表索引
CREATE INDEX idx_document_versions_document_id ON document_versions(document_id);
CREATE INDEX idx_document_versions_user_id ON document_versions(user_id);
CREATE INDEX idx_document_versions_is_current ON document_versions(is_current);
CREATE INDEX idx_document_versions_created_at ON document_versions(created_at);
CREATE INDEX idx_document_versions_version_number ON document_versions(document_id, version_number);

-- 创建验证码表
CREATE TABLE IF NOT EXISTS verification_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(64) NOT NULL,
    code VARCHAR(6) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    is_used BOOLEAN DEFAULT FALSE
);

-- 创建索引
CREATE INDEX idx_verification_codes_email ON verification_codes(email);
CREATE INDEX idx_verification_codes_expires ON verification_codes(expires_at);

-- 创建初始管理员用户（专门用于系统管理）
INSERT INTO users (id, username, password_hash, email, role)
VALUES (
    1, 
    'admin',
    'pbkdf2:sha256:600000$QWGRoTfPmR96e6kk$7b23cf89b62fe1b5797f17c3729afafbfec66bc56452bd6e10dd26e833b50d0c', -- 密码为'template123'
    'admin@smarteditor.com',
    'admin'
);

-- 创建模板库管理员用户（用户ID为2，专门用于存储模板文档）
INSERT INTO users (id, username, password_hash, email, role)
VALUES (
    2, 
    'template_admin',
    'pbkdf2:sha256:600000$QWGRoTfPmR96e6kk$7b23cf89b62fe1b5797f17c3729afafbfec66bc56452bd6e10dd26e833b50d0c', -- 密码为'template123'
    'template@admin.com',
    'admin'
);

-- 添加测试用户
INSERT INTO users (username, password_hash, email, created_at)
VALUES 
(
    'test_user',
    'pbkdf2:sha256:600000$QWGRoTfPmR96e6kk$7b23cf89b62fe1b5797f17c3729afafbfec66bc56452bd6e10dd26e833b50d0c', -- 密码为'template123'
    'test@example.com',
    NOW()
),
(
    '测试用户',
    'pbkdf2:sha256:600000$6S95XU8DgMlmMl35$2cfd59d30da54e19c9e1dc678f483b652bb2a9591c716ad98a3713bcba16c6bd', -- 密码为'123456'
    'user@test.com',
    NOW()
),
(
    '示例用户',
    'pbkdf2:sha256:600000$6S95XU8DgMlmMl35$2cfd59d30da54e19c9e1dc678f483b652bb2a9591c716ad98a3713bcba16c6bd', -- 密码为'123456'
    'example@test.com',
    NOW()
);

-- 添加一些模板文档示例
INSERT INTO documents (user_id, title, content, is_favorite, is_deleted, is_template, created_at, updated_at, category, word_count)
VALUES
(2, '会议记录模板', '<h1>会议记录</h1><h2>基本信息</h2><ul><li>会议时间：</li><li>会议地点：</li><li>参会人员：</li></ul><h2>议题</h2><ol><li>议题一</li><li>议题二</li></ol><h2>讨论内容</h2><p>在这里记录讨论内容...</p><h2>结论</h2><p>在这里记录会议结论...</p><h2>后续行动项</h2><p>在这里记录需要跟进的事项...</p>', FALSE, FALSE, TRUE, NOW(), NOW(), 'template', 120),

(2, '周报模板', '<h1>周报</h1><h2>本周工作内容</h2><ol><li>工作事项一</li><li>工作事项二</li></ol><h2>工作成果</h2><p>在这里描述工作成果...</p><h2>遇到的问题</h2><p>在这里描述遇到的问题...</p><h2>下周计划</h2><p>在这里描述下周计划...</p>', FALSE, FALSE, TRUE, NOW(), NOW(), 'template', 100),

(2, '项目计划模板', '<h1>项目计划</h1><h2>项目概述</h2><p>项目名称：</p><p>项目目标：</p><p>项目周期：</p><h2>团队成员</h2><ul><li>项目经理：</li><li>开发人员：</li><li>测试人员：</li></ul><h2>里程碑</h2><ol><li>需求分析 - 完成日期：</li><li>设计阶段 - 完成日期：</li><li>开发阶段 - 完成日期：</li><li>测试阶段 - 完成日期：</li><li>上线 - 完成日期：</li></ol><h2>风险评估</h2><p>在这里描述可能的风险和应对措施...</p>', FALSE, FALSE, TRUE, NOW(), NOW(), 'template', 150),

(2, '简历模板', '<h1>个人简历</h1><h2>基本信息</h2><p>姓名：</p><p>联系电话：</p><p>电子邮箱：</p><p>教育背景：</p><h2>专业技能</h2><ul><li>技能一</li><li>技能二</li><li>技能三</li></ul><h2>工作经历</h2><h3>公司名称（工作时间段）</h3><p>职位：</p><p>工作内容：</p><h2>项目经验</h2><h3>项目名称</h3><p>项目描述：</p><p>我的职责：</p><p>项目成果：</p><h2>自我评价</h2><p>在这里进行自我评价...</p>', FALSE, FALSE, TRUE, NOW(), NOW(), 'template', 180);

-- 添加一些用户文档示例
INSERT INTO documents (user_id, title, content, is_favorite, is_deleted, is_template, created_at, updated_at, category, word_count)
VALUES
-- 测试用户的文档
(3, '我的第一个文档', '<h1>我的第一个文档</h1><p>这是我创建的第一个文档，用于测试系统功能。</p><p>可以在这里编辑更多内容...</p>', TRUE, FALSE, FALSE, NOW(), NOW(), 'general', 50),

(3, '工作计划', '<h1>2023年工作计划</h1><h2>第一季度</h2><ul><li>完成项目A的需求分析</li><li>开始项目B的研发</li></ul><h2>第二季度</h2><ul><li>完成项目B的开发</li><li>项目A进入测试阶段</li></ul><h2>下半年计划</h2><p>待定...</p>', FALSE, FALSE, FALSE, NOW(), NOW(), 'work', 120),

(3, '读书笔记', '<h1>《高效能人士的七个习惯》读书笔记</h1><h2>习惯一：积极主动</h2><p>关注圈与影响圈的概念非常实用，可以帮助我们专注于能够改变的事情...</p><h2>习惯二：以终为始</h2><p>任何事情都是先在脑海中创造，然后再在现实中创造...</p>', TRUE, FALSE, FALSE, DATE_SUB(NOW(), INTERVAL 2 DAY), NOW(), 'notes', 200),

-- 示例用户的文档
(4, '学习笔记', '<h1>JavaScript高级特性</h1><h2>Promise</h2><pre><code>const promise = new Promise((resolve, reject) => {\n  // 异步操作\n});</code></pre><p>Promise用于处理异步操作，可以避免回调地狱问题...</p><h2>async/await</h2><p>ES2017引入的新特性，使异步代码看起来像同步代码...</p>', FALSE, FALSE, FALSE, DATE_SUB(NOW(), INTERVAL 5 DAY), NOW(), 'study', 180),

(4, '项目总结', '<h1>电商平台项目总结</h1><h2>项目背景</h2><p>本项目旨在构建一个现代化的电商平台，支持多商户入驻、商品管理、订单处理等功能...</p><h2>技术栈</h2><ul><li>前端：Vue.js, Element UI</li><li>后端：Node.js, Express</li><li>数据库：MongoDB</li></ul><h2>遇到的挑战</h2><p>在开发过程中，最大的挑战是...</p>', TRUE, FALSE, FALSE, DATE_SUB(NOW(), INTERVAL 10 DAY), NOW(), 'project', 300),

(4, '会议记录', '<h1>产品迭代会议</h1><h2>时间地点</h2><p>2023年3月15日 14:00-16:00，线上会议</p><h2>参会人员</h2><p>产品经理：张三</p><p>开发负责人：李四</p><p>设计师：王五</p><h2>讨论内容</h2><ol><li>讨论了用户反馈的几个主要问题</li><li>确定了下一个迭代的主要功能</li><li>讨论了UI改进方案</li></ol><h2>结论</h2><p>下一个迭代将专注于性能优化和用户体验改进...</p>', FALSE, FALSE, FALSE, DATE_SUB(NOW(), INTERVAL 1 DAY), NOW(), 'meeting', 220),

-- 放入回收站的文档示例
(3, '废弃的想法', '<h1>产品创意</h1><p>这是一些还不成熟的产品创意，可能需要进一步思考...</p>', FALSE, TRUE, FALSE, DATE_SUB(NOW(), INTERVAL 20 DAY), DATE_SUB(NOW(), INTERVAL 10 DAY), 'ideas', 40);

-- 创建验证码示例数据
INSERT INTO verification_codes (email, code, created_at, expires_at, is_used)
VALUES
('test@example.com', '123456', NOW(), DATE_ADD(NOW(), INTERVAL 5 MINUTE), FALSE),
('user@test.com', '654321', DATE_SUB(NOW(), INTERVAL 10 MINUTE), DATE_SUB(NOW(), INTERVAL 5 MINUTE), TRUE);

-- 创建文档版本历史示例数据
INSERT INTO document_versions (id, document_id, user_id, version_number, content, summary, created_at, is_current)
VALUES
-- 为"我的第一个文档"创建版本历史
(UUID(), 1, 3, 1, '<h1>我的第一个文档</h1><p>这是初始版本的内容。</p>', '初始版本', DATE_SUB(NOW(), INTERVAL 5 DAY), FALSE),
(UUID(), 1, 3, 2, '<h1>我的第一个文档</h1><p>这是初始版本的内容。</p><p>添加了一些新内容。</p>', '添加新内容', DATE_SUB(NOW(), INTERVAL 3 DAY), FALSE),
(UUID(), 1, 3, 3, '<h1>我的第一个文档</h1><p>这是我创建的第一个文档，用于测试系统功能。</p><p>可以在这里编辑更多内容...</p>', '当前版本', NOW(), TRUE),

-- 为"工作计划"创建版本历史
(UUID(), 2, 3, 1, '<h1>2023年工作计划</h1><h2>第一季度</h2><ul><li>完成项目A的需求分析</li></ul>', '初始计划', DATE_SUB(NOW(), INTERVAL 7 DAY), FALSE),
(UUID(), 2, 3, 2, '<h1>2023年工作计划</h1><h2>第一季度</h2><ul><li>完成项目A的需求分析</li><li>开始项目B的研发</li></ul><h2>第二季度</h2><ul><li>完成项目B的开发</li><li>项目A进入测试阶段</li></ul><h2>下半年计划</h2><p>待定...</p>', '当前版本', NOW(), TRUE),

-- 为"学习笔记"创建版本历史
(UUID(), 4, 4, 1, '<h1>JavaScript高级特性</h1><h2>Promise</h2><p>Promise用于处理异步操作...</p>', '初始版本', DATE_SUB(NOW(), INTERVAL 6 DAY), FALSE),
(UUID(), 4, 4, 2, '<h1>JavaScript高级特性</h1><h2>Promise</h2><pre><code>const promise = new Promise((resolve, reject) => {
  // 异步操作
});</code></pre><p>Promise用于处理异步操作，可以避免回调地狱问题...</p><h2>async/await</h2><p>ES2017引入的新特性，使异步代码看起来像同步代码...</p>', '当前版本', NOW(), TRUE);

-- 显示创建的表结构
SHOW TABLES;

-- 显示用户表数据
SELECT id, username, LEFT(password_hash, 20) as password_preview, email, created_at, role FROM users;

-- 显示文档表数据
SELECT id, user_id, title, LEFT(content, 30) as content_preview, created_at, updated_at, 
       is_favorite, is_deleted, is_template, category, word_count 
FROM documents;

-- 显示文档版本表数据
SELECT id, document_id, user_id, version_number, LEFT(content, 30) as content_preview, 
       summary, created_at, is_current 
FROM document_versions;

-- 汇总信息
SELECT 'Total users' as info, COUNT(*) as count FROM users
UNION
SELECT 'Total documents', COUNT(*) FROM documents
UNION
SELECT 'Template documents', COUNT(*) FROM documents WHERE is_template = TRUE
UNION
SELECT 'Favorite documents', COUNT(*) FROM documents WHERE is_favorite = TRUE
UNION
SELECT 'Deleted documents', COUNT(*) FROM documents WHERE is_deleted = TRUE
UNION
SELECT 'Total document versions', COUNT(*) FROM document_versions
UNION
SELECT 'Current versions', COUNT(*) FROM document_versions WHERE is_current = TRUE;