#!/usr/bin/env python3
"""
Canvas renderer: JSON data + HTML template → screenshot
Usage: python3 render.py <template> <data.json> [output.png]
"""
import sys, json, os, time, re
from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path("/tmp/hermes-canvas")
OUTPUT_DIR.mkdir(exist_ok=True)

def render(template_name: str, data: dict, output_path: str = None) -> str:
    tpl_path = TEMPLATES_DIR / f"{template_name}.html"
    if not tpl_path.exists():
        raise FileNotFoundError(f"Template not found: {tpl_path}")

    html = tpl_path.read_text()

    # Replace {{key}} and {{key.subkey}} placeholders
    def replacer(m):
        key = m.group(1).strip()
        parts = key.split(".")
        val = data
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p, "")
            else:
                val = ""
        if isinstance(val, list):
            field_name = parts[-1]
            # topic_cards: special multi-card layout
            if field_name == "topic_cards":
                return _render_topic_cards(val)
            # participants → tags
            elif field_name == "participants":
                return "\n".join(f'<span class="ptag">{i}</span>' for i in val)
            # root_causes → cause chain
            elif field_name == "root_causes":
                return _render_root_causes(val)
            # solutions → solution grid cards
            elif field_name == "solutions":
                return _render_solutions(val)
            # options → proposal option cards
            elif field_name == "options":
                return _render_options(val)
            # goals → goal tags
            elif field_name == "goals":
                return "\n".join(f'<span class="goal-tag">{g}</span>' for g in val)
            # compare_headers → table headers
            elif field_name == "compare_headers":
                return "\n".join(f'<th>{h}</th>' for h in val)
            # compare_rows → table rows
            elif field_name == "compare_rows":
                return _render_compare_rows(val)
            # next_steps → numbered steps
            elif field_name == "next_steps":
                return _render_next_steps(val)
            # current_state → bullet list items
            elif field_name == "current_state":
                return "\n".join(f'<li>{i}</li>' for i in val)
            # toc_items → table of contents
            elif field_name == "toc_items":
                return _render_toc(val)
            # sections → article sections
            elif field_name == "sections":
                return _render_article_sections(val)
            # key_takeaways → summary items
            elif field_name == "key_takeaways":
                return _render_takeaways(val)
            # criteria → decision criteria cards
            elif field_name == "criteria":
                return _render_criteria(val)
            # stakeholders → stakeholder list
            elif field_name == "stakeholders":
                return _render_stakeholders(val)
            # risks → risk items
            elif field_name == "risks":
                return _render_risks(val)
            # actions → action items (decision/brief)
            elif field_name == "actions":
                return _render_actions(val)
            # data_points → brief data cards
            elif field_name == "data_points":
                return _render_data_points(val)
            # signals → brief signal cards
            elif field_name == "signals":
                return _render_signals(val)
            # events → brief timeline events
            elif field_name == "events":
                return _render_events(val)
            # string lists (retro_good, retro_improve, etc.)
            elif val and isinstance(val[0], str):
                return "\n".join(f'<div class="retro-item">{i}</div>' for i in val)
            return _render_list(val, field_name)
        return str(val) if val else ""

    html = re.sub(r"\{\{([^}]+)\}\}", replacer, html)

    # Write temp HTML
    ts = int(time.time())
    html_path = OUTPUT_DIR / f"{template_name}_{ts}.html"
    html_path.write_text(html)

    # Screenshot via playwright
    if output_path is None:
        output_path = str(OUTPUT_DIR / f"{template_name}_{ts}.png")

    _screenshot(str(html_path), output_path)
    return output_path


