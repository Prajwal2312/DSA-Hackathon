#!/usr/bin/env python3
"""Budget Traveller with Coupons.

Layered DP over (flights used, city, coupons used).
At most K stops => at most K+1 flights. A coupon halves a fare (floor).
Time O((K+1) * M * C'), memory O((K+1) * N * C'), where C' = min(C, K+1).

Usage:
  python budget_traveller.py 1 < input.txt          # N M / K C / M lines "u v p"
  python budget_traveller.py 2 K C graph.csv        # CSV rows: u,v,p
  python budget_traveller.py 3 K C [N M]            # random graph
Writes result CSV to route_result.csv.
"""
import csv
import random
import sys

INF = float("inf")


def solve(n, k, c, edges):
    """Return (min_cost, path) ; path = list of (edge_index, used_coupon). -1 if impossible."""
    if n == 1:
        return 0, []
    F = k + 1                      # max number of flights
    C = min(c, F)                  # extra coupons can never be used
    W = C + 1
    size = (n + 1) * W
    dp = [[INF] * size for _ in range(F + 1)]
    par = [[None] * size for _ in range(F + 1)]   # (prev_state, edge_idx, coupon)
    dp[0][1 * W] = 0

    for f in range(F):
        cur, nxt, pn = dp[f], dp[f + 1], par[f + 1]
        for i, (u, v, p) in enumerate(edges):
            half = p // 2
            for j in range(W):
                d = cur[u * W + j]
                if d == INF:
                    continue
                s = v * W + j
                if d + p < nxt[s]:
                    nxt[s] = d + p
                    pn[s] = (u * W + j, i, 0)
                if j < C and d + half < nxt[s + 1]:
                    nxt[s + 1] = d + half
                    pn[s + 1] = (u * W + j, i, 1)

    best, bf, bs = INF, -1, -1
    for f in range(1, F + 1):
        for j in range(W):
            s = n * W + j
            if dp[f][s] < best:
                best, bf, bs = dp[f][s], f, s
    if best == INF:
        return -1, []

    path = []
    f, s = bf, bs
    while f > 0:
        prev, ei, cp = par[f][s]
        path.append((ei, cp))
        s, f = prev, f - 1
    return best, path[::-1]


def write_csv(fname, edges, path, cost):
    used = dict(path)
    with open(fname, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["from", "to", "price", "on_path", "coupon_used", "paid"])
        for i, (u, v, p) in enumerate(edges):
            on = i in used
            cp = on and used[i] == 1
            w.writerow([u, v, p, "x" if on else "", "x" if cp else "",
                        (p // 2 if cp else p) if on else ""])
        w.writerow(["# min_cost", cost])


def read_text():
    t = sys.stdin.read().split()
    n, m, k, c = map(int, t[:4])
    e = [tuple(map(int, t[4 + 3 * i:7 + 3 * i])) for i in range(m)]
    return n, k, c, e


def read_csv(fname, k, c):
    edges, n = [], 2
    with open(fname) as fh:
        for row in csv.reader(fh):
            try:
                u, v, p = (int(x) for x in row[:3])
            except (ValueError, TypeError):
                continue            # header / blank / comment
            edges.append((u, v, p))
            n = max(n, u, v)
    return n, k, c, edges


def generate(k, c, n=8, m=16):
    """Random graph that is guaranteed to contain a 1 -> N route with <= K stops."""
    seen, edges = set(), []

    def add(u, v, p):
        if u != v and (u, v) not in seen:
            seen.add((u, v))
            edges.append((u, v, p))

    mids = random.sample(range(2, n), min(k, n - 2))
    chain = [1] + mids + [n]
    for a, b in zip(chain, chain[1:]):
        add(a, b, random.randint(20, 120))
    m = min(max(m, len(edges)), n * (n - 1))
    while len(edges) < m:
        add(random.randint(1, n), random.randint(1, n), random.randint(10, 200))
    return n, k, c, edges


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "1"
    if mode == "1":
        n, k, c, edges = read_text()
    elif mode == "2":
        n, k, c, edges = read_csv(sys.argv[4], int(sys.argv[2]), int(sys.argv[3]))
    else:
        a = sys.argv
        n, k, c, edges = generate(int(a[2]), int(a[3]),
                                  int(a[4]) if len(a) > 4 else 8,
                                  int(a[5]) if len(a) > 5 else 16)
    cost, path = solve(n, k, c, edges)
    print(cost)
    write_csv("route_result.csv", edges, path, cost)
    if cost != -1:
        route = [1] + [edges[i][1] for i, _ in path]
        print("Route:", " -> ".join(map(str, route)))
        for i, cp in path:
            u, v, p = edges[i]
            print(f"  {u}->{v}: {p}" + (f" -> {p // 2} (coupon)" if cp else ""))


if __name__ == "__main__":
    main()
