from __future__ import annotations

import subprocess
import sys
import os
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"


@dataclass(frozen=True)
class MenuItem:
    key: str
    title: str
    description: str
    action: str


class Manual:
    def __init__(self, readme_path: Path, console: Console) -> None:
        self.readme_path = readme_path
        self.console = console

    def show(self) -> None:
        self.console.rule("[bold cyan]说明书[/bold cyan]")
        if not self.readme_path.exists():
            self.console.print(f"[red]README not found:[/red] {self.readme_path}")
            self._pause()
            return

        text = self.readme_path.read_text(encoding="utf-8")
        self.console.print(Markdown(text))
        self._pause()

    def _pause(self) -> None:
        try:
            self.console.input("\n[bold]按 Enter 返回主菜单...[/bold]")
        except EOFError:
            return


class MainMenu:
    def __init__(self) -> None:
        os.system("")
        self.console = Console(highlight=False, soft_wrap=True)
        self.manual = Manual(README_PATH, self.console)
        self.items = [
            MenuItem("1", "文本生成", "调用 generate_text.py", "text"),
            MenuItem("2", "多轮对话", "调用 chat_loop.py", "chat"),
            MenuItem("3", "图片生成", "调用 generate_image.py", "image"),
            MenuItem("4", "视频生成", "调用 generate_video.py", "video"),
            MenuItem("5", "说明书", "读取 README.md", "manual"),
            MenuItem("0", "退出", "关闭菜单", "exit"),
        ]

    def run(self) -> None:
        self._print_header()
        while True:
            self._print_menu()
            choice = self._read_line("\n[bold]请选择功能编号: [/bold]").strip()
            if not choice:
                self.console.rule()
                self.console.print("[green]已退出。[/green]")
                return
            item = self._find_item(choice)
            if item is None:
                self.console.print("[red]无效选择。[/red]")
                self._pause()
                continue

            if item.action == "exit":
                self.console.rule()
                self.console.print("[green]已退出。[/green]")
                return
            if item.action == "manual":
                self.manual.show()
            elif item.action == "text":
                self.generate_text()
            elif item.action == "chat":
                self.start_chat()
            elif item.action == "image":
                self.generate_image()
            elif item.action == "video":
                self.generate_video()

    def _print_header(self) -> None:
        self.console.print()
        self.console.print(Panel.fit("[bold cyan]Agnes AI Generation[/bold cyan]", border_style="cyan"))

    def _print_menu(self) -> None:
        self.console.rule("[bold cyan]主菜单[/bold cyan]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("编号", justify="center", style="bold", width=6)
        table.add_column("工具")
        table.add_column("说明")
        for item in self.items:
            table.add_row(item.key, item.title, item.description)
        self.console.print(table)
        self.console.print("[dim]提示：直接按 Enter 或选择 0 退出。[/dim]")

    def _find_item(self, key: str) -> MenuItem | None:
        return next((item for item in self.items if item.key == key), None)

    def generate_text(self) -> None:
        self._print_section("文本生成")
        prompt = self._required("请输入提示词")
        args = ["--prompt", prompt]
        self._append_text(args, "--system", "系统提示词", "You are a helpful AI assistant.")
        self._append_text(args, "--image-url", "图片 URL，可留空")
        self._append_text(args, "--model", "模型名，可留空")
        self._append_float(args, "--temperature", "temperature", 0.7)
        self._append_int(args, "--max-tokens", "max tokens", 1024)
        self._append_flag(args, "--stream", "是否流式输出")
        self._append_flag(args, "--enable-thinking", "是否开启 thinking")
        self._run_tool("generate_text.py", args)

    def start_chat(self) -> None:
        self._print_section("多轮对话")
        args: list[str] = []
        self._append_text(args, "--system", "系统提示词", "You are a helpful AI assistant. Answer in Chinese by default.")
        self._append_text(args, "--model", "模型名，可留空")
        self._append_float(args, "--temperature", "temperature", 0.7)
        self._append_int(args, "--max-tokens", "max tokens", 1024)
        self._run_tool("chat_loop.py", args, interactive=True)

    def generate_image(self) -> None:
        self._print_section("图片生成")
        prompt = self._required("请输入图片提示词")
        args = ["--prompt", prompt]
        self._append_text(args, "--size", "尺寸", "1024x768")
        self._append_text(args, "--model", "模型名，可留空")
        for image_url in self._collect_many("参考图片 URL，可重复输入，空行结束"):
            args.extend(["--image", image_url])
        self._append_flag(args, "--base64", "是否返回 base64 并保存")
        if self._yes_no("是否只显示 URL，不下载图片"):
            args.append("--no-download")
        self._run_tool("generate_image.py", args)

    def generate_video(self) -> None:
        self._print_section("视频生成")
        prompt = self._required("请输入视频提示词")
        args = ["--prompt", prompt]
        self._append_text(args, "--model", "模型名，可留空")
        self._append_text(args, "--image", "单张图生视频 URL，可留空")
        for image_url in self._collect_many("额外参考图/关键帧 URL，可重复输入，空行结束"):
            args.extend(["--extra-image", image_url])
        self._append_choice(args, "--mode", "生成模式", ["ti2vid", "keyframes"])
        self._append_int(args, "--width", "宽度", 1152)
        self._append_int(args, "--height", "高度", 768)
        self._append_int(args, "--num-frames", "帧数，需符合 8n + 1", 121)
        self._append_int(args, "--frame-rate", "帧率", 24)
        self._append_int(args, "--seed", "seed，可留空")
        self._append_text(args, "--negative-prompt", "反向提示词，可留空")
        no_wait = self._yes_no("是否只创建任务，不等待结果")
        if no_wait:
            args.append("--no-wait")
        else:
            self._append_int(args, "--poll-seconds", "轮询间隔秒", 10)
            self._append_int(args, "--timeout-seconds", "超时秒数", 1800)
            if self._yes_no("是否只显示 URL，不下载视频"):
                args.append("--no-download")
        self._run_tool("generate_video.py", args)

    def _print_section(self, title: str) -> None:
        self.console.rule(f"[bold cyan]{title}[/bold cyan]")

    def _run_tool(self, script_name: str, args: list[str], *, interactive: bool = False) -> None:
        script_path = ROOT / "scripts" / script_name
        command = [sys.executable, str(script_path), *args]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        self.console.rule("[bold green]工具开始[/bold green]")
        self.console.print(subprocess.list2cmdline(command), style="dim", markup=False)

        if interactive:
            completed = subprocess.run(command, cwd=ROOT, check=False, env=env)
            self.console.rule("[bold green]工具结束[/bold green]")
        else:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                check=False,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self._print_process_output(completed)

        if completed.returncode:
            self.console.print(f"\n工具退出码: {completed.returncode}", style="red", markup=False)
        else:
            self.console.print("\n[green]工具执行完成。[/green]")
        self._pause()

    def _print_process_output(self, completed: subprocess.CompletedProcess[str]) -> None:
        stdout = self._normalize_output(completed.stdout)
        stderr = self._normalize_output(completed.stderr)

        self.console.rule("[bold green]工具输出[/bold green]")
        if stdout:
            self.console.print(stdout.rstrip(), markup=False, soft_wrap=True)
        else:
            self.console.print("[dim]工具没有输出内容。[/dim]")

        if stderr:
            self.console.rule("[bold yellow]错误输出[/bold yellow]")
            self.console.print(stderr.rstrip(), style="yellow", markup=False, soft_wrap=True)

        self.console.rule("[bold green]输出结束[/bold green]")

    @staticmethod
    def _normalize_output(output: str | None) -> str:
        if not output:
            return ""
        return output.replace("\r\n", "\n").replace("\r", "\n")

    def _required(self, label: str) -> str:
        while True:
            value = self._read_line(f"{label}: ").strip()
            if value:
                return value
            self.console.print("[red]该项不能为空。[/red]")

    def _append_text(
        self,
        args: list[str],
        flag: str,
        label: str,
        default: str | None = None,
    ) -> None:
        value = self._input(label, default)
        if value:
            args.extend([flag, value])

    def _append_int(
        self,
        args: list[str],
        flag: str,
        label: str,
        default: int | None = None,
    ) -> None:
        value = self._input(label, None if default is None else str(default))
        if not value:
            return
        try:
            int(value)
        except ValueError:
            self.console.print(f"[yellow]{label} 不是整数，已忽略。[/yellow]")
            return
        args.extend([flag, value])

    def _append_float(
        self,
        args: list[str],
        flag: str,
        label: str,
        default: float | None = None,
    ) -> None:
        value = self._input(label, None if default is None else str(default))
        if not value:
            return
        try:
            float(value)
        except ValueError:
            self.console.print(f"[yellow]{label} 不是数字，已忽略。[/yellow]")
            return
        args.extend([flag, value])

    def _append_choice(
        self,
        args: list[str],
        flag: str,
        label: str,
        choices: list[str],
    ) -> None:
        prompt = f"{label} ({'/'.join(choices)}，可留空)"
        value = self._input(prompt)
        if not value:
            return
        if value not in choices:
            self.console.print(f"[yellow]{label} 无效，已忽略。[/yellow]")
            return
        args.extend([flag, value])

    def _append_flag(self, args: list[str], flag: str, label: str) -> None:
        if self._yes_no(label):
            args.append(flag)

    def _collect_many(self, label: str) -> list[str]:
        values: list[str] = []
        self.console.print(label)
        while True:
            value = self._read_line("  > ").strip()
            if not value:
                return values
            values.append(value)

    def _input(self, label: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default is not None else ""
        value = self._read_line(f"{label}{suffix}: ").strip()
        if value:
            return value
        return default or ""

    def _yes_no(self, label: str) -> bool:
        value = self._read_line(f"{label}? [y/N]: ").strip().lower()
        return value in {"y", "yes", "1", "true"}

    def _pause(self) -> None:
        self._read_line("\n[bold]按 Enter 返回主菜单...[/bold]")

    def _read_line(self, prompt: str) -> str:
        try:
            return self.console.input(prompt)
        except EOFError:
            return ""

    @staticmethod
    def _quote(value: str) -> str:
        if " " in value:
            return f'"{value}"'
        return value


if __name__ == "__main__":
    MainMenu().run()