def _render_topic_cards(cards: list) -> str:
    """Render meeting topic cards — each card is a themed discussion block."""
    COLOR_MAP = ["blue", "teal", "green", "orange", "purple", "red"]
    BADGE_MAP = ["badge-blue", "badge-green", "badge-orange", "badge-purple", "badge-red", "badge-gray"]
    rows = []
    for i, card in enumerate(cards):
        color = card.get("color", COLOR_MAP[i % len(COLOR_MAP)])
        badge_color = card.get("badge_color", BADGE_MAP[i % len(BADGE_MAP)])
        badge = card.get("badge", "")
        icon = card.get("icon", "")
        title = card.get("title", "")
        desc = card.get("desc", "")
        points = card.get("points", [])

        badge_html = f'<span class="card-badge {badge_color}">{badge}</span>' if badge else ""
        desc_html = f'<div class="card-desc">{desc}</div>' if desc else ""
        points_html = ""
        if points:
            items = "".join(f"<li>{p}</li>" for p in points)
            points_html = f'<ul class="card-points">{items}</ul>'

        rows.append(
            f'<div class="card card-{color}">'
            f'<div class="card-header">'
            f'<span class="card-title">{icon} {title}</span>'
            f'{badge_html}'
            f'</div>'
            f'{desc_html}'
            f'{points_html}'
            f'</div>'
        )
    return "\n".join(rows)


def _render_toc(items: list) -> str:
    rows = []
    for i, item in enumerate(items):
        text = item if isinstance(item, str) else item.get("title", "")
        rows.append(f'<li class="toc-item"><span class="toc-num">{i+1}.</span>{text}</li>')
    return "\n".join(rows)


def _render_article_sections(sections: list) -> str:
    rows = []
    for i, sec in enumerate(sections):
        title = sec.get("title", "")
        body = sec.get("body", "")
        callout = sec.get("callout", "")
        points = sec.get("points", [])
        quote = sec.get("quote", "")

        body_html = f'<div class="section-body"><p>{body}</p></div>' if body else ""
        callout_html = f'<div class="callout">{callout}</div>' if callout else ""
        quote_html = f'<div class="blockquote">{quote}</div>' if quote else ""
        points_html = ""
        if points:
            items = "".join(f'<div class="keypoint"><div class="kp-dot"></div>{p}</div>' for p in points)
            points_html = f'<div class="keypoints">{items}</div>'

        rows.append(
            f'<div class="article-section">'
            f'<div class="section-heading"><div class="section-num">{i+1}</div>{title}</div>'
            f'{body_html}{callout_html}{points_html}{quote_html}'
            f'</div>'
        )
    return "\n".join(rows)


def _render_takeaways(items: list) -> str:
    rows = []
    for i, item in enumerate(items):
        text = item if isinstance(item, str) else item.get("text", "")
        rows.append(
            f'<div class="sum-item">'
            f'<span class="sum-num">{i+1}.</span>'
            f'<span class="sum-text">{text}</span>'
            f'</div>'
        )
    return "\n".join(rows)


def _render_criteria(criteria: list) -> str:
    rows = []
    for c in criteria:
        weight = c.get("weight", 50)
        rows.append(
            f'<div class="criterion-card">'
            f'<div class="criterion-name">{c.get("name","")}</div>'
            f'<div class="criterion-weight">权重 {weight}%</div>'
            f'<div class="weight-bar"><div class="weight-fill" style="width:{weight}%"></div></div>'
            f'</div>'
        )
    return "\n".join(rows)


def _render_stakeholders(stakeholders: list) -> str:
    rows = []
    for sh in stakeholders:
        stance = sh.get("stance", "neutral")
        stance_map = {"support": ("stance-support", "支持"), "oppose": ("stance-oppose", "反对"), "neutral": ("stance-neutral", "中立")}
        stance_class, stance_text = stance_map.get(stance, ("stance-neutral", "中立"))
        initials = sh.get("name", "?")[:1]
        rows.append(
            f'<div class="stakeholder-item">'
            f'<div class="sh-avatar">{initials}</div>'
            f'<div><div class="sh-name">{sh.get("name","")}</div>'
            f'<div class="sh-role">{sh.get("role","")}</div></div>'
            f'<span class="sh-stance {stance_class}">{stance_text}</span>'
            f'</div>'
        )
    return "\n".join(rows)


def _render_risks(risks: list) -> str:
    rows = []
    for r in risks:
        level = r.get("level", "medium")
        level_map = {"high": "risk-high", "medium": "risk-medium", "low": "risk-low"}
        level_text = {"high": "高", "medium": "中", "low": "低"}
        rows.append(
            f'<div class="risk-item">'
            f'<span class="risk-level {level_map.get(level,"risk-medium")}">{level_text.get(level,"中")}</span>'
            f'<div class="risk-body">'
            f'<div class="risk-title">{r.get("title","")}</div>'
            f'<div class="risk-mitigation">应对：{r.get("mitigation","")}</div>'
            f'</div></div>'
        )
    return "\n".join(rows)


