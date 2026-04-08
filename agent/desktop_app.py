import io
import os
import queue
import threading
import tkinter as tk
from contextlib import redirect_stderr, redirect_stdout
from tkinter import messagebox, scrolledtext

from agent.config import AppConfig, DEFAULT_QUERY
from agent.pipeline import run_agent


class QueueWriter(io.TextIOBase):
    def __init__(self, output_queue: queue.Queue[str]) -> None:
        self.output_queue = output_queue

    def write(self, text: str) -> int:
        if text:
            self.output_queue.put(text)
        return len(text)

    def flush(self) -> None:
        return None


class ResearchDesktopApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Research Agent")
        self.root.geometry("980x700")
        self.root.configure(bg="#111111")

        self.output_queue: queue.Queue[str] = queue.Queue()
        self.latest_report_path = None
        self.is_running = False

        self.query_var = tk.StringVar(value=DEFAULT_QUERY)
        self.vault_var = tk.StringVar(value="Vault/Harish")
        self.model_var = tk.StringVar(value="qwen3.5:4b")
        self.max_results_var = tk.StringVar(value="5")

        self._build_ui()
        self.root.after(100, self._drain_output_queue)

    def _build_ui(self) -> None:
        header = tk.Label(
            self.root,
            text="Generic Research Agent",
            bg="#111111",
            fg="#f5f5f5",
            font=("Consolas", 18, "bold"),
        )
        header.pack(padx=12, pady=(12, 8), anchor="w")

        form = tk.Frame(self.root, bg="#111111")
        form.pack(fill="x", padx=12)

        self._add_labeled_entry(form, "Query", self.query_var, 0)
        self._add_labeled_entry(form, "Vault", self.vault_var, 1)
        self._add_labeled_entry(form, "Model", self.model_var, 2)
        self._add_labeled_entry(form, "Max Results", self.max_results_var, 3)

        actions = tk.Frame(self.root, bg="#111111")
        actions.pack(fill="x", padx=12, pady=10)

        self.run_button = tk.Button(
            actions,
            text="Run Research",
            command=self._start_run,
            bg="#1f6feb",
            fg="#ffffff",
            activebackground="#388bfd",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=8,
        )
        self.run_button.pack(side="left", padx=(0, 8))

        open_vault = tk.Button(
            actions,
            text="Open Vault",
            command=self._open_vault,
            bg="#30363d",
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=8,
        )
        open_vault.pack(side="left", padx=(0, 8))

        self.open_report_button = tk.Button(
            actions,
            text="Open Latest Report",
            command=self._open_latest_report,
            bg="#30363d",
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=8,
            state="disabled",
        )
        self.open_report_button.pack(side="left")

        self.status_label = tk.Label(
            self.root,
            text="Ready",
            bg="#111111",
            fg="#8b949e",
            font=("Consolas", 10),
        )
        self.status_label.pack(padx=12, pady=(0, 8), anchor="w")

        self.output = scrolledtext.ScrolledText(
            self.root,
            bg="#0d1117",
            fg="#c9d1d9",
            insertbackground="#c9d1d9",
            font=("Consolas", 11),
            wrap="word",
        )
        self.output.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.output.insert("end", "Research Agent desktop terminal ready.\n")
        self.output.insert("end", "Enter a query and click 'Run Research'.\n")
        self.output.configure(state="disabled")

    def _add_labeled_entry(self, parent: tk.Frame, label: str, variable: tk.StringVar, row: int) -> None:
        tk.Label(
            parent,
            text=label,
            bg="#111111",
            fg="#f5f5f5",
            font=("Consolas", 10),
        ).grid(row=row, column=0, sticky="w", pady=4)

        entry = tk.Entry(
            parent,
            textvariable=variable,
            bg="#0d1117",
            fg="#c9d1d9",
            insertbackground="#c9d1d9",
            relief="flat",
            font=("Consolas", 10),
            width=90,
        )
        entry.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=4)
        parent.grid_columnconfigure(1, weight=1)

    def _start_run(self) -> None:
        if self.is_running:
            return

        query = self.query_var.get().strip()
        vault_dir = self.vault_var.get().strip()
        model = self.model_var.get().strip()
        max_results = self.max_results_var.get().strip()

        if not query:
            messagebox.showerror("Missing Query", "Please enter a research query.")
            return

        try:
            max_results_int = int(max_results)
        except ValueError:
            messagebox.showerror("Invalid Max Results", "Max Results must be a number.")
            return

        self.is_running = True
        self.run_button.configure(state="disabled")
        self.status_label.configure(text="Running research...")
        self._write_output(f"\n> Query: {query}\n")
        self._write_output(f"> Vault: {vault_dir}\n")
        self._write_output(f"> Model: {model}\n\n")

        config = AppConfig(
            vault_dir=_path(vault_dir),
            model=model,
            max_results=max_results_int,
        )

        thread = threading.Thread(
            target=self._run_agent_worker,
            args=(query, config),
            daemon=True,
        )
        thread.start()

    def _run_agent_worker(self, query: str, config: AppConfig) -> None:
        writer = QueueWriter(self.output_queue)
        try:
            with redirect_stdout(writer), redirect_stderr(writer):
                result = run_agent(query, config)
                print(f"\nSaved report to: {result.report_path}")
                self.latest_report_path = result.report_path
                self.output_queue.put("__RUN_COMPLETE__")
        except Exception as exc:
            self.output_queue.put(f"\nRun failed: {exc}\n")
            self.output_queue.put("__RUN_COMPLETE__")

    def _drain_output_queue(self) -> None:
        while True:
            try:
                item = self.output_queue.get_nowait()
            except queue.Empty:
                break

            if item == "__RUN_COMPLETE__":
                self.is_running = False
                self.run_button.configure(state="normal")
                self.status_label.configure(text="Ready")
                if self.latest_report_path:
                    self.open_report_button.configure(state="normal")
            else:
                self._write_output(item)

        self.root.after(100, self._drain_output_queue)

    def _write_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def _open_vault(self) -> None:
        vault_dir = _path(self.vault_var.get().strip())
        if not vault_dir.exists():
            messagebox.showerror("Vault Not Found", f"Vault path does not exist:\n{vault_dir}")
            return
        os.startfile(vault_dir)

    def _open_latest_report(self) -> None:
        if not self.latest_report_path:
            messagebox.showerror("No Report", "Run the agent first to generate a report.")
            return
        os.startfile(self.latest_report_path)

    def run(self) -> None:
        self.root.mainloop()



def launch_desktop_app() -> None:
    app = ResearchDesktopApp()
    app.run()



def _path(value: str):
    from pathlib import Path

    return Path(value)
