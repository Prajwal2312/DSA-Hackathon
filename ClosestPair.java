import javax.swing.*;
import java.awt.*;
import java.awt.geom.*;
import java.util.*;
import java.util.List;

/**
 * Problem 2: Closest Pair of Points - Brute Force (O(n^2)) vs Divide and Conquer (O(n log n)).
 *
 * Run:
 *   javac ClosestPair.java
 *   echo 1000 | java ClosestPair             -> the three required output lines
 *   echo 1000 | java ClosestPair -gui        -> + plot, strip, animation, runtime-vs-N graph
 *   java ClosestPair -bench                  -> runtime table for increasing N (+ agreement check)
 *   java ClosestPair -test                   -> randomized corner-case verification
 *   optional: -seed=42 for reproducible input
 */
public class ClosestPair {

    // ------------------------------------------------------------------ model

    static final class Point {
        final double x, y;
        Point(double x, double y) { this.x = x; this.y = y; }
    }

    /** Animation event: a split (before recursing) or a merge (after combining, with strip half-width d). */
    static final class Ev {
        final boolean merge;
        final double xMin, xMax, midX, d;
        Ev(boolean merge, double xMin, double xMax, double midX, double d) {
            this.merge = merge; this.xMin = xMin; this.xMax = xMax; this.midX = midX; this.d = d;
        }
    }

    /** Best pair found so far. Squared distance is used internally (no sqrt in the hot loops). */
    static final class Result {
        double d2 = Double.POSITIVE_INFINITY;
        Point a, b;
        double splitX = Double.NaN, stripD = Double.NaN;   // top-level dividing line / strip half-width
        List<Ev> events;                                   // only filled when recording for the GUI

        void offer(Point p, Point q) {
            double dx = p.x - q.x, dy = p.y - q.y, v = dx * dx + dy * dy;
            if (v < d2) { d2 = v; a = p; b = q; }
        }
        boolean found() { return a != null; }
        double dist() { return Math.sqrt(d2); }
    }

    // ------------------------------------------------------------ algorithms

    /** O(n^2): check every pair. Handles N < 2 (returns an empty result). */
    static Result bruteForce(Point[] p) {
        Result r = new Result();
        for (int i = 0; i < p.length; i++)
            for (int j = i + 1; j < p.length; j++)
                r.offer(p[i], p[j]);
        return r;
    }

    /** O(n log n): sort by x once, then merge-sort by y inside the recursion. */
    static Result divideAndConquer(Point[] pts, boolean record) {
        Result r = new Result();
        int n = pts.length;
        if (n < 2) return r;
        Point[] a = pts.clone();                       // keep caller's array untouched
        Arrays.sort(a, (p, q) -> {
            int c = Double.compare(p.x, q.x);
            return c != 0 ? c : Double.compare(p.y, q.y);
        });
        if (record) r.events = new ArrayList<>();
        solve(a, new Point[n], 0, n, r, 0);
        return r;
    }

    /** On entry a[lo,hi) is sorted by x. On exit it is sorted by y. */
    private static void solve(Point[] a, Point[] t, int lo, int hi, Result r, int depth) {
        int n = hi - lo;
        if (n <= 3) {                                   // base case: brute force + insertion sort by y
            for (int i = lo; i < hi; i++)
                for (int j = i + 1; j < hi; j++)
                    r.offer(a[i], a[j]);
            for (int i = lo + 1; i < hi; i++) {
                Point k = a[i];
                int j = i - 1;
                while (j >= lo && a[j].y > k.y) { a[j + 1] = a[j]; j--; }
                a[j + 1] = k;
            }
            return;
        }

        int mid = (lo + hi) >>> 1;                      // split by INDEX -> always balanced, even with equal x
        double midX = a[mid].x;                         // read the dividing line before the halves get re-ordered
        if (r.events != null) r.events.add(new Ev(false, a[lo].x, a[hi - 1].x, midX, Double.NaN));

        solve(a, t, lo, mid, r, depth + 1);
        solve(a, t, mid, hi, r, depth + 1);

        int i = lo, j = mid, k = lo;                    // merge the two y-sorted halves
        while (i < mid && j < hi) t[k++] = a[i].y <= a[j].y ? a[i++] : a[j++];
        while (i < mid) t[k++] = a[i++];
        while (j < hi) t[k++] = a[j++];
        System.arraycopy(t, lo, a, lo, n);

        if (depth == 0) { r.splitX = midX; r.stripD = Math.sqrt(r.d2); }

        // strip: points within d of the dividing line, scanned in y order, each compared only
        // with earlier strip points whose y is within d (at most 7 of them by a packing argument)
        int m = 0;
        for (int s = lo; s < hi; s++) {
            double dx = a[s].x - midX;
            if (dx * dx >= r.d2) continue;
            for (int q = m - 1; q >= 0; q--) {
                double dy = a[s].y - t[q].y;
                if (dy * dy >= r.d2) break;
                r.offer(a[s], t[q]);
            }
            t[m++] = a[s];
        }
        if (r.events != null) r.events.add(new Ev(true, a[lo].x, a[hi - 1].x, midX, Math.sqrt(r.d2)));
    }