def _render_actions(actions: list) -> str:
    rows = []
    for a in actions:
        if isinstance(a, str):
            rows.append(f'<li>{a}</li>')
        else:
            text = a.get("text", "")
            owner = a.get("owner", "")
            deadline = a.get("deadline", "")
            owner_html = f'<span class="action-meta"><span>{owner}</span><span>{deadline}</span></span>' if owner or deadline else ""
            rows.append(
                f'<div class="action-item">'
                f'<div class="action-check"></div>'
                f'<div class="action-text">{text}{owner_html}</div>'
                f'</div>'
            )
    return "\n".join(rows)


def _render_data_points(points: list) -> str:
    rows = []
    for p in points:
        trend = p.get("trend", "flat")
        delta_class = {"up": "delta-up", "down": "delta-down", "flat": "delta-flat"}.get(trend, "delta-flat")
        rows.append(
            f'<div class="data-card">'
            f'<div class="data-val">{p.get("val","")}</div>'
            f'<div class="data-label">{p.get("label","")}</div>'
            f'<div class="data-delta {delta_class}">{p.get("delta","")}</div>'
            f'</div>'
        )
    return "\n".join(rows)


def _render_signals(signals: list) -> str:
    rows = []
    for s in signals:
        sentiment = s.get("sentiment", "neutral")
        rows.append(
            f'<div class="signal-card {sentiment}">'
            f'<div class="signal-source">{s.get("source","")}</div>'
            f'<div class="signal-text">{s.get("text","")}</div>'
            f'<div class="signal-impact">{s.get("impact","")}</div>'
            f'</div>'
        )
    return "\n".join(rows)


def _render_events(events: list) -> str:
    rows = []
    for e in events:
        rows.append(
            f'<div class="event-item">'
            f'<div class="event-left"><span class="event-time">{e.get("time","")}</span><div class="event-line"></div></div>'
            f'<div class="event-body">'
            f'<div class="event-title">{e.get("title","")}</div>'
            f'<div class="event-desc">{e.get("desc","")}</div>'
            f'</div></div>'
        )
    return "\n".join(rows)


def _render_options(options: list) -> str:
    rows = []
    for i, opt in enumerate(options):
        recommended = opt.get("recommended", False)
        rec_class = " recommended" if recommended else ""
        badge_class = "badge-rec" if recommended else "badge-alt"
        badge_text = "推荐" if recommended else f"方案{i+1}"
        pros = "".join(f"<li>{p}</li>" for p in opt.get("pros", []))
        cons = "".join(f"<li>{c}</li>" for c in opt.get("cons", []))
        effort = opt.get("effort", "")
        risk = opt.get("risk", "")
        metrics_html = ""
        if effort or risk:
            metrics_html = (
                f'<div class="option-metrics">'
                f'<div class="metric-pill"><div class="mp-val">{effort}</div><div class="mp-key">工作量</div></div>'
                f'<div class="metric-pill"><div class="mp-val">{risk}</div><div class="mp-key">风险</div></div>'
                f'</div>'
            )
        rows.append(
            f'<div class="option-card{rec_class}">'
            f'<div class="option-header">'
            f'<span class="option-num">方案 {i+1}</span>'
            f'<span class="option-badge {badge_class}">{badge_text}</span>'
            f'</div>'
            f'<div class="option-name">{opt.get("name","")}</div>'
            f'<div class="option-desc">{opt.get("desc","")}</div>'
            f'<div class="option-divider"></div>'
            f'<div class="pros-cons-grid">'
            f'<div class="pc-col pros"><div class="pc-label pros">优点</div><ul>{pros}</ul></div>'
            f'<div class="pc-col cons"><div class="pc-label cons">缺点</div><ul>{cons}</ul></div>'
            f'</div>'
            f'{metrics_html}'
            f'</div>'
        )
    return "\n".join(rows)


def _render_compare_rows(rows: list) -> str:
    html = []
    for row in rows:
        dim = row.get("dim", "")
        cells = row.get("cells", [])
        tds = "".join(f'<td>{c}</td>' for c in cells)
        html.append(f'<tr><td>{dim}</td>{tds}</tr>')
    return "\n".join(html)


