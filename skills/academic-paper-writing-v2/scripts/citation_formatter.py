#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文献引用格式化工具

功能：将文献数据转换为标准引用格式
支持格式：APA(第7版)、MLA(第9版)、Chicago(第17版)、GB/T 7714-2015

使用方法：
    python citation_formatter.py --format apa --input references.json --output output/

输入格式：参见 references/citation_formats.md
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional
from pathlib import Path


def _parse_english_author(author: str):
    """
    解析英文作者姓名，返回 (last_name, initials_str)。

    支持多种常见输入格式：
      - "Smith John"      → ("Smith", "J.")        # 姓 名
      - "Smith J"         → ("Smith", "J.")        # 姓 名首字母
      - "Smith J M"       → ("Smith", "J. M.")     # 姓 多个名首字母
      - "John Smith"      → ("Smith", "J.")        # 如检测到首词全小写/大写均视情况
      - "Smith"           → ("Smith", "")          # 仅姓

    判断策略：若最后一个词全为大写字母或只有1-2个字符（名首字母），
    则第一词为姓；否则按"名... 姓"顺序解析（姓在最后）。
    实际学术数据库中英文作者通常已为"姓 名/首字母"格式。
    """
    parts = author.strip().split()
    if len(parts) == 1:
        return (parts[0], "")

    # 判断是否已是"姓 名/首字母"格式：
    # 第一个词长度>2 且 后续词均为1-2字符（典型首字母形式）
    rest_are_initials = all(len(p.rstrip('.')) <= 2 for p in parts[1:])
    if rest_are_initials:
        last = parts[0]
        initials = ". ".join(p[0].upper() for p in parts[1:]) + "."
    else:
        # "名 姓"格式，姓在最后
        last = parts[-1]
        initials = ". ".join(p[0].upper() for p in parts[:-1]) + "."

    return (last, initials)


