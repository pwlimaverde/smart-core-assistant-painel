import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text
from rich.panel import Panel


def load_tasks():
    """Load tasks from the JSON file."""
    # Try to find the project root
    # Assuming script is in scripts/ folder, root is one level up
    root_dir = Path(__file__).parent.parent
    tasks_path = root_dir / ".taskmaster" / "tasks" / "tasks.json"

    if not tasks_path.exists():
        print(f"Error: Tasks file not found at {tasks_path}")
        sys.exit(1)

    try:
        with open(tasks_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Check if 'tasks' is at the root
            if "tasks" in data and isinstance(data["tasks"], list):
                return data["tasks"]

            # Check if it's nested under tags (e.g., "master": {"tasks": []})
            all_tasks = []
            for key, value in data.items():
                if (
                    isinstance(value, dict)
                    and "tasks" in value
                    and isinstance(value["tasks"], list)
                ):
                    all_tasks.extend(value["tasks"])

            if all_tasks:
                return all_tasks

            # Fallback: return empty list if structure is unknown but valid JSON
            print(
                "Warning: Could not find 'tasks' list in JSON structure. Returning empty list."
            )
            return []

        return []
    except Exception as e:
        print(f"Error reading tasks file: {e}")
        sys.exit(1)


def get_status_style(status):
    """Return a rich style and emoji for the status."""
    status = status.lower()
    if status == "completed" or status == "done":
        return "green", "✅"
    elif status == "in_progress" or status == "in-progress":
        return "blue", "🔄"
    elif status == "pending":
        return "yellow", "⏳"
    elif status == "blocked":
        return "red", "🚫"
    elif status == "deferred":
        return "dim", "zzz"
    else:
        return "white", "❓"


def get_priority_style(priority):
    """Return a rich style for priority."""
    priority = priority.lower() if priority else "medium"
    if priority == "high":
        return "bold red"
    elif priority == "medium":
        return "yellow"
    elif priority == "low":
        return "green"
    return "white"


def format_dependencies(deps):
    """Format dependencies list."""
    if not deps:
        return "-"
    return ", ".join(str(d) for d in deps)


def main():
    console = Console()
    tasks = load_tasks()

    # Sort tasks: pending/in-progress first, then by ID
    # A simple sort key: status_priority (0 for active, 1 for done) + id
    def sort_key(t):
        status = t.get("status", "").lower()
        is_done = status in ["completed", "done", "cancelled"]
        return (
            is_done,
            int(t.get("id", 0)) if str(t.get("id", "0")).isdigit() else 999,
        )

    tasks.sort(key=sort_key)

    table = Table(title="🤖 Task Master - Project Tasks", box=box.ROUNDED)

    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Prio", justify="center")
    table.add_column("Title", style="bold white")
    table.add_column("Deps", justify="center", style="dim")
    table.add_column("Codes/Modules", style="magenta")

    pending_count = 0
    completed_count = 0

    for task in tasks:
        t_id = str(task.get("id", "?"))
        title = task.get("title", "No Title")
        status = task.get("status", "pending")
        priority = task.get("priority", "medium")
        deps = task.get("dependencies", [])
        details = task.get("details", "")

        # Extract codes from details or title if possible (simple heuristic)
        # Just showing the first line of details or finding patterns like [MOD]
        module_code = ""
        if title.startswith("["):
            module_code = title.split("]")[0] + "]"

        # Count stats
        if status in ["completed", "done"]:
            completed_count += 1
        else:
            pending_count += 1

        color, emoji = get_status_style(status)
        prio_style = get_priority_style(priority)

        status_render = Text(f"{emoji} {status}", style=color)
        prio_render = Text(priority, style=prio_style)

        table.add_row(
            t_id,
            status_render,
            prio_render,
            title,
            format_dependencies(deps),
            module_code,
        )

        # Add Subtasks row if they exist
        subtasks = task.get("subtasks", [])
        if subtasks:
            subtask_table = Table(
                show_header=False, box=None, padding=(0, 0, 0, 4)
            )
            subtask_table.add_column("ID", style="dim cyan", width=4)
            subtask_table.add_column("Status", width=12)
            subtask_table.add_column("Title", style="dim white")

            for st in subtasks:
                st_id = str(st.get("id", "?"))
                st_title = st.get("title", "No Title")
                st_status = st.get("status", "pending")

                st_color, st_emoji = get_status_style(st_status)
                st_status_render = Text(
                    f"{st_emoji} {st_status}", style=st_color
                )

                subtask_table.add_row(
                    f"  └─ {st_id}", st_status_render, st_title
                )

            table.add_row("", "", "", subtask_table, "", "")

    console.print(table)

    # Summary Panel
    summary = f"[bold green]Completed:[/bold green] {completed_count} | [bold yellow]Pending/Active:[/bold yellow] {pending_count} | [bold]Total:[/bold] {len(tasks)}"
    console.print(Panel(summary, title="Summary", expand=False))


if __name__ == "__main__":
    main()
