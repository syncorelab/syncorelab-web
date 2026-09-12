"""Conway's Game of Life — tkinter, fixed window, scalable grid.

Controls:
  - Grid size slider: 10–500 cells per side (window stays the same size,
    cells scale so the whole grid is always visible)
  - Speed slider: generations per second
  - Random fill: seed the grid randomly (~25% alive)
  - Start/Pause: run or pause the simulation

Edges wrap around (torus): gliders leaving one side re-enter the other.
Uses numpy for fast stepping on large grids if available
(install with: pip3 install numpy); falls back to pure Python otherwise.
"""

import random
import tkinter as tk

try:
    import numpy as np
except ImportError:
    np = None

FILL_DENSITY = 0.25     # fraction of live cells for random fill
ALIVE = "#3ddc84"
DEAD = "#111111"


def canvas_size(root):
    """Largest square that fits the screen, leaving room for controls."""
    return min(root.winfo_screenwidth() - 40, root.winfo_screenheight() - 140)


def step(grid):
    """Pure-Python next generation. Grid is a list of lists of 0/1, wrapping edges."""
    n = len(grid)
    new = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            neighbors = (
                grid[(r - 1) % n][(c - 1) % n] + grid[(r - 1) % n][c] + grid[(r - 1) % n][(c + 1) % n]
                + grid[r][(c - 1) % n] + grid[r][(c + 1) % n]
                + grid[(r + 1) % n][(c - 1) % n] + grid[(r + 1) % n][c] + grid[(r + 1) % n][(c + 1) % n]
            )
            if grid[r][c]:
                new[r][c] = 1 if neighbors in (2, 3) else 0
            else:
                new[r][c] = 1 if neighbors == 3 else 0
    return new


def step_numpy(grid):
    """Numpy next generation with wrap-around edges."""
    neighbors = sum(
        np.roll(np.roll(grid, dr, 0), dc, 1)
        for dr in (-1, 0, 1) for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0)
    )
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(np.uint8)


class GameOfLife:
    def __init__(self, root):
        self.root = root
        root.title("Conway's Game of Life")
        root.resizable(False, False)

        self.running = False
        self.after_id = None
        self.canvas_size = canvas_size(root)

        # --- Controls ---
        controls = tk.Frame(root)
        controls.pack(fill="x", padx=8, pady=4)

        self.start_btn = tk.Button(controls, text="Start", width=8, command=self.toggle)
        self.start_btn.pack(side="left", padx=(0, 8))

        tk.Button(controls, text="Random fill", command=self.random_fill).pack(side="left", padx=(0, 16))

        tk.Label(controls, text="Grid size").pack(side="left")
        self.size_var = tk.IntVar(value=100)
        tk.Scale(controls, from_=10, to=500, orient="horizontal", variable=self.size_var,
                 command=self.on_size_change, length=220).pack(side="left", padx=(0, 16))

        tk.Label(controls, text="Speed (gen/s)").pack(side="left")
        self.speed_var = tk.IntVar(value=10)
        tk.Scale(controls, from_=1, to=60, orient="horizontal", variable=self.speed_var,
                 length=140).pack(side="left")

        self.gen_label = tk.Label(controls, text="Gen: 0")
        self.gen_label.pack(side="right")

        # --- Canvas (fixed size) ---
        self.canvas = tk.Canvas(root, width=self.canvas_size, height=self.canvas_size,
                                bg=DEAD, highlightthickness=0)
        self.canvas.pack(padx=8, pady=(0, 8))
        self.photo = None
        self.image_id = None

        self.generation = 0
        self.reset_grid(self.size_var.get())
        self.random_fill()

    # --- Grid management ---
    def reset_grid(self, n):
        self.n = n
        if np:
            self.grid = np.zeros((n, n), dtype=np.uint8)
        else:
            self.grid = [[0] * n for _ in range(n)]
        self.generation = 0
        self.draw()

    def on_size_change(self, _value):
        self.reset_grid(self.size_var.get())

    def random_fill(self):
        n = self.n
        if np:
            self.grid = (np.random.random((n, n)) < FILL_DENSITY).astype(np.uint8)
        else:
            self.grid = [[1 if random.random() < FILL_DENSITY else 0 for _ in range(n)]
                         for _ in range(n)]
        self.generation = 0
        self.draw()

    # --- Simulation ---
    def toggle(self):
        self.running = not self.running
        self.start_btn.config(text="Pause" if self.running else "Start")
        if self.running:
            self.tick()
        elif self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def tick(self):
        if not self.running:
            return
        self.grid = step_numpy(self.grid) if np else step(self.grid)
        self.generation += 1
        self.draw()
        delay = max(1, int(1000 / self.speed_var.get()))
        self.after_id = self.root.after(delay, self.tick)

    # --- Drawing ---
    def draw(self):
        n = self.n
        # Render the grid as an n x n image, then integer-zoom it to fill the canvas.
        small = tk.PhotoImage(width=n, height=n)
        rows = []
        for r in range(n):
            row = self.grid[r]
            rows.append("{" + " ".join(ALIVE if row[c] else DEAD for c in range(n)) + "}")
        small.put(" ".join(rows), to=(0, 0, n, n))

        zoom = max(1, self.canvas_size // n)
        self.photo = small.zoom(zoom) if zoom > 1 else small
        offset = (self.canvas_size - n * zoom) // 2

        if self.image_id is None:
            self.image_id = self.canvas.create_image(offset, offset, anchor="nw",
                                                     image=self.photo)
        else:
            self.canvas.itemconfig(self.image_id, image=self.photo)
            self.canvas.coords(self.image_id, offset, offset)
        self.gen_label.config(text=f"Gen: {self.generation}")


if __name__ == "__main__":
    root = tk.Tk()
    GameOfLife(root)
    root.mainloop()
