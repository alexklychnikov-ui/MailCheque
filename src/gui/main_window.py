import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date
from typing import List, Optional, Callable
from src.parser.receipt_parser import Receipt


class SettingsWindow:
    def __init__(self, parent, config_data: dict, on_save: Callable):
        self.parent = parent
        self.config_data = config_data
        self.on_save = on_save
        self.window = None
        
    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.parent)
        self.window.title("Настройки")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Центрируем окно
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (300 // 2)
        self.window.geometry(f"400x300+{x}+{y}")
        
        self._create_widgets()
        
    def _create_widgets(self):
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Email
        ttk.Label(main_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar(value=self.config_data.get('email', ''))
        email_entry = ttk.Entry(main_frame, textvariable=self.email_var, width=30)
        email_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # Password
        ttk.Label(main_frame, text="Пароль:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar(value=self.config_data.get('password', ''))
        password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*", width=30)
        password_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # Folder
        ttk.Label(main_frame, text="Папка:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.folder_var = tk.StringVar(value=self.config_data.get('folder', 'INBOX'))
        folder_entry = ttk.Entry(main_frame, textvariable=self.folder_var, width=30)
        folder_entry.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # IMAP Server
        ttk.Label(main_frame, text="IMAP сервер:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.server_var = tk.StringVar(value=self.config_data.get('imap_server', 'imap.mail.ru'))
        server_entry = ttk.Entry(main_frame, textvariable=self.server_var, width=30)
        server_entry.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # IMAP Port
        ttk.Label(main_frame, text="IMAP порт:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar(value=str(self.config_data.get('imap_port', 993)))
        port_entry = ttk.Entry(main_frame, textvariable=self.port_var, width=30)
        port_entry.grid(row=4, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=self._save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self._cancel).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
        
    def _save_settings(self):
        try:
            port = int(self.port_var.get())
            if not (1 <= port <= 65535):
                raise ValueError("Порт должен быть от 1 до 65535")
                
            new_config = {
                'email': self.email_var.get().strip(),
                'password': self.password_var.get(),
                'folder': self.folder_var.get().strip(),
                'imap_server': self.server_var.get().strip(),
                'imap_port': port
            }
            
            if not new_config['email']:
                messagebox.showerror("Ошибка", "Email не может быть пустым")
                return
                
            self.on_save(new_config)
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат порта: {e}")
            
    def _cancel(self):
        self.window.destroy()


class DateRangeDialog:
    def __init__(self, parent, start_date: date, end_date: date):
        self.parent = parent
        self.start_date = start_date
        self.end_date = end_date
        self.result = None
        
    def show(self) -> tuple:
        dialog = tk.Toplevel(self.parent)
        dialog.title("Выбор периода")
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Центрируем окно
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"350x200+{x}+{y}")
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Start Date
        ttk.Label(main_frame, text="Дата начала:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.start_var = tk.StringVar(value=self.start_date.strftime("%Y-%m-%d"))
        start_entry = ttk.Entry(main_frame, textvariable=self.start_var, width=15)
        start_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # End Date
        ttk.Label(main_frame, text="Дата окончания:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.end_var = tk.StringVar(value=self.end_date.strftime("%Y-%m-%d"))
        end_entry = ttk.Entry(main_frame, textvariable=self.end_var, width=15)
        end_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Quick buttons
        quick_frame = ttk.LabelFrame(main_frame, text="Быстрый выбор", padding="5")
        quick_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky=tk.EW)
        
        ttk.Button(quick_frame, text="Текущий месяц", 
                  command=lambda: self._set_current_month()).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="Прошлый месяц", 
                  command=lambda: self._set_last_month()).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="Последние 7 дней", 
                  command=lambda: self._set_last_week()).pack(side=tk.LEFT, padx=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="OK", command=lambda: self._ok(dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()
        return self.result
        
    def _set_current_month(self):
        today = date.today()
        start = today.replace(day=1)
        self.start_var.set(start.strftime("%Y-%m-%d"))
        self.end_var.set(today.strftime("%Y-%m-%d"))
        
    def _set_last_month(self):
        today = date.today()
        if today.month == 1:
            start = date(today.year - 1, 12, 1)
        else:
            start = date(today.year, today.month - 1, 1)
        
        if today.month == 1:
            end = date(today.year - 1, 12, 31)
        else:
            if today.month - 1 in [4, 6, 9, 11]:
                end = date(today.year, today.month - 1, 30)
            elif today.month - 1 == 2:
                end = date(today.year, today.month - 1, 28)
            else:
                end = date(today.year, today.month - 1, 31)
                
        self.start_var.set(start.strftime("%Y-%m-%d"))
        self.end_var.set(end.strftime("%Y-%m-%d"))
        
    def _set_last_week(self):
        today = date.today()
        from datetime import timedelta
        start = today - timedelta(days=7)
        self.start_var.set(start.strftime("%Y-%m-%d"))
        self.end_var.set(today.strftime("%Y-%m-%d"))
        
    def _ok(self, dialog):
        try:
            start = datetime.strptime(self.start_var.get(), "%Y-%m-%d").date()
            end = datetime.strptime(self.end_var.get(), "%Y-%m-%d").date()
            
            if start > end:
                messagebox.showerror("Ошибка", "Дата начала не может быть больше даты окончания")
                return
                
            self.result = (start, end)
            dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте YYYY-MM-DD")


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MailCheque - Поиск чеков в Mail.ru")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Переменные
        self.config_data = {}
        self.receipts = []
        
        # Callbacks
        self.on_settings_save = None
        self.on_search_receipts = None
        self.on_date_range_change = None
        
        self._create_widgets()
        self._setup_layout()
        
    def _create_widgets(self):
        # Main menu
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_command(label="Параметры подключения", command=self._show_settings)
        
        # Toolbar
        self.toolbar = ttk.Frame(self.root)
        
        self.settings_btn = ttk.Button(self.toolbar, text="⚙ Настройки", command=self._show_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.date_range_btn = ttk.Button(self.toolbar, text="📅 Период", command=self._show_date_dialog)
        self.date_range_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.search_btn = ttk.Button(self.toolbar, text="🔍 Найти чеки", command=self._search_receipts)
        self.search_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.clear_btn = ttk.Button(self.toolbar, text="🗑 Очистить", command=self._clear_results)
        self.clear_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Status frame
        self.status_frame = ttk.Frame(self.root)
        
        self.status_var = tk.StringVar(value="Готов к работе")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
        
        # Results frame
        self.results_frame = ttk.LabelFrame(self.root, text="Результаты поиска", padding="5")
        
        # Treeview for results
        columns = ('name', 'date', 'amount')
        self.tree = ttk.Treeview(self.results_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('name', text='Наименование')
        self.tree.heading('date', text='Дата')
        self.tree.heading('amount', text='Сумма (₽)')
        
        self.tree.column('name', width=400, minwidth=200)
        self.tree.column('date', width=150, minwidth=100)
        self.tree.column('amount', width=120, minwidth=80)
        
        # Scrollbars
        self.v_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.h_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Summary frame
        self.summary_frame = ttk.Frame(self.results_frame)
        
        self.summary_var = tk.StringVar(value="")
        self.summary_label = ttk.Label(self.summary_frame, textvariable=self.summary_var, 
                                     font=('TkDefaultFont', 10, 'bold'))
        self.summary_label.pack()
        
    def _setup_layout(self):
        self.toolbar.pack(fill=tk.X)
        self.status_frame.pack(fill=tk.X, padx=5, pady=2)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview layout
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.v_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.h_scrollbar.grid(row=1, column=0, sticky=tk.EW)
        
        self.summary_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        self.results_frame.rowconfigure(0, weight=1)
        self.results_frame.columnconfigure(0, weight=1)
        
    def _show_settings(self):
        if not self.on_settings_save:
            messagebox.showwarning("Предупреждение", "Обработчик настроек не установлен")
            return
            
        settings_window = SettingsWindow(self.root, self.config_data, self._on_settings_saved)
        settings_window.show()
        
    def _on_settings_saved(self, new_config):
        self.config_data.update(new_config)
        if self.on_settings_save:
            self.on_settings_save(new_config)
            
    def _show_date_dialog(self):
        if not self.on_date_range_change:
            messagebox.showwarning("Предупреждение", "Обработчик изменения периода не установлен")
            return
            
        # Получаем текущие даты из конфига
        start_date = self.config_data.get('last_start_date', date.today().replace(day=1))
        end_date = self.config_data.get('last_end_date', date.today())
        
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).date()
            
        dialog = DateRangeDialog(self.root, start_date, end_date)
        result = dialog.show()
        
        if result:
            start, end = result
            self.config_data['last_start_date'] = start.isoformat()
            self.config_data['last_end_date'] = end.isoformat()
            self.on_date_range_change(start, end)
            
    def _search_receipts(self):
        if not self.on_search_receipts:
            messagebox.showwarning("Предупреждение", "Обработчик поиска не установлен")
            return
            
        # Проверяем настройки
        if not self.config_data.get('email'):
            messagebox.showerror("Ошибка", "Не указан email. Проверьте настройки.")
            return
            
        if not self.config_data.get('password'):
            messagebox.showerror("Ошибка", "Не указан пароль. Проверьте настройки.")
            return
            
        self.on_search_receipts()
        
    def _clear_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.summary_var.set("")
        self.receipts = []
        
    def set_status(self, message: str, show_progress: bool = False):
        self.status_var.set(message)
        if show_progress:
            self.progress.start()
        else:
            self.progress.stop()
        self.root.update_idletasks()
        
    def update_config(self, config_data: dict):
        self.config_data = config_data
        
    def show_receipts(self, receipts: List[Receipt], total_amount: float):
        self.receipts = receipts
        
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Добавляем чеки
        for receipt in receipts:
            self.tree.insert('', tk.END, values=(
                receipt.email_subject,
                receipt.date,
                f"{receipt.amount:.2f}"
            ))
            
        # Обновляем сводку
        count = len(receipts)
        self.summary_var.set(f"Найдено чеков: {count}, Общая сумма: {total_amount:.2f} ₽")
        
    def show_error(self, message: str):
        messagebox.showerror("Ошибка", message)
        self.set_status("Ошибка выполнения запроса")
        
    def show_info(self, message: str):
        messagebox.showinfo("Информация", message)
        
    def run(self):
        self.root.mainloop()
        
    def destroy(self):
        self.root.destroy()
