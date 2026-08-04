#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
English Workbench - 每日真实新闻抓取脚本
- 直连 RSS（服务端无 CORS 限制，不需公共代理）
- 容错：能抓到几个源算几个
- 输出 news.json：{ updated, count, articles:[ {source,link,title,summary,paragraphs,date,real:true} ] }
- 供 GitHub Action 每天定时运行，也供本地手动运行。
"""
import urllib.request
import urllib.error
import json
import sys
import re
import html
import datetime
import email.utils

FEEDS = [
    ("BBC News", "http://feeds.bbci.co.uk/news/rss.xml"),
    ("NPR", "https://feeds.npr.org/1001/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
]

UA = "Mozilla/5.0 (compatible; english-workbench/1.0; +https://github.com/)"


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def clean(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tag_text(block, tag):
    # 兼容命名空间标签如 content:encoded
    m = re.search(r"<" + re.escape(tag) + r"\b[^>]*>(.*?)</" + re.escape(tag) + r">",
                  block, re.S | re.I)
    if m:
        return m.group(1)
    # atom: <tag attr="..."> 内容也可能为空，取属性 href
    m2 = re.search(r"<" + re.escape(tag) + r"\b[^>]*\shref=\"([^\"]+)\"", block, re.I)
    if m2:
        return m2.group(1)
    return ""


def html_to_paragraphs(h):
    if not h:
        return []
    h = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    parts = re.split(r"</(p|div|br|li|h\d)\b[^>]*>", h, flags=re.I)
    paras = []
    for p in parts:
        p = clean(p)
        if len(p) > 40:
            paras.append(p)
    return paras[:12]


def parse_date(s):
    if not s:
        return ""
    try:
        dt = email.utils.parsedate_to_datetime(s)
        if dt:
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return ""


def parse_items(xml, source):
    blocks = re.findall(r"<item\b[^>]*>.*?</item>", xml, re.S | re.I)
    if not blocks:
        # 尝试 atom entry
        blocks = re.findall(r"<entry\b[^>]*>.*?</entry>", xml, re.S | re.I)
    arts = []
    for b in blocks:
        title = clean(tag_text(b, "title"))
        link = tag_text(b, "link")
        desc = tag_text(b, "description") or tag_text(b, "summary")
        enc = tag_text(b, "content:encoded") or desc
        pub = tag_text(b, "pubDate") or tag_text(b, "updated") or tag_text(b, "dc:date")
        if not title:
            continue
        paragraphs = html_to_paragraphs(enc or desc)
        if not paragraphs:
            # 至少给个摘要
            paragraphs = [clean(desc)[:400]] if desc else []
        arts.append({
            "source": source,
            "link": link,
            "title": title,
            "summary": clean(desc)[:300],
            "paragraphs": paragraphs,
            "date": parse_date(pub),
            "real": True,
        })
    return arts


def main():
    all_articles = []
    sources_used = []
    for source, url in FEEDS:
        try:
            xml = fetch(url)
            arts = parse_items(xml, source)
            if arts:
                all_articles.extend(arts)
                sources_used.append(f"{source}:{len(arts)}")
                print(f"  + {source}: {len(arts)} 条", flush=True)
            else:
                print(f"  - {source}: 0 条（无 item）", flush=True)
        except Exception as e:
            print(f"  ! {source}: 失败 {e}", file=sys.stderr, flush=True)
    # 去重（按 link+title）
    seen = set()
    uniq = []
    for a in all_articles:
        key = (a["link"], a["title"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(a)
    uniq = uniq[:60]
    out = {
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(uniq),
        "articles": uniq,
    }
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"完成：共 {len(uniq)} 条真实新闻（来源 {sources_used or '无'}）-> news.json")


if __name__ == "__main__":
    main()
