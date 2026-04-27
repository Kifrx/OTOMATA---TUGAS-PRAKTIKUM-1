"""
FSM Visualizer — Language L = { x ∈ (0+1)⁺ | ends with 1, no "00" }

"""

import tkinter as tk
from tkinter import messagebox
import math, time

# ── FSM definition ────────────────────────────────────────────────────────────
TRANSITIONS = {
    'S': {'0': 'A', '1': 'B'},
    'A': {'0': 'C', '1': 'B'},
    'B': {'0': 'A', '1': 'B'},
    'C': {'0': 'C', '1': 'C'},
}
ACCEPT_STATES = {'B'}
START_STATE   = 'S'

# Canvas layout
STATE_COORDS = {
    'S': (110, 240),
    'A': (310, 110),
    'B': (310, 370),
    'C': (530, 110),
}
R = 32   # node radius

# ── helpers ───────────────────────────────────────────────────────────────────

def angle(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1)

def edge_point(cx, cy, toward_x, toward_y, r):
    """Point on circle circumference facing toward (toward_x, toward_y)."""
    a = angle(cx, cy, toward_x, toward_y)
    return cx + r * math.cos(a), cy + r * math.sin(a)

def midpoint(x1, y1, x2, y2):
    return (x1 + x2) / 2, (y1 + y2) / 2


# ── main GUI ──────────────────────────────────────────────────────────────────

