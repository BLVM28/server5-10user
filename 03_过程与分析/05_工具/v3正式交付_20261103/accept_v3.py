"""Verify the official path and emit a small public receipt from checked results."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time

HOME=Path("/storage2/2026contest/server5/s5_10usr")
COMMANDS=[["make","env"],["make","clean"],["make","compile"],["make","check"],
          ["make","waves"],["make","probe"],["make","package"],["make","-C","server_eda","report"]]
COUNTS={"tb_kwt_arithmetic":260,"tb_v3_carries":7,"tb_kwt_icb":4,"tb_kwt_system":29,
        "tb_kwt_overlap":5,"tb_kwt_negative":58,"tb_kwt_mul_pipeline":524288}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def receipt(root, timing, test_counts, commands):
    manifest=root/"releases/source_manifest.json"
    packages=json.loads((root/"packages/manifest.json").read_text(encoding="utf-8"))
    for name,j in packages.items():
        assert sha(root/"packages"/(name+".zip"))==j["sha256"], name
    record={"scope":"v3 official delivery: RTL regression, full-core pre-layout STA, SDF short probes and archives",
            "server_directory":(HOME/"v3").as_posix(),"source_manifest_sha256":sha(manifest),
            "verified_source_files":len(json.loads(manifest.read_text(encoding="utf-8"))["files"]),
            "pinned_vector_files":len(json.loads((root/"py/vector_manifest.json").read_text(encoding="utf-8"))),
            "commands_passed":[" ".join(x) for x in commands],"test_counts":test_counts,
            "qualified_netlist_sha256":json.loads((root/"results/ppa.json").read_text(encoding="utf-8"))["mapped_sha256"],
            "timing_200mhz_setup_hold_ns":timing,"sdf_annotation_probe":["ss","ff"],
            "full_layer_gate":"not run for deployment","package_files":{n:j["files"] for n,j in packages.items()},
            "package_sha256":{n:j["sha256"] for n,j in packages.items()}}
    src=(json.dumps(record,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode("utf-8")
    rows=[
        "# 正式 v3 目录验收 · 2026-11-03","",
        "已在 `/storage2/2026contest/server5/s5_10usr/v3` 通过日常入口验收。源码清单中的 %d 个文件逐个核对，黄金数据共 %d 个文件。"
        % (record["verified_source_files"],record["pinned_vector_files"]),"",
        "| 项目 | 正式目录结果 |","|---|---|",
        "| VCS 功能 | 算术 260/260、进位 7/7、ICB 4/4、系统 29/29、重叠 5/5、异常 58/58、乘法边界 524288/524288 |",
        "| PT 完整核心 200 MHz | SS setup/hold %+.6f/%+.6f ns，FF %+.6f/%+.6f ns；两角报告违例均为 0 |"%tuple(timing["ss"]+timing["ff"]),
        "| SDF 短探针 | SS、FF 注释日志均 0 errors、0 warnings；完整 12 层长门级另行运行 |",
        "| 波形 | 系统检查通过，生成顶层 VCD，之后可用 make verdi 查看 |",
        "| 分类包 | RTL %d、TB %d、Makefile %d、流程 %d、向量 %d 个成员，逐成员核对 SHA |"%tuple(record["package_files"][k] for k in ("rtl","tb","makefile","flow","vectors")),
        "| 操作入口 | clean、compile、check、waves、probe、package、下级转发 report 通过 |","",
        "服务器原始命令、退出状态及各日志保存在 `reports/delivery_checks/`。结构和指标见 [版本首页](README.md)、[工艺实测](RESULTS.md)，机器验收记录在 [verification.json](releases/verification.json)，归档指纹见 [packages/manifest.json](packages/manifest.json)。真实 E203 固件及正式共享 RAM 仍需整机联调。",""]
    return src,"\n".join(rows).encode("utf-8")


def main():
    root=Path.cwd().resolve()
    assert root==HOME/"v3"
    logs=root/"reports/delivery_checks";logs.mkdir(parents=True,exist_ok=True)
    prefix=str(int(time.time()*1000000))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1")
    runs=[]
    for i,cmd in enumerate(COMMANDS):
        log=logs/(prefix+"_%02d_%s.log"%(i,cmd[-1]))
        with log.open("w") as stream:
            p=subprocess.run(cmd,cwd=str(root),env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
        runs.append({"cmd":cmd,"exit":p.returncode,"log":log.name,"sha256":sha(log)})
        (logs/"commands.json").write_text(json.dumps(runs,indent=2)+"\n")
        print("CHECK",cmd[-1],"exit",p.returncode,flush=True)
        if p.returncode:raise RuntimeError(str(log)+"\n"+log.read_text()[-2000:])
    out=root/"build/manual"
    for t,n in COUNTS.items():
        j=json.loads((out/"runs/default"/t/"verified.json").read_text())
        assert j["passed"] and j["counts"]==[[str(n),str(n)]] and sha(Path(j["log"]))==j["log_sha256"]
    assert (out/"runs/waves/tb_kwt_system/waves.vcd").stat().st_size>0
    probe=(logs/runs[5]["log"]).read_text()
    assert all("ANNOTATION PROBE PASS "+c in probe for c in ("ss","ff"))
    assert "BASIC CHECK PASS" in (logs/runs[-1]["log"]).read_text()
    frozen=json.loads((root/"results/ppa.json").read_text())
    timing={}
    for j in json.loads((out/"timing_qualified200_5.0.json").read_text()):
        assert j["passed"] and not j["reported_violations"] and j["netlist_sha256"]==frozen["mapped_sha256"]
        timing[j["corner"]]=j["slacks_ns"]
    assert set(timing)=={"ss","ff"}
    for n,h in json.loads((root/"releases/source_manifest.json").read_text())["files"].items():
        assert sha(root/n)==h,n
    evidence,report=receipt(root,timing,COUNTS,COMMANDS)
    (root/"releases/verification.json").write_bytes(evidence)
    (root/"SERVER_RESULTS.md").write_bytes(report)
    print("SOURCE + PACKAGE + DAILY ACCEPTANCE PASS",flush=True)
    print("RECEIPT",sha(root/"releases/verification.json"),"REPORT",sha(root/"SERVER_RESULTS.md"),flush=True)
    print("TIMING",timing,flush=True)


if __name__=="__main__":main()
