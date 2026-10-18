"""Capture the real Tkinter experiment-1 interface for the report."""

import sys
import tkinter as tk
from pathlib import Path

from PIL import ImageGrab


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "exp1"))
from gui import DispatchGame  # noqa: E402


def main():
    root = tk.Tk()
    game = DispatchGame(root)
    root.update_idletasks()
    root.update()

    first_order = game.order_tree.get_children()[0]
    game.order_tree.selection_set(first_order)
    game.rider_tree.selection_set("R01")
    game.on_assign()
    game._add_next_order()
    game._add_next_order()
    game.refresh_all(select_rider="R01")
    root.update_idletasks()
    root.update()

    target = ROOT / "output" / "report_qa" / "exp1_gui.png"
    ImageGrab.grab(window=root.winfo_id()).save(target)
    game.holding_tree.selection_set(first_order)
    game.on_deliver()
    root.update_idletasks()
    root.update()
    ImageGrab.grab(window=root.winfo_id()).save(target.with_name("exp1_optional.png"))
    root.destroy()
    print(target)


if __name__ == "__main__":
    main()
