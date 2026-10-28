"""离线分析卖家精灵监控页：找出列表数据的真实来源。
用法: python tools/analyze_tracking_page.py data/debug/keyword_tracking.html
"""
import re
import sys

BT = chr(96)  # 反引号
Q = "[\"'" + BT + "]"


def main(path: str) -> None:
    h = open(path, encoding="utf-8", errors="ignore").read()
    print("file:", path, "size:", len(h))

    print("\n=== ajax url: 定义 ===")
    for m in re.finditer(r"url\s*:\s*" + Q + r"([^\"'" + BT + r"]+)" + Q, h):
        print("  ", m.group(1))

    print("\n=== $ .get / $ .post / $ .getJSON 直接地址 ===")
    pat = r"\$\.(?:get|post|ajax|getJSON)\(\s*" + Q + r"([^\"'" + BT + r"]+)"
    for m in sorted(set(re.findall(pat, h))):
        print("  ", m)

    print("\n=== 页面内出现的 tracking 相关路径 ===")
    print(sorted(set(re.findall(r"/v2/[a-z\-]*tracking[a-zA-Z0-9\-/._]*", h))))

    print("\n=== 疑似内嵌数据变量 ===")
    for m in re.finditer(r"(?:var|let|const|window\.)\s*([A-Za-z_$][\w$]*)\s*=\s*(\[|\{)", h):
        name, brace = m.group(1), m.group(2)
        # 仅展示后续 60 字符像 JSON 的
        seg = h[m.end() - 1: m.end() + 60]
        if any(k in seg for k in ('"', "'", "asin", "keyword", "status", "id")):
            print("  var %-22s = %s  ~ %s" % (name, brace, seg[:58].replace("\n", " ")))

    print("\n=== 模板占位符统计 ===")
    tpl_vars = re.findall(r"\{\{\s*=?\s*([a-zA-Z_$][\w$]*)\.([\w$]+)", h)
    from collections import Counter
    c = Counter(v[0] for v in tpl_vars)
    print("  模板根变量:", dict(c))
    print("  字段示例:", sorted(set("%s.%s" % v for v in tpl_vars))[:20])


if __name__ == "__main__":
    main(sys.argv[1])
