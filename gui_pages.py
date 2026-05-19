# -*- coding: utf-8 -*-
"""
Мастер конфигурации IP-АТС Т76-С - Графический интерфейс
Версия: 1.0
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import sys
from typing import Dict, List, Any, Optional, Callable
from config_master import ConfigData, ConfigGenerator, validate_hostname, validate_ipv4, validate_netmask, validate_mac, validate_iface_name, validate_integer, validate_exten_mask


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ВИДЖЕТЫ
# ============================================================================

class ToolTip:
    """Всплывающая подсказка."""
    
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        
        x = self.widget.winfo_rootx() + 30
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(
            tw, 
            text=self.text, 
            justify="left",
            wraplength=300,
            fg_color="#333333",
            text_color="white"
        )
        label.pack(padx=8, pady=8)
        
        # Поверх всех окон
        tw.attributes("-topmost", True)
    
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def set_text(self, text: str):
        self.text = text


def create_labeled_entry(parent, label_text: str, tooltip: str = "", default: str = "", **kwargs) -> tuple:
    """Создаёт подписанное поле ввода с подсказкой."""
    frame = ctk.CTkFrame(parent)
    frame.pack(fill="x", pady=5)
    
    label = ctk.CTkLabel(frame, text=label_text, anchor="w")
    label.pack(side="left", padx=(0, 10))
    
    entry = ctk.CTkEntry(frame, width=200, **kwargs)
    entry.pack(side="right", fill="x", expand=True)
    
    if default:
        entry.insert(0, default)
    
    if tooltip:
        ToolTip(entry, tooltip)
        ToolTip(label, tooltip)
    
    return frame, entry


def create_labeled_combobox(parent, label_text: str, values: list, tooltip: str = "", default: str = "", **kwargs) -> tuple:
    """Создаёт подписанный выпадающий список с подсказкой."""
    frame = ctk.CTkFrame(parent)
    frame.pack(fill="x", pady=5)
    
    label = ctk.CTkLabel(frame, text=label_text, anchor="w")
    label.pack(side="left", padx=(0, 10))
    
    combo = ctk.CTkComboBox(frame, values=values, width=200, **kwargs)
    combo.pack(side="right", fill="x", expand=True)
    
    if default and default in values:
        combo.set(default)
    elif values:
        combo.set(values[0])
    
    if tooltip:
        ToolTip(combo, tooltip)
        ToolTip(label, tooltip)
    
    return frame, combo


def create_labeled_checkbox(parent, label_text: str, tooltip: str = "", default: bool = False, **kwargs) -> tuple:
    """Создаёт чекбокс с подписью и подсказкой."""
    frame = ctk.CTkFrame(parent)
    frame.pack(fill="x", pady=5)
    
    checkbox = ctk.CTkCheckBox(frame, text=label_text, **kwargs)
    checkbox.pack(side="left")
    
    if default:
        checkbox.select()
    
    if tooltip:
        ToolTip(checkbox, tooltip)
    
    return frame, checkbox


# ============================================================================
# БАЗОВЫЙ КЛАСС СТРАНИЦЫ
# ============================================================================

class Page(ctk.CTkFrame):
    """Базовый класс для страницы мастера."""
    
    TITLE = "Страница"
    TOOLTIP = ""
    IS_OPTIONAL = False
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent)
        self.config_data = config_data
        self.app = app
        self.error_messages = []
    
    def load_data(self):
        """Загружает данные из ConfigData в элементы интерфейса."""
        pass
    
    def save_data(self):
        """Сохраняет данные из элементов интерфейса в ConfigData."""
        pass
    
    def validate(self) -> bool:
        """Проверяет корректность данных. Возвращает True если всё OK."""
        self.error_messages = []
        return True
    
    def get_error_messages(self) -> List[str]:
        return self.error_messages


# ============================================================================
# СТРАНИЦА 1: SYSTEM
# ============================================================================

class SystemPage(Page):
    TITLE = "SYSTEM"
    TOOLTIP = "Основные настройки системы"
    IS_OPTIONAL = False
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        # Заголовок
        title = ctk.CTkLabel(self, text="Настройки системы (SYSTEM)", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20)
        
        # Описание
        desc = ctk.CTkLabel(
            self, 
            text="Укажите имя хоста для IP-АТС. Это имя будет использоваться в домене.",
            wraplength=600,
            justify="left"
        )
        desc.pack(pady=10)
        
        # Поле HOSTNAME
        self.hostname_frame, self.hostname_entry = create_labeled_entry(
            self,
            "Имя хоста (HOSTNAME):",
            tooltip="Имя устройства в домене, только латиница, цифры, дефис, подчёркивание, точка. Максимум 63 символа. Пример: ats1",
            default=config_data.system.get('HOSTNAME', 'ats1')
        )
    
    def save_data(self):
        hostname = self.hostname_entry.get().strip()
        self.config_data.system['HOSTNAME'] = hostname if hostname else 'ats1'
    
    def validate(self) -> bool:
        self.error_messages = []
        hostname = self.hostname_entry.get().strip()
        
        valid, msg = validate_hostname(hostname)
        if not valid:
            self.error_messages.append(msg)
            self.hostname_entry.configure(border_color="red")
        else:
            self.hostname_entry.configure(border_color=None)
        
        return len(self.error_messages) == 0


# ============================================================================
# СТРАНИЦА 2: NTP
# ============================================================================

class NtpPage(Page):
    TITLE = "NTP"
    TOOLTIP = "Настройки синхронизации времени"
    IS_OPTIONAL = True
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        title = ctk.CTkLabel(self, text="Настройки NTP", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20)
        
        desc = ctk.CTkLabel(
            self, 
            text="Настройте синхронизацию времени с NTP-сервером. Оставьте пустым, если не требуется.",
            wraplength=600,
            justify="left"
        )
        desc.pack(pady=10)
        
        # Флажок использования NTP
        self.use_ntp_var = ctk.BooleanVar(value=config_data.ntp is not None)
        self.use_ntp_cb = ctk.CTkCheckBox(
            self, 
            text="Использовать NTP",
            variable=self.use_ntp_var,
            command=self._toggle_fields
        )
        self.use_ntp_cb.pack(pady=10)
        
        # Контейнер для полей
        self.fields_frame = ctk.CTkFrame(self)
        self.fields_frame.pack(fill="x", padx=20)
        
        if config_data.ntp:
            ip_srv = config_data.ntp.get('IP_SRV', '')
            interval = str(config_data.ntp.get('INTERVAL', '14400'))
        else:
            ip_srv = ''
            interval = '14400'
        
        self.ip_frame, self.ip_entry = create_labeled_entry(
            self.fields_frame,
            "IP сервера (IP_SRV):",
            tooltip="IPv4 адрес NTP сервера. Пример: 192.168.1.1",
            default=ip_srv
        )
        
        self.interval_frame, self.interval_entry = create_labeled_entry(
            self.fields_frame,
            "Интервал (INTERVAL):",
            tooltip="Интервал синхронизации в секундах (60-86400). По умолчанию: 14400",
            default=interval
        )
        
        self._toggle_fields()
    
    def _toggle_fields(self):
        state = "normal" if self.use_ntp_var.get() else "disabled"
        for child in self.fields_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, (ctk.CTkEntry, ctk.CTkLabel)):
                    widget.configure(state=state if hasattr(widget, 'configure') else "normal")
    
    def save_data(self):
        if self.use_ntp_var.get():
            self.config_data.ntp = {
                'IP_SRV': self.ip_entry.get().strip(),
                'INTERVAL': self.interval_entry.get().strip()
            }
        else:
            self.config_data.ntp = None
    
    def validate(self) -> bool:
        self.error_messages = []
        
        if not self.use_ntp_var.get():
            return True
        
        ip = self.ip_entry.get().strip()
        interval = self.interval_entry.get().strip()
        
        if ip:
            valid, msg = validate_ipv4(ip)
            if not valid:
                self.error_messages.append(f"NTP IP: {msg}")
                self.ip_entry.configure(border_color="red")
            else:
                self.ip_entry.configure(border_color=None)
        
        if interval:
            valid, msg = validate_integer(interval, 60, 86400)
            if not valid:
                self.error_messages.append(f"NTP INTERVAL: {msg}")
                self.interval_entry.configure(border_color="red")
            else:
                self.interval_entry.configure(border_color=None)
        
        return len(self.error_messages) == 0


# ============================================================================
# СТРАНИЦА 3: NETWORK
# ============================================================================

class NetworkPage(Page):
    TITLE = "NETWORK"
    TOOLTIP = "Настройки сети"
    IS_OPTIONAL = False
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        title = ctk.CTkLabel(self, text="Настройки сети (NETWORK)", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        # Создаём вкладки для IFACE, ROUTE, ARP
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.iface_tab = self.tabview.add("Интерфейсы (IFACE)")
        self.route_tab = self.tabview.add("Маршруты (ROUTE)")
        self.arp_tab = self.tabview.add("ARP")
        
        # Интерфейсы
        self.iface_list_frame = ctk.CTkScrollableFrame(self.iface_tab)
        self.iface_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.ifaces = []  # Список фреймов интерфейсов
        
        add_iface_btn = ctk.CTkButton(
            self.iface_tab, 
            text="Добавить интерфейс", 
            command=self._add_iface
        )
        add_iface_btn.pack(pady=5)
        
        # Маршруты
        self.route_list_frame = ctk.CTkScrollableFrame(self.route_tab)
        self.route_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.routes = []
        
        add_route_btn = ctk.CTkButton(
            self.route_tab,
            text="Добавить маршрут",
            command=self._add_route
        )
        add_route_btn.pack(pady=5)
        
        # ARP
        self.arp_list_frame = ctk.CTkScrollableFrame(self.arp_tab)
        self.arp_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.arps = []
        
        add_arp_btn = ctk.CTkButton(
            self.arp_tab,
            text="Добавить ARP запись",
            command=self._add_arp
        )
        add_arp_btn.pack(pady=5)
        
        # Загрузка данных
        self._load_ifaces()
        self._load_routes()
        self._load_arps()
    
    def _add_iface(self):
        """Добавляет новый интерфейс."""
        frame = ctk.CTkFrame(self.iface_list_frame)
        frame.pack(fill="x", pady=5)
        
        iface_data = {}
        
        # Название
        _, name_entry = create_labeled_entry(
            frame, "Имя:",
            tooltip="eth0, eth1, eth0:0..eth0:9, eth1:0..eth1:9",
            default="eth0"
        )
        iface_data['name'] = name_entry
        
        # IP
        _, ip_entry = create_labeled_entry(
            frame, "IP:",
            tooltip="IPv4 адрес интерфейса",
            default=""
        )
        iface_data['ip'] = ip_entry
        
        # Маска
        _, mask_entry = create_labeled_entry(
            frame, "Маска:",
            tooltip="Маска подсети, например 255.255.255.0",
            default="255.255.255.0"
        )
        iface_data['mask'] = mask_entry
        
        # MTU
        _, mtu_entry = create_labeled_entry(
            frame, "MTU:",
            tooltip="Максимальный размер пакета (68-1500)",
            default="1500"
        )
        iface_data['mtu'] = mtu_entry
        
        # Метрика
        _, metric_entry = create_labeled_entry(
            frame, "Метрика:",
            tooltip="Метрика интерфейса (0-65535)",
            default="1"
        )
        iface_data['metric'] = metric_entry
        
        # Удалить
        del_btn = ctk.CTkButton(frame, text="Удалить", width=80, command=lambda: self._remove_iface(frame))
        del_btn.pack(pady=5)
        
        self.ifaces.append((frame, iface_data))
    
    def _remove_iface(self, frame):
        for i, (f, _) in enumerate(self.ifaces):
            if f == frame:
                frame.destroy()
                self.ifaces.pop(i)
                break
    
    def _add_route(self):
        """Добавляет новый маршрут."""
        frame = ctk.CTkFrame(self.route_list_frame)
        frame.pack(fill="x", pady=5)
        
        route_data = {}
        
        # Интерфейс
        _, iface_entry = create_labeled_entry(
            frame, "Интерфейс:",
            tooltip="Имя интерфейса для маршрута",
            default="eth0"
        )
        route_data['iface'] = iface_entry
        
        # Сеть
        _, net_entry = create_labeled_entry(
            frame, "Сеть:",
            tooltip="IP сети назначения (оставьте пустым для шлюза по умолчанию)",
            default=""
        )
        route_data['net'] = net_entry
        
        # Маска
        _, mask_entry = create_labeled_entry(
            frame, "Маска:",
            tooltip="Маска сети",
            default="255.255.255.0"
        )
        route_data['mask'] = mask_entry
        
        # Шлюз
        _, gw_entry = create_labeled_entry(
            frame, "Шлюз:",
            tooltip="IP шлюза",
            default=""
        )
        route_data['gw'] = gw_entry
        
        # Шлюз по умолчанию
        default_gw_var = ctk.BooleanVar(value=False)
        default_gw_cb = ctk.CTkCheckBox(frame, text="Шлюз по умолчанию", variable=default_gw_var)
        default_gw_cb.pack(pady=5)
        route_data['default_gw'] = default_gw_var
        
        # Метрика
        _, metric_entry = create_labeled_entry(
            frame, "Метрика:",
            tooltip="Метрика маршрута",
            default="1"
        )
        route_data['metric'] = metric_entry
        
        # Удалить
        del_btn = ctk.CTkButton(frame, text="Удалить", width=80, command=lambda: self._remove_route(frame))
        del_btn.pack(pady=5)
        
        self.routes.append((frame, route_data))
    
    def _remove_route(self, frame):
        for i, (f, _) in enumerate(self.routes):
            if f == frame:
                frame.destroy()
                self.routes.pop(i)
                break
    
    def _add_arp(self):
        """Добавляет ARP запись."""
        frame = ctk.CTkFrame(self.arp_list_frame)
        frame.pack(fill="x", pady=5)
        
        arp_data = {}
        
        _, ip_entry = create_labeled_entry(
            frame, "IP:",
            tooltip="IPv4 адрес",
            default=""
        )
        arp_data['ip'] = ip_entry
        
        _, mac_entry = create_labeled_entry(
            frame, "MAC:",
            tooltip="MAC адрес в формате XX:XX:XX:XX:XX:XX",
            default=""
        )
        arp_data['mac'] = mac_entry
        
        del_btn = ctk.CTkButton(frame, text="Удалить", width=80, command=lambda: self._remove_arp(frame))
        del_btn.pack(pady=5)
        
        self.arps.append((frame, arp_data))
    
    def _remove_arp(self, frame):
        for i, (f, _) in enumerate(self.arps):
            if f == frame:
                frame.destroy()
                self.arps.pop(i)
                break
    
    def _load_ifaces(self):
        for iface in self.config_data.network.get('IFACE', []):
            self._add_iface()
            if self.ifaces:
                frame, data = self.ifaces[-1]
                data['name'].delete(0, 'end')
                data['name'].insert(0, iface.get('IFACE_NAME', 'eth0'))
                data['ip'].delete(0, 'end')
                data['ip'].insert(0, iface.get('IP', ''))
                data['mask'].delete(0, 'end')
                data['mask'].insert(0, iface.get('NETMASK', '255.255.255.0'))
                data['mtu'].delete(0, 'end')
                data['mtu'].insert(0, str(iface.get('MTU', '1500')))
                data['metric'].delete(0, 'end')
                data['metric'].insert(0, str(iface.get('METRIC', '1')))
    
    def _load_routes(self):
        for route in self.config_data.network.get('ROUTE', []):
            self._add_route()
            if self.routes:
                frame, data = self.routes[-1]
                data['iface'].delete(0, 'end')
                data['iface'].insert(0, route.get('IFACE_NAME', 'eth0'))
                data['net'].delete(0, 'end')
                data['net'].insert(0, route.get('NET', ''))
                data['mask'].delete(0, 'end')
                data['mask'].insert(0, route.get('NETMASK', '255.255.255.0'))
                data['gw'].delete(0, 'end')
                data['gw'].insert(0, route.get('GATEWAY', ''))
                data['default_gw'].set(route.get('DEFAULT_GW', False))
                data['metric'].delete(0, 'end')
                data['metric'].insert(0, str(route.get('METRIC', '1')))
    
    def _load_arps(self):
        for arp in self.config_data.network.get('ARP', []):
            self._add_arp()
            if self.arps:
                frame, data = self.arps[-1]
                data['ip'].delete(0, 'end')
                data['ip'].insert(0, arp.get('IP', ''))
                data['mac'].delete(0, 'end')
                data['mac'].insert(0, arp.get('MAC', ''))
    
    def save_data(self):
        # Сохраняем интерфейсы
        self.config_data.network['IFACE'] = []
        for frame, data in self.ifaces:
            iface = {
                'IFACE_NAME': data['name'].get().strip(),
                'IP': data['ip'].get().strip(),
                'NETMASK': data['mask'].get().strip(),
                'MTU': data['mtu'].get().strip(),
                'METRIC': data['metric'].get().strip()
            }
            self.config_data.network['IFACE'].append(iface)
        
        # Сохраняем маршруты
        self.config_data.network['ROUTE'] = []
        for frame, data in self.routes:
            route = {
                'IFACE_NAME': data['iface'].get().strip(),
                'NET': data['net'].get().strip(),
                'NETMASK': data['mask'].get().strip(),
                'GATEWAY': data['gw'].get().strip(),
                'DEFAULT_GW': data['default_gw'].get(),
                'METRIC': data['metric'].get().strip()
            }
            self.config_data.network['ROUTE'].append(route)
        
        # Сохраняем ARP
        self.config_data.network['ARP'] = []
        for frame, data in self.arps:
            arp = {
                'IP': data['ip'].get().strip(),
                'MAC': data['mac'].get().strip()
            }
            self.config_data.network['ARP'].append(arp)
    
    def validate(self) -> bool:
        self.error_messages = []
        
        # Проверяем что есть хотя бы один интерфейс
        if not self.ifaces:
            self.error_messages.append("Необходимо добавить хотя бы один сетевой интерфейс")
            return False
        
        # Валидация интерфейсов
        for frame, data in self.ifaces:
            name = data['name'].get().strip()
            ip = data['ip'].get().strip()
            mask = data['mask'].get().strip()
            mtu = data['mtu'].get().strip()
            metric = data['metric'].get().strip()
            
            valid, msg = validate_iface_name(name)
            if not valid:
                self.error_messages.append(f"IFACE {name}: {msg}")
                data['name'].configure(border_color="red")
            
            if ip:
                valid, msg = validate_ipv4(ip)
                if not valid:
                    self.error_messages.append(f"IFACE {name} IP: {msg}")
                    data['ip'].configure(border_color="red")
            
            if mask:
                valid, msg = validate_netmask(mask)
                if not valid:
                    self.error_messages.append(f"IFACE {name} NETMASK: {msg}")
                    data['mask'].configure(border_color="red")
            
            if mtu:
                valid, msg = validate_integer(mtu, 68, 1500)
                if not valid:
                    self.error_messages.append(f"IFACE {name} MTU: {msg}")
                    data['mtu'].configure(border_color="red")
            
            if metric:
                valid, msg = validate_integer(metric, 0, 65535)
                if not valid:
                    self.error_messages.append(f"IFACE {name} METRIC: {msg}")
                    data['metric'].configure(border_color="red")
        
        # Валидация маршрутов
        default_gw_count = 0
        for frame, data in self.routes:
            default_gw = data['default_gw'].get()
            if default_gw:
                default_gw_count += 1
            
            net = data['net'].get().strip()
            mask = data['mask'].get().strip()
            gw = data['gw'].get().strip()
            
            if net and not default_gw:
                valid, msg = validate_ipv4(net)
                if not valid:
                    self.error_messages.append(f"ROUTE NET: {msg}")
                    data['net'].configure(border_color="red")
            
            if mask:
                valid, msg = validate_netmask(mask)
                if not valid:
                    self.error_messages.append(f"ROUTE NETMASK: {msg}")
                    data['mask'].configure(border_color="red")
            
            if gw:
                valid, msg = validate_ipv4(gw)
                if not valid:
                    self.error_messages.append(f"ROUTE GATEWAY: {msg}")
                    data['gw'].configure(border_color="red")
        
        if default_gw_count > 1:
            self.error_messages.append("Только один маршрут может быть шлюзом по умолчанию (DEFAULT_GW=true)")
        
        # Валидация ARP
        for frame, data in self.arps:
            ip = data['ip'].get().strip()
            mac = data['mac'].get().strip()
            
            if ip:
                valid, msg = validate_ipv4(ip)
                if not valid:
                    self.error_messages.append(f"ARP IP: {msg}")
                    data['ip'].configure(border_color="red")
            
            if mac:
                valid, msg = validate_mac(mac)
                if not valid:
                    self.error_messages.append(f"ARP MAC: {msg}")
                    data['mac'].configure(border_color="red")
        
        return len(self.error_messages) == 0