    // -------------------------------------------------------- input / output

    /** mixed = true: each coordinate is randomly an integer or a floating point value. */
    static Point[] generate(int n, long seed, boolean mixed) {
        Random rnd = new Random(seed);
        Point[] p = new Point[n];
        for (int i = 0; i < n; i++) p[i] = new Point(coord(rnd, mixed), coord(rnd, mixed));
        return p;
    }

    private static double coord(Random rnd, boolean mixed) {
        if (!mixed) return rnd.nextDouble() * 1_000_000;
        return rnd.nextBoolean() ? rnd.nextInt(1000) : rnd.nextDouble() * 1000;
    }

    static String num(double v) {
        return (v == Math.rint(v) && Math.abs(v) < 1e15) ? String.valueOf((long) v)
                                                          : String.format(Locale.US, "%.6f", v);
    }

    static String describe(Result r) {
        if (!r.found()) return "N/A (fewer than 2 points)";
        return String.format(Locale.US, "%.6f (%s, %s) (%s, %s)",
                r.dist(), num(r.a.x), num(r.a.y), num(r.b.x), num(r.b.y));
    }

    static boolean agree(Result a, Result b) {
        if (a.found() != b.found()) return false;
        return !a.found() || Math.abs(a.dist() - b.dist()) <= 1e-9 * Math.max(1.0, a.dist());
    }

    // ------------------------------------------------- performance + testing

    static void warmUp() {                              // let the JIT compile both algorithms before timing
        Point[] w = generate(2000, 1, true);
        for (int i = 0; i < 3; i++) { bruteForce(w); divideAndConquer(w, false); }
    }

    static final int[] BENCH_SIZES = {100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000};

    /** returns {n, bruteMs, dcMs, agree(1/0)} using the best of several runs. */
    static double[] benchRow(int n) {
        Point[] p = generate(n, 12345L + n, false);
        int repsBf = n >= 20000 ? 1 : 3, repsDc = 5;
        double bt = Double.MAX_VALUE, dt = Double.MAX_VALUE;
        Result b = null, d = null;
        for (int i = 0; i < repsBf; i++) {
            long t0 = System.nanoTime(); b = bruteForce(p);
            bt = Math.min(bt, (System.nanoTime() - t0) / 1e6);
        }
        for (int i = 0; i < repsDc; i++) {
            long t0 = System.nanoTime(); d = divideAndConquer(p, false);
            dt = Math.min(dt, (System.nanoTime() - t0) / 1e6);
        }
        return new double[]{n, bt, dt, agree(b, d) ? 1 : 0};
    }

    static void runBenchmarkConsole() {
        warmUp();
        System.out.printf("%8s %15s %15s %10s %8s%n", "N", "Brute (ms)", "D&C (ms)", "Speedup", "Agree");
        for (int n : BENCH_SIZES) {
            double[] r = benchRow(n);
            System.out.printf(Locale.US, "%8d %15.3f %15.3f %9.1fx %8s%n",
                    (int) r[0], r[1], r[2], r[1] / Math.max(r[2], 1e-9), r[3] == 1 ? "yes" : "NO");
        }
    }

