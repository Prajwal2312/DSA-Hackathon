#!/usr/bin/env python3
"""
Exam Timetable Scheduling = capacitated graph colouring.

Colour classes (time slots) must be independent sets of the conflict graph
and contain at most R courses.  Minimise the number of slots.

Algorithms
  1. Welsh-Powell  (greedy, degree order, fills one slot at a time)
  2. DSatur        (greedy, dynamic saturation order)
  3. Exact         (DSatur-ordered branch & bound, seeded with the best greedy
                    solution, symmetry breaking, capacity-aware lower bound,
                    time limit -> reports whether optimality is PROVEN)

Usage
  python exam_timetable.py --input data.txt              # Option 1 (N M R, then M edge lines)
  python exam_timetable.py --n 30 --r 5 --density 0.25   # Option 2 (random graph)
  python exam_timetable.py --n 30 --r 5 --density 0.25 --bench 10,20,30,40,50,60

Outputs (in --out, default ./out):  timetable.csv, report.html
Courses are numbered 1..N in the input (0-based input is auto-detected).
"""
import argparse, csv, json, math, os, random, sys, time


# ----------------------------------------------------------------- input ----
def read_input(path):
    toks = open(path).read().split()
    n, m, r = int(toks[0]), int(toks[1]), int(toks[2])
    pairs = [(int(toks[3 + 2 * i]), int(toks[4 + 2 * i])) for i in range(m)]
    shift = 0 if any(0 in p for p in pairs) else 1   # auto-detect 0/1-based
    return n, r, [(u - shift, v - shift) for u, v in pairs]


def random_graph(n, density, seed):
    rnd = random.Random(seed)
    return [(i, j) for i in range(n) for j in range(i + 1, n) if rnd.random() < density]


