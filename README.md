# GLaDOS 自动签到  
使用教程：
1.点击 Star 和 Fork 这个项目

1.1 点击 Star
点个Star支持一下，非常感谢！！

1.2 Fork 项目
步骤：
打开该项目的 GitHub 页面。
在页面右上角，点击 Fork 按钮。
选择你要 Fork 到的 GitHub 账户或组织。

2. 配置环境变量

2.1 在 GitHub 中设置 Secrets（环境变量）

为了让 CI/CD 流程使用敏感信息（如 BOT_TOKEN, CHAT_ID, USER1, PASS1 等），我们使用 GitHub 的 Secrets 功能存储环境变量，这样可以安全地管理配置。

步骤：
打开你的 GitHub 仓库页面。

点击页面右上角的 Settings 按钮。

在左侧菜单栏找到 Secrets and variables，点击 Actions。

点击 New repository secret 按钮，添加以下 Secrets：


TG_BOT_TOKEN   你的电报机器人的Token

TG_CHAT_ID     你的Chat ID 

HTTP_PROXY        HTTP代理地址 如果你需要的话

HTTPS_PROXY      HTTPS代理地址 如果你需要的话

GLADOS_EMAIL_1=   你的邮箱

GLADOS_COOKIE_1=  账号的cookie

GLADOS_EMAIL_2=

GLADOS_COOKIE_2=


GLADOS_EMAIL_3=

GLADOS_COOKIE_3=

# 可以继续添加更多账号...

注意：Secrets 一旦设置好后，GitHub Actions 会自动读取它们，无需手动在每次提交时修改代码


2.2 手动运行工作流，后续每天都会自动运行
