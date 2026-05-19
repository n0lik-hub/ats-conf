"""
Главное приложение «Мастер конфигурации IP-АТС Т76-С».
Реализует линейный пошаговый интерфейс без боковой панели.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_data import ConfigData
from generator import ConfigGenerator
from validators import (
    validate_hostname, validate_ipv4, validate_netmask, validate_mac,
    validate_iface_name, validate_integer, validate_extension_mask
)

# Настройки customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ToolTip:
    """Всплывающая подсказка для виджетов."""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)
        
    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(
            tw, text=self.text, justify="left",
            fg_color="#333333", text_color="white",
            corner_radius=5, padx=10, pady=5
        )
        label.pack()
        
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class BasePage(ctk.CTkFrame):
    """Базовый класс для всех страниц."""
    
    def __init__(self, parent, app, title):
        super().__init__(parent)
        self.app = app
        self.title = title
        self.tooltips = []
        
    def add_tooltip(self, widget, text):
        """Добавить подсказку к виджету."""
        tooltip = ToolTip(widget, text)
        self.tooltips.append(tooltip)
        
    def clear_tooltips(self):
        """Очистить все подсказки."""
        for tooltip in self.tooltips:
            tooltip.hide_tooltip()
        self.tooltips = []
        
    def validate(self) -> tuple:
        """
        Валидация данных страницы.
        Возвращает (True, "") если успешно, или (False, "сообщение об ошибке").
        Должен быть переопределен в подклассах.
        """
        return True, ""
    
    def save_data(self):
        """Сохранить данные из полей ввода в ConfigData."""
        pass
    
    def load_data(self):
        """Загрузить данные из ConfigData в поля ввода."""
        pass


class SystemPage(BasePage):
    """Страница SYSTEM."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app, "SYSTEM")
        
        # Заголовок
        title_label = ctk.CTkLabel(self, text="Секция SYSTEM", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # Описание
        desc_label = ctk.CTkLabel(
            self, 
            text="Настройка базовых системных параметров IP-АТС",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        desc_label.pack(pady=(0, 20))
        
        # Поле HOSTNAME
        hostname_frame = ctk.CTkFrame(self)
        hostname_frame.pack(fill="x", padx=20, pady=10)
        
        hostname_label = ctk.CTkLabel(hostname_frame, text="Имя хоста (HOSTNAME):", font=ctk.CTkFont(size=14))
        hostname_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.hostname_entry = ctk.CTkEntry(hostname_frame, width=400, placeholder_text="ats1")
        self.hostname_entry.pack(anchor="w", padx=10, pady=(0, 10))
        self.add_tooltip(self.hostname_entry, 
            "Имя устройства в домене.\n"
            "Допустимы: латиница (a-z, A-Z), цифры (0-9), символы '_', '-', '.'\n"
            "Максимум 63 символа.\n"
            "Пример: ats1, pbx-office, server.test.local")
        
        # Подсказка под полем
        hint_label = ctk.CTkLabel(
            hostname_frame,
            text="Пример: ats1",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        hint_label.pack(anchor="w", padx=10, pady=(0, 10))
        
    def validate(self) -> tuple:
        hostname = self.hostname_entry.get().strip()
        valid, msg = validate_hostname(hostname)
        if not valid:
            self.hostname_entry.configure(border_color="red")
            return False, msg
        self.hostname_entry.configure(border_color="gray")
        return True, ""
    
    def save_data(self):
        self.app.data.system['hostname'] = self.hostname_entry.get().strip()
        
    def load_data(self):
        self.hostname_entry.delete(0, 'end')
        self.hostname_entry.insert(0, self.app.data.system.get('hostname', 'ats1'))


class NtpPage(BasePage):
    """Страница NTP."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app, "NTP")
        
        # Заголовок
        title_label = ctk.CTkLabel(self, text="Секция NTP", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # Флажок включения
        self.enabled_var = ctk.BooleanVar(value=False)
        enabled_checkbox = ctk.CTkCheckBox(
            self, 
            text="Включить синхронизацию времени (NTP)",
            variable=self.enabled_var,
            command=self.toggle_fields,
            font=ctk.CTkFont(size=14)
        )
        enabled_checkbox.pack(anchor="w", padx=20, pady=(10, 20))
        self.add_tooltip(enabled_checkbox,
            "Если отмечено, АТС будет синхронизировать время с NTP-сервером.\n"
            "Если не отмечено, секция NTP не будет включена в конфиг.")
        
        # Контейнер для полей
        self.fields_frame = ctk.CTkFrame(self)
        self.fields_frame.pack(fill="x", padx=20, pady=10)
        
        # IP_SRV
        ip_frame = ctk.CTkFrame(self.fields_frame)
        ip_frame.pack(fill="x", padx=10, pady=5)
        
        ip_label = ctk.CTkLabel(ip_frame, text="IP-адрес NTP-сервера:", font=ctk.CTkFont(size=14))
        ip_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.ip_srv_entry = ctk.CTkEntry(ip_frame, width=400, placeholder_text="192.168.1.1")
        self.ip_srv_entry.pack(anchor="w", padx=10, pady=(0, 10))
        self.add_tooltip(self.ip_srv_entry,
            "IPv4 адрес сервера времени.\n"
            "Пример: 192.168.1.1, 10.0.0.1")
        
        # INTERVAL
        interval_frame = ctk.CTkFrame(self.fields_frame)
        interval_frame.pack(fill="x", padx=10, pady=5)
        
        interval_label = ctk.CTkLabel(interval_frame, text="Интервал опроса (секунды):", font=ctk.CTkFont(size=14))
        interval_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.interval_entry = ctk.CTkEntry(interval_frame, width=400, placeholder_text="14400")
        self.interval_entry.pack(anchor="w", padx=10, pady=(0, 10))
        self.add_tooltip(self.interval_entry,
            "Интервал между запросами к NTP-серверу в секундах.\n"
            "Допустимый диапазон: 60-86400\n"
            "По умолчанию: 14400 (4 часа)")
        
        # Инициализация состояния полей
        self.toggle_fields()
        
    def toggle_fields(self):
        """Включить/выключить поля в зависимости от флажка."""
        state = "normal" if self.enabled_var.get() else "disabled"
        self.ip_srv_entry.configure(state=state)
        self.interval_entry.configure(state=state)
        
    def validate(self) -> tuple:
        if not self.enabled_var.get():
            return True, ""
        
        # Проверяем IP
        ip = self.ip_srv_entry.get().strip()
        valid, msg = validate_ipv4(ip)
        if not valid:
            self.ip_srv_entry.configure(border_color="red")
            return False, f"Некорректный IP-адрес: {msg}"
        self.ip_srv_entry.configure(border_color="gray")
        
        # Проверяем интервал
        interval = self.interval_entry.get().strip()
        valid, msg = validate_integer(interval, 60, 86400, allow_empty=True)
        if not valid and interval:
            self.interval_entry.configure(border_color="red")
            return False, msg
        self.interval_entry.configure(border_color="gray")
        
        return True, ""
    
    def save_data(self):
        self.app.data.ntp_enabled = self.enabled_var.get()
        if self.enabled_var.get():
            self.app.data.ntp['ip_srv'] = self.ip_srv_entry.get().strip()
            interval = self.interval_entry.get().strip()
            self.app.data.ntp['interval'] = int(interval) if interval else 14400
        else:
            self.app.data.ntp['ip_srv'] = ''
            self.app.data.ntp['interval'] = 14400
        
    def load_data(self):
        self.enabled_var.set(self.app.data.ntp_enabled)
        self.ip_srv_entry.delete(0, 'end')
        self.ip_srv_entry.insert(0, self.app.data.ntp.get('ip_srv', ''))
        self.interval_entry.delete(0, 'end')
        interval = self.app.data.ntp.get('interval', 14400)
        self.interval_entry.insert(0, str(interval) if interval != 14400 else '')
        self.toggle_fields()


class NetworkPage(BasePage):
    """Страница NETWORK с вкладками IFACE, ROUTE, ARP."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app, "NETWORK")
        
        # Заголовок
        title_label = ctk.CTkLabel(self, text="Секция NETWORK", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # Создаем вкладки
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.iface_tab = self.tabview.add("Интерфейсы")
        self.route_tab = self.tabview.add("Маршруты")
        self.arp_tab = self.tabview.add("ARP")
        
        # Инициализация вкладок
        self._init_iface_tab()
        self._init_route_tab()
        self._init_arp_tab()
        
        # Хранилище для виджетов интерфейсов
        self.iface_widgets = []
        self.route_widgets = []
        self.arp_widgets = []
        
    def _init_iface_tab(self):
        """Инициализация вкладки интерфейсов."""
        # Кнопка добавления
        add_btn = ctk.CTkButton(
            self.iface_tab, 
            text="Добавить интерфейс",
            command=self.add_iface,
            font=ctk.CTkFont(size=14)
        )
        add_btn.pack(anchor="w", padx=10, pady=10)
        self.add_tooltip(add_btn, "Добавить новый сетевой интерфейс")
        
        # Scrollable frame для интерфейсов
        self.iface_scroll = ctk.CTkScrollableFrame(self.iface_tab)
        self.iface_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
    def _init_route_tab(self):
        """Инициализация вкладки маршрутов."""
        add_btn = ctk.CTkButton(
            self.route_tab,
            text="Добавить маршрут",
            command=self.add_route,
            font=ctk.CTkFont(size=14)
        )
        add_btn.pack(anchor="w", padx=10, pady=10)
        self.add_tooltip(add_btn, "Добавить статический маршрут")
        
        self.route_scroll = ctk.CTkScrollableFrame(self.route_tab)
        self.route_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
    def _init_arp_tab(self):
        """Инициализация вкладки ARP."""
        add_btn = ctk.CTkButton(
            self.arp_tab,
            text="Добавить ARP запись",
            command=self.add_arp,
            font=ctk.CTkFont(size=14)
        )
        add_btn.pack(anchor="w", padx=10, pady=10)
        self.add_tooltip(add_btn, "Добавить статическую ARP запись")
        
        self.arp_scroll = ctk.CTkScrollableFrame(self.arp_tab)
        self.arp_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
    def add_iface(self):
        """Добавить форму для нового интерфейса."""
        iface_frame = ctk.CTkFrame(self.iface_scroll)
        iface_frame.pack(fill="x", padx=10, pady=5)
        
        # Заголовок формы
        header = ctk.CTkLabel(iface_frame, text="Новый интерфейс", font=ctk.CTkFont(weight="bold"))
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Кнопка удаления
        del_btn = ctk.CTkButton(iface_frame, text="X", width=30, command=lambda f=iface_frame: self.remove_iface(f))
        del_btn.grid(row=0, column=2, padx=10, pady=5)
        
        # IFACE_NAME
        ctk.CTkLabel(iface_frame, text="Имя интерфейса:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        iface_name = ctk.CTkComboBox(iface_frame, values=['eth0', 'eth1'] + [f'eth0:{i}' for i in range(10)] + [f'eth1:{i}' for i in range(10)])
        iface_name.set('eth0')
        iface_name.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.add_tooltip(iface_name, "Имя сетевого интерфейса")
        
        # IP
        ctk.CTkLabel(iface_frame, text="IP-адрес:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ip_entry = ctk.CTkEntry(iface_frame, placeholder_text="192.168.1.10")
        ip_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.add_tooltip(ip_entry, "IPv4 адрес интерфейса")
        
        # NETMASK
        ctk.CTkLabel(iface_frame, text="Маска подсети:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        netmask_entry = ctk.CTkEntry(iface_frame, placeholder_text="255.255.255.0")
        netmask_entry.insert(0, "255.255.255.0")
        netmask_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        self.add_tooltip(netmask_entry, "Маска подсети")
        
        # BROADCAST
        ctk.CTkLabel(iface_frame, text="Broadcast (опц.):").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        broadcast_entry = ctk.CTkEntry(iface_frame, placeholder_text="192.168.1.255")
        broadcast_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        self.add_tooltip(broadcast_entry, "Широковещательный адрес (необязательно)")
        
        # MTU
        ctk.CTkLabel(iface_frame, text="MTU:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        mtu_entry = ctk.CTkEntry(iface_frame, placeholder_text="1500")
        mtu_entry.insert(0, "1500")
        mtu_entry.grid(row=5, column=1, sticky="ew", padx=10, pady=5)
        self.add_tooltip(mtu_entry, "Максимальный размер пакета (68-1500)")
        
        # METRIC
        ctk.CTkLabel(iface_frame, text="Метрика:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        metric_entry = ctk.CTkEntry(iface_frame, placeholder_text="1")
        metric_entry.insert(0, "1")
        metric_entry.grid(row=6, column=1, sticky="ew", padx=10, pady=5)
        self.add_tooltip(metric_entry, "Метрика интерфейса (0-65535)")
        
        # SPEED
        ctk.CTkLabel(iface_frame, text="Скорость (опц.):").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        speed_combo = ctk.CTkComboBox(iface_frame, values=["", "10", "100", "1000"])
        speed_combo.set("")
        speed_combo.grid(row=7, column=1, sticky="ew", padx=10, pady=5)
        self.add_tooltip(speed_combo, "Скорость интерфейса в Мбит/с")
        
        # DUPLEX
        ctk.CTkLabel(iface_frame, text="Дуплекс (опц.):").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        duplex_combo = ctk.CTkComboBox(iface_frame, values=["", "full", "half"])
        duplex_combo.set("")
        duplex_combo.grid(row=8, column=1, sticky="ew", padx=10, pady=5)
        self.add_tooltip(duplex_combo, "Режим дуплекса")
        
        # AUTONEG
        ctk.CTkLabel(iface_frame, text="Autoneg (опц.):").grid(row=9, column=0, sticky="w", padx=10, pady=5)
        autoneg_combo = ctk.CTkComboBox(iface_frame, values=["on", "off"])
        autoneg_combo.set("on")
        autoneg_combo.grid(row=9, column=1, sticky="ew", padx=10, pady=5)
        self.add_tooltip(autoneg_combo, "Автосогласование скорости")
        
        iface_frame.grid_columnconfigure(1, weight=1)
        
        self.iface_widgets.append({
            'frame': iface_frame,
            'iface_name': iface_name,
            'ip': ip_entry,
            'netmask': netmask_entry,
            'broadcast': broadcast_entry,
            'mtu': mtu_entry,
            'metric': metric_entry,
            'speed': speed_combo,
            'duplex': duplex_combo,
            'autoneg': autoneg_combo
        })
        
    def remove_iface(self, frame):
        """Удалить интерфейс."""
        for i, w in enumerate(self.iface_widgets):
            if w['frame'] == frame:
                frame.destroy()
                del self.iface_widgets[i]
                break
                
    def add_route(self):
        """Добавить форму для маршрута."""
        route_frame = ctk.CTkFrame(self.route_scroll)
        route_frame.pack(fill="x", padx=10, pady=5)
        
        header = ctk.CTkLabel(route_frame, text="Новый маршрут", font=ctk.CTkFont(weight="bold"))
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        del_btn = ctk.CTkButton(route_frame, text="X", width=30, command=lambda f=route_frame: self.remove_route(f))
        del_btn.grid(row=0, column=2, padx=10, pady=5)
        
        # IFACE_NAME
        ctk.CTkLabel(route_frame, text="Интерфейс:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        iface_name = ctk.CTkComboBox(route_frame, values=[])
        iface_name.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        # NET
        ctk.CTkLabel(route_frame, text="Сеть (опц.):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        net_entry = ctk.CTkEntry(route_frame, placeholder_text="192.168.2.0")
        net_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        # NETMASK
        ctk.CTkLabel(route_frame, text="Маска (опц.):").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        netmask_entry = ctk.CTkEntry(route_frame, placeholder_text="255.255.255.0")
        netmask_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        
        # GATEWAY
        ctk.CTkLabel(route_frame, text="Шлюз:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        gateway_entry = ctk.CTkEntry(route_frame, placeholder_text="192.168.1.1")
        gateway_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        
        # DEFAULT_GW
        ctk.CTkLabel(route_frame, text="Шлюз по умолчанию:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        default_gw_var = ctk.BooleanVar(value=False)
        default_gw_cb = ctk.CTkCheckBox(route_frame, variable=default_gw_var)
        default_gw_cb.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        
        # METRIC
        ctk.CTkLabel(route_frame, text="Метрика (опц.):").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        metric_entry = ctk.CTkEntry(route_frame, placeholder_text="1")
        metric_entry.grid(row=6, column=1, sticky="ew", padx=10, pady=5)
        
        route_frame.grid_columnconfigure(1, weight=1)
        
        self.route_widgets.append({
            'frame': route_frame,
            'iface_name': iface_name,
            'net': net_entry,
            'netmask': netmask_entry,
            'gateway': gateway_entry,
            'default_gw_var': default_gw_var,
            'metric': metric_entry
        })
        
    def remove_route(self, frame):
        """Удалить маршрут."""
        for i, w in enumerate(self.route_widgets):
            if w['frame'] == frame:
                frame.destroy()
                del self.route_widgets[i]
                break
                
    def add_arp(self):
        """Добавить форму для ARP записи."""
        arp_frame = ctk.CTkFrame(self.arp_scroll)
        arp_frame.pack(fill="x", padx=10, pady=5)
        
        header = ctk.CTkLabel(arp_frame, text="Новая ARP запись", font=ctk.CTkFont(weight="bold"))
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        del_btn = ctk.CTkButton(arp_frame, text="X", width=30, command=lambda f=arp_frame: self.remove_arp(f))
        del_btn.grid(row=0, column=2, padx=10, pady=5)
        
        # IP
        ctk.CTkLabel(arp_frame, text="IP-адрес:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ip_entry = ctk.CTkEntry(arp_frame, placeholder_text="192.168.1.100")
        ip_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        # MAC
        ctk.CTkLabel(arp_frame, text="MAC-адрес:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        mac_entry = ctk.CTkEntry(arp_frame, placeholder_text="00:1A:2B:3C:4D:5E")
        mac_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        arp_frame.grid_columnconfigure(1, weight=1)
        
        self.arp_widgets.append({
            'frame': arp_frame,
            'ip': ip_entry,
            'mac': mac_entry
        })
        
    def remove_arp(self, frame):
        """Удалить ARP запись."""
        for i, w in enumerate(self.arp_widgets):
            if w['frame'] == frame:
                frame.destroy()
                del self.arp_widgets[i]
                break
    
    def validate(self) -> tuple:
        # Проверяем наличие хотя бы одного интерфейса
        if not self.iface_widgets:
            return False, "Требуется хотя бы один сетевой интерфейс"
        
        # Обновляем список интерфейсов для маршрутов
        iface_names = [w['iface_name'].get() for w in self.iface_widgets]
        for rw in self.route_widgets:
            rw['iface_name'].configure(values=iface_names)
        
        # Валидация интерфейсов
        for i, w in enumerate(self.iface_widgets):
            # IFACE_NAME
            iface_name = w['iface_name'].get()
            valid, msg = validate_iface_name(iface_name)
            if not valid:
                return False, f"Интерфейс {i+1}: {msg}"
            
            # IP
            ip = w['ip'].get().strip()
            valid, msg = validate_ipv4(ip)
            if not valid:
                w['ip'].configure(border_color="red")
                return False, f"Интерфейс {i+1}: {msg}"
            w['ip'].configure(border_color="gray")
            
            # NETMASK
            netmask = w['netmask'].get().strip()
            valid, msg = validate_netmask(netmask)
            if not valid:
                w['netmask'].configure(border_color="red")
                return False, f"Интерфейс {i+1}: {msg}"
            w['netmask'].configure(border_color="gray")
        
        # Валидация маршрутов
        default_gw_count = sum(1 for w in self.route_widgets if w['default_gw_var'].get())
        if default_gw_count > 1:
            return False, "Только один маршрут может быть шлюзом по умолчанию"
        
        for i, w in enumerate(self.route_widgets):
            # GATEWAY обязателен
            gateway = w['gateway'].get().strip()
            if not gateway:
                w['gateway'].configure(border_color="red")
                return False, f"Маршрут {i+1}: шлюз обязателен"
            valid, msg = validate_ipv4(gateway)
            if not valid:
                w['gateway'].configure(border_color="red")
                return False, f"Маршрут {i+1}: {msg}"
            w['gateway'].configure(border_color="gray")
            
            # Если не default_gw, то NET и NETMASK обязательны
            if not w['default_gw_var'].get():
                net = w['net'].get().strip()
                if net:
                    valid, msg = validate_ipv4(net)
                    if not valid:
                        w['net'].configure(border_color="red")
                        return False, f"Маршрут {i+1}: {msg}"
                    w['net'].configure(border_color="gray")
        
        # Валидация ARP
        for i, w in enumerate(self.arp_widgets):
            ip = w['ip'].get().strip()
            valid, msg = validate_ipv4(ip)
            if not valid:
                w['ip'].configure(border_color="red")
                return False, f"ARP запись {i+1}: {msg}"
            w['ip'].configure(border_color="gray")
            
            mac = w['mac'].get().strip()
            valid, msg = validate_mac(mac)
            if not valid:
                w['mac'].configure(border_color="red")
                return False, f"ARP запись {i+1}: {msg}"
            w['mac'].configure(border_color="gray")
        
        return True, ""
    
    def save_data(self):
        # Сохраняем интерфейсы
        self.app.data.network_ifaces = []
        for w in self.iface_widgets:
            iface = {
                'iface_name': w['iface_name'].get(),
                'ip': w['ip'].get().strip(),
                'netmask': w['netmask'].get().strip(),
                'broadcast': w['broadcast'].get().strip(),
                'mtu': w['mtu'].get().strip(),
                'metric': w['metric'].get().strip(),
                'speed': w['speed'].get(),
                'duplex': w['duplex'].get(),
                'autoneg': w['autoneg'].get()
            }
            self.app.data.add_iface(iface)
        
        # Сохраняем маршруты
        self.app.data.network_routes = []
        for w in self.route_widgets:
            route = {
                'iface_name': w['iface_name'].get(),
                'net': w['net'].get().strip(),
                'netmask': w['netmask'].get().strip(),
                'gateway': w['gateway'].get().strip(),
                'default_gw': w['default_gw_var'].get(),
                'metric': w['metric'].get().strip()
            }
            self.app.data.add_route(route)
        
        # Сохраняем ARP
        self.app.data.network_arp = []
        for w in self.arp_widgets:
            arp = {
                'ip': w['ip'].get().strip(),
                'mac': w['mac'].get().strip().upper()
            }
            self.app.data.add_arp(arp)
    
    def load_data(self):
        # Очищаем текущие виджеты
        for w in self.iface_widgets:
            w['frame'].destroy()
        self.iface_widgets = []
        
        for w in self.route_widgets:
            w['frame'].destroy()
        self.route_widgets = []
        
        for w in self.arp_widgets:
            w['frame'].destroy()
        self.arp_widgets = []
        
        # Загружаем интерфейсы
        for iface in self.app.data.network_ifaces:
            self.add_iface()
            if self.iface_widgets:
                w = self.iface_widgets[-1]
                w['iface_name'].set(iface.get('iface_name', 'eth0'))
                w['ip'].insert(0, iface.get('ip', ''))
                w['netmask'].delete(0, 'end')
                w['netmask'].insert(0, iface.get('netmask', '255.255.255.0'))
                if iface.get('broadcast'):
                    w['broadcast'].insert(0, iface['broadcast'])
                if iface.get('mtu'):
                    w['mtu'].delete(0, 'end')
                    w['mtu'].insert(0, str(iface['mtu']))
                if iface.get('metric'):
                    w['metric'].delete(0, 'end')
                    w['metric'].insert(0, str(iface['metric']))
                if iface.get('speed'):
                    w['speed'].set(iface['speed'])
                if iface.get('duplex'):
                    w['duplex'].set(iface['duplex'])
                if iface.get('autoneg'):
                    w['autoneg'].set(iface['autoneg'])
        
        # Загружаем маршруты
        for route in self.app.data.network_routes:
            self.add_route()
            if self.route_widgets:
                w = self.route_widgets[-1]
                w['iface_name'].set(route.get('iface_name', ''))
                if route.get('net'):
                    w['net'].insert(0, route['net'])
                if route.get('netmask'):
                    w['netmask'].insert(0, route['netmask'])
                w['gateway'].insert(0, route.get('gateway', ''))
                w['default_gw_var'].set(route.get('default_gw', False))
                if route.get('metric'):
                    w['metric'].insert(0, str(route['metric']))
        
        # Загружаем ARP
        for arp in self.app.data.network_arp:
            self.add_arp()
            if self.arp_widgets:
                w = self.arp_widgets[-1]
                w['ip'].insert(0, arp.get('ip', ''))
                w['mac'].insert(0, arp.get('mac', ''))


class ExtensionsPage(BasePage):
    """Страница EXTENSIONS."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app, "EXTENSIONS")
        
        # Заголовок
        title_label = ctk.CTkLabel(self, text="Секция EXTENSIONS", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # Создаем вкладки
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.general_tab = self.tabview.add("Общие")
        self.contexts_tab = self.tabview.add("Контексты")
        
        # Инициализация вкладок
        self._init_general_tab()
        self._init_contexts_tab()
        
        # Хранилище для виджетов контекстов
        self.context_widgets = []
        
    def _init_general_tab(self):
        """Инициализация вкладки общих настроек."""
        # GENERAL параметры
        gen_frame = ctk.CTkFrame(self.general_tab)
        gen_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(gen_frame, text="Параметры GENERAL", font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w", padx=10, pady=10)
        
        # STATIC
        self.static_var = ctk.BooleanVar(value=False)
        static_cb = ctk.CTkCheckBox(gen_frame, text="STATIC", variable=self.static_var)
        static_cb.pack(anchor="w", padx=20, pady=5)
        self.add_tooltip(static_cb, "Статический план набора (не перезаписывается)")
        
        # WRITEPROTECT
        self.writeprotect_var = ctk.BooleanVar(value=False)
        writeprotect_cb = ctk.CTkCheckBox(gen_frame, text="WRITEPROTECT", variable=self.writeprotect_var)
        writeprotect_cb.pack(anchor="w", padx=20, pady=5)
        self.add_tooltip(writeprotect_cb, "Защита от записи")
        
        # CLEARGLOBALVARS
        self.clearglobalvars_var = ctk.BooleanVar(value=False)
        clearglobalvars_cb = ctk.CTkCheckBox(gen_frame, text="CLEARGLOBALVARS", variable=self.clearglobalvars_var)
        clearglobalvars_cb.pack(anchor="w", padx=20, pady=5)
        self.add_tooltip(clearglobalvars_cb, "Очищать глобальные переменные")
        
        # AUTOFALLTHROUGH
        self.autofallthrough_var = ctk.BooleanVar(value=True)
        autofallthrough_cb = ctk.CTkCheckBox(gen_frame, text="AUTOFALLTHROUGH", variable=self.autofallthrough_var)
        autofallthrough_cb.pack(anchor="w", padx=20, pady=5)
        self.add_tooltip(autofallthrough_cb, "Автоматический переход к следующему приоритету")
        
        # GLOBALS
        globals_frame = ctk.CTkFrame(self.general_tab)
        globals_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(globals_frame, text="Глобальные переменные (GLOBALS)", font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w", padx=10, pady=10)
        
        add_global_btn = ctk.CTkButton(globals_frame, text="Добавить переменную", command=self.add_global)
        add_global_btn.pack(anchor="w", padx=10, pady=5)
        
        self.globals_scroll = ctk.CTkScrollableFrame(globals_frame)
        self.globals_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.global_widgets = []
        
    def _init_contexts_tab(self):
        """Инициализация вкладки контекстов."""
        add_context_btn = ctk.CTkButton(self.contexts_tab, text="Добавить контекст", command=self.add_context)
        add_context_btn.pack(anchor="w", padx=10, pady=10)
        self.add_tooltip(add_context_btn, "Добавить новый контекст (EXTENGROUP)")
        
        self.contexts_scroll = ctk.CTkScrollableFrame(self.contexts_tab)
        self.contexts_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
    def add_global(self):
        """Добавить глобальную переменную."""
        global_frame = ctk.CTkFrame(self.globals_scroll)
        global_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(global_frame, text="Имя:").pack(side="left", padx=5)
        var_entry = ctk.CTkEntry(global_frame, width=150, placeholder_text="VAR")
        var_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(global_frame, text="=").pack(side="left", padx=5)
        val_entry = ctk.CTkEntry(global_frame, width=200, placeholder_text="значение")
        val_entry.pack(side="left", padx=5)
        
        del_btn = ctk.CTkButton(global_frame, text="X", width=30, command=lambda f=global_frame: self.remove_global(f))
        del_btn.pack(side="left", padx=5)
        
        self.global_widgets.append({'frame': global_frame, 'var': var_entry, 'value': val_entry})
        
    def remove_global(self, frame):
        """Удалить глобальную переменную."""
        for i, w in enumerate(self.global_widgets):
            if w['frame'] == frame:
                frame.destroy()
                del self.global_widgets[i]
                break
                
    def add_context(self):
        """Добавить контекст."""
        context_frame = ctk.CTkFrame(self.contexts_scroll)
        context_frame.pack(fill="x", padx=10, pady=10)
        
        # Заголовок
        header_frame = ctk.CTkFrame(context_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Контекст:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        name_entry = ctk.CTkEntry(header_frame, width=200, placeholder_text="имя_контекста")
        name_entry.pack(side="left", padx=5)
        
        del_btn = ctk.CTkButton(header_frame, text="Удалить контекст", command=lambda f=context_frame: self.remove_context(f))
        del_btn.pack(side="right", padx=5)
        
        # Таблица расширений
        extens_frame = ctk.CTkFrame(context_frame)
        extens_frame.pack(fill="x", padx=10, pady=5)
        
        add_exten_btn = ctk.CTkButton(extens_frame, text="Добавить расширение", command=lambda: self.add_exten(extens_scroll))
        add_exten_btn.pack(anchor="w", padx=5, pady=5)
        
        extens_scroll = ctk.CTkScrollableFrame(extens_frame)
        extens_scroll.pack(fill="x", padx=5, pady=5)
        
        self.context_widgets.append({
            'frame': context_frame,
            'name': name_entry,
            'extens_scroll': extens_scroll,
            'exten_widgets': []
        })
        
    def add_exten(self, scroll_frame):
        """Добавить расширение в контекст."""
        exten_frame = ctk.CTkFrame(scroll_frame)
        exten_frame.pack(fill="x", padx=5, pady=3)
        
        # Поле 1 - маска/номер
        ctk.CTkLabel(exten_frame, text="Маска/номер:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        field1_entry = ctk.CTkEntry(exten_frame, width=150, placeholder_text="_1XX или 101")
        field1_entry.grid(row=0, column=1, padx=5, pady=2)
        self.add_tooltip(field1_entry, 
            "Номер или маска расширения.\n"
            "Примеры: 101, _1XX, _20[1-5], _XXX.\n"
            "X - любая цифра, Z - 1-9, N - 2-9, . - любое количество цифр")
        
        # Поле 2 - каналы/команды
        ctk.CTkLabel(exten_frame, text="Каналы/команды:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        field2_entry = ctk.CTkEntry(exten_frame, width=200, placeholder_text="SIP/101 или Dial(SIP/101)")
        field2_entry.grid(row=0, column=3, padx=5, pady=2)
        self.add_tooltip(field2_entry,
            "Каналы: SIP/101,Zap/1\n"
            "Команды: Dial(SIP/101),Answer,Hangup()")
        
        # Поле 3 - опционально (макс. соединений)
        ctk.CTkLabel(exten_frame, text="Макс. соед. (опц.):").grid(row=0, column=4, sticky="w", padx=5, pady=2)
        field3_entry = ctk.CTkEntry(exten_frame, width=80, placeholder_text="")
        field3_entry.grid(row=0, column=5, padx=5, pady=2)
        
        # Поле 4 - опционально (приоритетные каналы)
        ctk.CTkLabel(exten_frame, text="Приор. каналы (опц.):").grid(row=0, column=6, sticky="w", padx=5, pady=2)
        field4_entry = ctk.CTkEntry(exten_frame, width=150, placeholder_text="")
        field4_entry.grid(row=0, column=7, padx=5, pady=2)
        
        del_btn = ctk.CTkButton(exten_frame, text="X", width=30, command=lambda f=exten_frame, sf=scroll_frame: self.remove_exten(f, sf))
        del_btn.grid(row=0, column=8, padx=5, pady=2)
        
        # Находим родительский контекст
        context_idx = None
        for i, cw in enumerate(self.context_widgets):
            if cw['extens_scroll'] == scroll_frame:
                context_idx = i
                break
        
        if context_idx is not None:
            self.context_widgets[context_idx]['exten_widgets'].append({
                'frame': exten_frame,
                'field1': field1_entry,
                'field2': field2_entry,
                'field3': field3_entry,
                'field4': field4_entry
            })
            
    def remove_exten(self, frame, scroll_frame):
        """Удалить расширение."""
        for i, cw in enumerate(self.context_widgets):
            if cw['extens_scroll'] == scroll_frame:
                for j, ew in enumerate(cw['exten_widgets']):
                    if ew['frame'] == frame:
                        frame.destroy()
                        del cw['exten_widgets'][j]
                        return
                        
    def remove_context(self, frame):
        """Удалить контекст."""
        for i, cw in enumerate(self.context_widgets):
            if cw['frame'] == frame:
                frame.destroy()
                del self.context_widgets[i]
                break
    
    def validate(self) -> tuple:
        # Проверяем наличие хотя бы одного контекста
        if not self.context_widgets:
            return False, "Требуется хотя бы один контекст (EXTENGROUP)"
        
        # Проверяем каждый контекст
        for i, cw in enumerate(self.context_widgets):
            name = cw['name'].get().strip()
            if not name:
                cw['name'].configure(border_color="red")
                return False, f"Контекст {i+1}: имя не может быть пустым"
            cw['name'].configure(border_color="gray")
            
            # Проверяем наличие хотя бы одного расширения
            if not cw['exten_widgets']:
                return False, f"Контекст '{name}': требуется хотя бы одно расширение"
            
            # Валидация расширений
            for j, ew in enumerate(cw['exten_widgets']):
                field1 = ew['field1'].get().strip()
                if not field1:
                    ew['field1'].configure(border_color="red")
                    return False, f"Контекст '{name}', расширение {j+1}: маска/номер обязательны"
                
                valid, msg = validate_extension_mask(field1)
                if not valid:
                    ew['field1'].configure(border_color="red")
                    return False, f"Контекст '{name}', расширение {j+1}: {msg}"
                ew['field1'].configure(border_color="gray")
                
                field2 = ew['field2'].get().strip()
                if not field2:
                    ew['field2'].configure(border_color="red")
                    return False, f"Контекст '{name}', расширение {j+1}: каналы/команды обязательны"
                ew['field2'].configure(border_color="gray")
        
        return True, ""
    
    def save_data(self):
        # Сохраняем GENERAL
        self.app.data.extensions_general['static'] = self.static_var.get()
        self.app.data.extensions_general['writeprotect'] = self.writeprotect_var.get()
        self.app.data.extensions_general['clearglobalvars'] = self.clearglobalvars_var.get()
        self.app.data.extensions_general['autofallthrough'] = self.autofallthrough_var.get()
        
        # Сохраняем GLOBALS
        self.app.data.extensions_globals = []
        for gw in self.global_widgets:
            var = gw['var'].get().strip()
            val = gw['value'].get().strip()
            if var:
                self.app.data.extensions_globals.append({'var': var, 'value': val})
        
        # Сохраняем контексты
        self.app.data.extensions_groups = []
        for cw in self.context_widgets:
            group = {
                'name': cw['name'].get().strip(),
                'extens': []
            }
            
            for ew in cw['exten_widgets']:
                exten = {
                    'field1': ew['field1'].get().strip(),
                    'field2': ew['field2'].get().strip(),
                    'field3': ew['field3'].get().strip(),
                    'field4': ew['field4'].get().strip()
                }
                group['extens'].append(exten)
            
            self.app.data.add_extension_group(group)
    
    def load_data(self):
        # Очищаем текущие виджеты
        for gw in self.global_widgets:
            gw['frame'].destroy()
        self.global_widgets = []
        
        for cw in self.context_widgets:
            cw['frame'].destroy()
        self.context_widgets = []
        
        # Загружаем GENERAL
        self.static_var.set(self.app.data.extensions_general.get('static', False))
        self.writeprotect_var.set(self.app.data.extensions_general.get('writeprotect', False))
        self.clearglobalvars_var.set(self.app.data.extensions_general.get('clearglobalvars', False))
        self.autofallthrough_var.set(self.app.data.extensions_general.get('autofallthrough', True))
        
        # Загружаем GLOBALS
        for glob in self.app.data.extensions_globals:
            self.add_global()
            if self.global_widgets:
                gw = self.global_widgets[-1]
                gw['var'].insert(0, glob.get('var', ''))
                gw['value'].insert(0, glob.get('value', ''))
        
        # Загружаем контексты
        for group in self.app.data.extensions_groups:
            self.add_context()
            if self.context_widgets:
                cw = self.context_widgets[-1]
                cw['name'].insert(0, group.get('name', ''))
                
                for exten in group.get('extens', []):
                    self.add_exten(cw['extens_scroll'])
                    if cw['exten_widgets']:
                        ew = cw['exten_widgets'][-1]
                        ew['field1'].insert(0, exten.get('field1', ''))
                        ew['field2'].insert(0, exten.get('field2', ''))
                        if exten.get('field3'):
                            ew['field3'].insert(0, exten['field3'])
                        if exten.get('field4'):
                            ew['field4'].insert(0, exten['field4'])


class PreviewPage(BasePage):
    """Страница предпросмотра конфигурации."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app, "PREVIEW")
        
        # Заголовок
        title_label = ctk.CTkLabel(self, text="Предпросмотр конфигурации", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # Текстовое поле для предпросмотра
        self.preview_text = ctk.CTkTextbox(self, width=800, height=500)
        self.preview_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Кнопка обновления
        refresh_btn = ctk.CTkButton(self, text="Обновить предпросмотр", command=self.update_preview)
        refresh_btn.pack(pady=10)
        
    def update_preview(self):
        """Обновить предпросмотр."""
        # Сначала сохраняем данные со всех страниц
        self.app.save_current_page_data()
        
        # Генерируем конфиг
        generator = ConfigGenerator(self.app.data)
        config_text = generator.generate()
        
        # Отображаем
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", config_text)
    
    def validate(self) -> tuple:
        return True, ""
    
    def save_data(self):
        pass
    
    def load_data(self):
        self.update_preview()


class App(ctk.CTk):
    """Главное приложение."""
    
    PAGES = [
        ("SYSTEM", SystemPage),
        ("NTP", NtpPage),
        ("NETWORK", NetworkPage),
        ("EXTENSIONS", ExtensionsPage),
        ("PREVIEW", PreviewPage),
    ]
    
    def __init__(self):
        super().__init__()
        
        self.title("Мастер конфигурации IP-АТС Т76-С")
        self.geometry("900x700")
        
        self.data = ConfigData()
        self.current_page_index = 0
        self.pages = {}
        
        # Верхняя панель с прогрессом
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress_label = ctk.CTkLabel(self.top_frame, text="", font=ctk.CTkFont(size=14))
        self.progress_label.pack(side="left", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.top_frame, width=400)
        self.progress_bar.pack(side="left", padx=20)
        self.progress_bar.set(0)
        
        # Контейнер для страниц
        self.page_container = ctk.CTkFrame(self)
        self.page_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Нижняя панель с кнопками
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.pack(fill="x", padx=10, pady=10)
        
        self.prev_btn = ctk.CTkButton(self.bottom_frame, text="Назад", command=self.prev_page, state="disabled")
        self.prev_btn.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(self.bottom_frame, text="Далее", command=self.next_page)
        self.next_btn.pack(side="left", padx=5)
        
        self.cancel_btn = ctk.CTkButton(self.bottom_frame, text="Отмена", command=self.cancel, fg_color="gray")
        self.cancel_btn.pack(side="right", padx=5)
        
        self.help_btn = ctk.CTkButton(self.bottom_frame, text="Справка", command=self.show_help, fg_color="gray")
        self.help_btn.pack(side="right", padx=5)
        
        # Создаем все страницы
        for page_name, page_class in self.PAGES:
            page = page_class(self.page_container, self)
            self.pages[page_name] = page
        
        # Показываем первую страницу
        self.show_page(0)
        
    def show_page(self, index: int):
        """Показать страницу по индексу."""
        if index < 0 or index >= len(self.PAGES):
            return
        
        # Сохраняем данные текущей страницы перед переключением
        if 0 <= self.current_page_index < len(self.PAGES):
            current_page_name = self.PAGES[self.current_page_index][0]
            self.pages[current_page_name].save_data()
        
        self.current_page_index = index
        page_name, _ = self.PAGES[index]
        
        # Скрываем все страницы
        for page in self.pages.values():
            page.pack_forget()
        
        # Показываем нужную страницу
        self.pages[page_name].pack(fill="both", expand=True)
        
        # Загружаем данные
        self.pages[page_name].load_data()
        
        # Обновляем заголовок и прогресс
        total = len(self.PAGES)
        self.progress_label.configure(text=f"Шаг {index + 1} из {total}: {page_name}")
        self.progress_bar.set((index + 1) / total)
        
        # Обновляем кнопки
        self.prev_btn.configure(state="normal" if index > 0 else "disabled")
        
        if index == len(self.PAGES) - 1:
            self.next_btn.configure(text="Сохранить файл", command=self.save_config)
        else:
            self.next_btn.configure(text="Далее", command=self.next_page)
            
        # Обновляем предпросмотр если это последняя страница
        if page_name == "PREVIEW":
            self.pages["PREVIEW"].update_preview()
    
    def prev_page(self):
        """Перейти на предыдущую страницу."""
        if self.current_page_index > 0:
            self.show_page(self.current_page_index - 1)
    
    def next_page(self):
        """Перейти на следующую страницу после валидации."""
        # Валидация текущей страницы
        current_page_name = self.PAGES[self.current_page_index][0]
        current_page = self.pages[current_page_name]
        
        valid, error_msg = current_page.validate()
        if not valid:
            messagebox.showerror("Ошибка валидации", error_msg)
            return
        
        # Сохраняем данные
        current_page.save_data()
        
        # Переходим дальше
        if self.current_page_index < len(self.PAGES) - 1:
            self.show_page(self.current_page_index + 1)
    
    def save_current_page_data(self):
        """Сохранить данные текущей страницы."""
        if 0 <= self.current_page_index < len(self.PAGES):
            page_name = self.PAGES[self.current_page_index][0]
            self.pages[page_name].save_data()
    
    def save_config(self):
        """Сохранить конфигурационный файл."""
        # Финальная валидация
        for page_name, page_class in self.PAGES:
            if page_name != "PREVIEW":
                page = self.pages[page_name]
                valid, error_msg = page.validate()
                if not valid:
                    # Находим индекс страницы и переходим на неё
                    for i, (pn, _) in enumerate(self.PAGES):
                        if pn == page_name:
                            self.show_page(i)
                            break
                    messagebox.showerror("Ошибка валидации", error_msg)
                    return
        
        # Сохраняем все данные
        for page_name, _ in self.PAGES:
            if page_name != "PREVIEW":
                self.pages[page_name].save_data()
        
        # Обновляем справочники ссылочной целостности
        self.data.update_zapata_groups()
        self.data.update_iax_names()
        self.data.update_sip_numbers()
        
        # Генерируем конфиг
        generator = ConfigGenerator(self.data)
        config_text = generator.generate()
        
        # Диалог сохранения
        default_filename = f"{self.data.system['hostname']}.conf"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".conf",
            filetypes=[("Config files", "*.conf"), ("All files", "*.*")],
            initialfile=default_filename,
            title="Сохранить конфигурационный файл"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(config_text)
                
                messagebox.showinfo("Успех", f"Конфигурационный файл успешно сохранен:\n{filepath}")
                
                # Предлагаем начать заново или выйти
                result = messagebox.askyesno("Завершение", "Создать новую конфигурацию?")
                if result:
                    self.reset_and_start_over()
                else:
                    self.quit()
                    
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
    
    def reset_and_start_over(self):
        """Сбросить все данные и начать сначала."""
        self.data.reset()
        self.show_page(0)
    
    def cancel(self):
        """Отменить и выйти."""
        result = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите выйти без сохранения?")
        if result:
            self.quit()
    
    def show_help(self):
        """Показать справку."""
        page_name = self.PAGES[self.current_page_index][0]
        
        help_texts = {
            "SYSTEM": "Секция SYSTEM содержит базовые настройки АТС.\n\nHOSTNAME - имя устройства в сети.\nДопустимы латинские буквы, цифры, символы '_', '-', '.'\nМаксимальная длина - 63 символа.",
            "NTP": "Секция NTP настраивает синхронизацию времени.\n\nIP_SRV - IP-адрес NTP-сервера.\nINTERVAL - интервал опроса в секундах (60-86400).",
            "NETWORK": "Секция NETWORK настраивает сетевые интерфейсы, маршруты и ARP.\n\nIFACE - сетевой интерфейс (eth0, eth1 и т.д.)\nROUTE - статические маршруты\nARP - статические ARP записи",
            "EXTENSIONS": "Секция EXTENSIONS определяет план набора.\n\nGENERAL - общие настройки плана набора.\nGLOBALS - глобальные переменные.\nEXTENGROUP - контексты с расширениями.",
            "PREVIEW": "Предпросмотр готового конфигурационного файла.\n\nПроверьте содержимое и нажмите 'Сохранить файл'."
        }
        
        help_text = help_texts.get(page_name, "Справка по текущей секции.")
        messagebox.showinfo(f"Справка: {page_name}", help_text)


if __name__ == "__main__":
    app = App()
    app.mainloop()


