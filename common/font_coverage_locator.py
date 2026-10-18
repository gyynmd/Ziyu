#!/usr/bin/env python3
"""Read-only locator for apps that may not be using 字域's active font payload."""
from __future__ import annotations

import json
import os
import re
import signal
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from device_font_process_audit import PayloadIndex, inspect_process  # noqa: E402

PACKAGE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+(?::[A-Za-z0-9_.$-]+)?$")
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._+-]")
MAX_PID_ENTRIES = 1024
MAX_RUNNING_APPS = 96
MAX_SELECTED_PROCESSES = 3
MAX_SCAN_APPS = 24
MAX_SCAN_RESULTS = 16
MAX_FILES_PER_APP = 5
MAX_OUTPUT_BYTES = 24 * 1024
SCAN_BUDGET_SECONDS = 16.0
COMMAND_BUDGET_SECONDS = 22

GUIDES = {
    "not-running": ("应用当前未运行", "先打开目标应用并停留在要检查的界面，再返回字域检测。"),
    "no-payload": ("没有找到已应用的字域字体负载", "先在字体库应用字体并完成所需重启，再检测应用。"),
    "unreadable": ("无法读取应用的字体映射", "请检查字域的 Root 授权和目标进程状态后重试。"),
    "stale-process": ("进程仍缓存旧字体", "目标进程映射的是旧 inode，而该 PID 的命名空间当前路径已指向字域字体。强行停止并重新打开应用后复查；系统界面可在重启后再查。"),
    "route-not-visible": ("目标进程命名空间没有看到字域字体文件", "该 PID 当前映射的 inode 与它自己命名空间中的字体路径一致，但该路径没有解析到字域 payload。先重新应用字体并检查挂载验证，再重新打开应用检测。"),
    "theme-source": ("应用读取了系统主题或字体服务目录中的字体", "此结果只说明进程打开了该路径；请检查 ColorOS 当前主题/字体设置。字域不会在此处修改主题设置。"),
    "app-source": ("应用还读取了非字域字体文件", "应用内置字体、下载字体或网页引擎字体可能不受系统字体覆盖控制；字域不能替换这些文件。"),
    "mixed": ("应用同时读取字域和其他系统字体", "系统可能按字重、语种或字体回退选择不同文件；请查看列出的字体名，并在重开应用后复查。"),
    "system-font": ("当前映射的系统字体不属于字域负载", "请先确认字域字体已经应用并完成所需重启，然后重新打开目标应用检测。"),
    "covered": ("已观察到的字体文件来自字域负载", "这只代表当前可见的文件映射；应用自绘文字、内置字体或共享内存字体仍可能不受此结果覆盖。"),
    "inconclusive": ("当前映射不足以判断字体来源", "Android 可能通过共享内存提供字体，或目标界面尚未打开；保持目标页面可见后再试。"),
}


class BudgetExpired(Exception):
    pass


def _alarm(_signum: int, _frame: Any) -> None:
    raise BudgetExpired


def _safe_name(value: str) -> str:
    return SAFE_NAME_RE.sub("_", value)[:96]


def running_processes(proc_root: Path = Path("/proc"), limit: int = MAX_RUNNING_APPS) -> tuple[dict[str, list[dict[str, str]]], bool]:
    """Read at most a bounded number of cmdlines and group package processes."""
    pids: list[int] = []
    truncated = False
    try:
        with os.scandir(proc_root) as entries:
            for entry in entries:
                if entry.name.isdigit():
                    pids.append(int(entry.name))
                    if len(pids) >= MAX_PID_ENTRIES:
                        truncated = True
                        break
    except OSError:
        return {}, False

    apps: dict[str, list[dict[str, str]]] = {}
    for pid_number in sorted(pids):
        try:
            with (proc_root / str(pid_number) / "cmdline").open("rb") as stream:
                raw = stream.read(257)
        except OSError:
            continue
        process_bytes = raw.split(b"\0", 1)[0]
        if len(process_bytes) > 256:
            continue
        process = process_bytes.decode("utf-8", "replace")
        if not PACKAGE_RE.fullmatch(process):
            continue
        package = process.split(":", 1)[0]
        if package not in apps and len(apps) >= limit:
            truncated = True
            break
        rows = apps.setdefault(package, [])
        # A process name can occur more than once during an app restart. Preserve
        # only the first PID for that process name, then prefer the main process.
        if any(row["process"] == process for row in rows):
            continue
        rows.append({"pid": str(pid_number), "process": process})

    for rows in apps.values():
        rows.sort(key=lambda row: (row["process"].partition(":")[0] != row["process"], int(row["pid"])))
    return apps, truncated


