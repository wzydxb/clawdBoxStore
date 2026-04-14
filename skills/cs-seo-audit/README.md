# SEO 审计工具

## 简介

SEO 审计工具，自动识别网站的 SEO 问题并提供可操作的优化建议，帮助提升有机搜索排名和流量。

## 主要功能

- 页面 SEO 检查：标题标签、Meta 描述、H1/H2 结构、关键词密度
- 技术 SEO 审计：页面加载速度、移动端适配、canonical 标签、robots.txt、sitemap
- 内链/外链分析：识别断链、重定向链、锚文本分布问题
- 内容质量评估：重复内容检测、薄内容识别
- 可操作建议：每个问题附带优先级评级和具体修复步骤

## 使用方式

核心脚本：`scripts/seo_checker.py`

```bash
# 审计单个页面
python scripts/seo_checker.py --url https://example.com/page

# 审计整个站点（需提供 sitemap）
python scripts/seo_checker.py --sitemap https://example.com/sitemap.xml

# 输出报告到文件
python scripts/seo_checker.py --url https://example.com --output report.json
```

也可以直接告诉助手你的网站 URL，助手会调用脚本并以可读格式呈现审计结果。

示例提示：
- "帮我审计这个页面的 SEO 问题：https://example.com"
- "分析一下我的网站有哪些技术 SEO 问题"

## 依赖/前置条件

- Python >= 3.8
- 安装依赖：`pip install -r requirements.txt`
- 无需 API Key
- 审计外部网站需要网络访问权限

## 注意事项

- 部分检查项（如 Core Web Vitals）需要 Google PageSpeed API，可选配置
- 大型站点审计耗时较长，建议先对重点页面进行抽样审计
- 审计结果反映当前状态，SEO 优化效果需要数周才能在搜索引擎中体现