    /** Randomized comparison on tricky inputs: duplicates, collinear, same x / same y, negatives, N < 2. */
    static void stressTest() {
        Random rnd = new Random(7);
        int trials = 20000;
        for (int t = 0; t < trials; t++) {
            int n = rnd.nextInt(60), mode = rnd.nextInt(6);
            Point[] p = new Point[n];
            for (int i = 0; i < n; i++) {
                double x, y;
                switch (mode) {
                    case 0:  x = rnd.nextInt(5);    y = rnd.nextInt(5);    break;   // many duplicates
                    case 1:  x = rnd.nextInt(1000); y = 7;                 break;   // same y (horizontal line)
                    case 2:  x = 3;                 y = rnd.nextInt(1000); break;   // same x (vertical line)
                    case 3:  x = rnd.nextInt(1000); y = 2 * x + 1;         break;   // diagonal collinear
                    case 4:  x = rnd.nextDouble() * 100; y = rnd.nextDouble() * 100; break;
                    default: x = rnd.nextInt(100) - 50;  y = rnd.nextInt(100) - 50;  // negatives
                }
                p[i] = new Point(x, y);
            }
            Result a = bruteForce(p), b = divideAndConquer(p, false);
            if (!agree(a, b)) {
                System.out.println("MISMATCH (mode " + mode + ", n=" + n + "): " + describe(a) + " vs " + describe(b));
                return;
            }
        }
        System.out.println("All " + trials + " randomized tests passed (both algorithms agree).");
    }

    // ----------------------------------------------------------- visualization

    static final Color RED = new Color(0xD62728), BLUE = new Color(0x1F77B4);

    static final class PlotPanel extends JPanel {
        static final int PAD = 40;
        final Point[] pts; final Result bf, dc;
        boolean showStrip = true;
        int evIdx = -1;
        javax.swing.Timer timer;
        double minX = Double.MAX_VALUE, maxX = -Double.MAX_VALUE, minY = Double.MAX_VALUE, maxY = -Double.MAX_VALUE;
        double spanX, spanY;