def build(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        if u != v and 0 <= u < n and 0 <= v < n:
            adj[u].add(v); adj[v].add(u)
    adjm = [sum(1 << w for w in a) for a in adj]
    return [sorted(a) for a in adj], adjm


def popcount(x):
    return bin(x).count("1")


# ------------------------------------------------------------ heuristics ----
def welsh_powell(n, adj, adjm, R):
    order_by_deg = sorted(range(n), key=lambda v: -len(adj[v]))
    col, order, k, left = [-1] * n, [], 0, n
    while left:
        members = 0; size = 0
        for v in order_by_deg:
            if col[v] < 0 and size < R and not (adjm[v] & members):
                col[v] = k; members |= 1 << v; size += 1; order.append(v); left -= 1
        k += 1
    return k, col, order


def dsatur(n, adj, adjm, R):
    col, mask, sizes, order, full = [-1] * n, [0] * n, [], [], 0
    for _ in range(n):
        v = max((u for u in range(n) if col[u] < 0),
                key=lambda u: (popcount(mask[u] | full), len(adj[u])))
        forb = mask[v] | full
        c = next((c for c in range(len(sizes)) if not forb >> c & 1), len(sizes))
        if c == len(sizes):
            sizes.append(0)
        col[v] = c; sizes[c] += 1; order.append(v)
        if sizes[c] == R:
            full |= 1 << c
        for w in adj[v]:
            mask[w] |= 1 << c
    return len(sizes), col, order


# -------------------------------------------------------------- lower bound --
def lower_bound(n, adj, adjm, R):
    """max(ceil(N/R), size of a greedily found clique)."""
    best = 0
    for start in sorted(range(n), key=lambda v: -len(adj[v]))[:min(n, 30)]:
        cand, clique = adjm[start], [start]
        while cand:
            v = max((u for u in range(n) if cand >> u & 1), key=lambda u: popcount(adjm[u] & cand))
            clique.append(v); cand &= adjm[v]
        best = max(best, len(clique))
    return max(-(-n // R), best, 1 if n else 0)


# ------------------------------------------------------------------ exact ----
class Timeout(Exception):
    pass


def exact(n, adj, adjm, R, seed_sol, lb, time_limit):
    ub, ub_col, ub_order = seed_sol
    best = {"k": ub, "col": ub_col[:], "order": ub_order[:]}
    if ub <= lb:
        return best["k"], best["col"], best["order"], True, 0
    sys.setrecursionlimit(max(10000, n * 4))
    cnt = [[0] * ub for _ in range(n)]
    mask, col, sizes, path = [0] * n, [-1] * n, [0] * ub, []
    t0, nodes = time.perf_counter(), [0]

    def rec(done, used, full):
        nodes[0] += 1
        if nodes[0] & 1023 == 0 and time.perf_counter() - t0 > time_limit:
            raise Timeout
        if done == n:
            best.update(k=used, col=col[:], order=path[:])
            return
        free = used * R - done
        if used + -(-max(0, n - done - free) // R) >= best["k"]:
            return                                   # capacity-aware bound
        v = max((u for u in range(n) if col[u] < 0),
                key=lambda u: (popcount(mask[u] | full), len(adj[u])))
        forb = mask[v] | full
        options = [c for c in range(used) if not forb >> c & 1]
        if used + 1 < best["k"]:
            options.append(used)                     # symmetry breaking: only the next new slot
        for c in options:
            if best["k"] <= lb:
                return
            col[v] = c; sizes[c] += 1; path.append(v)
            for w in adj[v]:
                cnt[w][c] += 1
                if cnt[w][c] == 1: mask[w] |= 1 << c
            nf = full | (1 << c) if sizes[c] == R else full
            rec(done + 1, max(used, c + 1), nf)
            for w in adj[v]:
                cnt[w][c] -= 1
                if cnt[w][c] == 0: mask[w] &= ~(1 << c)
            col[v] = -1; sizes[c] -= 1; path.pop()

    proven = True
    try:
        rec(0, 0, 0)
    except Timeout:
        proven = False
    return best["k"], best["col"], best["order"], proven or best["k"] <= lb, nodes[0]


# ------------------------------------------------------------------ driver ---
def validate(n, adj, R, col):
    sizes = {}
    for v in range(n):
        sizes[col[v]] = sizes.get(col[v], 0) + 1
        if any(col[w] == col[v] for w in adj[v]): return False
    return all(s <= R for s in sizes.values())


def run_all(n, edges, R, tlimit):
    adj, adjm = build(n, edges)
    lb = lower_bound(n, adj, adjm, R)
    res = {}
    t = time.perf_counter(); k, c, o = welsh_powell(n, adj, adjm, R)
    res["Welsh-Powell"] = dict(k=k, col=c, order=o, time=time.perf_counter() - t, optimal=(k == lb))
    t = time.perf_counter(); k, c, o = dsatur(n, adj, adjm, R)
    res["DSatur"] = dict(k=k, col=c, order=o, time=time.perf_counter() - t, optimal=(k == lb))
    seed = min((res["Welsh-Powell"], res["DSatur"]), key=lambda r: r["k"])
    t = time.perf_counter()
    k, c, o, proven, nodes = exact(n, adj, adjm, R, (seed["k"], seed["col"], seed["order"]), lb, tlimit)
    res["Exact B&B"] = dict(k=k, col=c, order=o, time=time.perf_counter() - t, optimal=proven, nodes=nodes)
    for name, r in res.items():
        assert validate(n, adj, R, r["col"]), name + " produced an invalid timetable"
        r["slots"] = [[v + 1 for v in range(n) if r["col"][v] == s] for s in range(r["k"])]
    return res, lb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input"); ap.add_argument("--n", type=int); ap.add_argument("--r", type=int)
    ap.add_argument("--density", type=float, default=0.2); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--time-limit", type=float, default=10.0, help="seconds for exact solver")
    ap.add_argument("--bench", default="10,20,30,40,50,60", help="comma list of N for the comparison chart")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    if a.input:
        n, R, edges = read_input(a.input)
    else:
        if not (a.n and a.r):
            n, R = (int(x) for x in input("N R: ").split()); a.density = float(input("edge density (0-1): "))
        else:
            n, R = a.n, a.r
        edges = random_graph(n, a.density, a.seed)
    edges = sorted({(min(u, v), max(u, v)) for u, v in edges if u != v})
    res, lb = run_all(n, edges, R, a.time_limit)

    print(f"N={n}  conflicts={len(edges)}  R={R}  lower bound={lb}\n")
    print(f"{'Algorithm':<14}{'Slots':>6}  {'Time (s)':>9}  Proven optimal?")
    for name, r in res.items():
        print(f"{name:<14}{r['k']:>6}  {r['time']:>9.4f}  {'YES' if r['optimal'] else 'no (upper bound only)'}")
    best_name = min(res, key=lambda x: (res[x]["k"], res[x]["time"]))
    best = res[best_name]
    print(f"\nTimetable ({best_name}, {best['k']} slots):")
    for s, cs in enumerate(best["slots"], 1):
        print(f"Slot {s}: {', '.join(map(str, cs))}")

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "timetable.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Slot"] + [f"Hall {i}" for i in range(1, R + 1)])
        for s, cs in enumerate(best["slots"], 1):
            w.writerow([f"Slot {s}"] + cs + [""] * (R - len(cs)))

    bench = []
    for bn in [int(x) for x in a.bench.split(",") if x.strip()]:
        be = random_graph(bn, a.density, a.seed)
        br, _ = run_all(bn, be, R, min(a.time_limit, 5))
        bench.append({"n": bn, **{k: {"k": v["k"], "time": v["time"], "opt": v["optimal"]} for k, v in br.items()}})
        print(f"bench N={bn}: " + "  ".join(f"{k}={v['k']} ({v['time']:.3f}s)" for k, v in br.items()))

    data = dict(n=n, R=R, lb=lb, edges=edges, best=best_name, bench=bench,
                algos={k: {x: v[x] for x in ("k", "time", "optimal", "slots", "col", "order")} for k, v in res.items()})
    with open(os.path.join(a.out, "report.html"), "w", encoding="utf-8") as f:
        f.write(HTML.replace("__DATA__", json.dumps(data)))
    print(f"\nWrote {a.out}/timetable.csv and {a.out}/report.html")


HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Exam timetable</title>
<style>
:root{--bg:#f7f8fa;--card:#fff;--ink:#1c2430;--mut:#6b7686;--line:#dde2ea}
@media(prefers-color-scheme:dark){:root{--bg:#12161c;--card:#1b212a;--ink:#e8ecf2;--mut:#98a3b3;--line:#2c3542}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}
main{max-width:1100px;margin:auto;padding:24px 16px 48px}h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:0 0 10px}
p.s{color:var(--mut);margin:0 0 18px}section{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin-bottom:16px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
button{font:inherit;padding:6px 12px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;cursor:pointer}
button.on{background:var(--ink);color:var(--bg)}button:focus-visible{outline:2px solid #3b82f6}
table{border-collapse:collapse;width:100%}th,td{padding:6px 10px;border-bottom:1px solid var(--line);text-align:left}
.grid td,.grid th{text-align:center;border:1px solid var(--line);min-width:42px;height:34px}.grid td{color:#111;font-weight:600}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:800px){.two{grid-template-columns:1fr}}
svg{width:100%;height:auto;display:block}.wrap{overflow-x:auto}input[type=range]{flex:1;min-width:120px}
.ok{color:#15803d;font-weight:600}.no{color:#b45309;font-weight:600}
</style></head><body><main>
<h1>Exam timetable</h1><p class="s" id="sub"></p>
<section><h2>Algorithm comparison</h2><div class="wrap"><table id="tbl"></table></div></section>
<section><div class="row" id="tabs"></div>
<div class="row"><button id="play">Play assignment</button><button id="reset">Show final</button>
<input type="range" id="step" min="0" value="0" aria-label="assignment step"><span id="lbl"></span></div>
<div class="two"><div><h2>Conflict graph</h2><svg id="g" viewBox="0 0 560 560"></svg></div>
<div><h2>Timetable</h2><div class="wrap"><table class="grid" id="grid"></table></div></div></div></section>
<section><h2>Scaling with N (random graphs, same density)</h2><div class="two"><svg id="c1" viewBox="0 0 440 280"></svg><svg id="c2" viewBox="0 0 440 280"></svg></div></section>
</main><script>
const D=__DATA__,N=D.n,R=D.R,names=Object.keys(D.algos);let cur=D.best,step=N,timer=null;
const col=s=>`hsl(${(s*137.5)%360} 65% 70%)`,$=id=>document.getElementById(id),NS="http://www.w3.org/2000/svg";
const ac={"Welsh-Powell":"#e08a1e","DSatur":"#2b7bd6","Exact B&B":"#1f9d6b"};
$("sub").textContent=`${N} courses, ${D.edges.length} conflicts, at most ${R} exams per slot. Lower bound: ${D.lb} slots.`;
$("tbl").innerHTML="<tr><th>Algorithm</th><th>Slots</th><th>Time</th><th>Proven optimal</th></tr>"+names.map(n=>{const a=D.algos[n];
return `<tr><td>${n}</td><td>${a.k}</td><td>${a.time<1?(a.time*1000).toFixed(2)+" ms":a.time.toFixed(2)+" s"}</td><td class="${a.optimal?'ok':'no'}">${a.optimal?"Yes":"No, upper bound only"}</td></tr>`}).join("");
// force layout
const P=[];for(let i=0;i<N;i++){const t=2*Math.PI*i/N;P.push([280+200*Math.cos(t),280+200*Math.sin(t)])}
if(N>2){const nb=Array.from({length:N},()=>[]);D.edges.forEach(([u,v])=>{nb[u].push(v);nb[v].push(u)});
for(let it=0;it<300;it++){const F=P.map(()=>[0,0]);
for(let i=0;i<N;i++)for(let j=i+1;j<N;j++){let dx=P[i][0]-P[j][0],dy=P[i][1]-P[j][1],d2=dx*dx+dy*dy+.01,f=2500/d2,d=Math.sqrt(d2);
F[i][0]+=f*dx/d;F[i][1]+=f*dy/d;F[j][0]-=f*dx/d;F[j][1]-=f*dy/d}
D.edges.forEach(([u,v])=>{let dx=P[v][0]-P[u][0],dy=P[v][1]-P[u][1],d=Math.hypot(dx,dy)+.01,f=(d-70)*.02;
F[u][0]+=f*dx/d;F[u][1]+=f*dy/d;F[v][0]-=f*dx/d;F[v][1]-=f*dy/d});
for(let i=0;i<N;i++){F[i][0]+=(280-P[i][0])*.01;F[i][1]+=(280-P[i][1])*.01;
P[i][0]=Math.min(540,Math.max(20,P[i][0]+Math.max(-8,Math.min(8,F[i][0]))));P[i][1]=Math.min(540,Math.max(20,P[i][1]+Math.max(-8,Math.min(8,F[i][1]))))}}}
const el=(t,a,p)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);p&&p.appendChild(e);return e};
const g=$("g"),nodes=[];D.edges.forEach(([u,v])=>el("line",{x1:P[u][0],y1:P[u][1],x2:P[v][0],y2:P[v][1],stroke:"#8893a3","stroke-opacity":.5},g));
const rad=Math.max(8,Math.min(16,260/Math.sqrt(N+1)/1.6));
for(let i=0;i<N;i++){const c=el("circle",{cx:P[i][0],cy:P[i][1],r:rad,stroke:"#333","stroke-width":1},g),
t=el("text",{x:P[i][0],y:P[i][1]+4,"text-anchor":"middle","font-size":rad>11?11:9,fill:"#111"},g);t.textContent=i+1;nodes.push(c)}
function draw(){const a=D.algos[cur],done=new Set(a.order.slice(0,step));
nodes.forEach((c,i)=>c.setAttribute("fill",done.has(i)?col(a.col[i]):"#e5e7eb"));
let h="<tr><th></th>"+Array.from({length:R},(_,i)=>`<th>Hall ${i+1}</th>`).join("")+"</tr>";
const per=Array.from({length:a.k},()=>[]);a.order.slice(0,step).forEach(v=>per[a.col[v]].push(v+1));
per.forEach((cs,s)=>{h+=`<tr><th>Slot ${s+1}</th>`+Array.from({length:R},(_,j)=>cs[j]?`<td style="background:${col(s)}">${cs[j]}</td>`:"<td></td>").join("")+"</tr>"});
$("grid").innerHTML=h;$("step").value=step;$("lbl").textContent=`${step}/${N} assigned`}
$("tabs").innerHTML=names.map(n=>`<button data-n="${n}">${n}</button>`).join("");
function tabs(){document.querySelectorAll("#tabs button").forEach(b=>b.classList.toggle("on",b.dataset.n==cur))}
document.querySelectorAll("#tabs button").forEach(b=>b.onclick=()=>{cur=b.dataset.n;step=N;stop();tabs();draw()});
$("step").max=N;$("step").oninput=e=>{stop();step=+e.target.value;draw()};
function stop(){clearInterval(timer);timer=null;$("play").textContent="Play assignment"}
$("play").onclick=()=>{if(timer)return stop();if(step>=N)step=0;$("play").textContent="Pause";
timer=setInterval(()=>{step++;draw();if(step>=N)stop()},Math.max(60,1500/N*4))};
$("reset").onclick=()=>{stop();step=N;draw()};
function chart(id,key,title,fmt){const s=$(id),W=440,H=280,m={l:52,r:12,t:28,b:36};
const xs=D.bench.map(b=>b.n);if(!xs.length)return;const all=D.bench.flatMap(b=>names.map(n=>b[n][key]));
const ymax=Math.max(...all)*1.1||1,ymin=key=="k"?Math.min(...all)-1:0;
const X=v=>m.l+(xs.length>1?(v-xs[0])/(xs[xs.length-1]-xs[0]):.5)*(W-m.l-m.r),Y=v=>H-m.b-(v-ymin)/(ymax-ymin)*(H-m.t-m.b);
el("text",{x:m.l,y:16,"font-size":13,fill:"currentColor"},s).textContent=title;
for(let i=0;i<=4;i++){const v=ymin+(ymax-ymin)*i/4;el("line",{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),stroke:"#8893a3","stroke-opacity":.25},s);
el("text",{x:m.l-6,y:Y(v)+4,"text-anchor":"end","font-size":10,fill:"currentColor"},s).textContent=fmt(v)}
xs.forEach(x=>el("text",{x:X(x),y:H-m.b+14,"text-anchor":"middle","font-size":10,fill:"currentColor"},s).textContent=x);
el("text",{x:W/2,y:H-4,"text-anchor":"middle","font-size":11,fill:"currentColor"},s).textContent="N (courses)";
names.forEach((n,i)=>{const pts=D.bench.map(b=>[X(b.n),Y(b[n][key])]);
el("polyline",{points:pts.join(" "),fill:"none",stroke:ac[n],"stroke-width":2,"stroke-dasharray":i==1?"6 3":""},s);
pts.forEach(p=>el("circle",{cx:p[0],cy:p[1],r:3,fill:ac[n]},s));
el("rect",{x:W-130,y:6+i*13,width:9,height:9,fill:ac[n]},s);el("text",{x:W-117,y:15+i*13,"font-size":10,fill:"currentColor"},s).textContent=n})}
chart("c1","k","Slots used",v=>Math.round(v));chart("c2","time","Running time (s)",v=>v<.01?v.toExponential(0):v.toFixed(2));
tabs();draw();
</script></body></html>"""

if __name__ == "__main__":
    main()