def _render_next_steps(steps: list) -> str:
    rows = []
    for i, step in enumerate(steps):
        if isinstance(step, str):
            text, owner = step, ""
        else:
            text = step.get("text", "")
            owner = step.get("owner", "")
        owner_html = f'<div class="step-owner">负责人：{owner}</div>' if owner else ""
        rows.append(
            f'<div class="step-item">'
            f'<div class="step-num">{i+1}</div>'
            f'<div class="step-body">'
            f'<div class="step-text">{text}</div>'
            f'{owner_html}'
            f'</div></div>'
        )
    return "\n".join(rows)


def _render_root_causes(causes: list) -> str:
    rows = []
    for item in causes:
        rows.append(
            f'<div class="cause-item">'
            f'<div class="cause-left"><div class="cause-dot"></div><div class="cause-line"></div></div>'
            f'<div class="cause-body">'
            f'<div class="cause-label">{item.get("label","")}</div>'
            f'<div class="cause-text">{item.get("text","")}</div>'
            f'</div></div>'
        )
    return "\n".join(rows)


def _render_solutions(solutions: list) -> str:
    rows = []
    for sol in solutions:
        recommended = sol.get("recommended", False)
        rec_class = " recommended" if recommended else ""
        tag_class = "tag-recommended" if recommended else "tag-alternative"
        tag_text = "推荐" if recommended else "备选"
        pros = "".join(f"<li>{p}</li>" for p in sol.get("pros", []))
        cons = "".join(f"<li>{c}</li>" for c in sol.get("cons", []))
        rows.append(
            f'<div class="solution-card{rec_class}">'
            f'<div class="solution-header">'
            f'<span class="solution-name">{sol.get("name","")}</span>'
            f'<span class="solution-tag {tag_class}">{tag_text}</span>'
            f'</div>'
            f'<div class="solution-desc">{sol.get("desc","")}</div>'
            f'<div class="solution-pros-cons">'
            f'<ul class="pros"><div class="pros-label">优点</div>{pros}</ul>'
            f'<ul class="cons"><div class="cons-label">缺点</div>{cons}</ul>'
            f'</div></div>'
        )
    return "\n".join(rows)