        PlotPanel(Point[] pts, Result bf, Result dc) {
            this.pts = pts; this.bf = bf; this.dc = dc;
            for (Point p : pts) {
                minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x);
                minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y);
            }
            spanX = maxX - minX > 0 ? maxX - minX : 1;
            spanY = maxY - minY > 0 ? maxY - minY : 1;
            setBackground(Color.WHITE);
        }

        private double scale() { return Math.min((getWidth() - 2.0 * PAD) / spanX, (getHeight() - 2.0 * PAD) / spanY); }
        private double sx(double x) { return PAD + (x - minX) * scale(); }
        private double sy(double y) { return getHeight() - PAD - (y - minY) * scale(); }

        void animate() {
            if (dc.events == null || dc.events.isEmpty()) return;
            if (timer != null) timer.stop();
            evIdx = 0;
            int delay = Math.max(15, Math.min(500, 8000 / dc.events.size()));
            timer = new javax.swing.Timer(delay, ae -> {
                evIdx++;
                if (evIdx >= dc.events.size()) { evIdx = -1; timer.stop(); }
                repaint();
            });
            timer.start();
            repaint();
        }

        private void band(Graphics2D g, double x0, double x1, Color c) {
            double l = sx(Math.max(x0, minX)), r = sx(Math.min(x1, maxX));
            if (r <= l) return;
            g.setColor(c);
            g.fill(new Rectangle2D.Double(l, sy(maxY), r - l, sy(minY) - sy(maxY)));
        }

        private void vline(Graphics2D g, double x) {
            g.setColor(Color.DARK_GRAY);
            g.setStroke(new BasicStroke(1.5f, BasicStroke.CAP_BUTT, BasicStroke.JOIN_MITER, 10f, new float[]{6f, 4f}, 0f));
            g.draw(new Line2D.Double(sx(x), sy(maxY), sx(x), sy(minY)));
        }

        @Override protected void paintComponent(Graphics g0) {
            super.paintComponent(g0);
            Graphics2D g = (Graphics2D) g0;
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            g.setColor(new Color(0xCCCCCC));
            g.setStroke(new BasicStroke(1f));
            g.draw(new Rectangle2D.Double(sx(minX), sy(maxY), sx(maxX) - sx(minX), sy(minY) - sy(maxY)));

            Color stripCol = new Color(255, 165, 0, 70), segCol = new Color(31, 119, 180, 30);
            if (dc.events != null && evIdx >= 0 && evIdx < dc.events.size()) {
                Ev e = dc.events.get(evIdx);
                band(g, e.xMin, e.xMax, segCol);
                if (e.merge) band(g, e.midX - e.d, e.midX + e.d, stripCol);
                vline(g, e.midX);
                g.setColor(Color.DARK_GRAY);
                g.drawString((e.merge ? "Merge" : "Split") + " step " + (evIdx + 1) + "/" + dc.events.size(), PAD, 36);
            } else if (showStrip && !Double.isNaN(dc.splitX)) {
                band(g, dc.splitX - dc.stripD, dc.splitX + dc.stripD, stripCol);
                vline(g, dc.splitX);
            }

            g.setColor(new Color(0x55, 0x55, 0x55));
            for (Point p : pts) g.fill(new Ellipse2D.Double(sx(p.x) - 2.5, sy(p.y) - 2.5, 5, 5));

            if (bf.found()) {
                g.setColor(RED); g.setStroke(new BasicStroke(4f));
                g.draw(new Line2D.Double(sx(bf.a.x), sy(bf.a.y), sx(bf.b.x), sy(bf.b.y)));
                for (Point p : new Point[]{bf.a, bf.b}) g.fill(new Ellipse2D.Double(sx(p.x) - 5, sy(p.y) - 5, 10, 10));
            }
            if (dc.found()) {
                g.setColor(BLUE); g.setStroke(new BasicStroke(2f));
                g.draw(new Line2D.Double(sx(dc.a.x), sy(dc.a.y), sx(dc.b.x), sy(dc.b.y)));
                for (Point p : new Point[]{dc.a, dc.b}) g.draw(new Ellipse2D.Double(sx(p.x) - 9, sy(p.y) - 9, 18, 18));
            }

            g.setColor(RED);  g.drawString("Brute force: " + (bf.found() ? String.format(Locale.US, "d = %.6f", bf.dist()) : "N/A"), PAD, 16);
            g.setColor(BLUE); g.drawString("Divide & conquer: " + (dc.found() ? String.format(Locale.US, "d = %.6f", dc.dist()) : "N/A"), PAD + 220, 16);
        }
    }

    static final class ChartPanel extends JPanel {
        final List<double[]> rows = new ArrayList<>();      // {n, bruteMs, dcMs}
        boolean log = true;

        ChartPanel() { setBackground(Color.WHITE); }

        private double tf(double v) { return log ? Math.log10(Math.max(v, 1e-3)) : v; }

        @Override protected void paintComponent(Graphics g0) {
            super.paintComponent(g0);
            Graphics2D g = (Graphics2D) g0;
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            int L = 80, R = 30, T = 40, B = 60, w = getWidth() - L - R, h = getHeight() - T - B;
            g.setColor(Color.DARK_GRAY);
            if (rows.isEmpty()) { g.drawString("Running benchmark...", L, T); return; }

            double nMin = Double.MAX_VALUE, nMax = 0, yMin = Double.MAX_VALUE, yMax = 0;
            for (double[] r : rows) {
                nMin = Math.min(nMin, r[0]); nMax = Math.max(nMax, r[0]);
                yMin = Math.min(yMin, Math.min(r[1], r[2])); yMax = Math.max(yMax, Math.max(r[1], r[2]));
            }
            double x0 = log ? tf(nMin) : 0, x1 = tf(nMax), y0 = log ? tf(yMin) : 0, y1 = tf(yMax);
            if (x1 - x0 <= 0) x1 = x0 + 1;
            if (y1 - y0 <= 0) y1 = y0 + 1;
            final double fx0 = x0, fx1 = x1, fy0 = y0, fy1 = y1;
            java.util.function.DoubleUnaryOperator X = v -> L + (tf(v) - fx0) / (fx1 - fx0) * w;
            java.util.function.DoubleUnaryOperator Y = v -> T + h - (tf(v) - fy0) / (fy1 - fy0) * h;

            g.setStroke(new BasicStroke(1f));
            g.draw(new Line2D.Double(L, T, L, T + h));
            g.draw(new Line2D.Double(L, T + h, L + w, T + h));
            for (int i = 0; i <= 5; i++) {
                double vx = x0 + (x1 - x0) * i / 5, vy = y0 + (y1 - y0) * i / 5;
                String lx = String.format(Locale.US, "%.4g", log ? Math.pow(10, vx) : vx);
                String ly = String.format(Locale.US, "%.4g", log ? Math.pow(10, vy) : vy);
                g.setColor(new Color(0xE5E5E5));
                g.draw(new Line2D.Double(L, T + h - h * i / 5.0, L + w, T + h - h * i / 5.0));
                g.setColor(Color.DARK_GRAY);
                g.drawString(lx, (int) (L + w * i / 5.0) - 15, T + h + 18);
                g.drawString(ly, 8, (int) (T + h - h * i / 5.0) + 4);
            }
            g.drawString("N (number of points)", L + w / 2 - 55, T + h + 42);
            g.drawString("time (ms)", 8, T - 12);

            for (int s = 1; s <= 2; s++) {
                g.setColor(s == 1 ? RED : BLUE);
                g.setStroke(new BasicStroke(2f));
                Path2D path = new Path2D.Double();
                for (int i = 0; i < rows.size(); i++) {
                    double[] r = rows.get(i);
                    double px = X.applyAsDouble(r[0]), py = Y.applyAsDouble(r[s]);
                    if (i == 0) path.moveTo(px, py); else path.lineTo(px, py);
                }
                g.draw(path);
                for (double[] r : rows) g.fill(new Ellipse2D.Double(X.applyAsDouble(r[0]) - 3.5, Y.applyAsDouble(r[s]) - 3.5, 7, 7));
            }
            g.setColor(RED);  g.drawString("Brute force  O(n^2)", L + 20, T + 16);
            g.setColor(BLUE); g.drawString("Divide & conquer  O(n log n)", L + 20, T + 34);
        }
    }

    static void showGui(Point[] pts, Result bf, Result dc) {
        SwingUtilities.invokeLater(() -> {
            JFrame f = new JFrame("Closest pair of points");
            f.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

            PlotPanel plot = new PlotPanel(pts, bf, dc);
            JCheckBox strip = new JCheckBox("Show dividing line and strip (width 2d)", true);
            strip.addActionListener(e -> { plot.showStrip = strip.isSelected(); plot.repaint(); });
            JButton anim = new JButton("Animate split / merge");
            anim.addActionListener(e -> plot.animate());
            anim.setEnabled(dc.events != null);
            JPanel bar = new JPanel(new FlowLayout(FlowLayout.LEFT));
            bar.add(anim); bar.add(strip);
            JPanel p1 = new JPanel(new BorderLayout());
            p1.add(plot, BorderLayout.CENTER); p1.add(bar, BorderLayout.SOUTH);

            ChartPanel chart = new ChartPanel();
            JCheckBox lg = new JCheckBox("log-log scale", true);
            lg.addActionListener(e -> { chart.log = lg.isSelected(); chart.repaint(); });
            JPanel p2 = new JPanel(new BorderLayout());
            p2.add(chart, BorderLayout.CENTER);
            JPanel bar2 = new JPanel(new FlowLayout(FlowLayout.LEFT));
            bar2.add(lg);
            p2.add(bar2, BorderLayout.SOUTH);

            JTabbedPane tabs = new JTabbedPane();
            tabs.addTab("Points and closest pairs", p1);
            tabs.addTab("Running time vs N", p2);
            f.add(tabs);
            f.setSize(940, 700);
            f.setLocationRelativeTo(null);
            f.setVisible(true);

            new SwingWorker<Void, double[]>() {
                @Override protected Void doInBackground() {
                    for (int n : BENCH_SIZES) publish(benchRow(n));
                    return null;
                }
                @Override protected void process(List<double[]> chunks) {
                    chart.rows.addAll(chunks);
                    chart.repaint();
                }
            }.execute();
        });
    }

    // -------------------------------------------------------------------- main

    public static void main(String[] args) {
        boolean gui = false;
        long seed = System.nanoTime();
        for (String s : args) {
            if (s.equals("-gui")) gui = true;
            else if (s.equals("-bench")) { runBenchmarkConsole(); return; }
            else if (s.equals("-test")) { stressTest(); return; }
            else if (s.startsWith("-seed=")) seed = Long.parseLong(s.substring(6));
        }

        Scanner in = new Scanner(System.in);
        if (!in.hasNextInt()) { System.err.println("Enter N (integer) on standard input."); return; }
        int n = Math.max(in.nextInt(), 0);
        Point[] pts = generate(n, seed, true);

        warmUp();
        long t0 = System.nanoTime();
        Result bf = bruteForce(pts);
        double bfMs = (System.nanoTime() - t0) / 1e6;
        t0 = System.nanoTime();
        Result dc = divideAndConquer(pts, false);
        double dcMs = (System.nanoTime() - t0) / 1e6;

        System.out.println(describe(bf));
        System.out.println(describe(dc));
        System.out.println(String.format(Locale.US, "Brute-Force: %.3f ms, Divide-and-Conquer: %.3f ms", bfMs, dcMs));

        boolean ok = agree(bf, dc);
        System.err.println("Verification: " + (ok ? "both algorithms agree on the minimum distance." : "MISMATCH!"));

        if (gui) showGui(pts, bf, n <= 5000 ? divideAndConquer(pts, true) : dc);
        else if (!ok) System.exit(1);
    }
}
