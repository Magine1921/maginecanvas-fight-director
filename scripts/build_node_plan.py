#!/usr/bin/env python3
"""Build and validate a platform-neutral storyboard and node plan for MagineCanvas.

Python 3.10+, standard library only. No model calls and no native canvas import.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

VERSION = "0.1.0"

class PlanError(ValueError):
    """Invalid brief or workflow plan."""

def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise PlanError(f"{name} must be a nonempty string")
    return value.strip()

def _ticks(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PlanError(f"{name} must be a number")
    n = round(value * 10)
    if n < 1 or abs(value * 10 - n) > 1e-6:
        raise PlanError(f"{name} must be a positive multiple of 0.1 seconds")
    return n

def _sec(ticks):
    return round(ticks / 10, 1)

def validate_brief(brief):
    if not isinstance(brief, dict):
        raise PlanError("brief must be an object")
    for k in ("title", "aspect_ratio", "style", "location", "goal", "ending"):
        _required(brief.get(k), k)
    duration = _ticks(brief.get("duration_seconds"), "duration_seconds")
    if not 20 <= duration <= 1800:
        raise PlanError("duration must be 2-180 seconds")
    chars = brief.get("characters")
    if not isinstance(chars, list) or len(chars) < 2:
        raise PlanError("at least two characters required")
    ids = set()
    for i, c in enumerate(chars):
        if not isinstance(c, dict):
            raise PlanError(f"character {i} must be an object")
        for k in ("id", "name", "appearance", "weapon"):
            _required(c.get(k), k)
        if c["id"] in ids or c["id"] in ("LOC-1", "STYLE-1", "EDIT-1"):
            raise PlanError("duplicate/reserved character ID")
        ids.add(c["id"])
    beats = brief.get("beats")
    if not isinstance(beats, list) or not beats:
        raise PlanError("beats must be a nonempty list")
    total = 0
    for i, beat in enumerate(beats):
        if not isinstance(beat, dict):
            raise PlanError(f"beat {i} must be an object")
        for k in ("action", "camera", "entry_state", "exit_state"):
            _required(beat.get(k), k)
        total += _ticks(beat.get("duration_seconds"), f"beat {i}")
    if total != duration:
        raise PlanError(f"beats total {_sec(total)}s; expected {_sec(duration)}s")

def make_plan(brief):
    validate_brief(brief)
    chars = brief["characters"]
    project = {k: brief[k] for k in ("title", "duration_seconds", "aspect_ratio", "style", "location", "goal", "ending")}
    assets = {
        "characters": [dict(c, reference_file=None) for c in chars],
        "location": {"id": "LOC-1", "description": brief["location"], "reference_file": None},
        "style": {"id": "STYLE-1", "description": brief["style"]},
    }
    nodes = [{"id": c["id"], "type": "reference", "label": f"角色参考 / {c['name']}",
              "dependencies": [], "batch_group": None, "prompt": f"{c['name']}：{c['appearance']}；{c['weapon']}"}
             for c in chars]
    nodes.extend([
        {"id": "LOC-1", "type": "reference", "label": "场景参考", "dependencies": [], "batch_group": None, "prompt": brief["location"]},
        {"id": "STYLE-1", "type": "style", "label": "共享画风", "dependencies": [], "batch_group": None, "prompt": brief["style"]},
    ])
    anchors = "；".join(f"{c['id']} {c['name']}：{c['appearance']}；{c['weapon']}" for c in chars)
    shots, tick, prior = [], 0, None
    avoid = "人物面容漂移、衣服变化、错手持物、多余四肢、武器穿透、瞬间换位、无接触却被击退、突兀越轴"
    for i, beat in enumerate(brief["beats"], 1):
        sid = f"S{i:02d}"
        span = _ticks(beat["duration_seconds"], sid)
        entry, action, camera, exit_state = (beat[k] for k in ("entry_state", "action", "camera", "exit_state"))
        vfx = beat.get("vfx", "环境随动作发生真实反应")
        key = (f"【{sid} 关键帧】{brief['style']}，{brief['aspect_ratio']}；场景：{brief['location']}。"
               f"角色锁定：{anchors}。入镜：{entry}。构图：{camera}。突出可辨认的动作关键瞬间。")
        video = (f"【{sid} 视频 {_sec(span)}秒】沿用角色与场景参考。入场：{entry}。"
                 f"连续动作：{action}。摄影机：{camera}。环境反馈：{vfx}。"
                 f"结束：{exit_state}。保持物理因果和动作空间连续性。")
        note = ("请人工核对上镜离场与本镜入场能否无缝衔接" if prior is not None and prior != entry
                else "检查实际画面状态和相邻镜头衔接")
        shots.append({
            "shot_id": sid, "time": {"start_sec": _sec(tick), "end_sec": _sec(tick + span), "duration_sec": _sec(span)},
            "entry_state": entry, "action": action, "camera": camera, "vfx": vfx,
            "exit_state": exit_state, "continuity_note": note, "prompt_keyframe": key,
            "prompt_video": video, "avoid": avoid, "batch_groups": {"keyframe": "keyframe-pass", "video": "video-pass"},
        })
        inputs = [c["id"] for c in chars] + ["LOC-1", "STYLE-1"]
        nodes.extend([
            {"id": sid+"-KF", "type": "image_generation", "label": sid+" 关键帧", "dependencies": inputs,
             "batch_group": "keyframe-pass", "prompt": key},
            {"id": sid+"-VIDEO", "type": "video_generation", "label": sid+" 视频",
             "dependencies": inputs + [sid+"-KF"], "batch_group": "video-pass", "prompt": video},
            {"id": sid+"-QA", "type": "manual_review", "label": sid+" 复核",
             "dependencies": [sid+"-VIDEO"], "batch_group": None, "prompt": note + "；避免：" + avoid},
        ])
        prior, tick = exit_state, tick + span
    nodes.append({
        "id": "EDIT-1", "type": "edit", "label": "终版拼接",
        "dependencies": [s["shot_id"]+"-QA" for s in shots], "batch_group": None,
        "prompt": f"顺序拼接，总长{brief['duration_seconds']}秒；片尾：{brief['ending']}",
    })
    plan = {
        "schema_version": VERSION, "project": project, "assets": assets, "shots": shots,
        "workflow": {
            "format": "maginecanvas-neutral-plan", "native_import_supported": False,
            "nodes": nodes, "edges": [{"from": d, "to": n["id"]} for n in nodes for d in n["dependencies"]],
            "batching": {"keyframe-pass": "先框选所有关键帧图像节点，审核后继续",
                         "video-pass": "审核通过后框选所有视频节点，参数不同则拆批"},
        },
        "limitations": ["本文件不是 MagineCanvas 官方原生导入格式", "不会自动调用模型或操作无限画布"],
    }
    validate_plan(plan)
    return plan

def validate_plan(plan):
    if not isinstance(plan, dict) or plan.get("schema_version") != VERSION:
        raise PlanError("unsupported schema version")
    p, shots, wf = plan.get("project"), plan.get("shots"), plan.get("workflow")
    if not isinstance(p, dict) or not isinstance(shots, list) or not shots or not isinstance(wf, dict):
        raise PlanError("missing project, shots, or workflow")
    expected_duration = _ticks(p.get("duration_seconds"), "project duration")
    t = 0
    for i, shot in enumerate(shots, 1):
        if shot.get("shot_id") != f"S{i:02d}":
            raise PlanError("shot numbering invalid")
        tm = shot.get("time", {})
        a, b, d = (round(tm.get(k, -1)*10) for k in ("start_sec", "end_sec", "duration_sec"))
        if a != t or b <= a or b-a != d:
            raise PlanError("noncontiguous shot timeline")
        for k in ("prompt_keyframe", "prompt_video", "entry_state", "exit_state"):
            _required(shot.get(k), k)
        t = b
    if t != expected_duration:
        raise PlanError("wrong total duration")
    if wf.get("format") != "maginecanvas-neutral-plan" or wf.get("native_import_supported") is not False:
        raise PlanError("workflow must declare non-native format")
    nodes, edges = wf.get("nodes"), wf.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise PlanError("missing nodes or edges")
    index = {}
    for n in nodes:
        nid = _required(n.get("id"), "node ID")
        if nid in index or not isinstance(n.get("dependencies"), list):
            raise PlanError("duplicate node or invalid dependencies")
        index[nid] = n
    expected = {(d, n["id"]) for n in nodes for d in n["dependencies"]}
    actual = {(e.get("from"), e.get("to")) for e in edges}
    if expected != actual or len(edges) != len(actual):
        raise PlanError("edges do not match dependencies")
    visiting, done = set(), set()
    def visit(nid):
        if nid in visiting: raise PlanError("dependency cycle")
        if nid in done: return
        if nid not in index: raise PlanError("unknown dependency")
        visiting.add(nid)
        for d in index[nid]["dependencies"]: visit(d)
        visiting.remove(nid)
        done.add(nid)
    for nid in index: visit(nid)
    if "EDIT-1" not in index: raise PlanError("EDIT-1 missing")

def render_markdown(plan):
    validate_plan(plan)
    p = plan["project"]
    lines = [
        f"# {p['title']} | 打戏制作计划", "",
        f"- 总时长：{p['duration_seconds']}秒；画幅：{p['aspect_ratio']}；风格：{p['style']}",
        f"- 场景：{p['location']}", f"- 剧情目标：{p['goal']}", f"- 片尾：{p['ending']}",
        "", "## 镜头时间轴", "",
        "| 镜头 | 时间 | 动作 | 摄影 |", "|---|---|---|---|",
    ]
    for s in plan["shots"]:
        tm = s["time"]
        lines.append(f"| {s['shot_id']} | {tm['start_sec']:g}–{tm['end_sec']:g}s | {s['action']} | {s['camera']} |")
    lines.extend(["", "## 每镜节点提示词", ""])
    for s in plan["shots"]:
        lines.extend([f"### {s['shot_id']}", "", "**关键帧 / 生图节点**", "",
                      s["prompt_keyframe"], "", "**视频节点**", "", s["prompt_video"], "",
                      "**避错与衔接**", "", f"- 避免：{s['avoid']}",
                      f"- 审核：{s['continuity_note']}", ""])
    lines.extend(["## 无限画布批量组", "",
                  "- \`keyframe-pass\`：框选所有 \`Sxx-KF\` 节点先批量生图并审核。",
                  "- \`video-pass\`：关键帧审核后框选所有 \`Sxx-VIDEO\` 节点。",
                  "- \`Sxx-QA\` 和 \`EDIT-1\`：人工复核和拼接，不是生成节点。",
                  "", "**注意**：本文件不是 MagineCanvas 官方原生导入格式。", ""])
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()
    try:
        plan = make_plan(json.loads(args.brief.read_text(encoding="utf-8")))
        body = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(body, encoding="utf-8")
        else: print(body)
        if args.md_out:
            args.md_out.parent.mkdir(parents=True, exist_ok=True)
            args.md_out.write_text(render_markdown(plan), encoding="utf-8")
        import sys
        print(f"Validated {len(plan['shots'])} shots / {len(plan['workflow']['nodes'])} nodes", file=sys.stderr)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")

if __name__ == "__main__":
    main()
