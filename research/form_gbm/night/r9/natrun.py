"""natrun.py FROM TO OUT: dispatch one betwatch_national.py chunk on fk-experiment, wait for it, save its output."""
import sys, time, calendar, subprocess
sys.path.insert(0, "/home/user/fk-model/research/form_gbm/pipeline")
import price_run
a, b, out = sys.argv[1:4]
t0 = time.time()
price_run.gh("/actions/workflows/fk-experiment.yml/dispatches", {"ref": "main", "inputs": {"script": "betwatch_national.py", "args": f"{a} {b}"}})
time.sleep(12); rid = None
for _ in range(30):
    for x in price_run.gh("/actions/workflows/fk-experiment.yml/runs?per_page=8")["workflow_runs"]:
        if calendar.timegm(time.strptime(x["created_at"], "%Y-%m-%dT%H:%M:%SZ")) >= t0 - 5:
            rid = x["id"]
    if rid: break
    time.sleep(5)
# several chunks may be dispatched close together: take the run whose creation is nearest after our dispatch
runs = [x for x in price_run.gh("/actions/workflows/fk-experiment.yml/runs?per_page=8")["workflow_runs"] if calendar.timegm(time.strptime(x["created_at"], "%Y-%m-%dT%H:%M:%SZ")) >= t0 - 5]
rid = min(runs, key=lambda x: x["created_at"])["id"]
print(f"chunk {a} to {b}: run {rid}", flush=True)
while True:
    try: r = price_run.gh(f"/actions/runs/{rid}")
    except Exception as ex: time.sleep(30); continue
    if r["status"] == "completed": break
    time.sleep(30)
for _ in range(6):
    subprocess.run("cd /home/user/fk-model && git fetch -q origin experiments", shell=True)
    f = subprocess.run(f"cd /home/user/fk-model && git ls-tree --name-only origin/experiments | grep -- '-{rid}.md'", shell=True, capture_output=True, text=True).stdout.strip()
    if f:
        subprocess.run(f"cd /home/user/fk-model && git show origin/experiments:{f} > {out}", shell=True); break
    time.sleep(20)
tail = subprocess.run(f"tail -3 {out} | cut -c1-200; wc -c {out}", shell=True, capture_output=True, text=True).stdout
print(f"chunk {a} to {b}: {r['conclusion']} in {(time.time() - t0) / 60:.0f} min\n{tail}", flush=True)