def _finding(category: str, files: list[str] | None = None, detail: str = "") -> dict[str, Any]:
    title, action = GUIDES[category]
    return {"category": category, "title": title, "action": action,
            "detail": _safe_name(detail) if detail else "",
            "files": [_safe_name(name) for name in (files or [])[:MAX_FILES_PER_APP]]}


def _process_identity(proc_root: Path, process: dict[str, str]) -> str | None:
    """Bind the selected package to the same process lifetime around maps reads."""
    try:
        directory = proc_root / process["pid"]
        with (directory / "cmdline").open("rb") as stream:
            command = stream.read(257).split(b"\0", 1)[0]
        if command != process["process"].encode("utf-8"):
            return None
        with (directory / "stat").open("rb") as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            return None
        fields = raw.rsplit(b") ", 1)[-1].split()
        token = fields[19]
        return token.decode("ascii") if token.isdigit() else None
    except (OSError, IndexError, KeyError, UnicodeError):
        return None


def _inspect_package(package: str, processes: list[dict[str, str]], payload: PayloadIndex,
                     deadline: float, proc_root: Path = Path("/proc")) -> dict[str, Any]:
    if not len(payload):
        return {"package": package, "verdict": "no-payload", "audited": 0,
                "findings": [_finding("no-payload")], "files": []}
    if not processes:
        return {"package": package, "verdict": "not-running", "audited": 0,
                "findings": [_finding("not-running")], "files": []}

    gathered: dict[tuple[str, str, bool, bool], None] = {}
    unreadable = 0
    memfd = 0
    map_truncated = False
    audited = 0
    for process in processes[:MAX_SELECTED_PROCESSES]:
        if time.monotonic() >= deadline:
            raise BudgetExpired
        pid = process["pid"]
        before = _process_identity(proc_root, process)
        if before is None:
            unreadable += 1
            continue
        report = inspect_process(pid, proc_root / pid / "root", payload, proc_root)
        if report["state"] != "ok" or _process_identity(proc_root, process) != before:
            unreadable += 1
            continue
        audited += 1
        memfd += int(report.get("memfd", 0))
        map_truncated = map_truncated or bool(report.get("truncated"))
        for item in report["items"]:
            gathered[(item["kind"], item["name"], bool(item["staleCache"]),
                      bool(item["routeNotVisible"]))] = None

    kinds = {kind for kind, _name, _stale, _route_missing in gathered}
    stale = [name for _kind, name, is_stale, _route_missing in gathered if is_stale]
    route_missing = [name for _kind, name, _stale, is_missing in gathered if is_missing]
    files = [{"kind": kind, "name": name, "staleCache": is_stale,
              "routeNotVisible": route_missing_item}
             for kind, name, is_stale, route_missing_item in list(gathered)[:MAX_FILES_PER_APP]]

    if audited == 0:
        verdict = "unreadable"
        findings = [_finding("unreadable", detail=f"{unreadable} 个进程不可读")]
    elif not gathered:
        verdict = "inconclusive"
        findings = [_finding("inconclusive", detail=f"共享内存字体段 {memfd} 个")]
    elif stale:
        verdict = "stale-process"
        findings = [_finding("stale-process", stale)]
    elif route_missing:
        verdict = "route-not-visible"
        findings = [_finding("route-not-visible", route_missing)]
    elif "unknown" in kinds:
        verdict = "inconclusive"
        findings = [_finding("inconclusive", [name for kind, name, _, _ in gathered if kind == "unknown"])]
    elif "theme" in kinds:
        verdict = "theme-source"
        findings = [_finding("theme-source", [name for kind, name, _, _ in gathered if kind == "theme"])]
    elif "other" in kinds or "updatable" in kinds:
        verdict = "app-source"
        private_files = [name for kind, name, _, _ in gathered if kind in ("other", "updatable")]
        findings = [_finding("app-source", private_files)]
    elif "stock" in kinds and "payload" in kinds:
        verdict = "mixed"
        findings = [_finding("mixed", [name for kind, name, _, _ in gathered if kind == "stock"])]
    elif "stock" in kinds:
        verdict = "system-font"
        findings = [_finding("system-font", [name for kind, name, _, _ in gathered if kind == "stock"])]
    elif "payload" in kinds:
        verdict = "covered"
        findings = [_finding("covered", [name for kind, name, _, _ in gathered if kind == "payload"])]
    else:
        verdict = "inconclusive"
        findings = [_finding("inconclusive")]

    return {
        "package": package,
        "verdict": verdict,
        "audited": audited,
        "processCount": len(processes),
        "memfdFontSegments": memfd,
        "mapsTruncated": map_truncated,
        "findings": findings,
        "files": files,
    }