class FSMGui:
    def __init__(self, root):
        self.root = root
        self.root.title("FSM Visualizer — Language L")
        self.root.resizable(False, False)

        # ── top controls ──────────────────────────────────────────────────────
        top = tk.Frame(root, pady=8)
        top.pack(fill=tk.X, padx=12)

        tk.Label(top, text="Input string (0s & 1s):", font=("Arial", 11)).pack(side=tk.LEFT)
        self.entry = tk.Entry(top, font=("Courier", 13), width=16)
        self.entry.pack(side=tk.LEFT, padx=6)
        self.entry.insert(0, "101")
        self.entry.bind("<Return>", lambda e: self.start_animation())

        self.run_btn = tk.Button(top, text="▶  Run", font=("Arial", 11, "bold"),
                                 bg="#2ECC71", fg="white", padx=8,
                                 command=self.start_animation)
        self.run_btn.pack(side=tk.LEFT, padx=4)

        self.reset_btn = tk.Button(top, text="↺  Reset", font=("Arial", 11),
                                   bg="#BDC3C7", padx=8, command=self.reset)
        self.reset_btn.pack(side=tk.LEFT, padx=4)

        # speed slider
        tk.Label(top, text="  Speed:").pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=0.7)
        tk.Scale(top, from_=0.1, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
                 variable=self.speed_var, length=100, showvalue=False).pack(side=tk.LEFT)

        # ── canvas ────────────────────────────────────────────────────────────
        self.canvas = tk.Canvas(root, width=680, height=490, bg="white",
                                highlightthickness=1, highlightbackground="#ccc")
        self.canvas.pack(padx=12)

        # ── status ────────────────────────────────────────────────────────────
        self.status = tk.Label(root, text="Enter a string and press Run.",
                               font=("Arial", 12, "bold"), pady=4)
        self.status.pack()

        # ── trace log ─────────────────────────────────────────────────────────
        log_frame = tk.Frame(root)
        log_frame.pack(fill=tk.BOTH, padx=12, pady=(0, 10))
        tk.Label(log_frame, text="Step trace:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.log_text = tk.Text(log_frame, height=6, font=("Courier", 10),
                                state=tk.DISABLED, bg="#F4F6F7")
        sb = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        self.node_items = {}   # node_id → canvas oval id
        self._draw_graph()

    # ── draw static graph ─────────────────────────────────────────────────────

    def _draw_graph(self):
        self.canvas.delete("all")
        self.node_items.clear()

        self._draw_all_edges()
        self._draw_start_arrow()
        self._draw_nodes()

    def _draw_all_edges(self):
        # edges that need curved arcs to avoid overlap (bidirectional pairs)
        curved_pairs = {('A', 'B'), ('B', 'A')}

        for src, targets in TRANSITIONS.items():
            for char, dst in targets.items():
                if src == dst:
                    self._draw_self_loop(src, char)
                elif (src, dst) in curved_pairs:
                    self._draw_curved_edge(src, dst, char, curve=40)
                else:
                    self._draw_straight_edge(src, dst, char)

    def _draw_straight_edge(self, src, dst, char, color="gray"):
        x1, y1 = STATE_COORDS[src]
        x2, y2 = STATE_COORDS[dst]
        sx, sy = edge_point(x1, y1, x2, y2, R)
        ex, ey = edge_point(x2, y2, x1, y1, R)
        self.canvas.create_line(sx, sy, ex, ey, arrow=tk.LAST,
                                fill=color, width=2,
                                arrowshape=(12, 14, 5))
        mx, my = midpoint(sx, sy, ex, ey)
        # perpendicular offset for label
        a = angle(sx, sy, ex, ey)
        lx = mx + 14 * math.sin(a)
        ly = my - 14 * math.cos(a)
        self.canvas.create_text(lx, ly, text=char, font=("Arial", 11, "bold"))

    def _draw_curved_edge(self, src, dst, char, curve=40):
        x1, y1 = STATE_COORDS[src]
        x2, y2 = STATE_COORDS[dst]
        # control point offset perpendicular to the midpoint
        mx, my = midpoint(x1, y1, x2, y2)
        a = angle(x1, y1, x2, y2)
        perp = a + math.pi / 2
        cx = mx + curve * math.cos(perp)
        cy = my + curve * math.sin(perp)

        # approximate start/end on circle edge toward control point
        sx, sy = edge_point(x1, y1, cx, cy, R)
        ex, ey = edge_point(x2, y2, cx, cy, R)

        self.canvas.create_line(sx, sy, cx, cy, ex, ey,
                                smooth=True, arrow=tk.LAST,
                                fill="gray", width=2,
                                arrowshape=(12, 14, 5))
        # label near the control point, slightly inward
        lx = cx + 12 * math.cos(perp + math.pi)
        ly = cy + 12 * math.sin(perp + math.pi)
        self.canvas.create_text(lx, ly, text=char, font=("Arial", 11, "bold"))

    def _draw_self_loop(self, node, char):
        x, y = STATE_COORDS[node]
        # draw loop above the node
        lx, ly = x, y - R
        if char == '0':
            lx -= 10
        elif char == '1':
            lx += 10
        size = 24
        self.canvas.create_arc(lx - size, ly - size*2,
                               lx + size, ly,
                               start=20, extent=300,
                               style=tk.ARC, outline="gray", width=2)
        # arrowhead at the end of arc (approximate bottom-left of arc)
        a_rad = math.radians(20)  # start angle
        tip_x = lx + size * math.cos(math.radians(-10))
        tip_y = ly + size * math.sin(math.radians(-10)) - size
        # small manual arrowhead polygon
        ah = 8
        self.canvas.create_polygon(
            tip_x, tip_y + size * 0.85,
            tip_x - 5, tip_y + size * 0.85 - ah,
            tip_x + 5, tip_y + size * 0.85 - ah,
            fill="gray", outline="gray"
        )
        self.canvas.create_text(lx, ly - size*2 - 8, text=char,
                                font=("Arial", 11, "bold"))

    def _draw_start_arrow(self):
        x, y = STATE_COORDS[START_STATE]
        self.canvas.create_line(x - 65, y, x - R - 2, y,
                                arrow=tk.LAST, fill="#2980B9",
                                width=2.5, arrowshape=(12, 14, 5))
        self.canvas.create_text(x - 72, y, text="start",
                                font=("Arial", 9), fill="#2980B9", anchor=tk.E)

    def _draw_nodes(self):
        for node, (x, y) in STATE_COORDS.items():
            is_accept = node in ACCEPT_STATES
            outline_color = "#2980B9" if is_accept else "#2C3E50"
            lw = 3 if is_accept else 2

            if is_accept:
                # outer double-circle ring
                self.canvas.create_oval(x - R - 6, y - R - 6,
                                        x + R + 6, y + R + 6,
                                        outline="#2980B9", width=2)

            oid = self.canvas.create_oval(x - R, y - R, x + R, y + R,
                                          fill="white",
                                          outline=outline_color, width=lw)
            self.canvas.create_text(x, y, text=node,
                                    font=("Arial", 15, "bold"),
                                    fill="#2C3E50")
            self.node_items[node] = oid

        # trap label
        cx, cy = STATE_COORDS['C']
        self.canvas.create_text(cx, cy + R + 14, text="trap",
                                font=("Arial", 9, "italic"), fill="#E74C3C")

    # ── animation ─────────────────────────────────────────────────────────────

    def _set_node_color(self, node, color):
        self.canvas.itemconfig(self.node_items[node], fill=color)
        self.canvas.update()

    def _reset_colors(self):
        for n in self.node_items:
            self._set_node_color(n, "white")

    def _log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_animation(self):
        s = self.entry.get().strip()
        if not s or not all(c in '01' for c in s):
            messagebox.showerror("Invalid input",
                                 "Please enter a non-empty binary string (only 0s and 1s).")
            return

        self.run_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.DISABLED)
        self._reset_colors()
        self._clear_log()
        self._log(f"String: \"{s}\"")
        self._log(f"{'Step':<6} {'State':<8} {'Read':<6} {'→ State':<10} Note")
        self._log("─" * 45)

        delay = self.speed_var.get()
        state = START_STATE
        self._set_node_color(state, "#F39C12")   # orange = current

        for i, ch in enumerate(s):
            self.status.config(text=f"Step {i+1}: state={state}  reading='{ch}'",
                               fg="black")
            self.root.update()
            time.sleep(delay)

            next_state = TRANSITIONS[state][ch]
            note = "⚠ trap!" if next_state == 'C' and state != 'C' else (
                   "still in trap" if next_state == 'C' else "")
            self._log(f"  {i+1:<5} {state:<8} '{ch}'    → {next_state:<9} {note}")

            self._set_node_color(state, "white")
            state = next_state
            self._set_node_color(state, "#F39C12")
            self.root.update()

        # final
        if state in ACCEPT_STATES:
            self._set_node_color(state, "#2ECC71")   # green
            self.status.config(
                text=f"✓  ACCEPTED — ends with '1' and no '00' substring",
                fg="#27AE60")
            self._log(f"\nResult: ACCEPTED ✓  (final state: {state})")
        else:
            self._set_node_color(state, "#E74C3C")   # red
            reason = ("contains '00'" if state == 'C'
                      else f"does not end with '1' (state {state})")
            self.status.config(text=f"✗  REJECTED — {reason}", fg="#C0392B")
            self._log(f"\nResult: REJECTED ✗  ({reason})")

        self.run_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.NORMAL)

    def reset(self):
        self._reset_colors()
        self._clear_log()
        self.status.config(text="Enter a string and press Run.", fg="black")


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    FSMGui(root)
    root.mainloop()