class CitationFormatter:
    """文献引用格式化器"""

    def __init__(self, format_type: str = "apa"):
        """
        初始化格式化器

        Args:
            format_type: 引用格式类型 (apa/mla/chicago/gb7714)
        """
        self.format_type = format_type.lower()
        self.supported_formats = ["apa", "mla", "chicago", "gb7714"]

        if self.format_type not in self.supported_formats:
            raise ValueError(f"不支持的格式: {format_type}。支持的格式: {', '.join(self.supported_formats)}")

    def format_authors_apa(self, authors: List[str], is_chinese: bool = True) -> str:
        """
        APA格式作者处理

        Args:
            authors: 作者列表
            is_chinese: 是否为中文文献

        Returns:
            格式化后的作者字符串
        """
        if not authors:
            return ""

        if is_chinese:
            if len(authors) == 1:
                return authors[0]
            elif len(authors) == 2:
                return f"{authors[0]} & {authors[1]}"
            elif len(authors) <= 20:
                return ", ".join(authors[:-1]) + f", & {authors[-1]}"
            else:
                return ", ".join(authors[:19]) + ", ... " + f"& {authors[-1]}"
        else:
            # 英文作者 APA 格式：Last, I. M.（使用统一解析函数）
            formatted = []
            for author in authors:
                last, initials = _parse_english_author(author)
                formatted.append(f"{last}, {initials}" if initials else last)

            if len(formatted) == 1:
                return formatted[0]
            elif len(formatted) == 2:
                return f"{formatted[0]} & {formatted[1]}"
            elif len(formatted) <= 20:
                return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"
            else:
                return ", ".join(formatted[:19]) + f", ... & {formatted[-1]}"

    def format_authors_mla(self, authors: List[str], is_chinese: bool = True) -> str:
        """MLA格式作者处理"""
        if not authors:
            return ""

        if is_chinese:
            if len(authors) == 1:
                return authors[0]
            elif len(authors) == 2:
                return f"{authors[0]}, {authors[1]}"
            else:
                return f"{authors[0]}, 等"
        else:
            # 英文作者 MLA 格式：首作者 Last, First；其余 First Last
            formatted = []
            for i, author in enumerate(authors):
                last, initials = _parse_english_author(author)
                if i == 0:
                    name = f"{last}, {initials.rstrip('.')}" if initials else last
                else:
                    name = f"{initials.rstrip('.')} {last}" if initials else last
                formatted.append(name)

            if len(formatted) == 1:
                return formatted[0]
            elif len(formatted) == 2:
                return f"{formatted[0]}, and {formatted[1]}"
            else:
                return f"{formatted[0]}, et al"

    def format_authors_gb7714(self, authors: List[str], is_chinese: bool = True) -> str:
        """GB/T 7714格式作者处理"""
        if not authors:
            return ""

        if is_chinese:
            if len(authors) <= 3:
                return ", ".join(authors)
            else:
                return ", ".join(authors[:3]) + ", 等"
        else:
            # 英文作者 GB/T 7714 格式：LAST FM（姓全拼，名首字母连写无点）
            formatted = []
            for author in authors:
                last, initials = _parse_english_author(author)
                initials_nodot = initials.replace(".", "").replace(" ", "")
                formatted.append(f"{last} {initials_nodot}" if initials_nodot else last)

            if len(formatted) <= 3:
                return ", ".join(formatted)
            else:
                return ", ".join(formatted[:3]) + ", et al"

    def detect_chinese(self, text: str) -> bool:
        """检测是否为中文文本"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False

    def format_journal_apa(self, ref: Dict) -> str:
        """APA格式期刊论文"""
        is_chinese = self.detect_chinese(ref.get("title", ""))
        authors = self.format_authors_apa(ref.get("authors", []), is_chinese)
        year = ref.get("year", "n.d.")
        title = ref.get("title", "")
        journal = ref.get("journal", "")
        volume = ref.get("volume", "")
        issue = ref.get("issue", "")
        pages = ref.get("pages", "")
        doi = ref.get("doi", "")

        result = f"{authors} ({year}). {title}. {journal}"

        if volume:
            result += f", {volume}"
            if issue:
                result += f"({issue})"

        if pages:
            result += f", {pages}"

        result += "."

        if doi:
            result += f" https://doi.org/{doi}"

        return result

    def format_journal_mla(self, ref: Dict) -> str:
        """MLA格式期刊论文"""
        is_chinese = self.detect_chinese(ref.get("title", ""))
        authors = self.format_authors_mla(ref.get("authors", []), is_chinese)
        title = ref.get("title", "")
        journal = ref.get("journal", "")
        volume = ref.get("volume", "")
        issue = ref.get("issue", "")
        year = ref.get("year", "n.d.")
        pages = ref.get("pages", "")

        result = f'{authors}. "{title}." {journal}'

        if volume:
            result += f", vol. {volume}"
        if issue:
            result += f", no. {issue}"

        result += f", {year}"

        if pages:
            result += f", pp. {pages}"

        result += "."

        return result

    def format_journal_gb7714(self, ref: Dict) -> str:
        """GB/T 7714格式期刊论文"""
        is_chinese = self.detect_chinese(ref.get("title", ""))
        authors = self.format_authors_gb7714(ref.get("authors", []), is_chinese)
        title = ref.get("title", "")
        journal = ref.get("journal", "")
        year = ref.get("year", "n.d.")
        volume = ref.get("volume", "")
        issue = ref.get("issue", "")
        pages = ref.get("pages", "")

        result = f"{authors}. {title}[J]. {journal}, {year}"

        if volume:
            result += f", {volume}"
            if issue:
                result += f"({issue})"

        if pages:
            result += f": {pages}"

        result += "."

        return result

    def format_book_apa(self, ref: Dict) -> str:
        """APA格式图书"""
        is_chinese = self.detect_chinese(ref.get("title", ""))
        authors = self.format_authors_apa(ref.get("authors", []), is_chinese)
        year = ref.get("year", "n.d.")
        title = ref.get("title", "")
        edition = ref.get("edition", "")
        publisher = ref.get("publisher", "")

        result = f"{authors} ({year}). {title}"

        if edition:
            result += f" ({edition})"

        result += f". {publisher}."

        return result

    def format_book_mla(self, ref: Dict) -> str:
        """MLA格式图书"""
        is_chinese = self.detect_chinese(ref.get("title", ""))
        authors = self.format_authors_mla(ref.get("authors", []), is_chinese)
        title = ref.get("title", "")
        publisher = ref.get("publisher", "")
        year = ref.get("year", "n.d.")

        return f"{authors}. {title}. {publisher}, {year}."

    def format_book_gb7714(self, ref: Dict) -> str:
        """GB/T 7714格式图书"""
        is_chinese = self.detect_chinese(ref.get("title", ""))
        authors = self.format_authors_gb7714(ref.get("authors", []), is_chinese)
        title = ref.get("title", "")
        publisher = ref.get("publisher", "")
        year = ref.get("year", "n.d.")
        pages = ref.get("pages", "")

        result = f"{authors}. {title}[M]. {publisher}, {year}"

        if pages:
            result += f": {pages}"

        result += "."

        return result

    def format_conference_apa(self, ref: Dict) -> str:
        """APA格式会议论文"""
        is_chinese = self.detect_chinese(ref.get("title", ""))
        authors = self.format_authors_apa(ref.get("authors", []), is_chinese)
        year = ref.get("year", "n.d.")
        title = ref.get("title", "")
        conference = ref.get("conference", "")
        pages = ref.get("pages", "")

        result = f"{authors} ({year}). {title}. In {conference}"

        if pages:
            result += f" (pp. {pages})"

        result += "."

        return result

    def format_conference_mla(self, ref: Dict) -> str:
        """MLA格式会议论文（修复：实现真正的MLA格式，不再复用APA）"""
        is_chinese = self.detect_chinese(ref.get("title", ""))
        authors = self.format_authors_mla(ref.get("authors", []), is_chinese)
        title = ref.get("title", "")
        conference = ref.get("conference", "")
        year = ref.get("year", "n.d.")
        pages = ref.get("pages", "")

        # MLA会议论文格式：作者. "标题." 会议名称, 年份, 页码.
        result = f'{authors}. "{title}." {conference}, {year}'

        if pages:
            result += f", pp. {pages}"

        result += "."

        return result

    def format_conference_gb7714(self, ref: Dict) -> str:
        """GB/T 7714格式会议论文"""
        is_chinese = self.detect_chinese(ref.get("title", ""))
        authors = self.format_authors_gb7714(ref.get("authors", []), is_chinese)
        title = ref.get("title", "")
        conference = ref.get("conference", "")
        year = ref.get("year", "n.d.")
        pages = ref.get("pages", "")

        result = f"{authors}. {title}[C]//{conference}, {year}"

        if pages:
            result += f": {pages}"

        result += "."

        return result

    def format_reference(self, ref: Dict) -> str:
        """
        格式化单条参考文献

        Args:
            ref: 文献数据字典

        Returns:
            格式化后的参考文献字符串
        """
        ref_type = ref.get("type", "journal")

        if self.format_type == "apa":
            if ref_type == "journal":
                return self.format_journal_apa(ref)
            elif ref_type == "book":
                return self.format_book_apa(ref)
            elif ref_type == "conference":
                return self.format_conference_apa(ref)
            else:
                return self.format_journal_apa(ref)

        elif self.format_type == "mla":
            if ref_type == "journal":
                return self.format_journal_mla(ref)
            elif ref_type == "book":
                return self.format_book_mla(ref)
            elif ref_type == "conference":
                return self.format_conference_mla(ref)
            else:
                return self.format_journal_mla(ref)

        elif self.format_type == "gb7714":
            if ref_type == "journal":
                return self.format_journal_gb7714(ref)
            elif ref_type == "book":
                return self.format_book_gb7714(ref)
            elif ref_type == "conference":
                return self.format_conference_gb7714(ref)
            else:
                return self.format_journal_gb7714(ref)

        elif self.format_type == "chicago":
            # Chicago格式与APA类似，此处简化处理
            return self.format_journal_apa(ref)

        return ""

    def generate_in_text_citation(self, ref: Dict) -> str:
        """
        生成文内引用

        Args:
            ref: 文献数据字典

        Returns:
            文内引用字符串
        """
        authors = ref.get("authors", [])
        year = ref.get("year", "n.d.")
        is_chinese = self.detect_chinese(ref.get("title", ""))

        def _last(author: str) -> str:
            """从作者字符串中提取姓（使用统一解析函数）"""
            last, _ = _parse_english_author(author)
            return last

        if self.format_type in ["apa", "chicago"]:
            # APA第7版：≥3位作者一律用"et al."/"等"
            if is_chinese:
                if len(authors) == 1:
                    return f"({authors[0]}, {year})"
                elif len(authors) == 2:
                    return f"({authors[0]} & {authors[1]}, {year})"
                else:
                    # 修复：≥3位中文作者应用"等"，而非列出所有
                    return f"({authors[0]} 等, {year})"
            else:
                if len(authors) == 1:
                    return f"({_last(authors[0])}, {year})"
                elif len(authors) == 2:
                    return f"({_last(authors[0])} & {_last(authors[1])}, {year})"
                else:
                    return f"({_last(authors[0])} et al., {year})"

        elif self.format_type == "mla":
            # MLA：文内引用用姓+页码
            if is_chinese:
                page = ref.get("pages", "").split("-")[0] if ref.get("pages") else ""
                return f"({authors[0]} {page})".rstrip()
            else:
                page = ref.get("pages", "").split("-")[0] if ref.get("pages") else ""
                return f"({_last(authors[0])} {page})".rstrip()

        elif self.format_type == "gb7714":
            # GB/T 7714：通常用顺序编号引用，此处生成作者-年格式作为备选
            if is_chinese:
                if len(authors) == 1:
                    return f"({authors[0]}, {year})"
                elif len(authors) <= 3:
                    return f"({', '.join(authors)}, {year})"
                else:
                    return f"({authors[0]} 等, {year})"
            else:
                if len(authors) == 1:
                    return f"({_last(authors[0])}, {year})"
                elif len(authors) <= 3:
                    return f"({', '.join(_last(a) for a in authors)}, {year})"
                else:
                    return f"({_last(authors[0])} et al., {year})"

        return ""

    def format_all(self, references: List[Dict]) -> Dict:
        """
        格式化所有参考文献

        Args:
            references: 参考文献列表

        Returns:
            包含格式化结果和文内引用的字典
        """
        formatted_refs = []
        in_text_citations = {}

        for i, ref in enumerate(references, 1):
            # 格式化参考文献
            formatted = self.format_reference(ref)

            # GB/T 7714格式需要编号
            if self.format_type == "gb7714":
                formatted = f"[{i}] {formatted}"

            formatted_refs.append(formatted)

            # 生成文内引用键
            authors = ref.get("authors", [])
            year = ref.get("year", "n.d.")
            if authors:
                key = f"{authors[0].split()[-1] if not self.detect_chinese(ref.get('title', '')) else authors[0]}{year}"
                in_text_citations[key] = self.generate_in_text_citation(ref)

        return {
            "formatted_references": formatted_refs,
            "in_text_citations": in_text_citations
        }


def validate_input_data(data: Dict) -> bool:
    """
    验证输入数据格式

    Args:
        data: 输入数据字典

    Returns:
        验证是否通过
    """
    if "references" not in data:
        print("错误: 输入数据缺少 'references' 字段")
        return False

    if not isinstance(data["references"], list):
        print("错误: 'references' 必须是列表")
        return False

    for i, ref in enumerate(data["references"]):
        if not isinstance(ref, dict):
            print(f"错误: 参考文献 {i+1} 必须是字典")
            return False

        if "type" not in ref:
            print(f"错误: 参考文献 {i+1} 缺少 'type' 字段")
            return False

        if "authors" not in ref:
            print(f"错误: 参考文献 {i+1} 缺少 'authors' 字段")
            return False

        if "title" not in ref:
            print(f"错误: 参考文献 {i+1} 缺少 'title' 字段")
            return False

        if "year" not in ref:
            print(f"警告: 参考文献 {i+1} 缺少 'year' 字段，将使用 'n.d.'")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="文献引用格式化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python citation_formatter.py --format apa --input references.json --output output/
    python citation_formatter.py --format gb7714 --input refs.json --output ./results/
        """
    )

    parser.add_argument(
        "--format", "-f",
        required=True,
        choices=["apa", "mla", "chicago", "gb7714"],
        help="引用格式类型"
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="输入文献数据文件路径（JSON格式）"
    )

    parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出目录路径"
    )

    args = parser.parse_args()

    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        sys.exit(1)

    # 读取输入数据
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取文件失败: {e}")
        sys.exit(1)

    # 验证数据格式
    if not validate_input_data(data):
        sys.exit(1)

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取格式类型（优先使用输入数据中的格式，否则使用命令行参数）
    format_type = data.get("format", args.format)

    # 格式化参考文献
    try:
        formatter = CitationFormatter(format_type)
        result = formatter.format_all(data["references"])

        # 写入参考文献列表
        refs_file = output_dir / "formatted_references.txt"
        with open(refs_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(result["formatted_references"]))

        # 写入文内引用映射
        citations_file = output_dir / "in_text_citations.json"
        with open(citations_file, 'w', encoding='utf-8') as f:
            json.dump(result["in_text_citations"], f, ensure_ascii=False, indent=2)

        print(f"成功! 已生成以下文件:")
        print(f"  - 参考文献列表: {refs_file}")
        print(f"  - 文内引用映射: {citations_file}")
        print(f"  - 格式化文献数量: {len(result['formatted_references'])}")

    except Exception as e:
        print(f"错误: 格式化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
