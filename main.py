# -*- coding: utf-8 -*-
"""
Мастер конфигурации IP-АТС Т76-С - Главный файл приложения
Версия: 2.1
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import sys
from typing import Dict, List, Any, Optional

from config_master import ConfigData, ConfigGenerator, validate_ipv4, validate_netmask, validate_mac, validate_hostname, validate_integer


class Tooltip:
    """Всплывающая подсказка при наведении мыши."""
    
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
        y = self.widget.winfo_rooty() + 30
        
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(
            tw, 
            text=self.text, 
            justify="left",
            wraplength=350,
            font=ctk.CTkFont(size=11)
        )
        label.pack(padx=8, pady=4)
    
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class Page(ctk.CTkScrollableFrame):
    """Базовый класс для всех страниц мастера."""
    
    TITLE = "Страница"
    TOOLTIP = ""
    IS_OPTIONAL = False
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent)
        self.config_data = config_data
        self.app = app
        self.error_messages: List[str] = []
    
    def validate(self) -> bool:
        """Проверяет корректность данных. Возвращает True если всё ок."""
        raise NotImplementedError
    
    def save_data(self):
        """Сохраняет данные из полей в config_data."""
        raise NotImplementedError
    
    def load_data(self):
        """Загружает данные из config_data в поля."""
        pass
    
    def get_error_messages(self) -> List[str]:
        return self.error_messages


class SystemPage(Page):
    """Страница SYSTEM (обязательная)."""
    
    TITLE = "SYSTEM"
    TOOLTIP = "Системные настройки"
    IS_OPTIONAL = False
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        title = ctk.CTkLabel(self, text="Системные настройки (SYSTEM)", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20)
        
        desc = ctk.CTkLabel(
            self,
            text="Укажите имя устройства в домене. Только латиница, цифры, дефис, подчёркивание, точка.\nМаксимум 63 символа.",
            wraplength=600,
            justify="center"
        )
        desc.pack(pady=10)
        
        hostname_frame = ctk.CTkFrame(self)
        hostname_frame.pack(pady=30)
        
        ctk.CTkLabel(hostname_frame, text="Имя хоста (HOSTNAME):", font=ctk.CTkFont(weight="bold"), width=200).pack(side="left", padx=10)
        
        self.hostname_entry = ctk.CTkEntry(hostname_frame, width=300)
        self.hostname_entry.insert(0, config_data.system.get('HOSTNAME', 'ats1'))
        self.hostname_entry.pack(side="left", padx=10)
        
        Tooltip(self.hostname_entry, "Имя устройства в домене, только латиница, цифры, дефис, подчёркивание, точка. Максимум 63 символа. Пример: ats1")
    
    def save_data(self):
        self.config_data.system['HOSTNAME'] = self.hostname_entry.get().strip()
    
    def validate(self) -> bool:
        self.error_messages = []
        hostname = self.hostname_entry.get().strip()
        
        if not hostname:
            self.error_messages.append("Имя хоста не может быть пустым")
            self.hostname_entry.configure(border_color="red")
            return False
        
        if not validate_hostname(hostname):
            self.error_messages.append("Имя хоста должно содержать только латиницу, цифры, и символы _-. и не более 63 символов")
            self.hostname_entry.configure(border_color="red")
            return False
        
        self.hostname_entry.configure(border_color="green")
        return True


class NtpPage(Page):
    """Страница NTP (необязательная)."""
    
    TITLE = "NTP"
    TOOLTIP = "Синхронизация времени"
    IS_OPTIONAL = True
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        title = ctk.CTkLabel(self, text="Синхронизация времени (NTP)", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20)
        
        self.enabled_var = ctk.BooleanVar(value=config_data.ntp_enabled)
        self.enabled_cb = ctk.CTkCheckBox(
            self, 
            text="Включить синхронизацию времени (NTP)",
            variable=self.enabled_var,
            command=self._toggle_fields
        )
        self.enabled_cb.pack(pady=10)
        
        fields_frame = ctk.CTkFrame(self)
        fields_frame.pack(pady=10, fill="x", padx=50)
        
        ip_frame = ctk.CTkFrame(fields_frame)
        ip_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(ip_frame, text="IP сервера NTP:", width=150).pack(side="left", padx=5)
        self.ip_srv_entry = ctk.CTkEntry(ip_frame, width=200)
        self.ip_srv_entry.insert(0, config_data.ntp.get('IP_SRV', ''))
        self.ip_srv_entry.pack(side="left", padx=5)
        Tooltip(self.ip_srv_entry, "IPv4 адрес NTP сервера. Пример: 192.168.1.1")
        
        interval_frame = ctk.CTkFrame(fields_frame)
        interval_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(interval_frame, text="Интервал опроса (сек):", width=150).pack(side="left", padx=5)
        self.interval_entry = ctk.CTkEntry(interval_frame, width=100)
        self.interval_entry.insert(0, str(config_data.ntp.get('INTERVAL', 14400)))
        self.interval_entry.pack(side="left", padx=5)
        Tooltip(self.interval_entry, "Интервал синхронизации в секундах (60-86400). По умолчанию 14400.")
        
        self.fields = [self.ip_srv_entry, self.interval_entry]
        self._toggle_fields()
    
    def _toggle_fields(self):
        state = "normal" if self.enabled_var.get() else "disabled"
        for entry in self.fields:
            entry.configure(state=state)
    
    def save_data(self):
        self.config_data.ntp_enabled = self.enabled_var.get()
        self.config_data.ntp['IP_SRV'] = self.ip_srv_entry.get().strip()
        try:
            self.config_data.ntp['INTERVAL'] = int(self.interval_entry.get().strip() or 14400)
        except ValueError:
            self.config_data.ntp['INTERVAL'] = 14400
    
    def validate(self) -> bool:
        self.error_messages = []
        
        if not self.enabled_var.get():
            return True
        
        ip_srv = self.ip_srv_entry.get().strip()
        if not ip_srv or not validate_ipv4(ip_srv):
            self.error_messages.append("Некорректный IP адрес NTP сервера")
            self.ip_srv_entry.configure(border_color="red")
            return False
        
        interval_str = self.interval_entry.get().strip()
        if interval_str and not validate_integer(interval_str, 60, 86400):
            self.error_messages.append("Интервал должен быть от 60 до 86400 секунд")
            self.interval_entry.configure(border_color="red")
            return False
        
        return True


class NetworkPage(Page):
    """Страница NETWORK (обязательная)."""
    
    TITLE = "NETWORK"
    TOOLTIP = "Сетевые настройки"
    IS_OPTIONAL = False
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        title = ctk.CTkLabel(self, text="Сетевые настройки (NETWORK)", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.iface_tab = self.tabview.add("Интерфейсы")
        self.route_tab = self.tabview.add("Маршруты")
        self.arp_tab = self.tabview.add("ARP")
        
        self.iface_entries = []
        self.route_entries = []
        self.arp_entries = []
        
        self._setup_iface_tab()
        self._setup_route_tab()
        self._setup_arp_tab()
        
        self.after(100, self._load_data)
    
    def _setup_iface_tab(self):
        btn_frame = ctk.CTkFrame(self.iface_tab)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        add_btn = ctk.CTkButton(btn_frame, text="+ Добавить интерфейс", command=self._add_iface)
        add_btn.pack(side="left")
        
        self.ifaces_frame = ctk.CTkScrollableFrame(self.iface_tab)
        self.ifaces_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _setup_route_tab(self):
        btn_frame = ctk.CTkFrame(self.route_tab)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        add_btn = ctk.CTkButton(btn_frame, text="+ Добавить маршрут", command=self._add_route)
        add_btn.pack(side="left")
        
        self.routes_frame = ctk.CTkScrollableFrame(self.route_tab)
        self.routes_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _setup_arp_tab(self):
        btn_frame = ctk.CTkFrame(self.arp_tab)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        add_btn = ctk.CTkButton(btn_frame, text="+ Добавить ARP запись", command=self._add_arp)
        add_btn.pack(side="left")
        
        self.arps_frame = ctk.CTkScrollableFrame(self.arp_tab)
        self.arps_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _add_iface(self):
        frame = ctk.CTkFrame(self.ifaces_frame)
        frame.pack(fill="x", pady=5)
        
        entry_data = {}
        
        # Имя интерфейса
        iface_names = ['eth0', 'eth1'] + [f'eth0:{i}' for i in range(10)] + [f'eth1:{i}' for i in range(10)]
        
        row1 = ctk.CTkFrame(frame)
        row1.pack(fill="x", pady=2)
        ctk.CTkLabel(row1, text="Интерфейс:", width=100).pack(side="left", padx=5)
        entry_data['name'] = ctk.CTkComboBox(row1, values=iface_names, width=100)
        entry_data['name'].set('eth0')
        entry_data['name'].pack(side="left", padx=5)
        Tooltip(entry_data['name'], "Имя сетевого интерфейса")
        
        row2 = ctk.CTkFrame(frame)
        row2.pack(fill="x", pady=2)
        ctk.CTkLabel(row2, text="IP адрес:", width=100).pack(side="left", padx=5)
        entry_data['ip'] = ctk.CTkEntry(row2, width=150)
        entry_data['ip'].pack(side="left", padx=5)
        Tooltip(entry_data['ip'], "IPv4 адрес интерфейса")
        
        ctk.CTkLabel(row2, text="Маска:", width=60).pack(side="left", padx=5)
        entry_data['netmask'] = ctk.CTkEntry(row2, width=150)
        entry_data['netmask'].insert(0, '255.255.255.0')
        entry_data['netmask'].pack(side="left", padx=5)
        Tooltip(entry_data['netmask'], "Маска подсети")
        
        row3 = ctk.CTkFrame(frame)
        row3.pack(fill="x", pady=2)
        ctk.CTkLabel(row3, text="Broadcast:", width=100).pack(side="left", padx=5)
        entry_data['broadcast'] = ctk.CTkEntry(row3, width=150)
        entry_data['broadcast'].pack(side="left", padx=5)
        Tooltip(entry_data['broadcast'], "Широковещательный адрес (опционально)")
        
        row4 = ctk.CTkFrame(frame)
        row4.pack(fill="x", pady=2)
        ctk.CTkLabel(row4, text="MTU:", width=100).pack(side="left", padx=5)
        entry_data['mtu'] = ctk.CTkEntry(row4, width=80)
        entry_data['mtu'].insert(0, '1500')
        entry_data['mtu'].pack(side="left", padx=5)
        Tooltip(entry_data['mtu'], "Максимальный размер пакета (68-1500)")
        
        ctk.CTkLabel(row4, text="Метрика:", width=70).pack(side="left", padx=5)
        entry_data['metric'] = ctk.CTkEntry(row4, width=80)
        entry_data['metric'].insert(0, '1')
        entry_data['metric'].pack(side="left", padx=5)
        Tooltip(entry_data['metric'], "Метрика интерфейса (0-65535)")
        
        row5 = ctk.CTkFrame(frame)
        row5.pack(fill="x", pady=2)
        ctk.CTkLabel(row5, text="Скорость:", width=100).pack(side="left", padx=5)
        entry_data['speed'] = ctk.CTkComboBox(row5, values=['', '10', '100', '1000'], width=80)
        entry_data['speed'].pack(side="left", padx=5)
        Tooltip(entry_data['speed'], "Скорость интерфейса (опционально)")
        
        ctk.CTkLabel(row5, text="Дуплекс:", width=70).pack(side="left", padx=5)
        entry_data['duplex'] = ctk.CTkComboBox(row5, values=['', 'full', 'half'], width=80)
        entry_data['duplex'].pack(side="left", padx=5)
        Tooltip(entry_data['duplex'], "Режим дуплекса (опционально)")
        
        ctk.CTkLabel(row5, text="Автопереговоры:", width=110).pack(side="left", padx=5)
        entry_data['autoneg'] = ctk.CTkComboBox(row5, values=['on', 'off'], width=80)
        entry_data['autoneg'].set('on')
        entry_data['autoneg'].pack(side="left", padx=5)
        Tooltip(entry_data['autoneg'], "Автосогласование скорости")
        
        del_btn = ctk.CTkButton(frame, text="X", width=30, fg_color="red", hover_color="darkred", command=lambda f=frame, e=entry_data: self._remove_iface(f, e))
        del_btn.pack(side="right", padx=5, pady=5)
        
        self.iface_entries.append(entry_data)
    
    def _remove_iface(self, frame, entry_data):
        frame.destroy()
        if entry_data in self.iface_entries:
            self.iface_entries.remove(entry_data)
    
    def _add_route(self):
        frame = ctk.CTkFrame(self.routes_frame)
        frame.pack(fill="x", pady=5)
        
        entry_data = {}
        
        iface_names = [e['name'].get() for e in self.iface_entries] if self.iface_entries else ['eth0', 'eth1']
        
        row1 = ctk.CTkFrame(frame)
        row1.pack(fill="x", pady=2)
        ctk.CTkLabel(row1, text="Интерфейс:", width=100).pack(side="left", padx=5)
        entry_data['iface'] = ctk.CTkComboBox(row1, values=iface_names, width=100)
        entry_data['iface'].set('eth0')
        entry_data['iface'].pack(side="left", padx=5)
        Tooltip(entry_data['iface'], "Интерфейс для маршрута")
        
        ctk.CTkLabel(row1, text="Сеть:", width=50).pack(side="left", padx=5)
        entry_data['net'] = ctk.CTkEntry(row1, width=150)
        entry_data['net'].pack(side="left", padx=5)
        Tooltip(entry_data['net'], "IP сети (не требуется для шлюза по умолчанию)")
        
        ctk.CTkLabel(row1, text="Маска:", width=50).pack(side="left", padx=5)
        entry_data['netmask'] = ctk.CTkEntry(row1, width=150)
        entry_data['netmask'].insert(0, '255.255.255.0')
        entry_data['netmask'].pack(side="left", padx=5)
        Tooltip(entry_data['netmask'], "Маска сети")
        
        row2 = ctk.CTkFrame(frame)
        row2.pack(fill="x", pady=2)
        ctk.CTkLabel(row2, text="Шлюз:", width=100).pack(side="left", padx=5)
        entry_data['gateway'] = ctk.CTkEntry(row2, width=150)
        entry_data['gateway'].pack(side="left", padx=5)
        Tooltip(entry_data['gateway'], "IP шлюза")
        
        entry_data['default_gw'] = ctk.BooleanVar(value=False)
        gw_cb = ctk.CTkCheckBox(row2, text="Шлюз по умолчанию", variable=entry_data['default_gw'])
        gw_cb.pack(side="left", padx=10)
        Tooltip(gw_cb, "Отметьте если это маршрут по умолчанию")
        
        ctk.CTkLabel(row2, text="Метрика:", width=60).pack(side="left", padx=5)
        entry_data['metric'] = ctk.CTkEntry(row2, width=80)
        entry_data['metric'].insert(0, '1')
        entry_data['metric'].pack(side="left", padx=5)
        Tooltip(entry_data['metric'], "Метрика маршрута")
        
        del_btn = ctk.CTkButton(frame, text="X", width=30, fg_color="red", hover_color="darkred", command=lambda f=frame, e=entry_data: self._remove_route(f, e))
        del_btn.pack(side="right", padx=5, pady=5)
        
        self.route_entries.append(entry_data)
    
    def _remove_route(self, frame, entry_data):
        frame.destroy()
        if entry_data in self.route_entries:
            self.route_entries.remove(entry_data)
    
    def _add_arp(self):
        frame = ctk.CTkFrame(self.arps_frame)
        frame.pack(fill="x", pady=5)
        
        entry_data = {}
        
        row1 = ctk.CTkFrame(frame)
        row1.pack(fill="x", pady=2)
        ctk.CTkLabel(row1, text="IP адрес:", width=100).pack(side="left", padx=5)
        entry_data['ip'] = ctk.CTkEntry(row1, width=150)
        entry_data['ip'].pack(side="left", padx=5)
        Tooltip(entry_data['ip'], "IP адрес для статической ARP записи")
        
        ctk.CTkLabel(row1, text="MAC адрес:", width=100).pack(side="left", padx=5)
        entry_data['mac'] = ctk.CTkEntry(row1, width=150)
        entry_data['mac'].pack(side="left", padx=5)
        Tooltip(entry_data['mac'], "MAC адрес в формате XX:XX:XX:XX:XX:XX")
        
        del_btn = ctk.CTkButton(frame, text="X", width=30, fg_color="red", hover_color="darkred", command=lambda f=frame, e=entry_data: self._remove_arp(f, e))
        del_btn.pack(side="right", padx=5, pady=5)
        
        self.arp_entries.append(entry_data)
    
    def _remove_arp(self, frame, entry_data):
        frame.destroy()
        if entry_data in self.arp_entries:
            self.arp_entries.remove(entry_data)
    
    def _load_data(self):
        for iface in self.config_data.interfaces:
            self._add_iface()
            entry = self.iface_entries[-1]
            entry['name'].set(iface.get('IFACE_NAME', 'eth0'))
            entry['ip'].insert(0, iface.get('IP', ''))
            entry['netmask'].delete(0, 'end')
            entry['netmask'].insert(0, iface.get('NETMASK', '255.255.255.0'))
            entry['broadcast'].insert(0, iface.get('BROADCAST', ''))
            entry['mtu'].delete(0, 'end')
            entry['mtu'].insert(0, str(iface.get('MTU', 1500)))
            entry['metric'].delete(0, 'end')
            entry['metric'].insert(0, str(iface.get('METRIC', 1)))
            entry['speed'].set(iface.get('SPEED', ''))
            entry['duplex'].set(iface.get('DUPLEX', ''))
            entry['autoneg'].set(iface.get('AUTONEG', 'on'))
        
        for route in self.config_data.routes:
            self._add_route()
            entry = self.route_entries[-1]
            entry['iface'].set(route.get('IFACE_NAME', 'eth0'))
            entry['net'].insert(0, route.get('NET', ''))
            entry['netmask'].delete(0, 'end')
            entry['netmask'].insert(0, route.get('NETMASK', '255.255.255.0'))
            entry['gateway'].insert(0, route.get('GATEWAY', ''))
            entry['default_gw'].set(route.get('DEFAULT_GW', False))
            entry['metric'].delete(0, 'end')
            entry['metric'].insert(0, str(route.get('METRIC', 1)))
        
        for arp in self.config_data.arp_entries:
            self._add_arp()
            entry = self.arp_entries[-1]
            entry['ip'].insert(0, arp.get('IP', ''))
            entry['mac'].insert(0, arp.get('MAC', ''))
    
    def save_data(self):
        self.config_data.interfaces = []
        for entry in self.iface_entries:
            iface = {
                'IFACE_NAME': entry['name'].get(),
                'IP': entry['ip'].get().strip(),
                'NETMASK': entry['netmask'].get().strip(),
                'BROADCAST': entry['broadcast'].get().strip(),
                'MTU': int(entry['mtu'].get().strip() or 1500),
                'METRIC': int(entry['metric'].get().strip() or 1),
                'SPEED': entry['speed'].get(),
                'DUPLEX': entry['duplex'].get(),
                'AUTONEG': entry['autoneg'].get()
            }
            self.config_data.interfaces.append(iface)
        
        self.config_data.routes = []
        for entry in self.route_entries:
            route = {
                'IFACE_NAME': entry['iface'].get(),
                'NET': entry['net'].get().strip(),
                'NETMASK': entry['netmask'].get().strip(),
                'GATEWAY': entry['gateway'].get().strip(),
                'DEFAULT_GW': entry['default_gw'].get(),
                'METRIC': int(entry['metric'].get().strip() or 1)
            }
            self.config_data.routes.append(route)
        
        self.config_data.arp_entries = []
        for entry in self.arp_entries:
            arp = {
                'IP': entry['ip'].get().strip(),
                'MAC': entry['mac'].get().strip()
            }
            self.config_data.arp_entries.append(arp)
    
    def validate(self) -> bool:
        self.error_messages = []
        
        if not self.iface_entries:
            self.error_messages.append("Требуется хотя бы один сетевой интерфейс")
            return False
        
        for entry in self.iface_entries:
            ip = entry['ip'].get().strip()
            netmask = entry['netmask'].get().strip()
            
            if not ip or not validate_ipv4(ip):
                self.error_messages.append(f"Некорректный IP адрес для интерфейса {entry['name'].get()}")
                entry['ip'].configure(border_color="red")
                return False
            
            if not netmask or not validate_netmask(netmask):
                self.error_messages.append(f"Некорректная маска подсети для интерфейса {entry['name'].get()}")
                entry['netmask'].configure(border_color="red")
                return False
        
        default_gw_count = sum(1 for e in self.route_entries if e['default_gw'].get())
        if default_gw_count > 1:
            self.error_messages.append("Только один маршрут может быть шлюзом по умолчанию")
            return False
        
        for entry in self.route_entries:
            gateway = entry['gateway'].get().strip()
            if not gateway or not validate_ipv4(gateway):
                self.error_messages.append("Некорректный IP шлюза в маршруте")
                entry['gateway'].configure(border_color="red")
                return False
        
        for entry in self.arp_entries:
            ip = entry['ip'].get().strip()
            mac = entry['mac'].get().strip()
            
            if not ip or not validate_ipv4(ip):
                self.error_messages.append("Некорректный IP в ARP записи")
                entry['ip'].configure(border_color="red")
                return False
            
            if not mac or not validate_mac(mac):
                self.error_messages.append("Некорректный MAC адрес в ARP записи")
                entry['mac'].configure(border_color="red")
                return False
        
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
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.general_tab = self.tabview.add("Общие")
        self.contexts_tab = self.tabview.add("Контексты")
        
        self.extension_groups = []
        
        self._setup_general_tab()
        self._setup_contexts_tab()
        
        self.after(100, self._load_data)
    
    def _setup_general_tab(self):
        scroll_frame = ctk.CTkScrollableFrame(self.general_tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.static_var = ctk.BooleanVar(value=self.config_data.extensions_general.get('STATIC', False))
        static_cb = ctk.CTkCheckBox(scroll_frame, text="STATIC (статический контекст)", variable=self.static_var)
        static_cb.pack(anchor="w", pady=5)
        Tooltip(static_cb, "Если true, контекст не может быть изменён динамически")
        
        self.writeprotect_var = ctk.BooleanVar(value=self.config_data.extensions_general.get('WRITEPROTECT', False))
        writeprotect_cb = ctk.CTkCheckBox(scroll_frame, text="WRITEPROTECT (защита от записи)", variable=self.writeprotect_var)
        writeprotect_cb.pack(anchor="w", pady=5)
        Tooltip(writeprotect_cb, "Если true, защита от изменения через AMI")
        
        self.clearglobalvars_var = ctk.BooleanVar(value=self.config_data.extensions_general.get('CLEARGLOBALVARS', False))
        clearglobalvars_cb = ctk.CTkCheckBox(scroll_frame, text="CLEARGLOBALVARS (очищать глобальные переменные)", variable=self.clearglobalvars_var)
        clearglobalvars_cb.pack(anchor="w", pady=5)
        Tooltip(clearglobalvars_cb, "Если true, очищать глобальные переменные при перезагрузке")
        
        self.autofallthrough_var = ctk.BooleanVar(value=self.config_data.extensions_general.get('AUTOFALLTHROUGH', True))
        autofallthrough_cb = ctk.CTkCheckBox(scroll_frame, text="AUTOFALLTHROUGH (автоматический переход)", variable=self.autofallthrough_var)
        autofallthrough_cb.pack(anchor="w", pady=5)
        Tooltip(autofallthrough_cb, "Если true, продолжать выполнение следующего приоритета после Hangup")
        
        globals_label = ctk.CTkLabel(scroll_frame, text="Глобальные переменные (GLOBALS):", font=ctk.CTkFont(weight="bold"))
        globals_label.pack(anchor="w", pady=(20, 5))
        
        self.globals_frame = ctk.CTkFrame(scroll_frame)
        self.globals_frame.pack(fill="x", pady=5)
        
        self.global_entries = []
        
        add_global_btn = ctk.CTkButton(self.globals_frame, text="+ Добавить переменную", command=self._add_global)
        add_global_btn.pack(pady=5)
    
    def _add_global(self):
        frame = ctk.CTkFrame(self.globals_frame)
        frame.pack(fill="x", pady=2)
        
        entry_data = {}
        
        ctk.CTkLabel(frame, text="Имя:", width=50).pack(side="left", padx=5)
        entry_data['name'] = ctk.CTkEntry(frame, width=150)
        entry_data['name'].pack(side="left", padx=5)
        
        ctk.CTkLabel(frame, text="Значение:", width=60).pack(side="left", padx=5)
        entry_data['value'] = ctk.CTkEntry(frame, width=200)
        entry_data['value'].pack(side="left", padx=5)
        
        del_btn = ctk.CTkButton(frame, text="X", width=30, fg_color="red", hover_color="darkred", command=lambda f=frame, e=entry_data: self._remove_global(f, e))
        del_btn.pack(side="right", padx=5)
        
        self.global_entries.append(entry_data)
    
    def _remove_global(self, frame, entry_data):
        frame.destroy()
        if entry_data in self.global_entries:
            self.global_entries.remove(entry_data)
    
    def _setup_contexts_tab(self):
        btn_frame = ctk.CTkFrame(self.contexts_tab)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        add_btn = ctk.CTkButton(btn_frame, text="+ Добавить контекст", command=self._add_context)
        add_btn.pack(side="left")
        
        self.contexts_frame = ctk.CTkScrollableFrame(self.contexts_tab)
        self.contexts_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _add_context(self):
        context_frame = ctk.CTkFrame(self.contexts_frame)
        context_frame.pack(fill="x", pady=10)
        
        context_data = {'extensions': []}
        
        header = ctk.CTkFrame(context_frame)
        header.pack(fill="x", pady=5)
        
        ctk.CTkLabel(header, text="Контекст:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        context_data['name'] = ctk.CTkEntry(header, width=200)
        context_data['name'].insert(0, f"context_{len(self.extension_groups) + 1}")
        context_data['name'].pack(side="left", padx=5)
        Tooltip(context_data['name'], "Имя контекста (латиница, цифры, подчёркивание)")
        
        extens_label = ctk.CTkLabel(context_frame, text="Расширения:", font=ctk.CTkFont(weight="bold"))
        extens_label.pack(anchor="w", padx=5, pady=(10, 5))
        
        extens_container = ctk.CTkFrame(context_frame)
        extens_container.pack(fill="x", padx=5, pady=5)
        
        add_exten_btn = ctk.CTkButton(extens_container, text="+ Добавить расширение", command=lambda: self._add_exten(extens_frame, context_data))
        add_exten_btn.pack(pady=5)
        
        extens_frame = ctk.CTkScrollableFrame(context_frame)
        extens_frame.pack(fill="x", pady=5)
        
        del_btn = ctk.CTkButton(context_frame, text="Удалить контекст", width=150, fg_color="red", hover_color="darkred", command=lambda f=context_frame, c=context_data: self._remove_context(f, c))
        del_btn.pack(pady=10)
        
        self.extension_groups.append(context_data)
    
    def _add_exten(self, parent_frame, context_data):
        exten_frame = ctk.CTkFrame(parent_frame)
        exten_frame.pack(fill="x", pady=5)
        
        exten_data = {}
        
        row1 = ctk.CTkFrame(exten_frame)
        row1.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row1, text="Маска/номер:", width=100).pack(side="left", padx=5)
        exten_data['field1'] = ctk.CTkEntry(row1, width=150)
        exten_data['field1'].pack(side="left", padx=5)
        Tooltip(exten_data['field1'], "Номер или маска: 101, _1XX, _20[1-5], _XXX.")
        
        ctk.CTkLabel(row1, text="Каналы/команды:", width=110).pack(side="left", padx=5)
        exten_data['field2'] = ctk.CTkEntry(row1, width=300)
        exten_data['field2'].pack(side="left", padx=5)
        Tooltip(exten_data['field2'], "Каналы: SIP/101,Zap/32 или команды: '1,Dial(SIP/101)','2,Hangup()'")
        
        row2 = ctk.CTkFrame(exten_frame)
        row2.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row2, text="Макс. соединений:", width=120).pack(side="left", padx=5)
        exten_data['field3'] = ctk.CTkEntry(row2, width=80)
        exten_data['field3'].pack(side="left", padx=5)
        Tooltip(exten_data['field3'], "Опционально: максимальное число соединений в транке")
        
        ctk.CTkLabel(row2, text="Приоритетные каналы:", width=130).pack(side="left", padx=5)
        exten_data['field4'] = ctk.CTkEntry(row2, width=200)
        exten_data['field4'].pack(side="left", padx=5)
        Tooltip(exten_data['field4'], "Опционально: Zap/32,Zap/33")
        
        del_btn = ctk.CTkButton(exten_frame, text="X", width=30, fg_color="red", hover_color="darkred", command=lambda f=exten_frame, e=exten_data, c=context_data: self._remove_exten(f, e, c))
        del_btn.pack(side="right", padx=5, pady=5)
        
        context_data['extensions'].append(exten_data)
    
    def _remove_exten(self, frame, exten_data, context_data):
        frame.destroy()
        if exten_data in context_data['extensions']:
            context_data['extensions'].remove(exten_data)
    
    def _remove_context(self, frame, context_data):
        frame.destroy()
        if context_data in self.extension_groups:
            self.extension_groups.remove(context_data)
    
    def _load_data(self):
        for var, val in self.config_data.extensions_globals.items():
            self._add_global()
            entry = self.global_entries[-1]
            entry['name'].insert(0, var)
            entry['value'].insert(0, val)
        
        for group in self.config_data.extension_groups:
            self._add_context()
            ctx = self.extension_groups[-1]
            ctx['name'].delete(0, 'end')
            ctx['name'].insert(0, group.get('NAME', ''))
            
            for exten in group.get('EXTENSIONS', []):
                self._add_exten(self.contexts_frame.master.master.master if hasattr(self.contexts_frame, 'master') else self.contexts_frame, ctx)
                ext_entry = ctx['extensions'][-1]
                ext_entry['field1'].insert(0, exten.get('FIELD1', ''))
                ext_entry['field2'].insert(0, exten.get('FIELD2', ''))
                ext_entry['field3'].insert(0, exten.get('FIELD3', ''))
                ext_entry['field4'].insert(0, exten.get('FIELD4', ''))
    
    def save_data(self):
        self.config_data.extensions_general['STATIC'] = self.static_var.get()
        self.config_data.extensions_general['WRITEPROTECT'] = self.writeprotect_var.get()
        self.config_data.extensions_general['CLEARGLOBALVARS'] = self.clearglobalvars_var.get()
        self.config_data.extensions_general['AUTOFALLTHROUGH'] = self.autofallthrough_var.get()
        
        self.config_data.extensions_globals = {}
        for entry in self.global_entries:
            name = entry['name'].get().strip()
            value = entry['value'].get().strip()
            if name:
                self.config_data.extensions_globals[name] = value
        
        self.config_data.extension_groups = []
        for ctx in self.extension_groups:
            group = {
                'NAME': ctx['name'].get().strip(),
                'EXTENSIONS': []
            }
            for exten in ctx['extensions']:
                ext = {
                    'FIELD1': exten['field1'].get().strip(),
                    'FIELD2': exten['field2'].get().strip(),
                    'FIELD3': exten['field3'].get().strip(),
                    'FIELD4': exten['field4'].get().strip()
                }
                group['EXTENSIONS'].append(ext)
            self.config_data.extension_groups.append(group)
    
    def validate(self) -> bool:
        self.error_messages = []
        
        has_context = False
        for ctx in self.extension_groups:
            name = ctx['name'].get().strip()
            if not name:
                self.error_messages.append("Имя контекста не может быть пустым")
                ctx['name'].configure(border_color="red")
                return False
            
            if ctx['extensions']:
                has_context = True
                for exten in ctx['extensions']:
                    field1 = exten['field1'].get().strip()
                    field2 = exten['field2'].get().strip()
                    
                    if not field1:
                        self.error_messages.append("Маска/номер расширения не может быть пустой")
                        exten['field1'].configure(border_color="red")
                        return False
                    
                    if not field2:
                        self.error_messages.append("Каналы/команды не могут быть пустыми")
                        exten['field2'].configure(border_color="red")
                        return False
        
        if not has_context:
            self.error_messages.append("Требуется хотя бы один контекст с хотя бы одним расширением")
            return False
        
        return True


class PreviewPage(Page):
    """Итоговая страница предпросмотра."""
    
    TITLE = "Предпросмотр"
    TOOLTIP = "Предпросмотр конфигурации"
    IS_OPTIONAL = False
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        title = ctk.CTkLabel(self, text="Предпросмотр конфигурационного файла", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        self.preview_text = ctk.CTkTextbox(self, width=800, height=500)
        self.preview_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.update_preview()
    
    def update_preview(self):
        generator = ConfigGenerator(self.config_data)
        content = generator.generate()
        self.preview_text.delete("0.0", "end")
        self.preview_text.insert("0.0", content)
    
    def save_data(self):
        pass
    
    def validate(self) -> bool:
        return True


class PlaceholderPage(Page):
    """Страница-заглушка для необязательных секций."""
    
    def __init__(self, parent, config_data: ConfigData, app, title: str, tooltip: str, enabled_attr: str):
        super().__init__(parent, config_data, app)
        self.page_title = title
        self.TOOLTIP = tooltip
        self.enabled_attr = enabled_attr
        
        title_label = ctk.CTkLabel(self, text=f"{title} (необязательно)", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=20)
        
        desc = ctk.CTkLabel(
            self,
            text=f"Настройка {title} необязательна. Вы можете пропустить этот шаг.",
            wraplength=600,
            justify="center"
        )
        desc.pack(pady=10)
        
        self.enabled_var = ctk.BooleanVar(value=False)
        self.enabled_cb = ctk.CTkCheckBox(
            self,
            text=f"Включить секцию {title}",
            variable=self.enabled_var
        )
        self.enabled_cb.pack(pady=20)
    
    def save_data(self):
        setattr(self.config_data, self.enabled_attr, self.enabled_var.get())
    
    def validate(self) -> bool:
        return True


class App(ctk.CTk):
    """Главное приложение."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Мастер конфигурации IP-АТС Т76-С")
        self.geometry("900x700")
        
        self.config_data = ConfigData()
        self.current_page_index = 0
        
        self.pages: List[Page] = []
        
        self._setup_ui()
        self._create_pages()
        self.show_page(0)
    
    def _setup_ui(self):
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_label = ctk.CTkLabel(self.header_frame, text="Шаг 1 из 14", font=ctk.CTkFont(size=14))
        self.progress_label.pack(side="left", padx=10)
        
        self.section_label = ctk.CTkLabel(self.header_frame, text="SYSTEM", font=ctk.CTkFont(size=14, weight="bold"))
        self.section_label.pack(side="left", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.header_frame, mode="determinate")
        self.progress_bar.pack(side="right", padx=10, pady=10)
        self.progress_bar.set(0)
        
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.footer_frame = ctk.CTkFrame(self)
        self.footer_frame.pack(fill="x", padx=10, pady=5)
        
        self.back_btn = ctk.CTkButton(self.footer_frame, text="Назад", command=self.prev_page, state="disabled")
        self.back_btn.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(self.footer_frame, text="Далее", command=self.next_page)
        self.next_btn.pack(side="left", padx=5)
        
        self.cancel_btn = ctk.CTkButton(self.footer_frame, text="Отмена", command=self._cancel, fg_color="gray")
        self.cancel_btn.pack(side="right", padx=5)
        
        self.help_btn = ctk.CTkButton(self.footer_frame, text="Справка", command=self._show_help)
        self.help_btn.pack(side="right", padx=5)
        
        self.status_label = ctk.CTkLabel(self.footer_frame, text="", text_color="red")
        self.status_label.pack(side="left", padx=20)
    
    def _create_pages(self):
        self.pages = [
            SystemPage(self.container, self.config_data, self),
            NtpPage(self.container, self.config_data, self),
            NetworkPage(self.container, self.config_data, self),
            PlaceholderPage(self.container, self.config_data, self, "MPLS", "MPLS маршрутизация", "mpls_enabled"),
            PlaceholderPage(self.container, self.config_data, self, "TUNNELS", "VPN туннели", "tunnels_enabled"),
            PlaceholderPage(self.container, self.config_data, self, "TC", "Управление трафиком", "tc_enabled"),
            PlaceholderPage(self.container, self.config_data, self, "IPTABLES", "Межсетевой экран", "iptables_enabled"),
            PlaceholderPage(self.container, self.config_data, self, "IAX", "Протокол IAX2", "iax_enabled"),
            PlaceholderPage(self.container, self.config_data, self, "SIP", "Протокол SIP", "sip_enabled"),
            PlaceholderPage(self.container, self.config_data, self, "ZAPTEL", "Настройка ZAPTEL", "zaptel_enabled"),
            PlaceholderPage(self.container, self.config_data, self, "ZAPATA", "Настройка ZAPATA", "zapata_enabled"),
            ExtensionsPage(self.container, self.config_data, self),
            PlaceholderPage(self.container, self.config_data, self, "ALARM", "Обработка событий", "alarm_enabled"),
            PreviewPage(self.container, self.config_data, self)
        ]
        
        for page in self.pages:
            page.pack_forget()
    
    def show_page(self, index: int):
        if index < 0 or index >= len(self.pages):
            return
        
        if self.current_page_index < len(self.pages):
            self.pages[self.current_page_index].pack_forget()
        
        self.current_page_index = index
        page = self.pages[index]
        page.pack(fill="both", expand=True)
        
        total_pages = len(self.pages)
        self.progress_label.configure(text=f"Шаг {index + 1} из {total_pages}")
        self.section_label.configure(text=page.TITLE)
        self.progress_bar.set((index + 1) / total_pages)
        
        self.back_btn.configure(state="normal" if index > 0 else "disabled")
        
        if index == total_pages - 1:
            self.next_btn.configure(text="Сохранить файл", command=self.save_file)
        else:
            self.next_btn.configure(text="Далее", command=self.next_page)
        
        self.status_label.configure(text="")
    
    def next_page(self):
        current_page = self.pages[self.current_page_index]
        
        if not current_page.validate():
            errors = current_page.get_error_messages()
            if errors:
                self.status_label.configure(text=errors[0])
            return
        
        current_page.save_data()
        
        if self.current_page_index < len(self.pages) - 1:
            self.show_page(self.current_page_index + 1)
    
    def prev_page(self):
        if self.current_page_index > 0:
            self.pages[self.current_page_index].save_data()
            self.show_page(self.current_page_index - 1)
    
    def save_file(self):
        current_page = self.pages[self.current_page_index]
        current_page.save_data()
        
        generator = ConfigGenerator(self.config_data)
        content = generator.generate()
        
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
                    f.write(content)
                
                messagebox.showinfo("Успех", f"Файл успешно сохранён:\n{file_path}")
                
                restart = messagebox.askyesno("Завершение", "Создать новый конфиг?")
                if restart:
                    self.config_data = ConfigData()
                    for page in self.pages:
                        page.destroy()
                    self.pages.clear()
                    self._create_pages()
                    self.show_page(0)
                else:
                    self.quit()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
    
    def _cancel(self):
        if messagebox.askyesno("Подтверждение", "Отменить создание конфига?"):
            self.quit()
    
    def _show_help(self):
        page = self.pages[self.current_page_index]
        help_text = f"Справка: {page.TITLE}\n\n{page.TOOLTIP}"
        messagebox.showinfo("Справка", help_text)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = App()
    app.mainloop()
