import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from collections import defaultdict
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import json # Added for achievements

LOG_FILE = "work_log.csv"
METADATA_FILE = "task_metadata.csv"
PROJECTS_FILE = "projects.csv"
GAMES_FILE = "games.json" # Added for achievements

# Initialize CSV files if they don't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Project", "Task", "Hours"])

# === REQUIREMENT 1: Data and Storage Changes ===
# Modify the task_metadata.csv file structure to include a new column at the end named "Status".
if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Project", "Task", "Importance", "Urgency", "Deadline", "Status"])

if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows([["Bathymetry"], ["Synchronization"], ["Alaska"], ["Estimation"], ["Other"]])

# Initialize games.json if it doesn't exist
if not os.path.exists(GAMES_FILE):
    with open(GAMES_FILE, mode='w') as file:
        json.dump({"games": []}, file, indent=4)

class WorkLoggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Work Planner with Task Overview & Achievements")

        with open(PROJECTS_FILE, mode='r') as file:
            reader = csv.reader(file)
            self.projects = [row[0] for row in reader if row]

        self.notebook = ttk.Notebook(root)
        self.tab_logger = ttk.Frame(self.notebook)
        self.tab_overview = ttk.Frame(self.notebook)
        self.tab_achievements = ttk.Frame(self.notebook) # Added Achievements Tab

        self.notebook.add(self.tab_logger, text="Work Logger")
        self.notebook.add(self.tab_overview, text="Task Overview")
        self.notebook.add(self.tab_achievements, text="Achievements") # Added Achievements Tab
        self.notebook.pack(expand=True, fill="both")

        self.build_logger_tab()
        self.build_overview_tab()
        self.build_achievements_tab() # Added call to build achievements tab
        self.load_games_data() # Load achievement data at startup

    def build_logger_tab(self):
        tab = self.tab_logger
        ttk.Label(tab, text="Project:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(tab, textvariable=self.project_var, values=self.projects, state="readonly")
        self.project_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        if self.projects:
            self.project_combo.current(0)

        ttk.Label(tab, text="Task Description:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.task_entry = ttk.Entry(tab)
        self.task_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(tab, text="Hours Worked:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.hours_entry = ttk.Entry(tab)
        self.hours_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        self.log_button = ttk.Button(tab, text="Log Work", command=self.log_work)
        self.log_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.tree = ttk.Treeview(tab, columns=("Date", "Project", "Task", "Hours"), show="headings")
        for col in ("Date", "Project", "Task", "Hours"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=4, column=2, sticky="ns")

        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=5)

        ttk.Button(btn_frame, text="Edit Selected", command=self.edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Manage Projects", command=self.manage_projects_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Show Statistics", command=self.show_statistics).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export Stats to PDF", command=self.export_statistics_to_pdf).pack(side=tk.LEFT, padx=5)

        self.summary_frame = ttk.LabelFrame(tab, text="Summary")
        self.summary_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.today_label = ttk.Label(self.summary_frame, text="Today: 0 hrs")
        self.total_label = ttk.Label(self.summary_frame, text="Total: 0 hrs")
        self.year_label = ttk.Label(self.summary_frame, text="This Year: 0 hrs")
        self.week_label = ttk.Label(self.summary_frame, text="This Week: 0 hrs")
        self.avg_label = ttk.Label(self.summary_frame, text="Avg per day: 0 hrs")
        self.today_label.grid(row=0, column=0, padx=10, pady=2, sticky="w")
        self.total_label.grid(row=0, column=1, padx=10, pady=2, sticky="w")
        self.year_label.grid(row=0, column=2, padx=10, pady=2, sticky="w")
        self.week_label.grid(row=0, column=3, padx=10, pady=2, sticky="w")
        self.avg_label.grid(row=0, column=4, padx=10, pady=2, sticky="w")

        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(4, weight=1)

        self.load_logs()
        self.update_summary()

    def update_summary(self):
        now = datetime.now()
        year = now.year
        week_number = now.isocalendar()[1]
        week = f"{year}-W{week_number:02d}"
        today_date = now.date()
        stats = {
            "total": 0.0,
            "per_year": defaultdict(float),
            "per_week": defaultdict(float),
            "dates": set(),
            "today": 0.0
        }

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode='r', newline='') as file:
                reader = csv.reader(file)
                try:
                    next(reader)
                except StopIteration:
                    pass
                for row in reader:
                    try:
                        date_obj = datetime.strptime(row[0], "%Y-%m-%d %H:%M")
                        hours = float(row[3])
                    except (ValueError, IndexError):
                        continue

                    stats["total"] += hours
                    stats["dates"].add(date_obj.date())

                    if date_obj.date() == today_date:
                        stats["today"] += hours

                    y = date_obj.year
                    wn = date_obj.isocalendar()[1]
                    w = f"{y}-W{wn:02d}"

                    stats["per_year"][y] += hours
                    stats["per_week"][w] += hours

        avg = stats["total"] / len(stats["dates"]) if stats["dates"] else 0
        self.total_label.config(text=f"Total: {stats['total']:.1f} hrs")
        self.year_label.config(text=f"This Year: {stats['per_year'].get(year, 0.0):.1f} hrs")
        self.week_label.config(text=f"This Week: {stats['per_week'].get(week, 0.0):.1f} hrs")
        self.avg_label.config(text=f"Avg per day: {avg:.1f} hrs")
        self.today_label.config(text=f"Today: {stats['today']:.1f} hrs")

    # === REQUIREMENT 2: UI Enhancements in build_overview_tab ===
    def build_overview_tab(self):
        tab = self.tab_overview

        # --- Treeview for Task Metadata ---
        # Modify Treeview to display new columns in the specified order.
        cols = ("Priority", "Project", "Task", "Status", "Importance", "Urgency", "Deadline")
        self.meta_tree = ttk.Treeview(tab, columns=cols, show="headings")

        for col in cols:
            # Add command for clickable column sorting.
            self.meta_tree.heading(col, text=col, command=lambda _col=col: self.sort_overview_column(_col, False))
            self.meta_tree.column(col, width=100, anchor="w")

        # Adjust column widths for better readability.
        self.meta_tree.column("Priority", width=60, anchor="center")
        self.meta_tree.column("Task", width=250, anchor="w")
        self.meta_tree.column("Status", width=80, anchor="center")

        self.meta_tree.grid(row=0, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.meta_tree.yview)
        self.meta_tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=5, sticky="ns")

        # Add a tag to visually distinguish completed tasks.
        self.meta_tree.tag_configure('done', foreground='gray')

        # --- Input Frame for Adding/Updating Tasks ---
        input_frame = ttk.Frame(tab)
        input_frame.grid(row=1, column=0, columnspan=5, sticky="ew", padx=5, pady=5)

        self.meta_entries = {}
        rating_values = ["1", "2", "3", "4", "5"]
        labels = ("Project", "Task", "Importance", "Urgency", "Deadline")

        for idx, label_text in enumerate(labels):
            ttk.Label(input_frame, text=label_text + ":").grid(row=0, column=idx, sticky="w", padx=5, pady=2)
            # Replace Entry widgets with Comboboxes for specific fields.
            if label_text == "Project":
                entry = ttk.Combobox(input_frame, values=self.projects, width=15)
            elif label_text in ["Importance", "Urgency"]:
                entry = ttk.Combobox(input_frame, values=rating_values, width=15)
            else:  # Task, Deadline
                entry = ttk.Entry(input_frame, width=15)

            entry.grid(row=1, column=idx, sticky="ew", padx=5, pady=2)
            self.meta_entries[label_text] = entry
            input_frame.grid_columnconfigure(idx, weight=1)

        # --- Button and Options Frame ---
        button_frame = ttk.Frame(tab)
        button_frame.grid(row=2, column=0, columnspan=5, pady=10)

        # Add a Checkbutton to hide completed tasks.
        self.hide_completed_var = tk.BooleanVar(value=False)

        # Rename button and add new controls.
        ttk.Button(button_frame, text="Save Task", command=self.add_or_update_metadata).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_metadata_entry).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Toggle Status", command=self.toggle_task_status).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(button_frame, text="Hide Completed Tasks", variable=self.hide_completed_var, command=self.load_task_metadata).pack(side=tk.LEFT, padx=10)

        # Configure grid weights for responsive resizing.
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.load_task_metadata()

    # === REQUIREMENT 3: Functional Logic Implementation ===
    # --- Clickable Column Sorting ---
    def sort_overview_column(self, col, reverse):
        """Sorts the overview treeview by a column and updates the header command."""
        self.load_task_metadata(sort_col=col, reverse=reverse)
        # Update the column header's command to sort in the opposite direction on the next click.
        self.meta_tree.heading(col, text=col, command=lambda _col=col: self.sort_overview_column(_col, not reverse))

    # --- Task Status Management ---
    def toggle_task_status(self):
        """Toggles the status of the selected task between 'To-Do' and 'Done'."""
        selected_items = self.meta_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a task to toggle its status.")
            return

        selected_item = self.meta_tree.item(selected_items[0])
        # Retrieve task identifiers from the selected Treeview row.
        # Treeview columns: Priority, Project, Task, ...
        project_name = selected_item['values'][1]
        task_name = selected_item['values'][2]

        all_rows = []
        header = []
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', newline='') as file:
                reader = csv.reader(file)
                try:
                    header = next(reader)
                    all_rows.append(header)
                    # CSV columns: Project, Task, Importance, Urgency, Deadline, Status
                    for row in reader:
                        if len(row) < 6: continue
                        if row[0] == project_name and row[1] == task_name:
                            current_status = row[5]
                            new_status = "Done" if current_status in ["To-Do", ""] else "To-Do"
                            row[5] = new_status
                        all_rows.append(row)
                except StopIteration:
                    pass

        # Rewrite the CSV file with the updated status.
        with open(METADATA_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(all_rows)

        self.load_task_metadata()

    # --- Priority Calculation & Data Loading ---
    def load_task_metadata(self, sort_col="Priority", reverse=True):
        """Loads task data, calculates priority, filters, sorts, and displays it."""
        for row in self.meta_tree.get_children():
            self.meta_tree.delete(row)

        if not os.path.exists(METADATA_FILE): return

        all_tasks = []
        with open(METADATA_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            try:
                header = next(reader)
                col_map = {name: idx for idx, name in enumerate(header)}
                if "Status" not in col_map: # Handle old file format gracefully
                    col_map["Status"] = -1
                
                for row in reader:
                    if len(row) < 5: continue

                    # Filter based on the "Hide Completed Tasks" checkbox.
                    status = row[col_map["Status"]] if col_map["Status"] != -1 and len(row) > col_map["Status"] else "To-Do"
                    if self.hide_completed_var.get() and status == "Done":
                        continue

                    # Calculate Priority score. Default to 0 if values are invalid.
                    try:
                        importance = int(row[col_map["Importance"]])
                        urgency = int(row[col_map["Urgency"]])
                        priority = importance * urgency
                    except (ValueError, IndexError):
                        priority = 0

                    task_data = {
                        "Priority": priority,
                        "Project": row[col_map["Project"]],
                        "Task": row[col_map["Task"]],
                        "Status": status,
                        "Importance": row[col_map["Importance"]],
                        "Urgency": row[col_map["Urgency"]],
                        "Deadline": row[col_map["Deadline"]]
                    }
                    all_tasks.append(task_data)
            except (StopIteration, ValueError):
                return

        # Sort the data based on the selected column and direction.
        if sort_col == "Priority":
            all_tasks.sort(key=lambda x: x.get(sort_col, 0), reverse=reverse)
        else:
            all_tasks.sort(key=lambda x: str(x.get(sort_col, "")).lower(), reverse=reverse)

        # Insert sorted data into the Treeview.
        for task in all_tasks:
            values = (
                task["Priority"], task["Project"], task["Task"], task["Status"],
                task["Importance"], task["Urgency"], task["Deadline"]
            )
            # Use the 'done' tag for a visual indicator on completed tasks.
            tag = 'done' if task["Status"] == "Done" else ''
            self.meta_tree.insert("", tk.END, values=values, tags=(tag,))
    
    # --- Saving and Updating Data ---
    def add_or_update_metadata(self):
        """Saves a new task or updates an existing one, preserving its status."""
        project = self.meta_entries["Project"].get()
        task = self.meta_entries["Task"].get()
        importance = self.meta_entries["Importance"].get()
        urgency = self.meta_entries["Urgency"].get()
        deadline = self.meta_entries["Deadline"].get()

        if not project or not task:
            messagebox.showwarning("Missing Data", "Project and Task fields are required.")
            return
        
        # New task data without status.
        new_entry_values_base = [project, task, importance, urgency, deadline]

        all_rows = []
        updated = False
        original_status = "To-Do"  # Default status for new tasks.

        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', newline='') as file:
                reader = csv.reader(file)
                try:
                    headers = next(reader)
                    all_rows.append(headers)
                    if "Status" not in headers: headers.append("Status")
                    
                    for row in reader:
                        # Ensure row is long enough before accessing indices
                        if len(row) >= 2 and row[0] == project and row[1] == task:
                            # Preserve the original status when updating.
                            original_status = row[5] if len(row) > 5 else "To-Do"
                            updated = True
                            # The updated row will be added later, so we skip the old one.
                        else:
                            all_rows.append(row)
                except StopIteration:
                    if not all_rows:
                        all_rows.append(["Project", "Task", "Importance", "Urgency", "Deadline", "Status"])
        else:
            all_rows.append(["Project", "Task", "Importance", "Urgency", "Deadline", "Status"])

        # Append the new or updated row with the correct status.
        final_entry = new_entry_values_base + [original_status]
        all_rows.append(final_entry)

        with open(METADATA_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(all_rows)

        self.load_task_metadata()
        for entry_widget in self.meta_entries.values():
            entry_widget.delete(0, tk.END)

    def delete_metadata_entry(self):
        """Deletes a selected task from the metadata file."""
        selected_items = self.meta_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a metadata entry to delete.")
            return
            
        selected_item = self.meta_tree.item(selected_items[0])
        # Identify the row to delete by its Project and Task name.
        project_to_delete = selected_item['values'][1]
        task_to_delete = selected_item['values'][2]

        rows_to_keep = []
        header = []
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', newline='') as file:
                reader = csv.reader(file)
                try:
                    header = next(reader)
                    for row in reader:
                        if len(row) >= 2:
                            if not (row[0] == project_to_delete and row[1] == task_to_delete):
                                rows_to_keep.append(row)
                except StopIteration:
                    pass

        with open(METADATA_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            if header:
                writer.writerow(header)
            writer.writerows(rows_to_keep)
        self.load_task_metadata()

    def load_logs(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if not os.path.exists(LOG_FILE): return
        with open(LOG_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            try:
                next(reader) 
                for row in reader:
                    if len(row) == 4:
                        self.tree.insert("", tk.END, values=row)
            except StopIteration:
                pass

    def log_work(self):
        project = self.project_var.get()
        task = self.task_entry.get()
        hours_str = self.hours_entry.get()
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        if not project:
            messagebox.showwarning("Input Error", "Please select a project.")
            return
        if not task or not hours_str:
            messagebox.showwarning("Input Error", "Please enter both task description and hours.")
            return
        try:
            hours = float(hours_str)
            if hours <= 0:
                messagebox.showwarning("Input Error", "Hours must be a positive number.")
                return
        except ValueError:
            messagebox.showwarning("Input Error", "Hours must be a valid number.")
            return

        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([date_str, project, task, f"{hours:.2f}"])

        self.task_entry.delete(0, tk.END)
        self.hours_entry.delete(0, tk.END)
        self.load_logs()
        self.update_summary()
        self.check_achievements_on_log(project, date_str)
        messagebox.showinfo("Logged", f"Work logged for {project}.")


    def delete_selected(self):
        selected_item_ids = self.tree.selection()
        if not selected_item_ids:
            messagebox.showwarning("No selection", "Please select a log entry to delete.")
            return

        selected_values_to_delete = [self.tree.item(item_id)["values"] for item_id in selected_item_ids]

        all_rows = []
        header = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', newline='') as file:
                reader = csv.reader(file)
                try:
                    header = next(reader)
                    for row in reader:
                        is_selected_for_deletion = False
                        for sel_val_list in selected_values_to_delete:
                            if [str(x) for x in row] == [str(x) for x in sel_val_list]:
                                is_selected_for_deletion = True
                                break
                        if not is_selected_for_deletion:
                            all_rows.append(row)
                except StopIteration:
                    pass

        with open(LOG_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            if header:
                writer.writerow(header)
            writer.writerows(all_rows)

        self.load_logs()
        self.update_summary()

    def edit_selected(self):
        selected_item_id = self.tree.selection()
        if not selected_item_id:
            messagebox.showwarning("No selection", "Please select a log entry to edit.")
            return
        item_id = selected_item_id[0]
        old_values = self.tree.item(item_id)["values"]

        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Log Entry")
        edit_win.transient(self.root)
        edit_win.grab_set()

        labels = ["Date (YYYY-MM-DD HH:MM)", "Project", "Task", "Hours"]
        entries_vars = []

        for i, label_text in enumerate(labels):
            ttk.Label(edit_win, text=label_text + ":").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            var = tk.StringVar(edit_win, value=old_values[i])
            entry = ttk.Entry(edit_win, textvariable=var, width=30)
            if label_text == "Project":
                entry = ttk.Combobox(edit_win, textvariable=var, values=self.projects, state="readonly", width=28)
                if old_values[i] in self.projects:
                    var.set(old_values[i])
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            entries_vars.append(var)

        edit_win.columnconfigure(1, weight=1)

        def save_edit():
            new_values = [var.get() for var in entries_vars]

            try:
                datetime.strptime(new_values[0], "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Input Error", "Invalid date format. Please use YYYY-MM-DD HH:MM.", parent=edit_win)
                return

            if not new_values[1]:
                 messagebox.showerror("Input Error", "Project cannot be empty.", parent=edit_win)
                 return

            if not new_values[2] or not new_values[3]:
                messagebox.showerror("Input Error", "Task and Hours cannot be empty.", parent=edit_win)
                return
            try:
                hours = float(new_values[3])
                if hours <= 0:
                    messagebox.showerror("Input Error", "Hours must be a positive number.", parent=edit_win)
                    return
                new_values[3] = f"{hours:.2f}"
            except ValueError:
                messagebox.showerror("Input Error", "Hours must be a valid number.", parent=edit_win)
                return

            all_rows = []
            header = []
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', newline='') as file:
                    reader = csv.reader(file)
                    try:
                        header = next(reader)
                        for line_values in reader:
                            if [str(x) for x in line_values] == [str(x) for x in old_values]:
                                all_rows.append(new_values)
                            else:
                                all_rows.append(line_values)
                    except StopIteration:
                        pass
            else:
                messagebox.showerror("Error", "Log file not found.", parent=edit_win)
                return


            with open(LOG_FILE, 'w', newline='') as file:
                writer = csv.writer(file)
                if header:
                    writer.writerow(header)
                writer.writerows(all_rows)

            self.load_logs()
            self.update_summary()
            edit_win.destroy()
            messagebox.showinfo("Success", "Log entry updated successfully.")

        save_button = ttk.Button(edit_win, text="Save", command=save_edit)
        save_button.grid(row=len(labels), column=0, columnspan=2, pady=10)
        cancel_button = ttk.Button(edit_win, text="Cancel", command=edit_win.destroy)
        cancel_button.grid(row=len(labels), column=1, sticky='e', padx=5, pady=10)


    def manage_projects_window(self):
        win = tk.Toplevel(self.root)
        win.title("Manage Projects")
        win.transient(self.root)
        win.grab_set()
        win.geometry("300x300")

        list_frame = ttk.Frame(win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        project_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        project_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=project_listbox.yview)
        project_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for p in self.projects:
            project_listbox.insert(tk.END, p)

        entry_frame = ttk.Frame(win)
        entry_frame.pack(fill=tk.X, padx=5, pady=5)
        new_proj_entry = ttk.Entry(entry_frame)
        new_proj_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))

        def add_project_action():
            new_proj = new_proj_entry.get().strip()
            if new_proj and new_proj not in self.projects:
                self.projects.append(new_proj)
                self.projects.sort()
                project_listbox.insert(tk.END, new_proj)

                current_list = list(project_listbox.get(0, tk.END))
                current_list.sort()
                project_listbox.delete(0, tk.END)
                for item in current_list:
                    project_listbox.insert(tk.END, item)

                self.project_combo['values'] = self.projects
                if self.projects:
                    try:
                        self.project_combo.current(self.projects.index(self.project_var.get()))
                    except ValueError:
                         self.project_combo.current(0)


                with open(PROJECTS_FILE, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    for p_item in self.projects:
                        writer.writerow([p_item])
                new_proj_entry.delete(0, tk.END)
            elif not new_proj:
                messagebox.showwarning("Input Error", "Project name cannot be empty.", parent=win)
            else:
                messagebox.showwarning("Duplicate", "Project already exists.", parent=win)


        ttk.Button(entry_frame, text="Add", command=add_project_action).pack(side=tk.LEFT)

        def remove_selected_action():
            selected_indices = project_listbox.curselection()
            if selected_indices:
                proj_to_remove = project_listbox.get(selected_indices[0])

                if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove project '{proj_to_remove}'?", parent=win):
                    self.projects.remove(proj_to_remove)
                    project_listbox.delete(selected_indices[0])
                    self.project_combo['values'] = self.projects
                    if self.projects:
                         self.project_combo.current(0)
                    else:
                        self.project_combo.set('')

                    with open(PROJECTS_FILE, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        for p_item in self.projects:
                            writer.writerow([p_item])
            else:
                messagebox.showwarning("No Selection", "Please select a project to remove.", parent=win)

        ttk.Button(win, text="Remove Selected", command=remove_selected_action).pack(pady=5)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=5)


    def show_statistics(self):
        import matplotlib.dates as mdates

        project_hours_total = defaultdict(float)
        weekly_hours = defaultdict(lambda: defaultdict(float))
        cumulative_per_project = defaultdict(list)
        all_entries = []

        if not os.path.exists(LOG_FILE):
            messagebox.showinfo("No Data", "Log file is empty or does not exist.")
            return

        with open(LOG_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            try:
                next(reader)
                for row in reader:
                    if len(row) < 4: continue
                    try:
                        date_obj = datetime.strptime(row[0], "%Y-%m-%d %H:%M")
                        project = row[1]
                        hours = float(row[3])
                        all_entries.append((date_obj, project, hours))
                    except ValueError:
                        continue
            except StopIteration:
                messagebox.showinfo("No Data", "No data logged yet.")
                return

        if not all_entries:
            messagebox.showinfo("No Data", "No valid data found in logs for statistics.")
            return

        all_entries.sort(key=lambda x: x[0])

        current_cumulative_totals = defaultdict(float)
        for date_obj, project, hours in all_entries:
            project_hours_total[project] += hours

            year, week_num, _ = date_obj.isocalendar()
            week_str = f"{year}-W{week_num:02d}"
            weekly_hours[week_str][project] += hours

            current_cumulative_totals[project] += hours
            cumulative_per_project[project].append((date_obj, current_cumulative_totals[project]))

        if project_hours_total:
            plt.figure(figsize=(10, 6))
            projects_sorted_names = sorted(project_hours_total.keys())
            total_hrs_sorted = [project_hours_total[name] for name in projects_sorted_names]

            plt.bar(projects_sorted_names, total_hrs_sorted, color='skyblue')
            plt.title("Total Hours per Project")
            plt.xlabel("Project")
            plt.ylabel("Total Hours")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
        else:
            print("No data for total hours per project plot.")

        if weekly_hours:
            plt.figure(figsize=(12, 7))
            sorted_weeks = sorted(weekly_hours.keys())
            all_projects_in_log = sorted(list(set(proj for week_data in weekly_hours.values() for proj in week_data)))

            bottom_values = [0] * len(sorted_weeks)

            for project_name in all_projects_in_log:
                project_weekly_hours = [weekly_hours[week].get(project_name, 0) for week in sorted_weeks]
                plt.bar(sorted_weeks, project_weekly_hours, bottom=bottom_values, label=project_name)
                bottom_values = [b + h for b, h in zip(bottom_values, project_weekly_hours)]

            plt.title("Weekly Hours per Project (Stacked)")
            plt.xlabel("Week (YYYY-Www)")
            plt.ylabel("Hours")
            plt.xticks(rotation=70, ha="right")
            plt.legend(title="Projects", bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.subplots_adjust(right=0.85)
        else:
            print("No data for weekly hours plot.")

        if cumulative_per_project:
            plt.figure(figsize=(12, 7))
            projects_cumulative_sorted_names = sorted(cumulative_per_project.keys())
            for project_name in projects_cumulative_sorted_names:
                data_points = cumulative_per_project[project_name]
                if data_points:
                    dates = [dp[0] for dp in data_points]
                    cum_hours = [dp[1] for dp in data_points]
                    plt.plot(dates, cum_hours, marker='o', linestyle='-', label=project_name)

            plt.title("Cumulative Work Hours Over Time by Project")
            plt.xlabel("Date")
            plt.ylabel("Cumulative Hours")
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gcf().autofmt_xdate(rotation=45)
            plt.legend(title="Projects")
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
        else:
            print("No data for cumulative hours plot.")

        if not project_hours_total and not weekly_hours and not cumulative_per_project:
            messagebox.showinfo("No Data", "Not enough data to generate any statistics plots.")
            return

        plt.show()


    def export_statistics_to_pdf(self):
        stats = defaultdict(float)
        if not os.path.exists(LOG_FILE):
            messagebox.showinfo("No Data", "Log file is empty or does not exist.")
            return

        with open(LOG_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            try:
                next(reader)
                for row in reader:
                    if len(row) < 4: continue
                    try:
                        project = row[1]
                        hours = float(row[3])
                        stats[project] += hours
                    except ValueError:
                        continue
            except StopIteration:
                messagebox.showinfo("No Data", "No data logged yet to export.")
                return

        if not stats:
            messagebox.showinfo("No Data", "No valid data found in logs to export.")
            return

        filename = f"work_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(filename, pagesize=LETTER)
        width, height = LETTER

        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2.0, height - 50, "Work Statistics Report")

        c.setFont("Helvetica", 10)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.drawString(50, height - 75, f"Report Generated: {current_time}")

        y_position = height - 120
        line_height = 20

        c.setFont("Helvetica-Bold", 12)
        c.drawString(60, y_position, "Project")
        c.drawString(300, y_position, "Total Hours")
        y_position -= (line_height * 0.5)
        c.line(50, y_position, width - 50, y_position)
        y_position -= (line_height * 0.75)


        c.setFont("Helvetica", 11)
        total_overall_hours = 0
        for project, hours in sorted(stats.items()):
            if y_position < 60:
                c.showPage()
                c.setFont("Helvetica-Bold", 12)
                c.drawString(60, height - 50, "Project (Continued)")
                c.drawString(300, height-50, "Total Hours (Continued)")
                y_position = height - 80
                c.setFont("Helvetica", 11)


            c.drawString(60, y_position, project)
            c.drawString(300, y_position, f"{hours:.2f} hours")
            total_overall_hours += hours
            y_position -= line_height

        y_position -= (line_height * 0.5)
        c.line(50, y_position, width - 50, y_position)
        y_position -= (line_height * 0.75)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(60, y_position, "Overall Total")
        c.drawString(300, y_position, f"{total_overall_hours:.2f} hours")

        c.save()
        messagebox.showinfo("Export Successful", f"Statistics report exported to {filename}")

    # --- Achievement System Methods ---
    def load_games_data(self):
        try:
            with open(GAMES_FILE, 'r') as f:
                self.games_data = json.load(f)
                if "games" not in self.games_data:
                    self.games_data["games"] = []
        except (FileNotFoundError, json.JSONDecodeError):
            self.games_data = {"games": []}
            self.save_games_data()

    def save_games_data(self):
        with open(GAMES_FILE, 'w') as f:
            json.dump(self.games_data, f, indent=4)

    def build_achievements_tab(self):
        tab = self.tab_achievements
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=3)
        tab.rowconfigure(1, weight=1)

        game_frame = ttk.LabelFrame(tab, text="Games")
        game_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nswe")
        game_frame.columnconfigure(0, weight=1)

        ttk.Label(game_frame, text="Select Game:").pack(pady=(5,2), anchor="w", padx=5)
        self.game_var = tk.StringVar()
        self.game_combo = ttk.Combobox(game_frame, textvariable=self.game_var, state="readonly", postcommand=self.update_game_combo_values)
        self.game_combo.pack(fill="x", pady=(0,5), padx=5)
        self.game_combo.bind("<<ComboboxSelected>>", self.on_game_selected)

        game_btn_frame = ttk.Frame(game_frame)
        game_btn_frame.pack(fill="x", pady=5, padx=5)
        ttk.Button(game_btn_frame, text="Add Game", command=self.add_game).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(game_btn_frame, text="Edit Game", command=self.edit_game).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(game_btn_frame, text="Delete Game", command=self.delete_game).pack(side="left", expand=True, fill="x", padx=2)

        self.game_summary_frame = ttk.LabelFrame(game_frame, text="Summary")
        self.game_summary_frame.pack(fill="x", pady=(10,5), padx=5, anchor="n")
        
        self.summary_total_ach_label = ttk.Label(self.game_summary_frame, text="Total: 0")
        self.summary_total_ach_label.pack(anchor="w", padx=5, pady=1)
        self.summary_unlocked_ach_label = ttk.Label(self.game_summary_frame, text="Unlocked: 0")
        self.summary_unlocked_ach_label.pack(anchor="w", padx=5, pady=1)
        self.summary_locked_ach_label = ttk.Label(self.game_summary_frame, text="Locked: 0")
        self.summary_locked_ach_label.pack(anchor="w", padx=5, pady=1)

        ach_frame = ttk.LabelFrame(tab, text="Achievements")
        ach_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nswe")
        ach_frame.columnconfigure(0, weight=1)
        ach_frame.rowconfigure(0, weight=1)


        self.achievements_tree = ttk.Treeview(ach_frame, columns=("Name", "Description", "Type", "Target", "Linked Project", "Unlocked"), show="headings")
        self.achievements_tree.heading("Name", text="Name")
        self.achievements_tree.heading("Description", text="Description")
        self.achievements_tree.heading("Type", text="Type")
        self.achievements_tree.heading("Target", text="Target")
        self.achievements_tree.heading("Linked Project", text="Project")
        self.achievements_tree.heading("Unlocked", text="Unlocked")

        self.achievements_tree.column("Name", width=120, anchor="w")
        self.achievements_tree.column("Description", width=200, anchor="w")
        self.achievements_tree.column("Type", width=70, anchor="center")
        self.achievements_tree.column("Target", width=70, anchor="center")
        self.achievements_tree.column("Linked Project", width=120, anchor="w")
        self.achievements_tree.column("Unlocked", width=70, anchor="center")

        self.achievements_tree.grid(row=0, column=0, columnspan=3, sticky="nswe", pady=(0,5))

        ach_scrollbar = ttk.Scrollbar(ach_frame, orient="vertical", command=self.achievements_tree.yview)
        self.achievements_tree.configure(yscroll=ach_scrollbar.set)
        ach_scrollbar.grid(row=0, column=3, sticky="ns")


        ach_btn_frame = ttk.Frame(ach_frame)
        ach_btn_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        ttk.Button(ach_btn_frame, text="Add Achievement", command=self.add_achievement).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(ach_btn_frame, text="Edit Achievement", command=self.edit_achievement).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(ach_btn_frame, text="Delete Achievement", command=self.delete_achievement).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(ach_btn_frame, text="Toggle Unlock", command=self.toggle_manual_unlock_achievement).pack(side="left", expand=True, fill="x", padx=2)

        self.update_game_summary_display(0, 0, 0)


    def update_game_combo_values(self):
        game_names = [game["name"] for game in self.games_data.get("games", [])]
        current_selection = self.game_var.get()
        self.game_combo['values'] = game_names
        if game_names:
            if current_selection in game_names:
                self.game_var.set(current_selection)
            else:
                self.game_var.set(game_names[0])
            self.on_game_selected()
        else:
            self.game_var.set("")
            self.on_game_selected()


    def on_game_selected(self, event=None):
        for item in self.achievements_tree.get_children():
            self.achievements_tree.delete(item)

        selected_game_name = self.game_var.get()
        total_ach = 0
        unlocked_ach = 0
        locked_ach = 0

        if not selected_game_name:
            self.update_game_summary_display(0,0,0)
            return

        game_data = next((game for game in self.games_data.get("games", []) if game["name"] == selected_game_name), None)

        if game_data:
            achievements_list = game_data.get("achievements", [])
            total_ach = len(achievements_list)
            for ach in achievements_list:
                unlocked_status_bool = ach.get("unlocked", False)
                unlocked_status_str = "Yes" if unlocked_status_bool else "No"
                if unlocked_status_bool:
                    unlocked_ach += 1
                else:
                    locked_ach += 1
                
                target_display = ach.get("target", "") if ach.get("target") is not None else ""
                self.achievements_tree.insert("", tk.END, values=(
                    ach.get("name", ""),
                    ach.get("description", ""),
                    ach.get("type", ""),
                    target_display,
                    ach.get("linked_to", ""),
                    unlocked_status_str
                ))
        
        self.update_game_summary_display(total_ach, unlocked_ach, locked_ach)

    def update_game_summary_display(self, total, unlocked, locked):
        self.summary_total_ach_label.config(text=f"Total: {total}")
        self.summary_unlocked_ach_label.config(text=f"Unlocked: {unlocked} ({((unlocked/total*100) if total > 0 else 0):.1f}%)")
        self.summary_locked_ach_label.config(text=f"Locked: {locked} ({((locked/total*100) if total > 0 else 0):.1f}%)")


    def add_game(self):
        game_name = simpledialog.askstring("Add Game", "Enter the name for the new game:", parent=self.root)
        if game_name:
            game_name = game_name.strip()
            if not game_name:
                messagebox.showwarning("Invalid Name", "Game name cannot be empty.", parent=self.root)
                return
            if any(g["name"] == game_name for g in self.games_data.get("games",[])):
                messagebox.showwarning("Duplicate", f"A game named '{game_name}' already exists.", parent=self.root)
                return
            self.games_data.setdefault("games", []).append({"name": game_name, "achievements": []})
            self.save_games_data()
            self.update_game_combo_values()
            messagebox.showinfo("Success", f"Game '{game_name}' added.", parent=self.root)


    def edit_game(self):
        selected_game_name = self.game_var.get()
        if not selected_game_name:
            messagebox.showwarning("No Selection", "Please select a game to edit.", parent=self.root)
            return

        new_game_name = simpledialog.askstring("Edit Game", "Enter the new name for the game:",
                                               initialvalue=selected_game_name, parent=self.root)
        if new_game_name:
            new_game_name = new_game_name.strip()
            if not new_game_name:
                messagebox.showwarning("Invalid Name", "Game name cannot be empty.", parent=self.root)
                return
            if new_game_name != selected_game_name and any(g["name"] == new_game_name for g in self.games_data.get("games",[])):
                messagebox.showwarning("Duplicate", f"A game named '{new_game_name}' already exists.", parent=self.root)
                return

            for game in self.games_data.get("games", []):
                if game["name"] == selected_game_name:
                    game["name"] = new_game_name
                    break
            self.save_games_data()
            self.update_game_combo_values()
            messagebox.showinfo("Success", f"Game '{selected_game_name}' updated to '{new_game_name}'.", parent=self.root)


    def delete_game(self):
        selected_game_name = self.game_var.get()
        if not selected_game_name:
            messagebox.showwarning("No Selection", "Please select a game to delete.", parent=self.root)
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the game '{selected_game_name}' and all its achievements?", parent=self.root):
            self.games_data["games"] = [g for g in self.games_data.get("games", []) if g["name"] != selected_game_name]
            self.save_games_data()
            self.update_game_combo_values()
            messagebox.showinfo("Deleted", f"Game '{selected_game_name}' deleted.", parent=self.root)


    def add_achievement(self):
        selected_game_name = self.game_var.get()
        if not selected_game_name:
            messagebox.showwarning("No Game Selected", "Please select or add a game first.", parent=self.root)
            return
        self._open_achievement_dialog(game_name=selected_game_name)

    def edit_achievement(self):
        selected_game_name = self.game_var.get()
        selected_items = self.achievements_tree.selection()
        if not selected_game_name:
            messagebox.showwarning("No Game Selected", "Please select a game.", parent=self.root)
            return
        if not selected_items:
            messagebox.showwarning("No Achievement Selected", "Please select an achievement to edit.", parent=self.root)
            return

        item_values = self.achievements_tree.item(selected_items[0])["values"]
        ach_name = item_values[0]

        game_obj = next((g for g in self.games_data.get("games", []) if g["name"] == selected_game_name), None)
        if game_obj:
            for i, ach_data in enumerate(game_obj.get("achievements", [])):
                if ach_data.get("name") == ach_name:
                    self._open_achievement_dialog(game_name=selected_game_name, achievement_index=i, initial_data=ach_data)
                    return
        messagebox.showerror("Error", "Could not find the selected achievement for editing.", parent=self.root)


    def _open_achievement_dialog(self, game_name, achievement_index=None, initial_data=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Achievement" if initial_data else "Add Achievement")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        fields_setup = [
            {"label": "Name", "key": "name", "widget": "entry"},
            {"label": "Description", "key": "description", "widget": "entry"},
            {"label": "Type", "key": "type", "widget": "combobox", "values": ["counter", "streak", "manual"]},
            {"label": "Target", "key": "target", "widget": "entry"},
            {"label": "Linked Project", "key": "linked_to", "widget": "combobox", "values": ["None"] + self.projects}
        ]
        entries_vars = {}


        for i, field_info in enumerate(fields_setup):
            ttk.Label(dialog, text=field_info["label"] + ":").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            var = tk.StringVar(dialog)
            widget_type = field_info["widget"]

            if widget_type == "combobox":
                entry_widget = ttk.Combobox(dialog, textvariable=var, values=field_info["values"], state="readonly", width=38)
                if initial_data and initial_data.get(field_info["key"]) in field_info["values"]:
                    var.set(initial_data.get(field_info["key"]))
                elif field_info["values"]:
                     var.set(field_info["values"][0])
            else:
                entry_widget = ttk.Entry(dialog, textvariable=var, width=40)
                if initial_data:
                    initial_val = initial_data.get(field_info["key"], "")
                    var.set(str(initial_val) if initial_val is not None else "")


            entry_widget.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            entries_vars[field_info["key"]] = var


        def on_save():
            ach_data = {key: var.get().strip() for key, var in entries_vars.items()}
            
            if not ach_data["name"]:
                messagebox.showerror("Input Error", "Achievement name cannot be empty.", parent=dialog)
                return

            ach_type = ach_data.get("type")
            target_str = ach_data.get("target", "")

            if ach_type in ["counter", "streak"]:
                if not target_str:
                    messagebox.showerror("Input Error", f"Target is required and must be a positive integer for '{ach_type}' achievements.", parent=dialog)
                    return
                try:
                    ach_data["target"] = int(target_str)
                    if ach_data["target"] <= 0 and ach_type in ["counter", "streak"]:
                         messagebox.showerror("Input Error", "Target must be a positive integer for counter/streak.", parent=dialog)
                         return
                except ValueError:
                    messagebox.showerror("Input Error", "Target must be a valid integer for counter/streak.", parent=dialog)
                    return
            else:
                ach_data["target"] = None

            if ach_data.get("linked_to") == "None":
                ach_data["linked_to"] = None
            
            current_game_obj = next((g for g in self.games_data.get("games", []) if g["name"] == game_name), None)
            if not current_game_obj:
                messagebox.showerror("Error", "Game not found. Cannot save achievement.", parent=dialog)
                return

            is_editing = achievement_index is not None
            original_name_if_editing = current_game_obj["achievements"][achievement_index]["name"] if is_editing else None

            if ach_data["name"] != original_name_if_editing:
                if any(a["name"] == ach_data["name"] for idx, a in enumerate(current_game_obj.get("achievements", [])) if idx != achievement_index):
                    messagebox.showerror("Duplicate", f"An achievement named '{ach_data['name']}' already exists in this game.", parent=dialog)
                    return

            if is_editing:
                original_unlocked_status = current_game_obj["achievements"][achievement_index].get("unlocked", False)
                ach_data["unlocked"] = original_unlocked_status
                current_game_obj["achievements"][achievement_index].update(ach_data)
            else:
                ach_data["unlocked"] = False
                current_game_obj.setdefault("achievements", []).append(ach_data)

            self.save_games_data()
            self.on_game_selected()
            dialog.destroy()
            messagebox.showinfo("Success", "Achievement saved.", parent=self.root)

        save_btn = ttk.Button(dialog, text="Save", command=on_save)
        save_btn.grid(row=len(fields_setup), column=0, columnspan=2, pady=10)
        dialog.bind("<Return>", lambda event: on_save())
        dialog.bind("<Escape>", lambda event: dialog.destroy())


    def delete_achievement(self):
        selected_game_name = self.game_var.get()
        selected_items = self.achievements_tree.selection()

        if not selected_game_name:
            messagebox.showwarning("No Game Selected", "Please select a game.", parent=self.root)
            return
        if not selected_items:
            messagebox.showwarning("No Achievement Selected", "Please select an achievement to delete.", parent=self.root)
            return

        item_values = self.achievements_tree.item(selected_items[0])["values"]
        ach_name_to_delete = item_values[0]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the achievement '{ach_name_to_delete}' from '{selected_game_name}'?", parent=self.root):
            for game in self.games_data.get("games", []):
                if game["name"] == selected_game_name:
                    game["achievements"] = [ach for ach in game.get("achievements", []) if ach.get("name") != ach_name_to_delete]
                    break
            self.save_games_data()
            self.on_game_selected()
            messagebox.showinfo("Deleted", f"Achievement '{ach_name_to_delete}' deleted.", parent=self.root)


    def toggle_manual_unlock_achievement(self):
        selected_game_name = self.game_var.get()
        selected_items = self.achievements_tree.selection()

        if not selected_game_name:
            messagebox.showwarning("No Game Selected", "Please select a game.", parent=self.root)
            return
        if not selected_items:
            messagebox.showwarning("No Achievement Selected", "Please select an achievement to toggle its unlock status.", parent=self.root)
            return

        item_values = self.achievements_tree.item(selected_items[0])["values"]
        ach_name_to_toggle = item_values[0]

        game_obj = next((g for g in self.games_data.get("games", []) if g["name"] == selected_game_name), None)
        if not game_obj:
            messagebox.showerror("Error", "Game not found.", parent=self.root)
            return

        ach_obj = next((ach for ach in game_obj.get("achievements", []) if ach.get("name") == ach_name_to_toggle), None)
        if not ach_obj:
            messagebox.showerror("Error", "Could not find the selected achievement data.", parent=self.root)
            return
        
        current_unlocked_status = ach_obj.get("unlocked", False)
        new_status = not current_unlocked_status
        verb = "unlocked" if new_status else "locked"

        if ach_obj.get("type") != "manual":
            if not new_status :
                if not messagebox.askyesno("Confirm Lock", f"'{ach_name_to_toggle}' is an automatic achievement. Are you sure you want to manually lock it? It might re-unlock automatically if conditions are met.", parent=self.root):
                    return

        ach_obj["unlocked"] = new_status
        self.save_games_data()
        self.on_game_selected()
        messagebox.showinfo("Status Changed", f"Achievement '{ach_name_to_toggle}' is now {verb}.", parent=self.root)

    def check_achievements_on_log(self, logged_project_name, logged_date_str):
        self.load_games_data()
        try:
            logged_date_obj = datetime.strptime(logged_date_str, "%Y-%m-%d %H:%M").date()
        except ValueError:
            print(f"Error: Invalid date format in log entry: {logged_date_str}")
            return

        work_log_entries = self.get_all_work_logs()

        unlocked_achievements_info = []
        game_changed = False

        for game in self.games_data.get("games", []):
            for ach in game.get("achievements", []):
                if ach.get("unlocked"):
                    continue

                linked_project_for_ach = ach.get("linked_to")
                ach_type = ach.get("type")
                target = ach.get("target")

                is_relevant_project_for_ach = (linked_project_for_ach is None or linked_project_for_ach == "" or linked_project_for_ach == logged_project_name)


                if ach_type == "counter" and target is not None:
                    if linked_project_for_ach is None or linked_project_for_ach == "":
                        total_hours = 0
                        for _, _, _, entry_hours_str in work_log_entries:
                            try: total_hours += float(entry_hours_str)
                            except ValueError: continue
                    elif linked_project_for_ach == logged_project_name:
                        total_hours = 0
                        for _, entry_project, _, entry_hours_str in work_log_entries:
                            if entry_project == linked_project_for_ach:
                                try: total_hours += float(entry_hours_str)
                                except ValueError: continue
                    else:
                        continue


                    if total_hours >= target:
                        ach["unlocked"] = True
                        unlocked_achievements_info.append(f"{game['name']} - {ach['name']}")
                        game_changed = True

                elif ach_type == "streak" and target is not None:
                    relevant_work_dates = set()
                    for entry_date_str_from_log, entry_project, _, _ in work_log_entries:
                        try:
                            d = datetime.strptime(entry_date_str_from_log, "%Y-%m-%d %H:%M").date()
                            if linked_project_for_ach is None or linked_project_for_ach == "" or entry_project == linked_project_for_ach:
                                relevant_work_dates.add(d)
                        except ValueError:
                            continue

                    if not relevant_work_dates or logged_date_obj not in relevant_work_dates:
                        continue

                    sorted_dates = sorted(list(relevant_work_dates), reverse=True)

                    current_streak = 0
                    try:
                        start_index = sorted_dates.index(logged_date_obj)
                    except ValueError:
                        continue

                    current_streak = 1
                    expected_date = logged_date_obj - timedelta(days=1)

                    for i in range(start_index + 1, len(sorted_dates)):
                        if sorted_dates[i] == expected_date:
                            current_streak += 1
                            expected_date -= timedelta(days=1)
                        elif sorted_dates[i] < expected_date:
                            break
                    
                    if current_streak >= target:
                        ach["unlocked"] = True
                        unlocked_achievements_info.append(f"{game['name']} - {ach['name']}")
                        game_changed = True

        if game_changed:
            self.save_games_data()
            if self.notebook.index(self.notebook.select()) == self.notebook.tabs().index(str(self.tab_achievements)):
                 self.on_game_selected()

        if unlocked_achievements_info:
            summary_message = "New Achievements Unlocked!\n\n" + "\n".join(unlocked_achievements_info)
            messagebox.showinfo("Achievements Unlocked!", summary_message, parent=self.root)


    def get_all_work_logs(self):
        """Helper to read all entries from work_log.csv"""
        entries = []
        if not os.path.exists(LOG_FILE):
            return entries
        with open(LOG_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            try:
                next(reader)
                for row in reader:
                    if len(row) == 4:
                        entries.append(row)
            except StopIteration:
                pass
        return entries


if __name__ == "__main__":
    root = tk.Tk()
    app = WorkLoggerApp(root)
    # Center the window
    root.eval('tk::PlaceWindow . center')
    root.mainloop()