def _run(command: str, package_arg: str = "", proc_root: Path = Path("/proc")) -> dict[str, Any]:
    module_text = os.environ.get("MODDIR", "")
    if not module_text or not os.path.isabs(module_text):
        return {"status": "error", "message": "模块目录不可用"}
    module = Path(module_text)
    if command == "locate" and not PACKAGE_RE.fullmatch(package_arg):
        return {"status": "error", "message": "应用包名格式不正确"}

    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(COMMAND_BUDGET_SECONDS)
    try:
        process_limit = MAX_PID_ENTRIES if command == "locate" else MAX_RUNNING_APPS
        apps, process_truncated = running_processes(proc_root=proc_root, limit=process_limit)
        if command == "running":
            rows = [{"package": package, "processCount": len(processes)}
                    for package, processes in list(apps.items())[:MAX_RUNNING_APPS]]
            data = {"packages": rows, "truncated": process_truncated or len(apps) > MAX_RUNNING_APPS}
            return {"status": "ok", "data": data}

        payload = PayloadIndex(module)
        def checked(data: dict[str, Any]) -> dict[str, Any]:
            if len(payload) and not payload.current():
                return {"status": "error", "message": "扫描期间字体已切换，请等待应用完成后重试。"}
            return {"status": "ok", "data": data}
        if command == "locate":
            data = _inspect_package(package_arg.split(":", 1)[0], apps.get(package_arg.split(":", 1)[0], []),
                                    payload, time.monotonic() + SCAN_BUDGET_SECONDS, proc_root)
            data["truncated"] = process_truncated
            return checked(data)

        if command != "scan":
            return {"status": "error", "message": "未知诊断命令"}
        if not len(payload):
            return {"status": "ok", "data": {"verdict": "no-payload", "scanned": 0,
                    "covered": 0, "uncertain": 0, "items": [], "truncated": process_truncated}}
        packages = list(apps.items())
        truncated = process_truncated or len(packages) > MAX_SCAN_APPS
        deadline = time.monotonic() + SCAN_BUDGET_SECONDS
        items: list[dict[str, Any]] = []
        covered = 0
        uncertain = 0
        scanned = 0
        for package, processes in packages[:MAX_SCAN_APPS]:
            if time.monotonic() >= deadline:
                truncated = True
                break
            try:
                item = _inspect_package(package, processes, payload, deadline, proc_root)
            except BudgetExpired:
                truncated = True
                break
            scanned += 1
            if item["verdict"] == "covered":
                covered += 1
            elif item["verdict"] == "inconclusive":
                uncertain += 1
                if len(items) < MAX_SCAN_RESULTS:
                    items.append(item)
            elif len(items) < MAX_SCAN_RESULTS:
                items.append(item)
        data = {
            "verdict": "ok",
            "scanned": scanned,
            "covered": covered,
            "uncertain": uncertain,
            "items": items,
            "truncated": truncated or scanned < len(packages),
        }
        return checked(data)
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0] if args else ""
    package = args[1] if len(args) > 1 else ""
    valid_arity = (command in ("running", "scan") and len(args) == 1) or (command == "locate" and len(args) == 2)
    if not valid_arity:
        result: dict[str, Any] = {"status": "error", "message": "诊断参数无效"}
    else:
        try:
            result = _run(command, package)
        except BudgetExpired:
            result = {"status": "error", "message": "扫描超过安全时限，请缩小范围后重试"}
        except Exception as error:
            result = {"status": "error", "message": f"诊断失败：{error.__class__.__name__}"}

    encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_OUTPUT_BYTES:
        encoded = json.dumps({"status": "error", "message": "诊断结果超过安全输出上限，请重试"},
                             ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write(encoded + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
