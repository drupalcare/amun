#!/usr/bin/env python3
"""CSS layers check: the shared lint for the Flash Web Center CSS standard.

One script, the same in every project. Each project describes itself in a
JSON manifest (default: css-layers.json at the project root). Python 3.9+,
standard library only, reads files, changes nothing.

Usage:
  python3 scripts/css-layers-check.py [--manifest PATH] [--root DIR]
  python3 scripts/css-layers-check.py --self-test

Checks (each code is printed with every failure):
  L1  The ladder is declared once, in the manifest's ladder file, and names
      exactly the manifest's layers in the same order.
  L2  Every CSS file under the manifest's css_dirs is listed (layer list,
      "unlayered: <reason>", "admin", or "pending: <reason>" while a build
      moves it; pending files are counted in the summary, not checked), or
      "ignored: <reason>" for a file no library loads.
  L3  A layered file puts every rule inside @layer blocks it is allowed to use.
      An unlayered or admin file uses no @layer at all. A layered file whose
      spec carries "unlayered_tail": "<reason>" may also end with plain rules
      (the declarations that must beat unlayered core, contrib or PB CSS and
      so cannot sit in a layer); those follow the unlayered rules (A1 roots).
  L4  No anonymous @layer block, and no @layer name outside the ladder.
  L5  No @import ... layer(...): Drupal's aggregator does not handle it.
  L6  !important only where a value must never change: inside the manifest's
      locked layer (the FIRST layer of the ladder, so its !important beats
      every other layer and all unlayered !important), or on a selector in
      important_allow with a written reason. Anywhere else it fails, and in
      layered CSS it is reported by property for display, position,
      visibility, clip, clip-path, inset, z-index and pointer-events.
  L7  No hex, rgb() or hsl() color literal in layered CSS outside the tokens
      layer (admin files and files marked colors_ok are exempt).
  A1  In unlayered (module) files every selector starts from one of the
      manifest's roots. In layered files a bare element selector is allowed
      only in the base or reset layer.
  A2  No front-end selector names an admin part (contextual links, toolbar,
      Claro, Gin, Layout Builder, off-canvas, dialogs, messages, tabs,
      data-drupal attributes, visually-hidden), unless inside :not(...) or
      listed in the manifest's admin_allow (selector text -> written reason)
      for front-end restyles the owner approved.
  D1  The ladder file is in a library at css base weight -1000 or lower.

Sub-themes: a manifest with "ladder_parent": "<parent theme machine name>" owns
no ladder file. The ladder is read from the parent's css-layers.json when the
parent is found (the folder one level up, a sibling folder named like the
parent, "../d8w3css", or a composer path); L1 and D1 then run against the
parent's ladder only through the layer names. When the parent is not found the
checker says so and skips every check that needs the ladder (L1, L4, D1).

Exit 0 when clean, 1 when a check fails, 2 when the manifest is unusable.
What it cannot see: CSS added from PHP or JS at runtime, inline styles, and
whether a library is actually attached on admin routes (a person checks that
at release, rule A6 of the standard).
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys

ADMIN_PATTERNS = [
    r"\.contextual\b", r"\.contextual-links\b", r"\.toolbar\b", r"#toolbar-",
    r"\.gin-", r"\.claro-", r"\.layout-builder", r"#drupal-off-canvas",
    r"\.ui-dialog", r"\.messages\b", r"\.tabs\b", r"\.local-tasks",
    r"\[data-drupal-", r"\.visually-hidden\b",
]
GUARDED_PROPS = {"display", "position", "visibility", "clip", "clip-path",
                 "inset", "z-index", "pointer-events"}
COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")
ELEMENT_START = re.compile(r"^(?:html|body|[a-z][a-z0-9]*)(?=$|[\s.:#\[>+~,])")


def strip_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), text, flags=re.S)


def blank_strings(text: str) -> str:
    """Replace string contents with spaces so braces inside them are ignored."""
    return re.sub(r"(['\"])(?:\\.|(?!\1).)*\1", lambda m: m.group(0)[0] + " " * (len(m.group(0)) - 2) + m.group(0)[0], text)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def parse(text: str):
    """Yield (kind, data) items with their enclosing layer stack.

    kind: 'layer-statement' (names), 'layer-block' (name or ''), 'import' (raw),
    'rule' (selector, body, layers, pos).
    """
    src = blank_strings(strip_comments(text))
    items = []
    stack = []

    def at(s: int) -> int:
        # Report the first real character, not the whitespace before it.
        while s < n and src[s].isspace():
            s += 1
        return s
  # entries: ('layer', name) | ('at', name) | ('rule', None)
    i, n, start = 0, len(src), 0
    while i < n:
        c = src[i]
        if c == ";" and not any(k == "rule" for k, _ in stack):
            head = src[start:i].strip()
            if head.startswith("@layer"):
                names = [x.strip() for x in head[6:].split(",") if x.strip()]
                items.append(("layer-statement", names, [s for k, s in stack if k == "layer"], at(start)))
            elif head.startswith("@import"):
                items.append(("import", head, [], at(start)))
            start = i + 1
        elif c == "{":
            head = src[start:i].strip()
            if head.startswith("@layer"):
                stack.append(("layer", head[6:].strip()))
                items.append(("layer-block", head[6:].strip(), [s for k, s in stack[:-1] if k == "layer"], at(start)))
            elif head.startswith("@"):
                stack.append(("at", head.split()[0]))
            else:
                # A style rule: capture its body to the matching brace.
                depth, j = 1, i + 1
                while j < n and depth:
                    if src[j] == "{":
                        depth += 1
                    elif src[j] == "}":
                        depth -= 1
                    j += 1
                in_keyframes = any(k == "at" and "keyframes" in s for k, s in stack)
                if not in_keyframes:
                    items.append(("rule", (head, src[i + 1:j - 1]), [s for k, s in stack if k == "layer"], at(start)))
                i = j
                start = j
                continue
            start = i + 1
        elif c == "}":
            if stack:
                stack.pop()
            start = i + 1
        i += 1
    return items


def split_selectors(head: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in head:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(" ".join(cur.split()))
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(" ".join(cur.split()))
    return out


def without_not(sel: str) -> str:
    """Drop :not(...) groups so excluded admin parts are not counted."""
    out, i = "", 0
    while i < len(sel):
        if sel.startswith(":not(", i):
            depth, j = 1, i + 5
            while j < len(sel) and depth:
                depth += {"(": 1, ")": -1}.get(sel[j], 0)
                j += 1
            i = j
            continue
        out += sel[i]
        i += 1
    return out


def declarations(body: str):
    for m in re.finditer(r"([a-zA-Z_-][a-zA-Z0-9_-]*)\s*:\s*([^;]+)", body):
        yield m.group(1).lower(), m.group(2)


def leaf(layer_path: list[str]) -> str:
    return ".".join(layer_path)


def check_css(rel: str, text: str, spec, manifest) -> list[str]:
    out = []
    ladder = manifest["ladder"]
    allowed = None
    kind = "layered"
    if spec == "admin":
        kind = "admin"
    elif isinstance(spec, str) and spec.startswith("unlayered"):
        kind = "unlayered"
    elif isinstance(spec, dict):
        allowed = spec.get("layers", [])
    else:
        allowed = list(spec)
    colors_ok = isinstance(spec, dict) and spec.get("colors_ok")
    tail_ok = isinstance(spec, dict) and bool(spec.get("unlayered_tail"))
    roots = manifest.get("roots", [])
    imp_allow = manifest.get("important_allow", {})
    if isinstance(imp_allow, list):
        imp_allow = {s: "" for s in imp_allow}
    locked = manifest.get("locked_layer")
    tokens_layer = manifest.get("tokens_layer")
    base_layers = set(manifest.get("element_layers", []))
    ladder_file = manifest.get("ladder_file")

    for kind_i, data, layers, pos in parse(text):
        at = f"{rel}:{line_of(text, pos)}"
        if kind_i == "import" and re.search(r"\blayer\s*\(|\blayer\b", data):
            out.append(f"L5 {at} @import with a layer")
        if kind_i == "layer-statement" and (rel != ladder_file or not ladder_file):
            out.append(f"L1 {at} layer order statement outside the ladder file")
        if kind_i == "layer-block":
            full = leaf(layers + [data]) if data else ""
            if not data:
                out.append(f"L4 {at} anonymous @layer block")
            elif kind != "layered":
                out.append(f"L3 {at} @layer {full} in a file listed as {kind}")
            elif ladder is not None and full not in ladder and not any(full.startswith(x + ".") for x in ladder):
                out.append(f"L4 {at} @layer {full} is not in the ladder")
            elif allowed is not None and full not in allowed and not any(full.startswith(x + ".") for x in allowed):
                out.append(f"L3 {at} @layer {full} not allowed for this file (allowed: {', '.join(allowed)})")
        if kind_i != "rule":
            continue
        head, body = data
        layer_name = leaf(layers)
        tail = kind == "layered" and not layers and tail_ok
        if kind == "layered" and not layers and not tail_ok:
            out.append(f"L3 {at} rule outside any @layer: {' '.join(head.split())[:60]}")
        sels = split_selectors(head)
        for sel in sels:
            bare = without_not(sel)
            allowed_admin = any(a in " ".join(sel.split()) for a in (manifest.get("admin_allow") or {}))
            if kind != "admin" and not allowed_admin:
                for pat in ADMIN_PATTERNS:
                    if re.search(pat, bare):
                        out.append(f"A2 {at} selector reaches admin UI: {sel[:70]}")
                        break
            if (kind == "unlayered" or tail) and roots and not allowed_admin and sel.strip() not in ("html", "body") and not any(r in sel for r in roots):
                out.append(f"A1 {at} selector not under a project root: {sel[:70]}")
            if kind == "layered" and not tail and not allowed_admin and ELEMENT_START.match(re.sub(r"^:where\(", "", sel).strip()) and layer_name not in base_layers and not any(r in sel for r in roots):
                out.append(f"A1 {at} bare element selector outside the base layers: {sel[:70]}")
        sel_allowed = any(a in head for a in imp_allow) or (locked and layer_name == locked)
        for prop, value in declarations(body):
            if "!important" in value and not sel_allowed and kind == "layered" and not tail:
                if prop in GUARDED_PROPS:
                    out.append(f"L6 {at} layered !important on {prop}")
                else:
                    out.append(f"L6 {at} !important on {prop} outside the locked layer and the allow-list")
            if (kind == "layered" and not tail and not colors_ok and layer_name != tokens_layer
                    and not prop.startswith("--") and COLOR_RE.search(value)):
                out.append(f"L7 {at} color literal in {prop} outside the tokens layer")
    return out


def find_parent(root: str, name: str):
    """Return the parent theme's manifest dict, or None when it is not found."""
    root = os.path.abspath(root)
    up = os.path.dirname(root)
    candidates = [
        up,
        os.path.join(up, name),
        os.path.join(up, "d8w3css"),
        os.path.join(os.path.dirname(up), "contrib", name),
        os.path.join(os.path.dirname(up), name),
    ]
    for c in candidates:
        mp = os.path.join(c, "css-layers.json")
        if os.path.isfile(mp):
            try:
                data = json.load(open(mp, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(data.get("ladder"), list):
                return data
    return None


def check_ladder(root: str, manifest) -> list[str]:
    out = []
    if manifest.get("ladder_parent"):
        return out
    locked = manifest.get("locked_layer")
    if locked and manifest["ladder"][:1] != [locked]:
        out.append(f"L6 locked layer {locked} must be the first layer of the ladder")
    for sel, why in (manifest.get("important_allow") or {}).items() if isinstance(manifest.get("important_allow"), dict) else []:
        if not str(why).strip():
            out.append(f"L6 important_allow entry {sel} has no reason")
    lf = manifest.get("ladder_file")
    path = os.path.join(root, lf or "")
    if not lf or not os.path.isfile(path):
        return [f"L1 ladder file missing: {lf}"]
    stmts = [d for k, d, _, _ in parse(open(path, encoding="utf-8").read()) if k == "layer-statement"]
    if len(stmts) != 1:
        out.append(f"L1 {lf} must hold exactly one layer order statement, found {len(stmts)}")
    elif stmts[0] != manifest["ladder"]:
        out.append(f"L1 {lf} order {stmts[0]} differs from the manifest {manifest['ladder']}")
    return out


def check_library(root: str, manifest) -> list[str]:
    if manifest.get("ladder_parent"):
        return []
    libfile = manifest.get("libraries_file")
    lf = manifest.get("ladder_file")
    if not libfile:
        return []
    path = os.path.join(root, libfile)
    if not os.path.isfile(path):
        return [f"D1 libraries file missing: {libfile}"]
    text = open(path, encoding="utf-8").read()
    # Drupal lists the file relative to the extension that owns the library.
    lf_rel = os.path.relpath(os.path.join(root, lf), os.path.dirname(path))
    m = re.search(r"(?m)^\s+" + re.escape(lf_rel) + r"\s*:\s*\{([^}]*)\}", text)
    if not m:
        return [f"D1 {libfile} does not load {lf}"]
    w = re.search(r"weight\s*:\s*(-?\d+)", m.group(1))
    if not w or int(w.group(1)) > -1000:
        return [f"D1 {libfile}: {lf} needs weight -1000 or lower"]
    # The nearest less-indented key above the entry must be "base:".
    lines = text[:m.end()].splitlines()
    entry_indent = len(lines[-1]) - len(lines[-1].lstrip()) if lines else 0
    for line in reversed(lines[:-1]):
        if not line.strip():
            continue
        ind = len(line) - len(line.lstrip())
        if ind < entry_indent:
            if line.strip() != "base:":
                return [f"D1 {libfile}: {lf} must sit under css base, found '{line.strip()}'"]
            break
    return []


def spec_for(rel: str, manifest):
    # An exact path entry wins over any glob, whatever the key order.
    if rel in manifest["files"]:
        return manifest["files"][rel]
    for pattern, spec in manifest["files"].items():
        if fnmatch.fnmatch(rel, pattern):
            return spec
    return None


def run(root: str, manifest) -> list[str]:
    manifest = dict(manifest)
    run.note = ""
    if manifest.get("ladder_parent"):
        for key in ("files", "css_dirs"):
            if key not in manifest:
                raise ValueError(f"manifest needs '{key}'")
        parent = find_parent(root, manifest["ladder_parent"])
        if parent is None:
            run.note = "ladder taken from parent, not found here: skipped"
            manifest["ladder"] = None
        else:
            manifest["ladder"] = parent["ladder"]
            run.note = f"ladder taken from parent {manifest['ladder_parent']}"
        manifest.setdefault("ladder_file", None)
    else:
        for key in ("ladder", "ladder_file", "files", "css_dirs"):
            if key not in manifest:
                raise ValueError(f"manifest needs '{key}'")
    out = check_ladder(root, manifest) + check_library(root, manifest)
    pending: list[str] = []
    for d in manifest["css_dirs"]:
        for base, dirs, files in os.walk(os.path.join(root, d)):
            dirs[:] = sorted(x for x in dirs if x not in ("tests", "node_modules", "vendor", ".git"))
            for f in sorted(files):
                if not f.endswith(".css"):
                    continue
                rel = os.path.relpath(os.path.join(base, f), root)
                spec = spec_for(rel, manifest)
                if spec is None:
                    out.append(f"L2 {rel} is not listed in the manifest")
                    continue
                if manifest["ladder_file"] and rel == manifest["ladder_file"]:
                    continue
                if isinstance(spec, str) and spec.startswith("ignored"):
                    continue
                if isinstance(spec, str) and spec.startswith("pending"):
                    pending.append(rel)
                    continue
                out += check_css(rel, open(os.path.join(base, f), encoding="utf-8", errors="replace").read(), spec, manifest)
    run.pending = pending
    return out


def self_test() -> int:
    m = {
        "ladder": ["p.locked", "p.reset", "p.tokens", "p.base", "p.theme", "p.utilities"],
        "locked_layer": "p.locked",
        "ladder_file": "css/layers.css", "css_dirs": ["css"], "files": {},
        "roots": [".mod"], "important_allow": {".p-hide": "show/hide must win"}, "admin_allow": {".p-login ul.tabs": "login tabs restyle, owner approved"}, "tokens_layer": "p.tokens",
        "element_layers": ["p.reset", "p.base"],
    }
    lay = ["p.theme"]
    cases = [
        # (css, spec, expected code or None for clean)
        ("@layer p.theme { .a { margin: 0; } }", lay, None),
        (".a { margin: 0; }", lay, "L3"),
        ("@layer p.base { .a { margin: 0; } }", lay, "L3"),
        ("@layer { .a { margin: 0; } }", lay, "L4"),
        ("@layer p.nope { .a { margin: 0; } }", lay, "L4"),
        ("@layer p.reset, p.base;", lay, "L1"),
        ("@import url(x.css) layer(p.base);", lay, "L5"),
        ("@layer p.theme { .a { display: none !important; } }", lay, "L6"),
        ("@layer p.theme { .a { color: red !important; } }", lay, "L6"),
        ("@layer p.utilities { .p-hide { display: none !important; } }", ["p.utilities"], None),
        ("@layer p.locked { .a { position: absolute !important; } }", ["p.locked"], None),
        ("@layer p.theme { .a { color: #fff; } }", lay, "L7"),
        ("@layer p.tokens { :root { --x: #fff; } .a { color: #fff; } }", ["p.tokens"], None),
        ("@layer p.theme { .a { color: var(--x); } }", lay, None),
        ("@layer p.theme { ul { margin: 0; } }", lay, "A1"),
        ("@layer p.base { ul { margin: 0; } }", ["p.base"], None),
        (".mod a { color: red; }", "unlayered: module", None),
        ("a { color: red; }", "unlayered: module", "A1"),
        ("@layer p.theme { .a { margin: 0; } }", "unlayered: module", "L3"),
        (".mod .contextual-links a { color: red; }", "unlayered: module", "A2"),
        (".mod a:not(.contextual-links *) { color: red; }", "unlayered: module", None),
        ("@layer p.theme { .toolbar .x { margin: 0; } }", lay, "A2"),
        (".contextual-links a { color: red; }", "admin", None),
        (".mod .a { color: red; }", {"layers": ["p.theme"], "unlayered_tail": "answers unlayered CSS"}, None),
        ("a { color: red; }", {"layers": ["p.theme"], "unlayered_tail": "answers unlayered CSS"}, "A1"),
        (".mod .a { color: red; }", {"layers": ["p.theme"]}, "L3"),
        (".mod .a { color: #fff !important; }", {"layers": ["p.theme"], "unlayered_tail": "answers unlayered CSS"}, None),
        (".mod .p-login ul.tabs a { color: red; }", "unlayered: module", None),
        (".mod .p-other ul.tabs a { color: red; }", "unlayered: module", "A2"),
        ("@layer p.theme { body .p-login ul.tabs { margin: 0; } }", ["p.theme"], None),
        ("@layer p.theme { body .p-x { margin: 0; } }", ["p.theme"], "A1"),
        ("body { font-family: serif; }", "unlayered: answers module CSS", None),
        ("body p { font-family: serif; }", "unlayered: answers module CSS", "A1"),
        ("@layer p.theme { .a { content: \"{\"; margin: 0; } }", lay, None),
        ("@layer p.theme { @keyframes k { from { color: #000; } } }", lay, None),
        ("@layer p.theme { :root { --p3-a: #fff; } }", lay, None),
        ("@layer p.theme { .a { color: #fff; --p3-a: red; } }", lay, "L7"),
    ]
    fails = 0
    for css, spec, want in cases:
        got = check_css("css/x.css", css, spec, m)
        codes = {g.split()[0] for g in got}
        ok = (not got) if want is None else (want in codes)
        if not ok:
            fails += 1
            print(f"SELF-TEST FAIL want={want} got={sorted(codes)} css={css}")
    import tempfile
    lib_ok = "x:\n  css:\n    base:\n      css/layers.css: { weight: -1000 }\n"
    disk = [
        # (files, manifest overrides, expected code or None)
        ({"css/layers.css": "@layer p.locked, p.reset, p.tokens, p.base, p.theme, p.utilities;", "p.libraries.yml": lib_ok}, {}, None),
        ({"css/layers.css": "@layer p.reset, p.locked;", "p.libraries.yml": lib_ok}, {}, "L1"),
        ({"css/layers.css": "@layer p.locked, p.reset, p.tokens, p.base, p.theme, p.utilities;", "p.libraries.yml": lib_ok, "css/new.css": ".a{}"}, {}, "L2"),
        ({"css/layers.css": "@layer p.locked, p.reset, p.tokens, p.base, p.theme, p.utilities;", "p.libraries.yml": lib_ok, "css/new.css": ".a{}"}, {"files": {"css/new.css": "pending: batch 2"}}, None),
        ({"css/layers.css": "@layer p.locked, p.reset, p.tokens, p.base, p.theme, p.utilities;", "p.libraries.yml": lib_ok.replace("-1000", "-5")}, {}, "D1"),
        ({"css/layers.css": "@layer p.locked, p.reset, p.tokens, p.base, p.theme, p.utilities;", "p.libraries.yml": lib_ok.replace("base:", "theme:")}, {}, "D1"),
        ({"css/layers.css": "@layer p.locked, p.reset, p.tokens, p.base, p.theme, p.utilities;", "p.libraries.yml": lib_ok}, {"important_allow": {".x": ""}}, "L6"),
    ]
    for files, over, want in disk:
        with tempfile.TemporaryDirectory() as d:
            for rel, body in files.items():
                os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
                open(os.path.join(d, rel), "w").write(body)
            mm = dict(m, libraries_file="p.libraries.yml", files={"css/layers.css": ["p.locked"]})
            mm.update(over)
            if "files" in over:
                mm["files"] = {"css/layers.css": ["p.locked"], **over["files"]}
            got = run(d, mm)
            codes = {g.split()[0] for g in got}
            ok = (not got) if want is None else (want in codes)
            if not ok:
                fails += 1
                print(f"SELF-TEST FAIL want={want} got={got}")
        cases.append(None)
    # Sub-theme manifests: ladder from the parent, found or not found.
    parent_m = {"ladder": ["p.locked", "p.reset", "p.tokens", "p.base", "p.theme", "p.utilities", "p.subtheme"]}
    sub_m = {"ladder_parent": "p_theme", "locked_layer": "p.locked", "tokens_layer": "p.tokens",
             "element_layers": ["p.reset", "p.base"], "css_dirs": ["css"], "roots": [".sub"],
             "files": {"css/s.css": ["p.subtheme"]}}
    sub_disk = [
        # (parent present, css, expected code or None, expected note fragment)
        (True, "@layer p.subtheme { .a { margin: 0; } }", None, "ladder taken from parent p_theme"),
        (True, "@layer p.nope { .a { margin: 0; } }", "L4", "ladder taken from parent p_theme"),
        (True, "@layer p.subtheme, p.base;", "L1", "ladder taken from parent p_theme"),
        (False, "@layer p.nope { .a { margin: 0; } }", "L3", "not found here: skipped"),
        (False, "@layer p.subtheme { .a { margin: 0; } }", None, "not found here: skipped"),
    ]
    for have_parent, css, want, note in sub_disk:
        with tempfile.TemporaryDirectory() as d:
            sub_root = os.path.join(d, "work", "sub")
            os.makedirs(os.path.join(sub_root, "css"))
            open(os.path.join(sub_root, "css", "s.css"), "w").write(css)
            if have_parent:
                os.makedirs(os.path.join(d, "work", "p_theme"))
                json.dump(parent_m, open(os.path.join(d, "work", "p_theme", "css-layers.json"), "w"))
            got = run(sub_root, sub_m)
            codes = {g.split()[0] for g in got}
            ok = ((not got) if want is None else (want in codes)) and note in run.note
            if not ok:
                fails += 1
                print(f"SELF-TEST FAIL sub-theme want={want} note={note!r} got={got} note={run.note!r}")
        cases.append(None)
    print(f"self-test: {len(cases)} cases, {fails} failures")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--manifest")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    mpath = args.manifest or os.path.join(args.root, "css-layers.json")
    try:
        manifest = json.load(open(mpath, encoding="utf-8"))
        out = run(args.root, manifest)
    except (OSError, ValueError, KeyError) as e:
        print(f"manifest unusable: {e}")
        return 2
    for line in out:
        print(line)
    pend = getattr(run, "pending", [])
    if getattr(run, "note", ""):
        print(f"css-layers-check: {run.note}")
    print(f"css-layers-check: {len(out)} failures, {len(pend)} files pending migration")
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main())
