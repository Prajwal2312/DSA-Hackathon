# 🚀 DSA Hackathon - Algorithmic Problem Solutions & Visualizers

A comprehensive collection of optimized algorithms, dynamic programming solutions, graph algorithms, and interactive visualizers developed for the **5th Semester DSA Hackathon**.

---

## 📌 Problem Directory & Overview

| # | Problem | Core Topic | Tech Stack | Files |
|---|---------|------------|------------|-------|
| **1** | **Budget Traveller with Coupons** | Layered Dynamic Programming | Python 3, HTML/CSS/JS | [`budget_traveller.py`](budget_traveller.py), [`Budget Traveller with Coupons.html`](Budget%20Traveller%20with%20Coupons.html) |
| **2** | **Closest Pair of Points** | Divide & Conquer vs Brute Force | Java (Swing GUI), HTML/CSS/JS | [`ClosestPair.java`](ClosestPair.java), [`closest-pair-visualizer.html`](closest-pair-visualizer.html) |
| **3** | **Shortest Path to Get All Keys** | Multi-State BFS with Bitmask | HTML/CSS/JS Visualizer | [`shortest-path-all-keys.html`](shortest-path-all-keys.html) |
| **4** | **Exam Timetable Scheduling** | Capacitated Graph Colouring | Python 3, HTML/CSS/JS | [`Problem-4.py`](Problem-4.py), [`Problem-4.html`](Problem-4.html) |

---

## 🛠 Problem Details & Execution Guide

### 1. Budget Traveller with Coupons
- **Problem Statement**: Find the cheapest flight route between cities with at most $K$ stops ($K+1$ flights) and up to $C$ 50%-off discount coupons.
- **Approach**: Layered Dynamic Programming over states `(flights_used, city, coupons_used)`.
- **Complexity**:
  - Time: $O((K + 1) \times M \times C')$ where $C' = \min(C, K + 1)$
  - Space: $O((K + 1) \times N \times C')$
- **How to Run**:
  ```bash
  # Option 1: Standard input
  python budget_traveller.py 1 < input.txt

  # Option 2: CSV input
  python budget_traveller.py 2 <K> <C> graph.csv

  # Option 3: Random graph benchmark
  python budget_traveller.py 3 <K> <C> [N M]
  ```
- **Interactive Visualizer**: Open [`Budget Traveller with Coupons.html`](Budget%20Traveller%20with%20Coupons.html) directly in any browser.

---

### 2. Closest Pair of Points
- **Problem Statement**: Given $N$ points in 2D space, determine the pair of points with the minimal Euclidean distance.
- **Approach**: Comparison between $O(N^2)$ Brute Force and $O(N \log N)$ Divide & Conquer (sorting, vertical midline splitting, and narrow strip comparison).
- **Features**: Complete Java implementation with an interactive Swing GUI, step-by-step merge animation, runtime vs. $N$ benchmark curves, and edge-case verification tests.
- **How to Run (Java)**:
  ```bash
  javac ClosestPair.java

  # Benchmark runtime for increasing N
  java ClosestPair -bench

  # Interactive GUI with step-by-step split/merge animation
  echo 1000 | java ClosestPair -gui

  # Randomized corner-case verification test
  java ClosestPair -test
  ```
- **Web Visualizer**: Open [`closest-pair-visualizer.html`](closest-pair-visualizer.html) in your browser.

---

### 3. Shortest Path to Get All Keys
- **Problem Statement**: Navigate a 2D grid containing obstacles (`#`), start position (`@`), keys (`a-z`), and matching doors/locks (`A-Z`) to collect all keys in the minimum number of steps.
- **Approach**: Multi-state Breadth-First Search (BFS) tracking `(row, col, key_bitmask)`.
- **Interactive Visualizer**: Open [`shortest-path-all-keys.html`](shortest-path-all-keys.html) in any browser to interactively step through the pathfinder, toggle wall/key states, and watch queue expansions.

---

### 4. Exam Timetable Scheduling (Capacitated Graph Colouring)
- **Problem Statement**: Schedule exams into conflict-free time slots such that no two courses with common students are scheduled simultaneously, and each time slot contains at most $R$ exams.
- **Algorithms Implemented**:
  1. **Welsh-Powell**: Greedy degree-ordered colouring with capacity enforcement.
  2. **DSatur**: Dynamic degree-of-saturation greedy heuristic.
  3. **Exact Branch & Bound**: DSatur-ordered search with symmetry breaking, capacity lower bounds, and proven optimality detection.
- **How to Run**:
  ```bash
  # Run on custom conflict data
  python Problem-4.py --input data.txt

  # Generate random conflict graph & benchmark
  python Problem-4.py --n 30 --r 5 --density 0.25

  # Run benchmark across graph sizes
  python Problem-4.py --n 30 --r 5 --density 0.25 --bench 10,20,30,40,50,60
  ```
- **Interactive Report**: Open [`Problem-4.html`](Problem-4.html) to view timetable slot assignments and color matrices.

---

## 💻 Tech Stack
- **Python 3**: Algorithms, Branch & Bound, Dynamic Programming
- **Java**: Swing GUI, Divide & Conquer geometry algorithms
- **HTML5 / CSS3 / JavaScript**: Interactive algorithmic simulations & dashboards

---

## 👤 Author
- **Prajwal Halaharvi** ([@Prajwal2312](https://github.com/Prajwal2312))
