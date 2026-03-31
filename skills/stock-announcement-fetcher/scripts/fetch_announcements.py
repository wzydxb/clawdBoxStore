#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /// script
# dependencies = [
#   "akshare",
#   "pandas",
#   "requests",
#   "PyPDF2"
# ]
# ///

"""
上市公司公告获取工具 - 优化版
解决编码问题，优化PDF提取
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
import pandas as pd
import requests
import io
import re

# 设置标准输出编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def fetch_announcements(stock_code, start_date=None, end_date=None, days=30):
    """获取股票公告"""
    try:
        import akshare as ak
    except ImportError:
        print("Error: akshare not installed", file=sys.stderr)
        return []
    
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    code = stock_code.replace('.SZ', '').replace('.SS', '').replace('.SH', '')
    
    print(f"\n[INFO] Fetching announcements for {code} ({start_date} ~ {end_date})...\n", file=sys.stderr)
    
    try:
        date_str = end_date.replace('-', '')
        
        print(f"[1/2] Fetching from Eastmoney...", file=sys.stderr)
        df_all = ak.stock_notice_report(symbol='全部', date=date_str)
        
        if df_all is None or len(df_all) == 0:
            print("  --> No data", file=sys.stderr)
            return []
        
        print(f"  --> Got {len(df_all)} announcements", file=sys.stderr)
        
        print(f"[2/2] Filtering for {code}...", file=sys.stderr)
        
        cols = list(df_all.columns)
        df_filtered = df_all[df_all[cols[0]] == code].copy()
        
        if len(df_filtered) == 0:
            print(f"  --> No match for {code}", file=sys.stderr)
            return []
        
        print(f"  --> Found {len(df_filtered)} announcements\n", file=sys.stderr)
        
        results = []
        for _, row in df_filtered.iterrows():
            ann_date = str(row[cols[4]])
            
            if start_date and ann_date < start_date:
                continue
            if end_date and ann_date > end_date:
                continue
            
            url = str(row[cols[5]])
            ann_id = url.split('/')[-1].replace('.html', '')
            
            results.append({
                'date': ann_date,
                'title': str(row[cols[2]]),
                'type': str(row[cols[3]]),
                'url': url,
                'pdf_url': f'http://pdf.dfcfw.com/pdf/H2_{ann_id}_1.pdf',
                'ann_id': ann_id,
                'stock_code': str(row[cols[0]]),
                'stock_name': str(row[cols[1]]),
                'source': 'Eastmoney'
            })
        
        return results
        
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return []

def extract_pdf_text_simple(pdf_url):
    """
    简化的PDF文本提取（使用PyPDF2，兼容性更好）
    """
    try:
        from PyPDF2 import PdfReader
        
        print(f"[PDF] Downloading...", file=sys.stderr)
        response = requests.get(pdf_url, timeout=15)
        response.raise_for_status()
        
        pdf = PdfReader(io.BytesIO(response.content))
        total_pages = len(pdf.pages)
        
        print(f"[PDF] Extracting {total_pages} page(s)...", file=sys.stderr)
        
        text_parts = []
        for page in pdf.pages[:5]:  # 最多前5页
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        full_text = '\n'.join(text_parts)
        
        # 清理文本
        full_text = re.sub(r'\s+', ' ', full_text)
        full_text = full_text.strip()
        
        print(f"[PDF] Extracted {len(full_text)} chars\n", file=sys.stderr)
        return full_text
        
    except Exception as e:
        print(f"[PDF ERROR] {e}", file=sys.stderr)
        return None

def smart_summarize(title, content):
    """智能总结公告"""
    if not content or len(content) < 50:
        return "【无法提取有效内容】"
    
    summary = []
    summary.append(f"【标题】{title}\n")
    
    # 提取关键句子
    sentences = re.split(r'[。！？\n]', content)
    key_sentences = []
    
    keywords = [
        '通知', '决定', '变更', '任命', '聘任', '辞职',
        '增持', '减持', '业绩', '利润', '营收', '净利',
        '合同', '投资', '收购', '重组', '分红', '股东'
    ]
    
    for sent in sentences:
        sent = sent.strip()
        if len(sent) > 15 and len(sent) < 200:
            if any(kw in sent for kw in keywords):
                key_sentences.append(sent)
                if len(key_sentences) >= 5:
                    break
    
    if key_sentences:
        summary.append("【核心内容】")
        for i, sent in enumerate(key_sentences, 1):
            summary.append(f"{i}. {sent}")
    else:
        summary.append("【摘要】")
        summary.append(content[:300] + "...")
    
    return '\n'.join(summary)

def format_output(announcements, format_type='text', detail=False):
    """格式化输出"""
    if not announcements:
        print("\n未找到公告")
        return
    
    if format_type == 'json':
        print(json.dumps(announcements, ensure_ascii=False, indent=2))
        return
    
    # Text
    print(f"\n{'='*80}")
    print(f"共找到 {len(announcements)} 条公告")
    if announcements[0].get('stock_name'):
        print(f"股票: {announcements[0]['stock_name']} ({announcements[0]['stock_code']})")
    print(f"{'='*80}\n")
    
    for i, ann in enumerate(announcements, 1):
        print(f"[{i}] {ann['date']}")
        print(f"    标题: {ann['title']}")
        if ann.get('type'):
            print(f"    类型: {ann['type']}")
        if ann.get('url'):
            print(f"    链接: {ann['url']}")
        if ann.get('pdf_url'):
            print(f"    PDF: {ann['pdf_url']}")
        
        if detail and ann.get('summary'):
            print(f"\n    {'-'*70}")
            print(f"    {ann['summary']}")
            print(f"    {'-'*70}\n")
        else:
            print()

def main():
    parser = argparse.ArgumentParser(description='上市公司公告获取工具（优化版）')
    parser.add_argument('stock_code', help='股票代码')
    parser.add_argument('--from', dest='start_date', help='开始日期 YYYY-MM-DD', default=None)
    parser.add_argument('--to', dest='end_date', help='结束日期 YYYY-MM-DD', default=None)
    parser.add_argument('--days', type=int, help='最近N天', default=30)
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--keyword', help='关键词筛选', default=None)
    parser.add_argument('--detail', action='store_true', help='提取PDF内容并总结')
    
    args = parser.parse_args()
    
    # 获取公告列表
    announcements = fetch_announcements(
        args.stock_code,
        start_date=args.start_date,
        end_date=args.end_date,
        days=args.days
    )
    
    # 关键词筛选
    if args.keyword and announcements:
        announcements = [ann for ann in announcements if args.keyword in ann['title']]
    
    # 提取PDF并总结
    if args.detail and announcements:
        print(f"[INFO] Extracting PDF content...\n", file=sys.stderr)
        for ann in announcements:
            if ann.get('pdf_url'):
                content = extract_pdf_text_simple(ann['pdf_url'])
                if content:
                    summary = smart_summarize(ann['title'], content)
                    ann['summary'] = summary
                    ann['full_text'] = content
    
    # 输出
    format_output(announcements, args.format, detail=args.detail)

if __name__ == "__main__":
    main()
