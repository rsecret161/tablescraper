import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from . import fetcher, saver, db, worker

app_state = {"tables": []}


def run_app():
    root = tk.Tk()
    root.title("Table Scraper")
    root.geometry("1280x720")

    def set_status(msg, color=None):
        status_label.config(text=msg, foreground=color or "black")
        root.update_idletasks()

    def clear_preview():
        for col in preview_tree.get_children():
            preview_tree.delete(col)
        preview_tree['columns'] = ()
        preview_tree['show'] = ''

    def preview_table(index):
        clear_preview()
        try:
            df = app_state['tables'][index]
        except Exception:
            set_status("No table selected or table list empty", "red")
            return

        max_cols = 8
        max_rows = 10
        cols = list(df.columns.astype(str))[:max_cols]

        preview_tree['columns'] = cols
        preview_tree['show'] = 'headings'
        for c in cols:
            preview_tree.heading(c, text=c)
            preview_tree.column(c, width=100, anchor='w')

        for row in df.iloc[:max_rows].itertuples(index=False, name=None):
            preview_tree.insert('', 'end', values=[str(x)[:100] for x in row[:max_cols]])

        set_status(f"Previewing table {index+1}: {df.shape[0]} rows × {df.shape[1]} cols")

    def on_table_select(event=None):
        sel = tables_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        preview_table(index)

    def fetch_tables_bg():
        url = url_entry.get().strip()
        if not url:
            messagebox.showerror("Input error", "Please enter a URL.")
            return

        set_status("Fetching tables...")
        fetch_btn.config(state='disabled')

        def on_complete(tables):
            def ui_update():
                app_state['tables'] = tables
                tables_listbox.delete(0, tk.END)
                for i, df in enumerate(tables):
                    tables_listbox.insert(tk.END, f"Table {i+1}: {df.shape[0]} rows × {df.shape[1]} cols")
                if tables:
                    tables_listbox.selection_set(0)
                    preview_table(0)
                set_status(f"Found {len(tables)} table(s)", "green")
                fetch_btn.config(state='normal')

            root.after(0, ui_update)

        def on_error(e):
            def ui_err():
                messagebox.showerror("Fetch error", f"Could not fetch tables:\n{e}")
                set_status("Error fetching tables", "red")
                fetch_btn.config(state='normal')

            root.after(0, ui_err)

        worker.run_background(fetcher.fetch_tables, args=(url,), on_complete=on_complete, on_error=on_error)

    def save_action():
        sel = tables_listbox.curselection()
        if not sel:
            messagebox.showerror("No table", "Please fetch and select a table first.")
            return
        df = app_state['tables'][sel[0]]

        if save_mode.get() == 'file':
            filetypes = [('CSV', '*.csv'), ('Excel Workbook', '*.xlsx'), ('JSON', '*.json'), ('All files', '*.*')]
            initialdir = os.path.join(os.getcwd(), 'csv')
            os.makedirs(initialdir, exist_ok=True)
            default_name = filename_entry.get().strip() or f"table_{sel[0]+1}"
            path = filedialog.asksaveasfilename(defaultextension='.csv', initialdir=initialdir,
                                                initialfile=default_name, filetypes=filetypes)
            if not path:
                set_status("Save cancelled")
                return

            if os.path.exists(path):
                if not messagebox.askyesno("Confirm overwrite", f"File exists. Overwrite {path}?"):
                    set_status("Save cancelled by user")
                    return

            set_status("Saving...")

            def on_complete(_):
                def ui_ok():
                    messagebox.showinfo("Saved", f"Table saved to {path}")
                    set_status(f"Saved to {path}", "green")

                root.after(0, ui_ok)

            def on_error(e):
                def ui_err():
                    messagebox.showerror("Save error", f"Could not save file:\n{e}")
                    set_status("Error saving file", "red")

                root.after(0, ui_err)

            worker.run_background(saver.save_to_file, args=(df, path), on_complete=on_complete, on_error=on_error)

        else:  # db
            db_choice = db_type.get()
            params = {
                'host': db_host.get(),
                'port': db_port.get(),
                'user': db_user.get(),
                'password': db_password.get(),
                'database': db_name.get(),
                'table_name': db_table.get(),
            }
            set_status("Saving to DB...")

            def on_complete(_):
                def ui_ok():
                    messagebox.showinfo("Saved", f"Table saved to {db_choice} (stub) with params shown in code.")
                    set_status(f"Saved to {db_choice}", "green")

                root.after(0, ui_ok)

            def on_error(e):
                def ui_err():
                    if isinstance(e, NotImplementedError):
                        messagebox.showinfo("DB stub", str(e))
                        set_status("DB stub - implement save logic", "orange")
                    else:
                        messagebox.showerror("DB save error", f"Error saving to DB:\n{e}")
                        set_status("Error saving to DB", "red")

                root.after(0, ui_err)

            if db_choice == 'SQLite':
                worker.run_background(db.save_to_db_sqlite, args=(df, params), on_complete=on_complete, on_error=on_error)
            elif db_choice == 'PostgreSQL':
                worker.run_background(db.save_to_db_postgresql, args=(df, params), on_complete=on_complete, on_error=on_error)
            elif db_choice == 'MySQL':
                worker.run_background(db.save_to_db_mysql, args=(df, params), on_complete=on_complete, on_error=on_error)
            else:
                messagebox.showerror("DB error", "Please select a valid DB type.")
                set_status("No DB selected", "red")
                return

    # Build UI
    # Top frame: URL input and fetch control
    top_frame = ttk.Frame(root, padding=10)
    top_frame.grid(row=0, column=0, sticky='ew')

    # URL label and entry
    ttk.Label(top_frame, text="URL:").grid(row=0, column=0, sticky='w')
    url_entry = ttk.Entry(top_frame, width=80)
    url_entry.grid(row=0, column=1, padx=6, sticky='w')

    # Fetch button
    fetch_btn = ttk.Button(top_frame, text="Fetch Tables", command=fetch_tables_bg)
    fetch_btn.grid(row=0, column=2, padx=6)

    # Main area
    middle_frame = ttk.Frame(root, padding=10)
    middle_frame.grid(row=1, column=0, sticky='nsew')
    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)

    # Left column: list of discovered tables
    left_frame = ttk.Frame(middle_frame)
    left_frame.grid(row=0, column=0, sticky='ns')

    ttk.Label(left_frame, text="Tables found:").grid(row=0, column=0, sticky='w')
    # Listbox: select to preview that table
    tables_listbox = tk.Listbox(left_frame, height=12, width=40)
    tables_listbox.grid(row=1, column=0, pady=6)
    tables_listbox.bind('<<ListboxSelect>>', on_table_select)

    # Right column: preview of selected table (shows first rows/cols)
    right_frame = ttk.Frame(middle_frame)
    right_frame.grid(row=0, column=1, padx=10, sticky='nsew')
    middle_frame.columnconfigure(1, weight=1)

    ttk.Label(right_frame, text="Preview (first rows):").grid(row=0, column=0, sticky='w')
    preview_tree = ttk.Treeview(right_frame)
    preview_tree.grid(row=1, column=0, sticky='nsew')
    right_frame.rowconfigure(1, weight=1)
    right_frame.columnconfigure(0, weight=1)

    # Save options area: choose file or DB and supply parameters
    options_frame = ttk.Frame(root, padding=10)
    options_frame.grid(row=2, column=0, sticky='ew')

    save_mode = tk.StringVar(value='file')
    file_rb = ttk.Radiobutton(options_frame, text='Save as File', variable=save_mode, value='file', command=lambda: toggle_save_mode_ui())
    file_rb.grid(row=0, column=0, sticky='w')
    db_rb = ttk.Radiobutton(options_frame, text='Save to DB (stub)', variable=save_mode, value='db', command=lambda: toggle_save_mode_ui())
    db_rb.grid(row=0, column=1, sticky='w')

    filename_frame = ttk.Frame(options_frame)
    filename_frame.grid(row=1, column=0, columnspan=2, sticky='w', pady=6)

    # Optional filename used by file save dialog
    ttk.Label(filename_frame, text='Filename (optional):').grid(row=0, column=0, sticky='w')
    filename_entry = ttk.Entry(filename_frame, width=40)
    filename_entry.grid(row=0, column=1, padx=6, sticky='w')

    # DB inputs (shown when 'Save to DB' selected). DB logic to be implemented.
    db_frame = ttk.Frame(options_frame)
    db_frame.grid(row=1, column=0, columnspan=2, sticky='w', pady=6)

    ttk.Label(db_frame, text='DB Type:').grid(row=0, column=0, sticky='w')
    db_type = ttk.Combobox(db_frame, values=['SQLite', 'PostgreSQL', 'MySQL'], width=15)
    db_type.grid(row=0, column=1, padx=6, sticky='w')

    ttk.Label(db_frame, text='Host:').grid(row=1, column=0, sticky='w')
    db_host = ttk.Entry(db_frame, width=20)
    db_host.grid(row=1, column=1, padx=6, sticky='w')

    ttk.Label(db_frame, text='Port:').grid(row=1, column=2, sticky='w')
    db_port = ttk.Entry(db_frame, width=8)
    db_port.grid(row=1, column=3, padx=6, sticky='w')

    ttk.Label(db_frame, text='User:').grid(row=2, column=0, sticky='w')
    db_user = ttk.Entry(db_frame, width=20)
    db_user.grid(row=2, column=1, padx=6, sticky='w')

    ttk.Label(db_frame, text='Password:').grid(row=2, column=2, sticky='w')
    db_password = ttk.Entry(db_frame, width=20, show='*')
    db_password.grid(row=2, column=3, padx=6, sticky='w')

    ttk.Label(db_frame, text='Database:').grid(row=3, column=0, sticky='w')
    db_name = ttk.Entry(db_frame, width=20)
    db_name.grid(row=3, column=1, padx=6, sticky='w')

    ttk.Label(db_frame, text='Table name:').grid(row=3, column=2, sticky='w')
    db_table = ttk.Entry(db_frame, width=20)
    db_table.grid(row=3, column=3, padx=6, sticky='w')

    if save_mode.get() != 'db':
        db_frame.grid_remove()

    def toggle_save_mode_ui():
        if save_mode.get() == 'db':
            db_frame.grid()
            filename_frame.grid_remove()
        else:
            db_frame.grid_remove()
            filename_frame.grid()

    # Action buttons: Save and Quit
    actions_frame = ttk.Frame(root, padding=10)
    actions_frame.grid(row=3, column=0, sticky='e')

    # Save currently selected table using chosen mode
    save_btn = ttk.Button(actions_frame, text='Save Selected', command=save_action)
    save_btn.grid(row=0, column=0, padx=6)

    # Exit the application
    quit_btn = ttk.Button(actions_frame, text='Quit', command=root.destroy)
    quit_btn.grid(row=0, column=1, padx=6)

    # Status bar shows messages about progress and errors
    status_label = ttk.Label(root, text='Ready', relief='sunken', anchor='w')
    status_label.grid(row=4, column=0, sticky='ew')

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    set_status('Ready')
    root.mainloop()
