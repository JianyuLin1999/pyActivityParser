# PyActivityParser GitHub 上传指南

## 步骤一：创建 GitHub 仓库

### 1.1 登录 GitHub
1. 打开 [GitHub.com](https://github.com)
2. 登录你的账户

### 1.2 创建新仓库
1. 点击右上角的 "+" 号，选择 "New repository"
2. 填写仓库信息：
   - **Repository name**: `PyActivityParser` 
   - **Description**: `A Python implementation for accelerometer data analysis inspired by ActivityParser`
   - **Visibility**: 选择 Public（公开）或 Private（私有）
   - **Initialize**: 不要勾选任何选项（因为本地已有文件）
3. 点击 "Create repository"

## 步骤二：本地 Git 初始化

### 2.1 打开终端
在 PyActivityParser 项目目录中打开终端：
```bash
cd /Users/jianyulin/Desktop/ActivityParser-main/PyActivityParser
```

### 2.2 初始化 Git 仓库
```bash
# 初始化 Git 仓库
git init

# 添加所有文件到暂存区
git add .

# 查看文件状态（可选）
git status

# 创建初始提交
git commit -m "Initial commit: PyActivityParser accelerometer data analysis tool

- Implemented six-stage analysis pipeline inspired by ActivityParser
- Added CSV data loader with metadata parsing
- Implemented core analysis (wear detection, activity classification)
- Added quality assessment and activity pattern analysis
- Implemented sleep analysis and report generation
- Included example scripts and comprehensive documentation"
```

## 步骤三：连接远程仓库

### 3.1 添加远程仓库
```bash
# 添加远程仓库（替换 yourusername 为你的 GitHub 用户名）
git remote add origin https://github.com/yourusername/PyActivityParser.git

# 验证远程仓库设置
git remote -v
```

### 3.2 推送到 GitHub
```bash
# 推送代码到 GitHub（首次推送）
git push -u origin main

# 如果遇到分支名称问题，先设置默认分支
git branch -M main
git push -u origin main
```

## 步骤四：验证上传

### 4.1 检查 GitHub 仓库
1. 刷新你的 GitHub 仓库页面
2. 确认所有文件都已上传
3. 检查 README.md 是否正确显示

### 4.2 预期的文件结构
```
PyActivityParser/
├── .gitignore
├── LICENSE
├── README.md
├── GITHUB_UPLOAD_GUIDE.md
├── requirements.txt
├── setup.py
├── example.py
├── src/
│   └── pyactivityparser/
│       ├── __init__.py
│       ├── main.py
│       ├── data_loader.py
│       ├── core_analysis.py
│       ├── quality_assessment.py
│       ├── activity_analysis.py
│       ├── sleep_analysis.py
│       └── report_generator.py
├── data/
│   ├── 1067459_90004_0_0.csv
│   └── 3396599_90004_0_0.csv
├── output/
│   ├── reports/
│   └── data/
├── tests/
└── docs/
```

## 步骤五：后续维护

### 5.1 日常更新流程
```bash
# 添加更改的文件
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送到 GitHub
git push origin main
```

### 5.2 创建发布版本
```bash
# 创建标签
git tag -a v0.1.0 -m "Release version 0.1.0"

# 推送标签
git push origin v0.1.0
```

## 步骤六：增强仓库

### 6.1 添加 GitHub Actions（可选）
创建 `.github/workflows/ci.yml` 文件用于自动化测试：

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.7, 3.8, 3.9]
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Test with pytest
      run: |
        python example.py
```

### 6.2 添加 Issue 和 PR 模板（可选）
在 `.github/` 目录下创建：
- `ISSUE_TEMPLATE.md`
- `PULL_REQUEST_TEMPLATE.md`

## 故障排除

### 常见问题解决

**问题 1**: `remote: Repository not found`
```bash
# 检查远程仓库 URL
git remote -v
# 重新设置正确的 URL
git remote set-url origin https://github.com/yourusername/PyActivityParser.git
```

**问题 2**: `Authentication failed`
```bash
# 使用 GitHub CLI (推荐)
gh auth login

# 或使用个人访问令牌
# 在 GitHub Settings > Developer settings > Personal access tokens 创建令牌
```

**问题 3**: 文件过大
```bash
# 检查大文件
find . -size +100M

# 移除大文件并添加到 .gitignore
git rm --cached large_file.csv
echo "large_file.csv" >> .gitignore
```

## 完成检查清单

- [ ] GitHub 仓库创建成功
- [ ] 本地 Git 初始化完成
- [ ] 远程仓库连接成功
- [ ] 代码成功推送到 GitHub
- [ ] README.md 显示正常
- [ ] 许可证文件存在
- [ ] .gitignore 配置正确
- [ ] 示例脚本可以运行

## 下一步建议

1. **添加 CI/CD**: 设置自动化测试
2. **创建文档**: 在 `docs/` 目录添加详细文档
3. **编写测试**: 在 `tests/` 目录添加单元测试
4. **发布包**: 考虑发布到 PyPI
5. **社区互动**: 回应 Issues 和 Pull Requests

完成以上步骤后，你的 PyActivityParser 项目就成功上传到 GitHub 了！