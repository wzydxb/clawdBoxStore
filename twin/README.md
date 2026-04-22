# twin/ — 数字分身初始模板（hermes-opc）

存放 clawdbox 数字分身的「出厂模板」。当用户在小程序点击「切换到数字分身」时，
gateway 会调用 `switch_persona` 命令（persona_id="twin" 或不传），
把本目录下的全部内容部署到盒子的 `~/.hermes/` 目录。

## 工作原理

1. SOUL.md 处于初始化状态，对用户说"你好，我是你的数字分身，还没有形态"
2. 用户对话 → SOUL.md 里定义的 5 步引导流程启动：
   - 问职业
   - 问行业 + 公司/产品
   - 3 道选择题
   - 匹配认知原型并展示 2 个选项让用户选
   - 用户确认后，从 `personas/<role_dir>/` 加载原型 SKILL.md，写入 USER.md 和 SOUL.md
3. 初始化结束后，SOUL.md 被改写为**该用户专属的个性化版本**，不再触发引导

## 目录说明

- `SOUL.md` / `AGENTS.md` / `USER.md` / `TASKLOG.md` —— 根级 MD，装到 `~/.hermes/` 根下
- `personas/` —— 6 个职业原型，作为引导第 4 步的内部素材
- `skills/` —— 16 个共享 skills，整体装到 `~/.hermes/skills/` 下

## 维护原则

- 不直接改 `twin/SOUL.md` 里的业务逻辑，除非确认要迭代 onboarding 流程
- 新增预置职业角色 → 同时更新 `twin/personas/` 和仓库根下的 `personas/`
- 新增 skills → 放 `twin/skills/` 下（如果是 twin 专属）或仓库根下的 `skills/`（如果是跨模板通用）