def _render_list(items: list, field_hint: str = "") -> str:
    if not items:
        return ""
    if not isinstance(items[0], dict):
        return "\n".join(f'<div class="list-item">{i}</div>' for i in items)

    rows = []
    for item in items:
        # participants → tags
        if field_hint == "participants" or (isinstance(item, str)):
            rows.append(f'<span class="participant-tag">{item}</span>')
        # todos
        elif "owner" in item or "deadline" in item:
            rows.append(
                f'<div class="todo-item">'
                f'<div class="todo-checkbox"></div>'
                f'<div class="todo-body">'
                f'<span class="todo-text">{item.get("text","")}</span>'
                f'<div class="todo-meta">'
                f'<span class="todo-owner">{item.get("owner","")}</span>'
                f'<span class="todo-deadline">{item.get("deadline","")}</span>'
                f'</div></div></div>'
            )
        # decisions
        elif field_hint == "decisions":
            rows.append(
                f'<div class="decision-item">'
                f'<div class="decision-dot"></div>'
                f'<span>{item.get("text","")}</span>'
                f'</div>'
            )
        # chapters — timeline layout
        elif "time" in item and "title" in item:
            rows.append(
                f'<div class="chapter-item">'
                f'<div class="chapter-left">'
                f'<span class="chapter-time">{item.get("time","")}</span>'
                f'<div class="chapter-line"></div>'
                f'</div>'
                f'<div class="chapter-body">'
                f'<div class="chapter-title">{item.get("title","")}</div>'
                f'<div class="chapter-summary">{item.get("summary","")}</div>'
                f'</div>'
                f'</div>'
            )
        # done/doing/blocked tasks
        elif "tag" in item:
            status = item.get("status", field_hint.replace("_tasks", "") or "done")
            rows.append(
                f'<div class="task-item {status}">'
                f'<div class="task-status-dot"></div>'
                f'<span class="task-text">{item.get("text","")}</span>'
                f'<span class="task-tag">{item.get("tag","")}</span>'
                f'</div>'
            )
        # next tasks (numbered)
        elif field_hint in ("next_tasks", "next_plans"):
            priority = item.get("priority", "p2")
            rows.append(
                f'<div class="plan-item">'
                f'<span class="plan-priority {priority}">{priority.upper()}</span>'
                f'<span>{item.get("text","")}</span>'
                f'</div>'
            )
        # okr items
        elif "pct" in item:
            pct = item.get("pct", 0)
            rows.append(
                f'<div class="okr-item">'
                f'<div class="okr-header">'
                f'<span class="okr-name">{item.get("name","")}</span>'
                f'<span class="okr-pct">{pct}%</span>'
                f'</div>'
                f'<div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div>'
                f'</div>'
            )
        # metrics
        elif "label" in item and "val" in item and "delta" in item:
            trend = item.get("trend", "flat")
            rows.append(
                f'<div class="metric-card">'
                f'<div class="metric-val">{item.get("val","")}<span class="unit">{item.get("unit","")}</span></div>'
                f'<div class="metric-label">{item.get("label","")}</div>'
                f'<div class="metric-delta {trend}">{item.get("delta","")}</div>'
                f'</div>'
            )
        # big metrics
        elif "label" in item and "val" in item:
            trend = item.get("trend", "flat")
            rows.append(
                f'<div class="big-metric">'
                f'<div class="big-metric-val">{item.get("val","")}<span class="unit">{item.get("unit","")}</span></div>'
                f'<div class="big-metric-label">{item.get("label","")}</div>'
                f'<div class="big-metric-delta {trend}">{item.get("delta","")}</div>'
                f'</div>'
            )
        # highlights (weekly)
        elif "icon" in item and "impact" in item:
            rows.append(
                f'<div class="highlight-item">'
                f'<span class="highlight-icon">{item.get("icon","")}</span>'
                f'<div><div class="highlight-text">{item.get("text","")}</div>'
                f'<div class="highlight-impact">{item.get("impact","")}</div></div>'
                f'</div>'
            )
        # highlights (monthly timeline)
        elif "date" in item and "title" in item:
            rows.append(
                f'<div class="timeline-item">'
                f'<div class="timeline-left"><div class="timeline-dot"></div><div class="timeline-line"></div></div>'
                f'<div class="timeline-content">'
                f'<div class="timeline-title">{item.get("title","")}</div>'
                f'<div class="timeline-desc">{item.get("desc","")}</div>'
                f'<div class="timeline-date">{item.get("date","")}</div>'
                f'</div></div>'
            )
        # issues
        elif "icon" in item and "action" in item:
            rows.append(
                f'<div class="issue-item">'
                f'<span class="issue-icon">{item.get("icon","")}</span>'
                f'<div class="issue-body">'
                f'<div class="issue-title">{item.get("title","")}</div>'
                f'<div class="issue-action">应对：{item.get("action","")}</div>'
                f'</div></div>'
            )
        # next focus
        elif "num" in item:
            rows.append(
                f'<div class="focus-item">'
                f'<div class="focus-num">{item.get("num","")}</div>'
                f'<div class="focus-body">'
                f'<div class="focus-title">{item.get("title","")}</div>'
                f'<div class="focus-desc">{item.get("desc","")}</div>'
                f'</div></div>'
            )
        # retro items (strings in list)
        else:
            rows.append(f'<div class="retro-item">{item.get("text", str(item))}</div>')
    return "\n".join(rows)


def _screenshot(html_path: str, output_path: str):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 800, "height": 600})
        page.goto(f"file://{html_path}")
        page.wait_for_load_state("networkidle")
        time.sleep(0.5)
        # Auto-height: get actual content height
        height = page.evaluate("document.body.scrollHeight")
        page.set_viewport_size({"width": 800, "height": height})
        page.screenshot(path=output_path, full_page=True)
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render.py <template> <data.json> [output.png]")
        sys.exit(1)
    template = sys.argv[1]
    data = json.loads(Path(sys.argv[2]).read_text())
    out = sys.argv[3] if len(sys.argv) > 3 else None
    result = render(template, data, out)
    print(result)
