"""Require unchanged structural Verilog statements except the named cell references."""
import re


def modules(path):
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", path.read_text(), flags=re.S)
    return {m.group(1):m.group(0) for m in re.finditer(r"^\s*module\s+(\w+)\b.*?\bendmodule\b",text,re.S|re.M)}


def audit(before, after, plan):
    expected = modules(before)
    actual = modules(after)
    assert set(expected)==set(actual) and "kwt_nice_core" in expected
    changes=[]
    for row in plan.read_text().splitlines():
        if not row.strip() or row.lstrip().startswith("#"):
            continue
        target,old,new,_,_=row.split()
        parts=target.split("/")
        name="kwt_nice_core"
        for inst in parts[:-1]:
            hit=re.search(r"(?m)^\s*(\w+)\s+"+re.escape(inst)+r"\s*\(",expected[name])
            assert hit, "Missing hierarchical cell "+target
            name=hit.group(1)
        pattern=r"(?m)^(\s*)"+re.escape(old)+r"(\s+"+re.escape(parts[-1])+r"\s*\()"
        expected[name],count=re.subn(pattern,lambda m:m[1]+new+m[2],expected[name])
        assert count==1, "Wrong original cell "+target
        changes.append([target,old,new])
    for name in expected:
        def statements(text):
            return sorted(re.sub(r"\s+","",x) for x in text.split(";") if x.strip())
        assert statements(expected[name])==statements(actual[name]), "Other mapped statement changed in "+name
    assert changes
    return changes
