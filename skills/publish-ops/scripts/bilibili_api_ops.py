#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Any

import requests
from pycookiecheat import chrome_cookies
from biliup.plugins.bili_webup import BiliBili, Data

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
DEFAULT_TID = 171


def emit(payload: Any) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def fail(message: str, **extra: Any) -> None:
    emit({'ok': False, 'error': message, **extra})
    sys.exit(1)


def load_cookies() -> dict[str, str]:
    cookies = chrome_cookies('https://www.bilibili.com')
    needed = ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'sid']
    result = {name: cookies.get(name, '') for name in needed if cookies.get(name)}
    if 'SESSDATA' not in result or 'bili_jct' not in result:
        fail('missing required bilibili cookies', cookies=list(result.keys()))
    return result


def cookie_file_payload(cookies: dict[str, str]) -> dict[str, Any]:
    return {
        'cookie_info': {
            'cookies': [{'name': k, 'value': v} for k, v in cookies.items()]
        },
        'token_info': {
            'access_token': '',
            'refresh_token': '',
        },
    }


def with_cookie_file(cookies: dict[str, str], fn):
    import tempfile
    with tempfile.NamedTemporaryFile('w+', suffix='-bili-cookies.json', delete=False) as tmp:
        json.dump(cookie_file_payload(cookies), tmp, ensure_ascii=False)
        tmp.flush()
        path = tmp.name
    try:
        return fn(path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def cmd_publish(args: argparse.Namespace) -> None:
    cookies = load_cookies()

    def do_upload(cookie_path: str):
        video = Data()
        video.title = args.title[:80]
        video.desc = args.description
        video.desc_v2 = [{'raw_text': args.description, 'biz_id': '', 'type': 1}]
        video.copyright = 1
        video.tid = int(args.tid or DEFAULT_TID)
        tags = [tag.strip() for tag in (args.tags or '').split(',') if tag.strip()]
        if tags:
            video.set_tag(tags)
        with BiliBili(video) as bili:
            bili.login('bili.cookie', cookie_path)
            part = bili.upload_file(args.video_path, lines='AUTO', tasks=3)
            part['title'] = part['title'][:80]
            video.append(part)
            ret = bili.submit('web')
            return ret

    result = with_cookie_file(cookies, do_upload)
    emit({'ok': result.get('code') == 0, 'result': result})


def resolve_aid(args: argparse.Namespace, cookies: dict[str, str]) -> str:
    if args.aid:
        return str(args.aid)
    if not args.bvid:
        fail('missing aid_or_bvid')
    headers = {'User-Agent': USER_AGENT, 'Referer': f'https://www.bilibili.com/video/{args.bvid}'}
    res = requests.get(
        'https://api.bilibili.com/x/web-interface/view',
        params={'bvid': args.bvid},
        headers=headers,
        cookies=cookies,
        timeout=15,
    )
    data = res.json()
    aid = data.get('data', {}).get('aid')
    if not aid:
        fail('failed to resolve aid from bvid', response=data)
    return str(aid)


def cmd_monitor(args: argparse.Namespace) -> None:
    cookies = load_cookies()
    aid = resolve_aid(args, cookies)
    sort_code = 0 if (args.sort or 'new').lower() == 'new' else 2
    headers = {'User-Agent': USER_AGENT, 'Referer': f'https://www.bilibili.com/video/{args.bvid}' if args.bvid else f'https://www.bilibili.com/video/av{aid}'}
    res = requests.get(
        'https://api.bilibili.com/x/v2/reply',
        params={'pn': 1, 'type': 1, 'oid': aid, 'sort': sort_code, 'ps': int(args.limit or 20)},
        headers=headers,
        cookies=cookies,
        timeout=15,
    )
    data = res.json()
    replies = data.get('data', {}).get('replies') or []
    rows = [{
        'author': reply.get('member', {}).get('uname', ''),
        'content': (reply.get('content', {}).get('message', '') or '').strip(),
        'comment_id': reply.get('rpid_str') or str(reply.get('rpid') or ''),
        'oid': aid,
        'reply_type': '1',
        'root': reply.get('rpid_str') or str(reply.get('rpid') or ''),
        'parent': reply.get('rpid_str') or str(reply.get('rpid') or ''),
        'url': f'https://www.bilibili.com/video/{args.bvid}' if args.bvid else f'https://www.bilibili.com/video/av{aid}'
    } for reply in replies]
    emit({'ok': data.get('code') == 0, 'aid': aid, 'response': data, 'comments': rows})


def cmd_reply(args: argparse.Namespace) -> None:
    cookies = load_cookies()
    aid = resolve_aid(args, cookies)
    csrf = cookies.get('bili_jct', '')
    if not csrf:
        fail('missing bili_jct')
    body = {
        'oid': aid,
        'type': '1',
        'message': args.text,
        'plat': '1',
        'root': args.root,
        'parent': args.parent or args.root,
        'csrf': csrf,
    }
    headers = {
        'User-Agent': USER_AGENT,
        'Referer': f'https://www.bilibili.com/video/{args.bvid}' if args.bvid else f'https://www.bilibili.com/video/av{aid}',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }
    res = requests.post('https://api.bilibili.com/x/v2/reply/add', data=body, headers=headers, cookies=cookies, timeout=15)
    data = res.json()
    emit({'ok': data.get('code') == 0, 'aid': aid, 'response': data})


def cmd_add_comment(args: argparse.Namespace) -> None:
    cookies = load_cookies()
    aid = resolve_aid(args, cookies)
    csrf = cookies.get('bili_jct', '')
    if not csrf:
        fail('missing bili_jct')
    body = {
        'oid': aid,
        'type': '1',
        'message': args.text,
        'plat': '1',
        'csrf': csrf,
    }
    headers = {
        'User-Agent': USER_AGENT,
        'Referer': f'https://www.bilibili.com/video/{args.bvid}' if args.bvid else f'https://www.bilibili.com/video/av{aid}',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }
    res = requests.post('https://api.bilibili.com/x/v2/reply/add', data=body, headers=headers, cookies=cookies, timeout=15)
    data = res.json()
    emit({'ok': data.get('code') == 0, 'aid': aid, 'response': data})


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)

    publish = sub.add_parser('publish')
    publish.add_argument('--video-path', required=True)
    publish.add_argument('--title', required=True)
    publish.add_argument('--description', required=True)
    publish.add_argument('--tags', default='')
    publish.add_argument('--tid', default=str(DEFAULT_TID))
    publish.set_defaults(func=cmd_publish)

    monitor = sub.add_parser('monitor')
    monitor.add_argument('--aid')
    monitor.add_argument('--bvid')
    monitor.add_argument('--limit', default='20')
    monitor.add_argument('--sort', default='new')
    monitor.set_defaults(func=cmd_monitor)

    reply = sub.add_parser('reply')
    reply.add_argument('--aid')
    reply.add_argument('--bvid')
    reply.add_argument('--root', required=True)
    reply.add_argument('--parent', default='')
    reply.add_argument('--text', required=True)
    reply.set_defaults(func=cmd_reply)

    add_comment = sub.add_parser('add-comment')
    add_comment.add_argument('--aid')
    add_comment.add_argument('--bvid')
    add_comment.add_argument('--text', required=True)
    add_comment.set_defaults(func=cmd_add_comment)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
