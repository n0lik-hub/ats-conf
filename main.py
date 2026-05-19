# -*- coding: utf-8 -*-
"""
Мастер конфигурации IP-АТС Т76-С - Главный файл приложения
Версия: 2.1
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import sys
from typing import Dict, List, Any, Optional

from config_master import ConfigData, ConfigGenerator


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def create_labeled_entry(parent, label_text: str, tooltip: str = "", default: str = "", width: int = 200):
    """Создаёт подписанное поле ввода с подсказкой."""
    frame = ctk.CTkFrame(parent)
    
    label = ctk.CTkLabel(frame, text=label_text, width=150, anchor="w")
    label.pack(side="left", padx=5)
    
    entry = ctk.CTkEntry(frame, width=width)
    if default:
        entry.insert(0, default)
    entry.pack(side="left", padx=5)
    
    if tooltip:
        Tooltip(entry, tooltip)
        Tooltip(label, tooltip)
    
    return frame, entry


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
        
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(
            tw, 
            text=self.text, 
            justify="left",
            wraplength=300,
            font=ctk.CTkFont(size=12)
        )
        label.pack(padx=8, pady=4)
    
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


# ============================================================================
# БАЗОВЫЙ КЛАСС СТРАНИЦЫ
# ============================================================================

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


# ============================================================================
# СТРАНИЦА SYSTEM (обязательная, страница 1)
# ============================================================================

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
        
        # Поле HOSTNAME
        hostname_frame = ctk.CTkFrame(self)
        hostname_frame.pack(pady=20)
        
        ctk.CTkLabel(hostname_frame, text="Имя хоста (HOSTNAME):", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
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
        
        if len(hostname) > 63:
            self.error_messages.append("Имя хоста не должно превышать 63 символа")
            self.hostname_entry.configure(border_color="red")
            return False
        
        import re
        if not re.match(r'^[a-zA-Z0-9._-]+$', hostname):
            self.error_messages.append("Имя хоста должно содержать только латиницу, цифры, и символы _-.")
            self.hostname_entry.configure(border_color="red")
            return False
        
        self.hostname_entry.configure(border_color="green")
        return True


# ============================================================================
# СТРАНИЦА NTP (необязательная, страница 2)
# ============================================================================

class NtpPage(Page):
    """Страница NTP (необязательная)."""
    
    TITLE = "NTP"
    TOOLTIP = "Синхронизация времени"
    IS_OPTIONAL = True
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        title = ctk.CTkLabel(self, text="Синхронизация времени (NTP)", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20)
        
        # Флажок включения
        self.enabled_var = ctk.BooleanVar(value=config_data.ntp_enabled)
        self.enabled_cb = ctk.CTkCheckBox(
            self, 
            text="Включить синхронизацию времени (NTP)",
            variable=self.enabled_var,
            command=self._toggle_fields
        )
        self.enabled_cb.pack(pady=10)
        
        # Поля ввода
        fields_frame = ctk.CTkFrame(self)
        fields_frame.pack(pady=10)
        
        _, self.ip_srv_entry = create_labeled_entry(
            fields_frame, 
            "IP сервера NTP:", 
            tooltip="IPv4 адрес NTP сервера. Пример: 192.168.1.1",
            default=config_data.ntp.get('IP_SRV', ''),
            width=200
        )
        
        _, self.interval_entry = create_labeled_entry(
            fields_frame,
            "Интервал опроса (сек):",
            tooltip="Интервал синхронизации в секундах (60-86400). По умолчанию 14400.",
            default=str(config_data.ntp.get('INTERVAL', 14400)),
            width=100
        )
        
        self.fields = [self.ip_srv_entry, self.interval_entry]
        self._toggle_fields()
    
    def _toggle_fields(self):
        """Включает/выключает поля ввода."""
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
        
        from config_master import validate_ipv4, validate_integer
        
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


# ============================================================================
# СТРАНИЦА NETWORK (обязательная, страница 3)
# ============================================================================

class NetworkPage(Page):
    """Страница NETWORK (обязательная)."""
    
    TITLE = "NETWORK"
    TOOLTIP = "Сетевые настройки"
    IS_OPTIONAL = False
    
    def __init__(self, parent, config_data: ConfigData, app):
        super().__init__(parent, config_data, app)
        
        title = ctk.CTkLabel(self, text="Сетевые настройки (NETWORK)", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        # Вкладки
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.iface_tab = self.tabview.add("Интерфейсы")
        self.route_tab = self.tabview.add("Маршруты")
        self.arp_tab = self.tabview.add("ARP")
        
        # Интерфейсы
        self._setup_iface_tab()
        self._setup_route_tab()
        self._setup_arp_tab()
        
        # Загрузка данных
        self._load_data()
    
    def _setup_iface_tab(self):
        """Настройка вкладки интерфейсов."""
        btn_frame = ctk.CTkFrame(self.iface_tab)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        add_btn = ctk.CTkButton(btn_frame, text="+ Добавить интерфейс", command=self._add_iface)
        add_btn.pack(side="left")
        
        self.ifaces_frame = ctk.CTkScrollableFrame(self.iface_tab)
        self.ifaces_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.iface_entries = []
    
    def _setup_route_tab(self):
        """Настройка вкладки маршрутов."""
        btn_frame = ctk.CTkFrame(self.route_tab)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        add_btn = ctk.CTkButton(btn_frame, text="+ Добавить маршрут", command=self._add_route)
        add_btn.pack(side="left")
        
        self.routes_frame = ctk.CTkScrollableFrame(self.route_tab)
        self.routes_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.route_entries = []
    
    def _setup_arp_tab(self):
        """Настройка вкладки ARP."""
        btn_frame = ctk.CTkFrame(self.arp_tab)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        add_btn = ctk.CTkButton(btn_frame, text="+ Добавить ARP запись", command=self._add_arp)
        add_btn.pack(side="left")
        
        self.arps_frame = ctk.CTkScrollableFrame(self.arp_tab)
        self.arps_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.arp_entries = []
    
    def _add_iface(self):
        """Добавляет новый интерфейс."""
        frame = ctk.CTkFrame(self.ifaces_frame)
        frame.pack(fill="x", pady=5)
        
        entry_data = {}
        
        # Имя интерфейса
        iface_names = ['eth0', 'eth1'] + [f'eth0:{i}' for i in range(10)] + [f'eth1:{i}' for i in range(10)]
        
        name_frame = ctk.CTkFrame(frame)
        name_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(name_frame, text="Интерфейс:", width=100).pack(side="left")
        entry_data['name'] = ctk.CTkComboBox(name_frame, values=iface_names, width=100)
        entry_data['name'].set('eth0')
        entry_data['name'].pack(side="left", padx=5)
        Tooltip(entry_data['name'], "Имя сетевого интерфейса")
        
        # IP
        ip_frame = ctk.CTkFrame(frame)
        ip_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(ip_frame, text="IP адрес:", width=100).pack(side="left")
        entry_data['ip'] = ctk.CTkEntry(ip_frame, width=150)
        entry_data['ip'].pack(side="left", padx=5)
        Tooltip(entry_data['ip'], "IPv4 адрес интерфейса")
        
        # NETMASK
        mask_frame = ctk.CTkFrame(frame)
        mask_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(mask_frame, text="Маска:", width=100).pack(side="left")
        entry_data['netmask'] = ctk.CTkEntry(mask_frame, width=150)
        entry_data['netmask'].insert(0, '255.255.255.0')
        entry_data['netmask'].pack(side="left", padx=5)
        Tooltip(entry_data['netmask'], "Маска подсети")
        
        # BROADCAST
        bc_frame = ctk.CTkFrame(frame)
        bc_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(bc_frame, text="Broadcast:", width=100).pack(side="left")
        entry_data['broadcast'] = ctk.CTkEntry(bc_frame, width=150)
        entry_data['broadcast'].pack(side="left", padx=5)
        Tooltip(entry_data['broadcast'], "Широковещательный адрес (опционально)")
        
        # MTU
        mtu_frame = ctk.CTkFrame(frame)
        mtu_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(mtu_frame, text="MTU:", width=100).pack(side="left")
        entry_data['mtu'] = ctk.CTkEntry(mtu_frame, width=80)
        entry_data['mtu'].insert(0, '1500')
        entry_data['mtu'].pack(side="left", padx=5)
        Tooltip(entry_data['mtu'], "Максимальный размер пакета (68-1500)")
        
        # METRIC
        metric_frame = ctk.CTkFrame(frame)
        metric_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(metric_frame, text="Метрика:", width=100).pack(side="left")
        entry_data['metric'] = ctk.CTkEntry(metric_frame, width=80)
        entry_data['metric'].insert(0, '1')
        entry_data['metric'].pack(side="left", padx=5)
        Tooltip(entry_data['metric'], "Метрика интерфейса (0-65535)")
        
        # SPEED
        speed_frame = ctk.CTkFrame(frame)
        speed_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(speed_frame, text="Скорость:", width=100).pack(side="left")
        entry_data['speed'] = ctk.CTkComboBox(speed_frame, values=['', '10', '100', '1000'], width=80)
        entry_data['speed'].pack(side="left", padx=5)
        Tooltip(entry_data['speed'], "Скорость интерфейса (опционально)")
        
        # DUPLEX
        duplex_frame = ctk.CTkFrame(frame)
        duplex_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(duplex_frame, text="Дуплекс:", width=100).pack(side="left")
        entry_data['duplex'] = ctk.CTkComboBox(duplex_frame, values=['', 'full', 'half'], width=80)
        entry_data['duplex'].pack(side="left", padx=5)
        Tooltip(entry_data['duplex'], "Режим дуплекса (опционально)")
        
        # AUTONEG
        autoneg_frame = ctk.CTkFrame(frame)
        autoneg_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(autoneg_frame, text="Автопереговоры:", width=100).pack(side="left")
        entry_data['autoneg'] = ctk.CTkComboBox(autoneg_frame, values=['on', 'off'], width=80)
        entry_data['autoneg'].set('on')
        entry_data['autoneg'].pack(side="left", padx=5)
        Tooltip(entry_data['autoneg'], "Автосогласование скорости")
        
        # Удалить
        del_btn = ctk.CTkButton(frame, text="X", width=30, fg_color="red", command=lambda: self._remove_iface(frame, entry_data))
        del_btn.pack(side="right", padx=5)
        
        self.iface_entries.append(entry_data)
    
    def _remove_iface(self, frame, entry_data):
        frame.destroy()
        self.iface_entries.remove(entry_data)
    
    def _add_route(self):
        """Добавляет новый маршрут."""
        frame = ctk.CTkFrame(self.routes_frame)
        frame.pack(fill="x", pady=5)
        
        entry_data = {}
        
        # IFACE_NAME
        iface_names = [e['name'].get() for e in self.iface_entries] or ['eth0']
        iface_frame = ctk.CTkFrame(frame)
        iface_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(iface_frame, text="Интерфейс:", width=100).pack(side="left")
        entry_data['iface'] = ctk.CTkComboBox(iface_frame, values=iface_names, width=100)
        entry_data['iface'].set(iface_names[0])
        entry_data['iface'].pack(side="left", padx=5)
        
        # NET
        net_frame = ctk.CTkFrame(frame)
        net_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(net_frame, text="Сеть:", width=100).pack(side="left")
        entry_data['net'] = ctk.CTkEntry(net_frame, width=150)
        entry_data['net'].pack(side="left", padx=5)
        Tooltip(entry_data['net'], "IP сети назначения (опционально для шлюза по умолчанию)")
        
        # NETMASK
        mask_frame = ctk.CTkFrame(frame)
        mask_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(mask_frame, text="Маска:", width=100).pack(side="left")
        entry_data['netmask'] = ctk.CTkEntry(mask_frame, width=150)
        entry_data['netmask'].pack(side="left", padx=5)
        
        # GATEWAY
        gw_frame = ctk.CTkFrame(frame)
        gw_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(gw_frame, text="Шлюз:", width=100).pack(side="left")
        entry_data['gateway'] = ctk.CTkEntry(gw_frame, width=150)
        entry_data['gateway'].pack(side="left", padx=5)
        Tooltip(entry_data['gateway'], "IP шлюза")
        
        # DEFAULT_GW
        defgw_frame = ctk.CTkFrame(frame)
        defgw_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(defgw_frame, text="Шлюз по умолчанию:", width=100).pack(side="left")
        entry_data['default_gw'] = ctk.CTkCheckBox(defgw_frame, text="")
        entry_data['default_gw'].pack(side="left", padx=5)
        Tooltip(entry_data['default_gw'], "Только один маршрут может быть шлюзом по умолчанию")
        
        # METRIC
        metric_frame = ctk.CTkFrame(frame)
        metric_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(metric_frame, text="Метрика:", width=100).pack(side="left")
        entry_data['metric'] = ctk.CTkEntry(metric_frame, width=80)
        entry_data['metric'].insert(0, '1')
        entry_data['metric'].pack(side="left", padx=5)
        
        # Удалить
        del_btn = ctk.CTkButton(frame, text="X", width=30, fg_color="red", command=lambda: self._remove_route(frame, entry_data))
        del_btn.pack(side="right", padx=5)
        
        self.route_entries.append(entry_data)
    
    def _remove_route(self, frame, entry_data):
        frame.destroy()
        self.route_entries.remove(entry_data)
    
    def _add_arp(self):
        """Добавляет ARP запись."""
        frame = ctk.CTkFrame(self.arps_frame)
        frame.pack(fill="x", pady=5)
        
        entry_data = {}
        
        # IP
        ip_frame = ctk.CTkFrame(frame)
        ip_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(ip_frame, text="IP адрес:", width=100).pack(side="left")
        entry_data['ip'] = ctk.CTkEntry(ip_frame, width=150)
        entry_data['ip'].pack(side="left", padx=5)
        
        # MAC
        mac_frame = ctk.CTkFrame(frame)
        mac_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(mac_frame, text="MAC адрес:", width=100).pack(side="left")
        entry_data['mac'] = ctk.CTkEntry(mac_frame, width=150)
        entry_data['mac'].pack(side="left", padx=5)
        Tooltip(entry_data['mac'], "Формат: 00:18:E7:15:A6:2B")
        
        # Удалить
        del_btn = ctk.CTkButton(frame, text="X", width=30, fg_color="red", command=lambda: self._remove_arp(frame, entry_data))
        del_btn.pack(side="right", padx=5)
        
        self.arp_entries.append(entry_data)
    
    def _remove_arp(self, frame, entry_data):
        frame.destroy()
        self.arp_entries.remove(entry_data)
    
    def _load_data(self):
        """Загружает данные из config_data."""
        # IFACE
        for iface in self.config_data.network.get('IFACE', []):
            self._add_iface()
            if self.iface_entries:
                e = self.iface_entries[-1]
                e['name'].set(iface.get('IFACE_NAME', 'eth0'))
                e['ip'].insert(0, iface.get('IP', ''))
                e['netmask'].delete(0, 'end')
                e['netmask'].insert(0, iface.get('NETMASK', '255.255.255.0'))
                e['broadcast'].insert(0, iface.get('BROADCAST', ''))
                e['mtu'].delete(0, 'end')
                e['mtu'].insert(0, str(iface.get('MTU', 1500)))
                e['metric'].delete(0, 'end')
                e['metric'].insert(0, str(iface.get('METRIC', 1)))
                e['speed'].set(iface.get('SPEED', ''))
                e['duplex'].set(iface.get('DUPLEX', ''))
                e['autoneg'].set(iface.get('AUTONEG', 'on'))
        
        # ROUTE
        for route in self.config_data.network.get('ROUTE', []):
            self._add_route()
            if self.route_entries:
                e = self.route_entries[-1]
                e['iface'].set(route.get('IFACE_NAME', 'eth0'))
                e['net'].insert(0, route.get('NET', ''))
                e['netmask'].insert(0, route.get('NETMASK', ''))
                e['gateway'].insert(0, route.get('GATEWAY', ''))
                e['default_gw'].select() if route.get('DEFAULT_GW') else e['default_gw'].deselect()
                e['metric'].delete(0, 'end')
                e['metric'].insert(0, str(route.get('METRIC', 1)))
        
        # ARP
        for arp in self.config_data.network.get('ARP', []):
            self._add_arp()
            if self.arp_entries:
                e = self.arp_entries[-1]
                e['ip'].insert(0, arp.get('IP', ''))
                e['mac'].insert(0, arp.get('MAC', ''))
    
    def save_data(self):
        """Сохраняет данные в config_data."""
        self.config_data.network['IFACE'] = []
        for e in self.iface_entries:
            iface = {
                'IFACE_NAME': e['name'].get(),
                'IP': e['ip'].get().strip(),
                'NETMASK': e['netmask'].get().strip(),
                'BROADCAST': e['broadcast'].get().strip(),
                'MTU': e['mtu'].get().strip(),
                'METRIC': e['metric'].get().strip(),
                'SPEED': e['speed'].get(),
                'DUPLEX': e['duplex'].get(),
                'AUTONEG': e['autoneg'].get()
            }
            self.config_data.network['IFACE'].append(iface)
        
        self.config_data.network['ROUTE'] = []
        for e in self.route_entries:
            route = {
                'IFACE_NAME': e['iface'].get(),
                'NET': e['net'].get().strip(),
                'NETMASK': e['netmask'].get().strip(),
                'GATEWAY': e['gateway'].get().strip(),
                'DEFAULT_GW': e['default_gw'].get(),
                'METRIC': e['metric'].get().strip()
            }
            self.config_data.network['ROUTE'].append(route)
        
        self.config_data.network['ARP'] = []
        for e in self.arp_entries:
            arp = {
                'IP': e['ip'].get().strip(),
                'MAC': e['mac'].get().strip()
            }
            self.config_data.network['ARP'].append(arp)
    
    def validate(self) -> bool:
        """Проверяет корректность данных."""
        self.error_messages = []
        from config_master import validate_ipv4, validate_netmask, validate_mac, validate_iface_name
        
        # Проверяем что есть хотя бы один интерфейс
        if not self.iface_entries:
            self.error_messages.append("Необходимо добавить хотя бы один сетевой интерфейс")
            return False
        
        # Валидация интерфейсов
        for e in self.iface_entries:
            iface_name = e['name'].get()
            ip = e['ip'].get().strip()
            netmask = e['netmask'].get().strip()
            
            if not iface_name or not validate_iface_name(iface_name):
                self.error_messages.append(f"Некорректное имя интерфейса: {iface_name}")
                return False
            
            if not ip or not validate_ipv4(ip):
                self.error_messages.append(f"Некорректный IP адрес: {ip}")
                e['ip'].configure(border_color="red")
                return False
            
            if not netmask or not validate_netmask(netmask):
                self.error_messages.append(f"Некорректная маска подсети: {netmask}")
                e['netmask'].configure(border_color="red")
                return False
        
        # Валидация маршрутов
        default_gw_count = sum(1 for e in self.route_entries if e['default_gw'].get())
        if default_gw_count > 1:
            self.error_messages.append("Только один маршрут может быть шлюзом по умолчанию")
            return False
        
        for e in self.route_entries:
            gateway = e['gateway'].get().strip()
            net = e['net'].get().strip()
            netmask = e['netmask'].get().strip()
            
            if gateway and not validate_ipv4(gateway):
                self.error_messages.append(f"Некорректный IP шлюза: {gateway}")
                return False
            
            if net and not validate_ipv4(net):
                self.error_messages.append(f"Некорректный IP сети: {net}")
                return False
            
            if netmask and not validate_netmask(netmask):
                self.error_messages.append(f"Некорректная маска: {netmask}")
                return False
        
        # Валидация ARP
        for e in self.arp_entries:
            ip = e['ip'].get().strip()
            mac = e['mac'].get().strip()
            
            if ip and not validate_ipv4(ip):
                self.error_messages.append(f"Некорректный IP в ARP: {ip}")
                return False
            
            if mac and not validate_mac(mac):
                self.error_messages.append(f"Некорректный MAC адрес: {mac}")
                e['mac'].configure(border_color="red")
                return False
        
        return True


# ============================================================================
# СТРАНИЦА EXTENSIONS (обязательная, страница 12)
# ============================================================================

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
            default="",
            width=200
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
            
            _, field1 = create_labeled_entry(exten_frame, "Номер/маска:", tooltip="Номер или маска (_XXX.)", default="", width=150)
            exten_data['field1'] = field1
            
            _, field2 = create_labeled_entry(exten_frame, "Каналы/команды:", tooltip="SIP/101 или команды", default="", width=200)
            exten_data['field2'] = field2
            
            _, field3 = create_labeled_entry(exten_frame, "Макс. соединений:", tooltip="Опционально", default="", width=80)
            exten_data['field3'] = field3
            
            _, field4 = create_labeled_entry(exten_frame, "Приоритетные каналы:", tooltip="Опционально", default="", width=150)
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
        frame.destroy()
        context_data['extens'] = [e for e in context_data['extens'] if e.get('field1') and hasattr(e['field1'], 'winfo_rootx') and e['field1'].winfo_rootx() != frame.winfo_rootx()]
    
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
                    extens_list_frame = data['extens_list']
                    exten_frame = ctk.CTkFrame(extens_list_frame)
                    exten_frame.pack(fill="x", pady=2)
                    
                    exten_data = {}
                    
                    _, field1 = create_labeled_entry(exten_frame, "Номер/маска:", tooltip="", default=exten.get('field1', ''), width=150)
                    exten_data['field1'] = field1
                    
                    _, field2 = create_labeled_entry(exten_frame, "Каналы/команды:", tooltip="", default=exten.get('field2', ''), width=200)
                    exten_data['field2'] = field2
                    
                    _, field3 = create_labeled_entry(exten_frame, "Макс. соединений:", tooltip="", default=exten.get('field3', ''), width=80)
                    exten_data['field3'] = field3
                    
                    _, field4 = create_labeled_entry(exten_frame, "Приоритетные каналы:", tooltip="", default=exten.get('field4', ''), width=150)
                    exten_data['field4'] = field4
                    
                    del_btn = ctk.CTkButton(exten_frame, text="X", width=30, command=lambda f=exten_frame, d=data: self._remove_exten(f, d))
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


# Placeholder страницы для необязательных секций
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
    
    def save_data(self):
        pass


# ============================================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================================

class App(ctk.CTk):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Мастер конфигурации IP-АТС Т76-С")
        self.geometry("900x700")
        
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
        # Основная область
        self.main_area = ctk.CTkFrame(self)
        self.main_area.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Контейнер для страниц
        self.page_container = ctk.CTkFrame(self.main_area)
        self.page_container.pack(fill="both", expand=True)
        
        # Индикатор прогресса
        self.progress_frame = ctk.CTkFrame(self.main_area)
        self.progress_frame.pack(fill="x", pady=5)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Шаг 1 из 14")
        self.progress_label.pack(side="left", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.pack(side="left", padx=10)
        self.progress_bar.set(0)
        
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
        self.pages.append(PlaceholderPage(self.page_container, self.config_data, self, "ALARM", "Обработка событий"))
        
        # Предпросмотр
        self.pages.append(PreviewPage(self.page_container, self.config_data, self))
        
        # Обновляем прогресс бар
        self._update_progress()
    
    def show_page(self, index: int):
        """Показывает страницу по индексу."""
        if index < 0 or index >= len(self.pages):
            return
        
        # Сохраняем данные текущей страницы перед переключением
        if 0 <= self.current_page_index < len(self.pages):
            self.pages[self.current_page_index].save_data()
        
        # Удаляем текущую страницу
        for widget in self.page_container.winfo_children():
            widget.destroy()
        
        # Показываем новую страницу
        self.current_page_index = index
        page = self.pages[index]
        page.pack(fill="both", expand=True)
        page.load_data()
        
        # Обновляем кнопки
        self.btn_back.configure(state="normal" if index > 0 else "disabled")
        
        if index == len(self.pages) - 1:
            self.btn_next.configure(text="Сохранить файл")
        else:
            self.btn_next.configure(text="Далее")
        
        self._update_progress()
    
    def _update_progress(self):
        """Обновляет индикатор прогресса."""
        total = len(self.pages)
        current = self.current_page_index + 1
        self.progress_label.configure(text=f"Шаг {current} из {total}: {self.pages[self.current_page_index].TITLE}")
        self.progress_bar.set(current / total)
    
    def _go_next(self):
        """Переход к следующей странице."""
        current_page = self.pages[self.current_page_index]
        
        # Проверяем валидацию
        if not current_page.validate():
            errors = current_page.get_error_messages()
            if errors:
                messagebox.showerror("Ошибка валидации", "\n".join(errors))
            return
        
        # Сохраняем данные
        current_page.save_data()
        
        # Переходим дальше или сохраняем
        if self.current_page_index == len(self.pages) - 1:
            self._save_file()
        else:
            self.show_page(self.current_page_index + 1)
    
    def _go_back(self):
        """Переход к предыдущей странице."""
        if self.current_page_index > 0:
            self.pages[self.current_page_index].save_data()
            self.show_page(self.current_page_index - 1)
    
    def _save_file(self):
        """Сохраняет конфигурационный файл."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".conf",
            filetypes=[("Config files", "*.conf"), ("All files", "*.*")],
            initialfile=f"{self.config_data.system.get('HOSTNAME', 'ats1')}.conf"
        )
        
        if filename:
            try:
                generator = ConfigGenerator(self.config_data)
                config_text = generator.generate()
                
                with open(filename, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(config_text)
                
                messagebox.showinfo("Успех", f"Конфигурационный файл сохранён:\n{filename}")
                
                # Предлагаем начать заново или выйти
                result = messagebox.askyesno("Завершение", "Создать новый конфигурационный файл?")
                if result:
                    self._reset()
                else:
                    self.quit()
            except Exception as e:
                messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить файл:\n{str(e)}")
    
    def _reset(self):
        """Сбрасывает все данные и начинает сначала."""
        self.config_data.reset()
        self.show_page(0)
    
    def _cancel(self):
        """Отменяет настройку и выходит."""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите выйти без сохранения?"):
            self.quit()
    
    def _show_help(self):
        """Показывает справку по текущей секции."""
        page = self.pages[self.current_page_index]
        help_text = f"Справка по секции {page.TITLE}\n\n{page.TOOLTIP}"
        messagebox.showinfo("Справка", help_text)


# ============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = App()
    app.mainloop()
