# 科目一在线考试系统

一个可在 Windows 本机一键运行的科目一在线考试系统发布包，包含后端 JAR、MySQL 初始化脚本、题目配图和题库分析材料。

> 这是发布版而非完整源码仓库：前端静态资源和后端代码已打入 `app/driving-subject1.jar`。

## 功能

- 学员刷题、模拟考试、错题本与成绩记录
- 题库、分类、试卷、用户和角色权限管理
- 2309 道题目及配图初始化脚本
- 题库分类、重复题与答案审计分析报告

## 环境要求

- Windows 10/11
- JDK 8 或更高版本（`java -version` 可用）
- MySQL 8.0 或更高版本，并确保 `mysql` 命令可用；也可在本地配置中指定其完整路径

## 快速开始

1. 复制 `config.example.bat` 并将副本重命名为 `config.local.bat`。
2. 在 `config.local.bat` 中填写本机 MySQL 信息，尤其是 `DB_PASS`；建议同时设置足够长且随机的 `JWT_SECRET`。留空时启动脚本会为当前运行临时生成一个，重启后需重新登录。这个文件已被 Git 忽略。
3. 双击 `start-system.bat`。首次启动会创建数据库并导入题库，随后打开 <http://localhost:8080>。
4. 需要停止服务时运行 `stop-system.bat`；需要清空并重建演示数据时运行 `reset-db.bat`。

默认演示账号均使用密码 `123456`：`admin`、`questionadmin`、`student`。它们只用于本地演示，请勿用于公开或生产环境。

## 目录说明

```text
app/        可执行 JAR、题目图片与助手嵌入资源
db/         MySQL 建表、初始化、题库和图片映射脚本
docs/       UML / ER 图说明
reports/    题库分析结果与生成的图表
tools/      用于分析题库和渲染图表的 Python 脚本
*.bat       Windows 启动、停止、重置脚本
```

## GitHub 发布说明

- 本仓库特意提交 `app/driving-subject1.jar`，以保留开箱即用能力；该文件约 73MB，低于 GitHub 的 100MB 单文件限制。
- `.gitignore` 已排除日志、本机数据库配置、环境文件、证书/私钥和 Python 缓存。提交前仍建议运行：`git status --ignored` 并人工确认待提交内容。
- 本项目不附带开源许可证。公开前请确认题库、图片、第三方助手链接及其他材料均拥有传播授权，再按你的意图添加许可证。

更多安全注意事项见 [SECURITY.md](SECURITY.md)。
