# Personas - 数字分身模板库

存放 clawdbox 预制数字分身的人格模板，供 gateway 的 `install_persona` + `switch_twin` 命令使用。

## 目录规范
- 每个 persona 一个目录，目录名用英文 slug（如 `product-manager`）
- 目录内必须有 `manifest.json`、`SOUL.md`、`AGENTS.md`
- 角色专属 skills 放在 `skills/<skill_name>/SKILL.md`

## 新增 persona 流程
1. 新建目录 `personas/<new_id>/`
2. 写 `manifest.json`（格式见仓库 Wiki 或协作文档）
3. 写 `SOUL.md`（用 `{{职业}}` `{{行业}}` `{{产品}}` `{{原型}}` `{{思维框架}}` 占位符）
4. 写 `AGENTS.md`
5. 提 PR，CI 会校验结构
