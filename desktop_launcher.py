"""Launcher desktop da MARCOS IDE 17.0; inicia servidor local e abre o navegador."""
from __future__ import annotations

import socket
import threading
import time
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import messagebox

import uvicorn
from app import app as fastapi_app


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class MarcosDesktop:
    def __init__(self):
        self.port = get_free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        config = uvicorn.Config(
            fastapi_app,
            host="127.0.0.1",
            port=self.port,
            log_level="warning",
            access_log=False,
            lifespan="on",
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.root = tk.Tk()
        self.root.title("MARCOS IDE 17.0")
        self.root.geometry("440x230")
        self.root.resizable(False, False)
        self.root.configure(bg="#101827")
        self.status = tk.StringVar(value="Iniciando o ambiente...")
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.thread.start()
        self.root.after(250, self.check_ready)

    def _build_ui(self):
        tk.Label(
            self.root, text="MARCOS IDE 17.0",
            font=("Segoe UI", 19, "bold"), fg="#e7efff", bg="#101827"
        ).pack(pady=(20, 4))
        tk.Label(
            self.root, text="Ambiente de programação da Linguagem MARCOS",
            font=("Segoe UI", 9), fg="#9aabc4", bg="#101827"
        ).pack()
        tk.Label(
            self.root, textvariable=self.status,
            font=("Segoe UI", 10), fg="#55d6a5", bg="#101827"
        ).pack(pady=15)
        buttons = tk.Frame(self.root, bg="#101827")
        buttons.pack()
        tk.Button(
            buttons, text="Abrir MARCOS IDE", command=self.open_browser,
            bg="#247bd1", fg="white", activebackground="#318ce6",
            relief="flat", padx=15, pady=8
        ).pack(side="left", padx=5)
        tk.Button(
            buttons, text="Encerrar", command=self.close,
            bg="#26364d", fg="white", activebackground="#354965",
            relief="flat", padx=15, pady=8
        ).pack(side="left", padx=5)
        tk.Label(
            self.root, text=self.url, font=("Consolas", 9),
            fg="#8ea1bd", bg="#101827"
        ).pack(pady=12)

    def check_ready(self):
        if not self.thread.is_alive():
            self.status.set("Não foi possível iniciar o servidor local.")
            messagebox.showerror(
                "MARCOS IDE", "O servidor local foi encerrado. Consulte os requisitos da instalação."
            )
            return
        try:
            with urllib.request.urlopen(self.url + "/health", timeout=1) as response:
                if response.status == 200:
                    self.status.set("Servidor ativo — navegador pronto.")
                    self.open_browser()
                    return
        except Exception:
            pass
        self.root.after(250, self.check_ready)

    def open_browser(self):
        webbrowser.open(self.url, new=2)

    def close(self):
        self.status.set("Encerrando...")
        self.server.should_exit = True
        self.root.after(300, self.root.destroy)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MarcosDesktop().run()
