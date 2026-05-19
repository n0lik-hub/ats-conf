# -*- coding: utf-8 -*-
"""
Мастер конфигурации IP-АТС Т76-С - Главный файл приложения
Версия: 1.0
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import sys
from typing import Dict, List, Any, Optional

from config_master import ConfigData, ConfigGenerator
from gui_pages import Page, SystemPage, NtpPage, NetworkPage


# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ СТРАНИЦЫ (упрощённые)
# ============================================================================

class PlaceholderPage(Page):
    """Страница-заглушка для ещё не реализованных секций."""
    
    IS_OPTIONAL = True
    
    def __init__(self, parent, config_data: ConfigData, app, title: str, tooltip: str = ""):
        super().__init__(parent, config_data, app)
        self.TITLE = title
        self.TOOLTIP = tooltip
        
        title_label = ctk.CTkLabel(
            self, 
            text=f"Настройки {title}", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        desc = ctk.CTkLabel(
            self,
            text=f"Редактирование секции {title} будет реализовано в следующей версии.\n\nВы можете пропустить эту секцию.",
            wraplength=600,
            justify="center"
        )
        desc.pack(pady=20)
    
    def validate(self) -> bool:
        return True


class ExtensionsPage(Page):
    """Страница EXTENSIONS (обязательная)."""
    
    TITLE = "EXTENSIONS"
    TOOLTIP = "План набора"
    IS_OPTIONAL = False
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        title = ctk.CTkLabel(self, text="План набора (EXTENSIONS)", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        # GENERAL настройки
        general_frame = ctk.CTkFrame(self)
        general_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(general_frame, text="Общие настройки", font=ctk.CTkFont(weight="bold")).pack()
        
        self.static_var = ctk.BooleanVar(value=config_data.extensions['GENERAL'].get('STATIC', False))
        self.static_cb = ctk.CTkCheckBox(general_frame, text="STATIC", variable=self.static_var)
        self.static_cb.pack(side="left", padx=10)
        
        self.writeprotect_var = ctk.BooleanVar(value=config_data.extensions['GENERAL'].get('WRITEPROTECT', False))
        self.writeprotect_cb = ctk.CTkCheckBox(general_frame, text="WRITEPROTECT", variable=self.writeprotect_var)
        self.writeprotect_cb.pack(side="left", padx=10)
        
        self.autofallthrough_var = ctk.BooleanVar(value=config_data.extensions['GENERAL'].get('AUTOFALLTHROUGH', True))
        self.autofallthrough_cb = ctk.CTkCheckBox(general_frame, text="AUTOFALLTHROUGH", variable=self.autofallthrough_var)
        self.autofallthrough_cb.pack(side="left", padx=10)
        
        # Контексты (EXTENGROUP)
        contexts_frame = ctk.CTkFrame(self)
        contexts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(contexts_frame, text="Контексты и расширения", font=ctk.CTkFont(weight="bold")).pack()
        
        self.contexts_list_frame = ctk.CTkScrollableFrame(contexts_frame)
        self.contexts_list_frame.pack(fill="both", expand=True)
        
        self.contexts = []
        
        add_context_btn = ctk.CTkButton(contexts_frame, text="Добавить контекст", command=self._add_context)
        add_context_btn.pack(pady=5)
        
        # Загрузка данных
        self._load_contexts()
    
    def _add_context(self):
        """Добавляет новый контекст."""
        frame = ctk.CTkFrame(self.contexts_list_frame)
        frame.pack(fill="x", pady=5)
        
        context_data = {}
        
        # Имя контекста
        _, name_entry = create_labeled_entry(
            frame, "Имя контекста:",
            tooltip="Имя контекста (латиница, цифры, подчёркивание). Пример: main, from-internal",
            default=""
        )
        context_data['name'] = name_entry
        
        # Расширения
        extens_frame = ctk.CTkFrame(frame)
        extens_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(extens_frame, text="Расширения:").pack()
        
        extens_list_frame = ctk.CTkScrollableFrame(extens_frame, height=100)
        extens_list_frame.pack(fill="x")
        
        context_data['extens_list'] = extens_list_frame
        context_data['extens'] = []
        
        def add_exten():
            exten_frame = ctk.CTkFrame(extens_list_frame)
            exten_frame.pack(fill="x", pady=2)
            
            exten_data = {}
            
            _, field1 = create_labeled_entry(exten_frame, "Номер/маска:", tooltip="Номер или маска (_XXX.)", default="")
            exten_data['field1'] = field1
            
            _, field2 = create_labeled_entry(exten_frame, "Каналы/команды:", tooltip="SIP/101 или команды", default="")
            exten_data['field2'] = field2
            
            _, field3 = create_labeled_entry(exten_frame, "Макс. соединений:", tooltip="Опционально", default="")
            exten_data['field3'] = field3
            
            _, field4 = create_labeled_entry(exten_frame, "Приоритетные каналы:", tooltip="Опционально", default="")
            exten_data['field4'] = field4
            
            del_btn = ctk.CTkButton(exten_frame, text="X", width=30, command=lambda: self._remove_exten(exten_frame, context_data))
            del_btn.pack(side="right", padx=5)
            
            context_data['extens'].append(exten_data)
        
        add_exten_btn = ctk.CTkButton(extens_frame, text="+ Добавить расширение", command=add_exten)
        add_exten_btn.pack(pady=2)
        
        # Удалить контекст
        del_btn = ctk.CTkButton(frame, text="Удалить контекст", width=120, command=lambda: self._remove_context(frame))
        del_btn.pack(pady=5)
        
        self.contexts.append((frame, context_data))
    
    def _remove_exten(self, frame, context_data):
        for i, exten_data in enumerate(context_data['extens']):
            if all(v == frame for k, v in exten_data.items() if hasattr(v, 'winfo_children')):
                pass
        # Простое удаление
        for widget in frame.winfo_children():
            widget.destroy()
        frame.destroy()
    
    def _remove_context(self, frame):
        for i, (f, _) in enumerate(self.contexts):
            if f == frame:
                frame.destroy()
                self.contexts.pop(i)
                break
    
    def _load_contexts(self):
        for group in self.config_data.extensions.get('EXTENGROUP', []):
            self._add_context()
            if self.contexts:
                frame, data = self.contexts[-1]
                data['name'].delete(0, 'end')
                data['name'].insert(0, group.get('NAME', ''))
                
                for exten in group.get('EXTEN', []):
                    # Добавляем расширение
                    extens_list_frame = data['extens_list']
                    exten_frame = ctk.CTkFrame(extens_list_frame)
                    exten_frame.pack(fill="x", pady=2)
                    
                    exten_data = {}
                    
                    _, field1 = create_labeled_entry(exten_frame, "Номер/маска:", tooltip="", default=exten.get('field1', ''))
                    exten_data['field1'] = field1
                    
                    _, field2 = create_labeled_entry(exten_frame, "Каналы/команды:", tooltip="", default=exten.get('field2', ''))
                    exten_data['field2'] = field2
                    
                    _, field3 = create_labeled_entry(exten_frame, "Макс. соединений:", tooltip="", default=exten.get('field3', ''))
                    exten_data['field3'] = field3
                    
                    _, field4 = create_labeled_entry(exten_frame, "Приоритетные каналы:", tooltip="", default=exten.get('field4', ''))
                    exten_data['field4'] = field4
                    
                    del_btn = ctk.CTkButton(exten_frame, text="X", width=30, command=lambda f=exten_frame: self._remove_exten(f, data))
                    del_btn.pack(side="right", padx=5)
                    
                    data['extens'].append(exten_data)
    
    def save_data(self):
        # Общие настройки
        self.config_data.extensions['GENERAL'] = {
            'STATIC': self.static_var.get(),
            'WRITEPROTECT': self.writeprotect_var.get(),
            'CLEARGLOBALVARS': False,
            'AUTOFALLTHROUGH': self.autofallthrough_var.get()
        }
        
        # Контексты
        self.config_data.extensions['EXTENGROUP'] = []
        for frame, data in self.contexts:
            group = {
                'NAME': data['name'].get().strip(),
                'EXTEN': []
            }
            
            for exten_data in data['extens']:
                exten = {
                    'field1': exten_data['field1'].get().strip(),
                    'field2': exten_data['field2'].get().strip(),
                    'field3': exten_data['field3'].get().strip(),
                    'field4': exten_data['field4'].get().strip()
                }
                group['EXTEN'].append(exten)
            
            self.config_data.extensions['EXTENGROUP'].append(group)
    
    def validate(self) -> bool:
        self.error_messages = []
        
        # Проверяем что есть хотя бы один контекст
        if not self.contexts:
            self.error_messages.append("Необходимо добавить хотя бы один контекст (EXTENGROUP)")
            return False
        
        # Проверяем каждый контекст
        for frame, data in self.contexts:
            name = data['name'].get().strip()
            if not name:
                self.error_messages.append("Имя контекста не может быть пустым")
                data['name'].configure(border_color="red")
            
            # Проверяем что есть хотя бы одно расширение
            if not data['extens']:
                self.error_messages.append(f"Контекст '{name}' должен содержать хотя бы одно расширение")
            
            # Валидация расширений
            for exten_data in data['extens']:
                field1 = exten_data['field1'].get().strip()
                if not field1:
                    self.error_messages.append("Номер/маска расширения не могут быть пустыми")
                    exten_data['field1'].configure(border_color="red")
        
        return len(self.error_messages) == 0


# Импортируем из gui_pages
from gui_pages import create_labeled_entry


# ============================================================================
# СТРАНИЦА ПРЕДПРОСМОТРА
# ============================================================================

class PreviewPage(Page):
    """Страница предпросмотра конфигурации."""
    
    TITLE = "Предпросмотр"
    TOOLTIP = "Просмотр готового файла"
    IS_OPTIONAL = False
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        title = ctk.CTkLabel(self, text="Предпросмотр конфигурационного файла", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        self.textbox = ctk.CTkTextbox(self, width=800, height=500)
        self.textbox.pack(fill="both", expand=True, padx=20, pady=10)
    
    def load_data(self):
        """Генерирует и отображает конфигурацию."""
        generator = ConfigGenerator(self.config_data)
        config_text = generator.generate()
        
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", config_text)
    
    def validate(self) -> bool:
        return True


# ============================================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================================

class App(ctk.CTk):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Мастер конфигурации IP-АТС Т76-С")
        self.geometry("1200x800")
        
        # Данные конфигурации
        self.config_data = ConfigData()
        
        # Список страниц
        self.pages: List[Page] = []
        self.current_page_index = 0
        
        # Создаём интерфейс
        self._create_ui()
        
        # Создаём страницы
        self._create_pages()
        
        # Показываем первую страницу
        self.show_page(0)
    
    def _create_ui(self):
        """Создаёт основной интерфейс."""
        # Левая панель со списком шагов
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.pack(side="left", fill="y", padx=5, pady=5)
        
        ctk.CTkLabel(
            self.sidebar, 
            text="Шаги мастера", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        self.step_buttons = []
        self.step_labels = []
        
        # Основная область
        self.main_area = ctk.CTkFrame(self)
        self.main_area.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Контейнер для страниц
        self.page_container = ctk.CTkFrame(self.main_area)
        self.page_container.pack(fill="both", expand=True)
        
        # Нижняя панель с кнопками
        self.bottom_panel = ctk.CTkFrame(self.main_area)
        self.bottom_panel.pack(fill="x", pady=10)
        
        self.btn_help = ctk.CTkButton(self.bottom_panel, text="Справка", command=self._show_help)
        self.btn_help.pack(side="left", padx=10)
        
        self.btn_cancel = ctk.CTkButton(self.bottom_panel, text="Отмена", command=self._cancel)
        self.btn_cancel.pack(side="left", padx=10)
        
        self.btn_back = ctk.CTkButton(self.bottom_panel, text="Назад", command=self._go_back)
        self.btn_back.pack(side="right", padx=10)
        
        self.btn_next = ctk.CTkButton(self.bottom_panel, text="Далее", command=self._go_next)
        self.btn_next.pack(side="right", padx=10)
    
    def _create_pages(self):
        """Создаёт все страницы мастера."""
        # SYSTEM (обязательная)
        self.pages.append(SystemPage(self.page_container, self.config_data, self))
        
        # NTP (необязательная)
        self.pages.append(NtpPage(self.page_container, self.config_data, self))
        
        # NETWORK (обязательная)
        self.pages.append(NetworkPage(self.page_container, self.config_data, self))
        
        # MPLS (необязательная)
        self.pages.append(PlaceholderPage(self.page_container, self.config_data, self, "MPLS", "Маршрутизация MPLS"))
        
        # TUNNELS (необязательная)
        self.pages.append(PlaceholderPage(self.page_container, self.config_data, self, "TUNNELS", "Настройка туннелей"))
        
        # TC (необязательная)
        self.pages.append(PlaceholderPage(self.page_container, self.config_data, self, "TC", "Управление трафиком"))
        
        # IPTABLES (необязательная)
        self.pages.append(PlaceholderPage(self.page_container, self.config_data, self, "IPTABLES", "Межсетевой экран"))
        
        # IAX (необязательная)
        self.pages.append(PlaceholderPage(self.page_container, self.config_data, self, "IAX", "Настройка IAX"))
        
        # SIP (необязательная)
        self.pages.append(PlaceholderPage(self.page_container, self.config_data, self, "SIP", "Настройка SIP"))
        
        # ZAPTEL (необязательная)
        self.pages.append(PlaceholderPage(self.page_container, self.config_data, self, "ZAPTEL", "Настройка Zaptel"))
        
        # ZAPATA (необязательная)
        self.pages.append(PlaceholderPage(self.page_container, self.config_data, self, "ZAPATA", "Настройка Zapata"))
        
        # EXTENSIONS (обязательная)
        self.pages.append(ExtensionsPage(self.page_container, self.config_data, self))
        
        # ALARM (необязательная)
        self.pages.append(PlaceholderPage(self.page_container, self.config_data, self, "ALARM", "Настройка тревог"))
        
        # PREVIEW
        self.pages.append(PreviewPage(self.page_container, self.config_data, self))
        
        # Обновляем боковую панель
        self._update_sidebar()
    
    def _update_sidebar(self):
        """Обновляет боковую панель со списком шагов."""
        # Очищаем старое
        for btn in self.step_buttons:
            btn.destroy()
        for lbl in self.step_labels:
            lbl.destroy()
        
        self.step_buttons = []
        self.step_labels = []
        
        for i, page in enumerate(self.pages):
            # Кнопка для перехода
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{i+1}. {page.TITLE}",
                command=lambda idx=i: self.go_to_page(idx),
                fg_color="transparent",
                border_width=1
            )
            btn.pack(fill="x", padx=5, pady=2)
            self.step_buttons.append(btn)
            
            # Индикатор статуса
            lbl = ctk.CTkLabel(self.sidebar, text="○", width=20)
            lbl.pack()
            self.step_labels.append(lbl)
        
        self._update_step_indicators()
    
    def _update_step_indicators(self):
        """Обновляет индикаторы прохождения шагов."""
        for i, lbl in enumerate(self.step_labels):
            if i < self.current_page_index:
                lbl.configure(text="✔", text_color="green")
            elif i == self.current_page_index:
                lbl.configure(text="●", text_color="blue")
            else:
                lbl.configure(text="○", text_color="gray")
        
        # Обновляем кнопки
        for i, btn in enumerate(self.step_buttons):
            if i == self.current_page_index:
                btn.configure(fg_color=("gray20", "gray50"))
            else:
                btn.configure(fg_color="transparent")
    
    def show_page(self, index: int):
        """Показывает страницу по индексу."""
        if index < 0 or index >= len(self.pages):
            return
        
        # Сохраняем данные текущей страницы
        if 0 <= self.current_page_index < len(self.pages):
            self.pages[self.current_page_index].save_data()
        
        # Скрываем текущую страницу
        for page in self.pages:
            page.pack_forget()
        
        # Показываем новую
        self.current_page_index = index
        page = self.pages[index]
        page.pack(fill="both", expand=True)
        page.load_data()
        
        # Обновляем индикаторы
        self._update_step_indicators()
        
        # Обновляем кнопки
        if index == len(self.pages) - 1:
            self.btn_next.configure(text="Сохранить файл")
        else:
            self.btn_next.configure(text="Далее")
    
    def go_to_page(self, index: int):
        """Переходит к странице (с проверкой валидации)."""
        # Проверяем текущую страницу
        if not self.pages[self.current_page_index].validate():
            errors = self.pages[self.current_page_index].get_error_messages()
            if errors:
                messagebox.showerror("Ошибка валидации", "\n".join(errors))
                return
        
        self.show_page(index)
    
    def _go_back(self):
        """Кнопка Назад."""
        if self.current_page_index > 0:
            self.show_page(self.current_page_index - 1)
    
    def _go_next(self):
        """Кнопка Далее."""
        # Проверяем текущую страницу
        if not self.pages[self.current_page_index].validate():
            errors = self.pages[self.current_page_index].get_error_messages()
            if errors:
                messagebox.showerror("Ошибка валидации", "\n".join(errors))
                return
        
        if self.current_page_index < len(self.pages) - 1:
            self.show_page(self.current_page_index + 1)
        else:
            # Последняя страница - сохраняем
            self._save_file()
    
    def _save_file(self):
        """Сохраняет конфигурационный файл."""
        # Генерируем конфигурацию
        generator = ConfigGenerator(self.config_data)
        config_text = generator.generate()
        
        # Диалог сохранения
        default_name = f"{self.config_data.system.get('HOSTNAME', 'ats1')}.conf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".conf",
            filetypes=[("Config files", "*.conf"), ("All files", "*.*")],
            initialfile=default_name,
            title="Сохранить конфигурационный файл"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(config_text)
                
                messagebox.showinfo("Успех", f"Файл успешно сохранён:\n{file_path}")
                
                # Предлагаем начать заново или выйти
                result = messagebox.askyesno("Завершение", "Создать новую конфигурацию?\n\nНет - выйти из программы.")
                if result:
                    self._reset_config()
                else:
                    self.quit()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
    
    def _reset_config(self):
        """Сбрасывает конфигурацию и начинает заново."""
        self.config_data.reset()
        self.show_page(0)
    
    def _cancel(self):
        """Кнопка Отмена."""
        if messagebox.askyesno("Подтверждение", "Вы действительно хотите отменить создание конфигурации?"):
            self.quit()
    
    def _show_help(self):
        """Показывает справку."""
        help_text = """
