import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

LOG_FILE = "work_log.csv"
METADATA_FILE = "task_metadata.csv"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Project", "Task", "Hours"])

if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Project", "Task", "Importance", "Urgency", "Deadline"])

class WorkLoggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Work Planner with Task Overview")
        #self.projects = ["Bathymetry", "Synchronization", "Alaska", "Estimation", "Other"]
        PROJECTS_FILE = "projects.csv"
        if not os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows([["Bathymetry"], ["Synchronization"], ["Alaska"], ["Estimation"], ["Other"]])
        with open(PROJECTS_FILE, mode='r') as file:
            reader = csv.reader(file)
            self.projects = [row[0] for row in reader if row]


        self.notebook = ttk.Notebook(root)
        self.tab_logger = ttk.Frame(self.notebook)
        self.tab_overview = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_logger, text="Work Logger")
        self.notebook.add(self.tab_overview, text="Task Overview")
        self.notebook.pack(expand=True, fill="both")

        self.build_logger_tab()
        self.build_overview_tab()

    def build_logger_tab(self):
        tab = self.tab_logger
        ttk.Label(tab, text="Project:").grid(row=0, column=0, sticky="w")
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(tab, textvariable=self.project_var, values=self.projects)
        self.project_combo.grid(row=0, column=1, sticky="ew")
        self.project_combo.current(0)

        ttk.Label(tab, text="Task Description:").grid(row=1, column=0, sticky="w")
        self.task_entry = ttk.Entry(tab)
        self.task_entry.grid(row=1, column=1, sticky="ew")

        ttk.Label(tab, text="Hours Worked:").grid(row=2, column=0, sticky="w")
        self.hours_entry = ttk.Entry(tab)
        self.hours_entry.grid(row=2, column=1, sticky="ew")



        self.log_button = ttk.Button(tab, text="Log Work", command=self.log_work)
        self.log_button.grid(row=3, column=0, columnspan=2, pady=5)

        self.tree = ttk.Treeview(tab, columns=("Date", "Project", "Task", "Hours"), show="headings")
        for col in ("Date", "Project", "Task", "Hours"):
            self.tree.heading(col, text=col)
        self.tree.grid(row=5, column=0, columnspan=2, sticky="nsew")

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=5, column=2, sticky="ns")

        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=5)

        ttk.Button(btn_frame, text="Edit Selected", command=self.edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Manage Projects", command=self.manage_projects_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Show Statistics", command=self.show_statistics).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export Stats to PDF", command=self.export_statistics_to_pdf).pack(side=tk.LEFT, padx=5)

        # Summary
        self.summary_frame = ttk.LabelFrame(tab, text="Summary")
        self.summary_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.today_label = ttk.Label(self.summary_frame, text="Today: 0 hrs")
        self.total_label = ttk.Label(self.summary_frame, text="Total: 0 hrs")
        self.year_label = ttk.Label(self.summary_frame, text="This Year: 0 hrs")
        self.week_label = ttk.Label(self.summary_frame, text="This Week: 0 hrs")
        self.avg_label = ttk.Label(self.summary_frame, text="Avg per day: 0 hrs")
        self.today_label.grid(row=0, column=0, padx=10, pady=2)
        self.total_label.grid(row=0, column=1, padx=10, pady=2)
        self.year_label.grid(row=0, column=2, padx=10, pady=2)
        self.week_label.grid(row=0, column=3, padx=10, pady=2)
        self.avg_label.grid(row=0, column=4, padx=10, pady=2)

        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(5, weight=1)

        self.load_logs()
        self.update_summary()

    def update_summary(self):
        now = datetime.now()
        year = now.year
        week = f"{year}-W{now.strftime('%U')}"
        today = now.date()
        stats = {
            "total": 0.0,
            "per_year": {},
            "per_week": {},
            "dates": set(),
            "today": 0.0
        }

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode='r') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    try:
                        date = datetime.strptime(row[0], "%Y-%m-%d %H:%M")
                        hours = float(row[3])
                    except:
                        continue
                    stats["total"] += hours
                    stats["dates"].add(date.date())
                    if date.date() == today:
                        stats["today"] += hours
                    y = date.year
                    w = f"{date.year}-W{date.strftime('%U')}"
                    stats["per_year"][y] = stats["per_year"].get(y, 0.0) + hours
                    stats["per_week"][w] = stats["per_week"].get(w, 0.0) + hours

        avg = stats["total"] / len(stats["dates"]) if stats["dates"] else 0
        self.total_label.config(text=f"Total: {stats['total']:.1f} hrs")
        self.year_label.config(text=f"This Year: {stats['per_year'].get(year, 0.0):.1f} hrs")
        self.week_label.config(text=f"This Week: {stats['per_week'].get(week, 0.0):.1f} hrs")
        self.avg_label.config(text=f"Avg per day: {avg:.1f} hrs")
        self.today_label.config(text=f"Today: {stats['today']:.1f} hrs")

    def update_summary_(self):
        now = datetime.now()
        year = now.year
        week = f"{year}-W{now.strftime('%U')}"
        stats = {"total": 0.0, "per_year": {}, "per_week": {}, "dates": set()}

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode='r') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    try:
                        date = datetime.strptime(row[0], "%Y-%m-%d %H:%M")
                        hours = float(row[3])
                    except:
                        continue
                    stats["total"] += hours
                    stats["dates"].add(date.date())
                    y = date.year
                    w = f"{date.year}-W{date.strftime('%U')}"
                    stats["per_year"][y] = stats["per_year"].get(y, 0.0) + hours
                    stats["per_week"][w] = stats["per_week"].get(w, 0.0) + hours

        avg = stats["total"] / len(stats["dates"]) if stats["dates"] else 0
        self.total_label.config(text=f"Total: {stats['total']:.1f} hrs")
        self.year_label.config(text=f"This Year: {stats['per_year'].get(year, 0.0):.1f} hrs")
        self.week_label.config(text=f"This Week: {stats['per_week'].get(week, 0.0):.1f} hrs")
        self.avg_label.config(text=f"Avg per day: {avg:.1f} hrs")

    def build_overview_tab(self):
        tab = self.tab_overview
        self.meta_tree = ttk.Treeview(tab, columns=("Project", "Task", "Importance", "Urgency", "Deadline"), show="headings")
        for col in ("Project", "Task", "Importance", "Urgency", "Deadline"):
            self.meta_tree.heading(col, text=col)
            self.meta_tree.column(col, width=100)
        self.meta_tree.grid(row=0, column=0, columnspan=4, sticky="nsew")
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.meta_tree.yview)
        self.meta_tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=4, sticky="ns")
        self.meta_entries = {}
        for idx, label in enumerate(("Project", "Task", "Importance", "Urgency", "Deadline")):
            ttk.Label(tab, text=label).grid(row=1, column=idx)
            entry = ttk.Entry(tab)
            entry.grid(row=2, column=idx)
            self.meta_entries[label] = entry
        ttk.Button(tab, text="Add / Update Entry", command=self.add_or_update_metadata).grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Button(tab, text="Delete Selected", command=self.delete_metadata_entry).grid(row=3, column=2, columnspan=2, pady=5)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self.load_task_metadata()

    def load_logs(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        with open(LOG_FILE, mode='r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                self.tree.insert("", tk.END, values=row)

    def add_or_update_metadata(self):
        new_entry = [self.meta_entries[field].get() for field in ("Project", "Task", "Importance", "Urgency", "Deadline")]
        if not new_entry[0] or not new_entry[1]:
            messagebox.showwarning("Missing Data", "Project and Task are required.")
            return
        existing = []
        with open(METADATA_FILE, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)
            existing = [row for row in reader]
        with open(METADATA_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            updated = False
            for row in existing:
                if row[0] == new_entry[0] and row[1] == new_entry[1]:
                    writer.writerow(new_entry)
                    updated = True
                else:
                    writer.writerow(row)
            if not updated:
                writer.writerow(new_entry)
        self.load_task_metadata()
        for entry in self.meta_entries.values():
            entry.delete(0, tk.END)

    def load_task_metadata(self):
        for row in self.meta_tree.get_children():
            self.meta_tree.delete(row)
        with open(METADATA_FILE, mode='r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                self.meta_tree.insert("", tk.END, values=row)

    def delete_metadata_entry(self):
        selected = self.meta_tree.selection()
        if not selected:
            return
        selected_values = self.meta_tree.item(selected[0])["values"]
        with open(METADATA_FILE, 'r') as file:
            lines = list(csv.reader(file))
        with open(METADATA_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            for line in lines:
                if line != selected_values:
                    writer.writerow(line)
        self.load_task_metadata()

    def log_work(self):
        project = self.project_var.get()
        task = self.task_entry.get()
        hours = self.hours_entry.get()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        if not task or not hours:
            messagebox.showwarning("Input Error", "Please enter both task and hours.")
            return
        try:
            float(hours)
        except ValueError:
            messagebox.showwarning("Input Error", "Hours must be a number.")
            return
        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([date, project, task, hours])
        self.task_entry.delete(0, tk.END)
        self.hours_entry.delete(0, tk.END)
        self.load_logs()
        self.update_summary()

    def delete_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No selection", "Please select a log to delete.")
            return
        item_id = selected_item[0]
        values = self.tree.item(item_id)["values"]
        self.tree.delete(item_id)
        with open(LOG_FILE, 'r') as file:
            lines = list(csv.reader(file))
        with open(LOG_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            for line in lines:
                if [str(x) for x in line] != [str(x) for x in values]:
                    writer.writerow(line)
        self.load_logs()
        self.update_summary()

    def edit_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No selection", "Please select a log to edit.")
            return
        item_id = selected_item[0]
        old_values = self.tree.item(item_id)["values"]
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Entry")
        labels = ["Date", "Project", "Task", "Hours"]
        entries = []
        for i, label in enumerate(labels):
            ttk.Label(edit_win, text=label + ":").grid(row=i, column=0)
            entry = ttk.Entry(edit_win)
            entry.grid(row=i, column=1)
            entry.insert(0, old_values[i])
            entries.append(entry)
        def save_edit():
            new_values = [e.get() for e in entries]
            if not new_values[2] or not new_values[3]:
                messagebox.showwarning("Input Error", "Task and Hours cannot be empty.")
                return
            with open(LOG_FILE, 'r') as file:
                lines = list(csv.reader(file))
            with open(LOG_FILE, 'w', newline='') as file:
                writer = csv.writer(file)
                for line in lines:
                    if [str(x) for x in line] == [str(x) for x in old_values]:
                        writer.writerow(new_values)
                    else:
                        writer.writerow(line)
            self.load_logs()
            self.update_summary()
            edit_win.destroy()
        ttk.Button(edit_win, text="Save", command=save_edit).grid(row=4, column=0, columnspan=2)

    def manage_projects_window(self):
        win = tk.Toplevel(self.root)
        win.title("Manage Projects")
        project_listbox = tk.Listbox(win)
        project_listbox.pack(fill=tk.BOTH, expand=True)
        for p in self.projects:
            project_listbox.insert(tk.END, p)
        new_proj_entry = ttk.Entry(win)
        new_proj_entry.pack(fill=tk.X, padx=5, pady=5)
        def add_project():
            new_proj = new_proj_entry.get().strip()
            if new_proj and new_proj not in self.projects:
                self.projects.append(new_proj)
                project_listbox.insert(tk.END, new_proj)
                self.project_combo['values'] = self.projects

                # ✅ Persist the new project
                with open("projects.csv", mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([new_proj])

        def remove_selected():
            selected = project_listbox.curselection()
            if selected:
                proj = project_listbox.get(selected[0])
                if proj in ["Radar", "Writing", "Gym", "Coursework", "Other"]:
                    messagebox.showinfo("Info", "Cannot remove default project.")
                    return

                self.projects.remove(proj)
                project_listbox.delete(selected[0])
                self.project_combo['values'] = self.projects

                # ✅ Persist the updated project list
                with open("projects.csv", mode='w', newline='') as file:
                    writer = csv.writer(file)
                    for p in self.projects:
                        writer.writerow([p])



        ttk.Button(win, text="Add", command=add_project).pack(pady=2)
        ttk.Button(win, text="Remove Selected", command=remove_selected).pack(pady=2)

    def show_statistics(self):
        from datetime import datetime
        import matplotlib.dates as mdates
        project_hours_total = defaultdict(float)
        weekly_hours = defaultdict(lambda: defaultdict(float))
        cumulative_per_project = defaultdict(list)
        with open(LOG_FILE, mode='r') as file:
            reader = csv.reader(file)
            next(reader)
            entries = []
            for row in reader:
                try:
                    date = datetime.strptime(row[0], "%Y-%m-%d %H:%M")
                    project = row[1]
                    hours = float(row[3])
                    entries.append((date, project, hours))
                except:
                    continue
        if not entries:
            messagebox.showinfo("No Data", "No data available for statistics.")
            return
        entries.sort(key=lambda x: x[0])
        cumulative_totals = defaultdict(float)
        for date, project, hours in entries:
            project_hours_total[project] += hours
            week_str = date.strftime("%Y-W%U")
            weekly_hours[week_str][project] += hours
            cumulative_totals[project] += hours
            cumulative_per_project[project].append((date, cumulative_totals[project]))
        plt.figure(figsize=(8, 4))
        plt.bar(project_hours_total.keys(), project_hours_total.values())
        plt.title("Total Hours per Project")
        plt.ylabel("Hours")
        plt.tight_layout()
        weeks = sorted(weekly_hours.keys())
        all_projects = sorted(set(p for w in weekly_hours.values() for p in w))
        project_stacks = {p: [] for p in all_projects}
        for week in weeks:
            for p in all_projects:
                project_stacks[p].append(weekly_hours[week].get(p, 0))
        plt.figure(figsize=(10, 5))
        bottom = [0] * len(weeks)
        for p in all_projects:
            plt.bar(weeks, project_stacks[p], bottom=bottom, label=p)
            bottom = [sum(x) for x in zip(bottom, project_stacks[p])]
        plt.xticks(rotation=45)
        plt.title("Weekly Hours per Project (Stacked)")
        plt.xlabel("Week")
        plt.ylabel("Hours")
        plt.legend()
        plt.tight_layout()
        plt.figure(figsize=(10, 5))
        for project, values in cumulative_per_project.items():
            dates = [v[0] for v in values]
            cum_hours = [v[1] for v in values]
            plt.plot(dates, cum_hours, label=project)
        plt.title("Cumulative Work Hours Over Time")
        plt.xlabel("Date")
        plt.ylabel("Cumulative Hours")
        plt.gcf().autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.legend()
        plt.tight_layout()
        plt.show()

    def export_statistics_to_pdf(self):
        stats = defaultdict(float)
        with open(LOG_FILE, mode='r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                try:
                    stats[row[1]] += float(row[3])
                except:
                    continue
        if not stats:
            messagebox.showinfo("No Data", "No data available to export.")
            return
        filename = f"work_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(filename, pagesize=LETTER)
        width, height = LETTER
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Work Statistics Report")
        c.setFont("Helvetica", 12)
        y = height - 100
        for project, hours in sorted(stats.items()):
            c.drawString(50, y, f"{project}: {hours:.2f} hours")
            y -= 20
        c.save()
        messagebox.showinfo("Exported", f"Statistics exported to {filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WorkLoggerApp(root)
    root.mainloop()
