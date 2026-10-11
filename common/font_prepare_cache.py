"""Content-addressed preparation cache. Cached warnings are replayed on every use."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def copy_atomic(source, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + f".{os.getpid()}.copy")
    try:
        shutil.copyfile(source, temporary)
        os.chmod(temporary, 0o644)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def prune(cache_dir, protected=()):
    cache_dir = Path(cache_dir)
    protected = {Path(path) for path in protected}
    total = 0
    for cached in sorted(cache_dir.glob("*.ttf"), key=lambda path: path.stat().st_mtime, reverse=True):
        total += cached.stat().st_size
        if total > 384 * 1024 * 1024 and cached not in protected:
            cached.unlink(missing_ok=True)
            cached.with_suffix(".json").unlink(missing_ok=True)


def prepare(source, output, role, weight, axes, cache_dir, materialize, engine_path, face_selector=None):
    from fontTools import __version__
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    source_digest = digest(source)
    face = face_selector(Path(source), role, weight) if face_selector is not None else None
    # Collection roles may choose different faces: share only the exact selected
    # face, and only when the materializer supplies the shared donor contract.
    cache_role = "donor" if face_selector is not None and role in ("latin", "digit") else role
    key_data = {"schema": 2, "source": source_digest, "engine": digest(engine_path),
                "cacheEngine": digest(__file__), "fontTools": __version__, "role": cache_role, "face": face,
                "weight": weight, "axes": axes}
    key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    font = cache_dir / f"{key}.ttf"
    report_file = cache_dir / f"{key}.json"
    report = None
    try:
        saved = json.loads(report_file.read_text(encoding="utf-8"))
        if (font.is_file() and not font.is_symlink() and not report_file.is_symlink()
                and isinstance(saved["report"], dict) and digest(font) == saved["outputSha256"]):
            report = saved["report"]
            expected_digest = saved["outputSha256"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if report is None:
        temporary = cache_dir / f"{key}.{os.getpid()}.tmp"
        try:
            report = materialize(Path(source), temporary, role, weight, axes)
            # A source being replaced during calculation cannot populate the cache.
            if (digest(source) != key_data["source"] or digest(engine_path) != key_data["engine"]
                    or digest(__file__) != key_data["cacheEngine"]):
                raise ValueError("字体源文件在处理过程中发生变化，请重新应用")
            checksum = digest(temporary)
            expected_digest = checksum
            os.replace(temporary, font)
            metadata = report_file.with_name(report_file.name + f".{os.getpid()}.tmp")
            metadata.write_text(json.dumps({"outputSha256": checksum, "report": report},
                                           ensure_ascii=False), encoding="utf-8")
            os.replace(metadata, report_file)
        finally:
            temporary.unlink(missing_ok=True)
        hit = False
    else:
        hit = True
    copy_atomic(font, output)
    if (digest(source) != key_data["source"] or digest(engine_path) != key_data["engine"]
            or digest(__file__) != key_data["cacheEngine"] or digest(output) != expected_digest):
        Path(output).unlink(missing_ok=True)
        raise ValueError("字体源、引擎或缓存内容在处理过程中发生变化，请重新应用")
    os.utime(font, None)
    # Bound only this private cache. Output files are independent copies.
    if os.environ.get("ZIYU_DEFER_PREPARE_CACHE_CLEANUP") != "1":
        prune(cache_dir, protected=(font,))
    return {**report, "source": str(source), "output": str(output), "role": role, "cacheHit": hit}


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--prune":
    prune(sys.argv[2])