Мастер конфигурации IP-АТС Т76-С

Программа позволяет создать конфигурационный файл для IP-АТС Т76-С в пошаговом режиме.

Обязательные разделы:
- SYSTEM: имя хоста устройства
- NETWORK: хотя бы один сетевой интерфейс
- EXTENSIONS: хотя бы один контекст с расширением

Навигация:
- Используйте кнопки «Назад» и «Далее» для перемещения между шагами
- Можно кликнуть на любой шаг в левой панели для быстрого перехода
- Необязательные разделы можно пропустить

Валидация:
- Программа проверяет корректность всех вводимых данных
- При ошибке проблемные поля подсвечиваются красным
- Переход к следующему шагу блокируется при наличии ошибок

Советы:
- Наведите курсор на поле ввода чтобы увидеть подсказку
- Для IP-адресов используйте формат xxx.xxx.xxx.xxx
- MAC адреса в формате XX:XX:XX:XX:XX:XX
"""
        
        help_window = ctk.CTkToplevel(self)
        help_window.title("Справка")
        help_window.geometry("600x500")
        
        textbox = ctk.CTkTextbox(help_window)
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("0.0", help_text)
        textbox.configure(state="disabled")


def main():
    """Точка входа."""
    # Настройка темы
    ctk.set_appearance_mode("light")  # Светлая тема
    ctk.set_default_color_theme("blue")
    
    # Запуск приложения
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
