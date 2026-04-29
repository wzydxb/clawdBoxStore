#!/usr/bin/env python3
"""
kb_wiki_check.py — wiki 格式校验
用法：python3 kb_wiki_check.py <mount_path>
输出需要修复的问题列表，exit 0 = 通过，exit 1 = 有问题
"""
import os, re, sys

def check(mount):
    wiki = os.path.join(mount, '.hermes-index', 'wiki')
    issues = []

    # 1. _index.md 格式检查
    index_path = os.path.join(wiki, '_index.md')
    if not os.path.exists(index_path):
        issues.append('_index.md 不存在')
    else:
        idx = open(index_path).read()
        if idx.strip() == '# 知识库索引' or len(idx.strip()) < 30:
            issues.append('_index.md 内容为空，缺少文件条目')

        # 检查 wiki link 格式：[[X] 少闭合
        bad_links = re.findall(r'\[\[[^\]]+\](?!\])', idx)
        for bl in bad_links:
            issues.append(f'_index.md wiki link 未闭合：{bl}')

        # 检查必要字段
        entries = re.findall(r'^## .+$', idx, re.M)
        for entry in entries:
            name = entry.lstrip('# ').strip()
            block_match = re.search(
                re.escape(entry) + r'(.*?)(?=^## |\Z)',
                idx, re.DOTALL | re.M
            )
            if not block_match:
                continue
            block = block_match.group(1)
            if '- 路径：' not in block:
                issues.append(f'_index.md 条目「{name}」缺少「- 路径：」字段')
            if '- 摘要：' not in block:
                issues.append(f'_index.md 条目「{name}」缺少「- 摘要：」字段')
            if '- 关联：' not in block:
                issues.append(f'_index.md 条目「{name}」缺少「- 关联：」字段')
            # 摘要不能是「关于xxx的文档」这种占位符
            summary_m = re.search(r'- 摘要：(.+)', block)
            if summary_m:
                s = summary_m.group(1).strip()
                if s.startswith('关于') and s.endswith('的文档'):
                    issues.append(f'_index.md 条目「{name}」摘要是占位符，应写实际内容摘要')

    # 2. concepts 页格式检查
    concepts_dir = os.path.join(wiki, 'concepts')
    if os.path.isdir(concepts_dir):
        for fname in os.listdir(concepts_dir):
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(concepts_dir, fname)
            content = open(fpath).read()
            name = fname[:-3]

            if not re.search(r'^# .+', content, re.M):
                issues.append(f'concepts/{fname} 缺少一级标题')

            if '## 核心内容' not in content:
                issues.append(f'concepts/{fname} 缺少「## 核心内容」章节')

            if '## 相关文件' not in content:
                issues.append(f'concepts/{fname} 缺少「## 相关文件」章节')

            # 检查相关文件里的 wiki link 闭合
            bad = re.findall(r'\[\[[^\]]+\](?!\])', content)
            for bl in bad:
                issues.append(f'concepts/{fname} wiki link 未闭合：{bl}')

            # 核心内容不能为空
            core_m = re.search(r'## 核心内容\n+(.*?)(?=\n## |\Z)', content, re.DOTALL)
            if core_m and len(core_m.group(1).strip()) < 10:
                issues.append(f'concepts/{fname}「核心内容」过短或为空')
    else:
        issues.append('concepts/ 目录不存在')

    # 3. _index.md 里关联的 concept 是否实际存在
    if os.path.exists(index_path):
        idx = open(index_path).read()
        linked = set(re.findall(r'\[\[([^\]]+)\]\]', idx))
        for name in linked:
            cp = os.path.join(concepts_dir, f'{name}.md')
            if not os.path.exists(cp):
                issues.append(f'_index.md 引用了 [[{name}]] 但 concepts/{name}.md 不存在')

    if issues:
        print(f'❌ 发现 {len(issues)} 个问题：')
        for i, issue in enumerate(issues, 1):
            print(f'  {i}. {issue}')
        return 1
    else:
        print('✅ wiki 格式校验通过')
        return 0

if __name__ == '__main__':
    mount = sys.argv[1] if len(sys.argv) > 1 else '/data/龙虾智盒网盘'
    sys.exit(check(mount))
