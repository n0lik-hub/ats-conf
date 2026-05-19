# -*- coding: utf-8 -*-
"""
Мастер конфигурации IP-АТС Т76-С
Версия: 1.0
Дата: 2026-05-19
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import re
import ipaddress
from typing import Dict, List, Any, Optional, Tuple


# ============================================================================
# КЛАСС ДЛЯ ХРАНЕНИЯ ДАННЫХ КОНФИГУРАЦИИ
# ============================================================================

class ConfigData:
    """Класс-контейнер для хранения всех введённых данных конфигурации."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Сброс всех данных."""
        # SYSTEM
        self.system = {'HOSTNAME': 'ats1'}
        
        # NTP (необязательная)
        self.ntp = None  # None если не используется
        
        # NETWORK
        self.network = {
            'IFACE': [],  # список словарей
            'ROUTE': [],
            'ARP': []
        }
        
        # MPLS (необязательная)
        self.mpls = {
            'MPLS_RULE_OUT': [],
            'MPLS_RULE_IN': []
        }
        
        # TUNNELS (необязательная)
        self.tunnels = None
        
        # TC (необязательная)
        self.tc = []
        
        # IPTABLES (необязательная)
        self.iptables = {
            'INPUT': [],
            'OUTPUT': [],
            'FORWARD': [],
            'PREROUTING': [],
            'POSTROUTING': [],
            'CHAIN': []
        }
        
        # IAX (необязательная)
        self.iax = {
            'GENERAL': {},
            'IAX_ROUTE': []
        }
        
        # SIP (необязательная)
        self.sip = {
            'GENERAL': {},
            'PHONE': []
        }
        
        # ZAPTEL (необязательная)
        self.zaptel = {
            'LOADZONE': 'ru',
            'DEFAULTZONE': 'ru',
            'FXOKS': '',
            'DYNAMIC': '',
            'CHAN_E1': []
        }
        
        # ZAPATA (необязательная)
        self.zapata = {
            'CONTEXT': '',
            'SWITCHTYPE': '',
            'SIGNALLING': '',
            'ECHOCANCEL': True,
            'OVERLAPDIAL': False,
            'RXGAIN': 0.0,
            'TXGAIN': 0.0,
            'GROUP': 0,
            'CHAN': []
        }
        
        # EXTENSIONS (обязательная)
        self.extensions = {
            'GENERAL': {
                'STATIC': False,
                'WRITEPROTECT': False,
                'CLEARGLOBALVARS': False,
                'AUTOFALLTHROUGH': True
            },
            'GLOBALS': [],
            'EXTENGROUP': []
        }
        
        # ALARM (необязательная)
        self.alarm = []
        
        # Справочники для проверки ссылочной целостности
        self.zap_groups = set()  # номера групп из ZAPATA
        self.iax_names = set()   # имена из IAX_ROUTE
        self.sip_numbers = set() # номера из SIP PHONE
        self.context_names = set() # имена контекстов из EXTENSIONS
    
    def get_defined_groups(self) -> set:
        """Возвращает множество определённых групп Zap."""
        return self.zap_groups
    
    def get_iax_names(self) -> set:
        """Возвращает множество имён IAX каналов."""
        return self.iax_names
    
    def get_sip_numbers(self) -> set:
        """Возвращает множество SIP номеров."""
        return self.sip_numbers
    
    def get_context_names(self) -> set:
        """Возвращает множество имён контекстов."""
        return self.context_names


# ============================================================================
# ФУНКЦИИ ВАЛИДАЦИИ
# ============================================================================

def validate_hostname(value: str) -> Tuple[bool, str]:
    """Проверка имени хоста."""
    if not value:
        return False, "Имя хоста не может быть пустым"
    if len(value) > 63:
        return False, "Длина имени хоста не должна превышать 63 символа"
    pattern = r'^[a-zA-Z0-9._-]+$'
    if not re.match(pattern, value):
        return False, "Имя хоста должно содержать только латиницу, цифры, дефис, подчёркивание и точку"
    return True, ""


def validate_ipv4(value: str) -> Tuple[bool, str]:
    """Проверка IPv4 адреса."""
    if not value:
        return True, ""  # пустое значение допустимо для опциональных полей
    try:
        addr = ipaddress.IPv4Address(value)
        # Проверка на ведущие нули
        parts = value.split('.')
        for part in parts:
            if len(part) > 1 and part.startswith('0'):
                return False, f"Октет '{part}' содержит ведущие нули"
        return True, ""
    except ipaddress.AddressValueError:
        return False, "Некорректный формат IPv4 адреса"


def validate_netmask(value: str) -> Tuple[bool, str]:
    """Проверка маски подсети."""
    if not value:
        return True, ""
    valid, msg = validate_ipv4(value)
    if not valid:
        return False, msg
    
    # Проверка что маска корректна (последовательность единиц слева)
    try:
        addr = ipaddress.IPv4Address(value)
        binary = bin(int(addr))[2:].zfill(32)
        # Маска должна быть последовательностью 1 затем 0
        if '01' in binary:
            return False, "Некорректная маска подсети"
        return True, ""
    except:
        return False, "Некорректная маска подсети"


def validate_mac(value: str) -> Tuple[bool, str]:
    """Проверка MAC адреса."""
    if not value:
        return True, ""
    pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
    if not re.match(pattern, value):
        return False, "MAC адрес должен быть в формате XX:XX:XX:XX:XX:XX"
    return True, ""


def validate_iface_name(value: str) -> Tuple[bool, str]:
    """Проверка имени интерфейса."""
    if not value:
        return False, "Имя интерфейса не может быть пустым"
    pattern = r'^eth[01](:[0-9])?$'
    if not re.match(pattern, value):
        return False, "Имя интерфейса должно быть eth0, eth1, eth0:0..eth0:9, eth1:0..eth1:9"
    return True, ""


def validate_integer(value: str, min_val: int, max_val: int) -> Tuple[bool, str]:
    """Проверка целого числа в диапазоне."""
    if not value:
        return True, ""
    try:
        num = int(value)
        if num < min_val or num > max_val:
            return False, f"Значение должно быть в диапазоне {min_val}-{max_val}"
        return True, ""
    except ValueError:
        return False, "Должно быть целое число"


def validate_port_range(value: str, min_port: int = 1, max_port: int = 65535) -> Tuple[bool, str]:
    """Проверка диапазона портов вида '1-15,17-31'."""
    if not value:
        return True, ""
    
    parts = value.split(',')
    all_ports = set()
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = part.split('-')
                start = int(start.strip())
                end = int(end.strip())
                if start < min_port or end > max_port or start > end:
                    return False, f"Некорректный диапазон: {part}"
                ports = set(range(start, end + 1))
            except:
                return False, f"Некорректный диапазон: {part}"
        else:
            try:
                port = int(part)
                if port < min_port or port > max_port:
                    return False, f"Порт {port} вне диапазона {min_port}-{max_port}"
                ports = {port}
            except:
                return False, f"Некорректный порт: {part}"
        
        # Проверка пересечений
        if ports & all_ports:
            return False, f"Пересекающиеся порты в диапазоне"
        all_ports.update(ports)
    
    return True, ""


def validate_cidr(value: str) -> Tuple[bool, str]:
    """Проверка CIDR нотации."""
    if not value:
        return True, ""
    try:
        ipaddress.IPv4Network(value, strict=False)
        return True, ""
    except:
        return False, "Некорректный формат CIDR (например, 192.168.1.0/24)"


def validate_exten_mask(value: str) -> Tuple[bool, str]:
    """Проверка маски расширения."""
    if not value:
        return False, "Маска/номер не могут быть пустыми"
    
    # Простая проверка - номер или маска с _
    if value.startswith('_'):
        # Маска
        mask = value[1:]
        if not mask:
            return False, "Пустая маска после '_'"
        # Допустимые символы в маске: цифры, X, Z, N, [], .
        pattern = r'^[0-9XZN.\[\]-]+$'
        if not re.match(pattern, mask):
            return False, "Недопустимые символы в маске"
    else:
        # Номер - только цифры
        if not value.isdigit():
            return False, "Номер должен содержать только цифры"
    
    return True, ""


def validate_logic_bool(value: str) -> Tuple[bool, str]:
    """Проверка логического значения."""
    if value.lower() in ('true', 'false', 'on', 'off', 'yes', 'no', '1', '0'):
        return True, ""
    return False, "Допустимые значения: true/false, on/off, yes/no"


# ============================================================================
# ГЕНЕРАТОР КОНФИГУРАЦИОННОГО ФАЙЛА
# ============================================================================

class ConfigGenerator:
    """Генератор конфигурационного файла."""
    
    def __init__(self, data: ConfigData):
        self.data = data
    
    def generate(self) -> str:
        """Генерирует полный текст конфигурационного файла."""
        lines = []
        
        # SYSTEM (обязательная)
        lines.append("SYSTEM {")
        lines.append(f" HOSTNAME={self.data.system['HOSTNAME']}")
        lines.append("}")
        lines.append("")
        
        # NTP (необязательная)
        if self.data.ntp:
            lines.append("NTP {")
            if self.data.ntp.get('IP_SRV'):
                lines.append(f" IP_SRV={self.data.ntp['IP_SRV']}")
            if self.data.ntp.get('INTERVAL'):
                lines.append(f" INTERVAL={self.data.ntp['INTERVAL']}")
            lines.append("}")
            lines.append("")
        
        # NETWORK (обязательная)
        lines.append("NETWORK {")
        for iface in self.data.network['IFACE']:
            lines.append(" IFACE {")
            lines.append(f"  IFACE_NAME={iface.get('IFACE_NAME', 'eth0')}")
            if iface.get('IP'):
                lines.append(f"  IP={iface['IP']}")
            if iface.get('NETMASK'):
                lines.append(f"  NETMASK={iface['NETMASK']}")
            if iface.get('BROADCAST'):
                lines.append(f"  BROADCAST={iface['BROADCAST']}")
            if iface.get('MTU'):
                lines.append(f"  MTU={iface['MTU']}")
            if iface.get('METRIC'):
                lines.append(f"  METRIC={iface['METRIC']}")
            if iface.get('SPEED'):
                lines.append(f"  SPEED={iface['SPEED']}")
            if iface.get('DUPLEX'):
                lines.append(f"  DUPLEX={iface['DUPLEX']}")
            if iface.get('AUTONEG'):
                lines.append(f"  AUTONEG={iface['AUTONEG']}")
            lines.append(" }")
        
        for route in self.data.network['ROUTE']:
            lines.append(" ROUTE {")
            if route.get('IFACE_NAME'):
                lines.append(f"  IFACE_NAME={route['IFACE_NAME']}")
            if route.get('NET'):
                lines.append(f"  NET={route['NET']}")
            if route.get('NETMASK'):
                lines.append(f"  NETMASK={route['NETMASK']}")
            if route.get('GATEWAY'):
                lines.append(f"  GATEWAY={route['GATEWAY']}")
            if route.get('DEFAULT_GW'):
                lines.append(f"  DEFAULT_GW={'true' if route['DEFAULT_GW'] else 'false'}")
            if route.get('METRIC'):
                lines.append(f"  METRIC={route['METRIC']}")
            lines.append(" }")
        
        for arp in self.data.network['ARP']:
            lines.append(" ARP {")
            if arp.get('IP'):
                lines.append(f"  IP={arp['IP']}")
            if arp.get('MAC'):
                lines.append(f"  MAC={arp['MAC'].lower()}")
            lines.append(" }")
        
        lines.append("}")
        lines.append("")
        
        # MPLS (необязательная)
        if self.data.mpls['MPLS_RULE_OUT'] or self.data.mpls['MPLS_RULE_IN']:
            lines.append("MPLS {")
            for rule in self.data.mpls['MPLS_RULE_OUT']:
                lines.append(" MPLS_RULE_OUT {")
                if rule.get('IP_DEST'):
                    lines.append(f"  IP_DEST={rule['IP_DEST']}")
                if rule.get('LABEL'):
                    lines.append(f"  LABEL={rule['LABEL']}")
                if rule.get('OUT_IFACE_NAME'):
                    lines.append(f"  OUT_IFACE_NAME={rule['OUT_IFACE_NAME']}")
                if rule.get('IP_NEXT'):
                    lines.append(f"  IP_NEXT={rule['IP_NEXT']}")
                lines.append(" }")
            
            for rule in self.data.mpls['MPLS_RULE_IN']:
                lines.append(" MPLS_RULE_IN {")
                if rule.get('IN_IFACE_NAME'):
                    lines.append(f"  IN_IFACE_NAME={rule['IN_IFACE_NAME']}")
                if rule.get('LABEL'):
                    lines.append(f"  LABEL={rule['LABEL']}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # TUNNELS (необязательная)
        if self.data.tunnels:
            lines.extend(self._generate_tunnels())
        
        # TC (необязательная)
        if self.data.tc:
            lines.append("TC {")
            for tc in self.data.tc:
                lines.extend(self._generate_tc(tc))
            lines.append("}")
            lines.append("")
        
        # IPTABLES (необязательная)
        if self.iptables_has_rules():
            lines.extend(self._generate_iptables())
        
        # IAX (необязательная)
        if self.data.iax['GENERAL'] or self.data.iax['IAX_ROUTE']:
            lines.append("IAX {")
            if self.data.iax['GENERAL']:
                lines.append(" GENERAL {")
                for key, val in self.data.iax['GENERAL'].items():
                    if val is not None and val != '':
                        if isinstance(val, bool):
                            val = 'true' if val else 'false'
                        lines.append(f"  {key}={val}")
                lines.append(" }")
            
            for route in self.data.iax['IAX_ROUTE']:
                lines.append(" IAX_ROUTE {")
                for key, val in route.items():
                    if val is not None and val != '':
                        if isinstance(val, bool):
                            val = 'true' if val else 'false'
                        elif isinstance(val, list):
                            val = ','.join(str(v) for v in val)
                        lines.append(f"  {key}={val}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # SIP (необязательная)
        if self.data.sip['GENERAL'] or self.data.sip['PHONE']:
            lines.append("SIP {")
            if self.data.sip['GENERAL']:
                lines.append(" GENERAL {")
                for key, val in self.data.sip['GENERAL'].items():
                    if val is not None and val != '':
                        if isinstance(val, bool):
                            val = 'true' if val else 'false'
                        lines.append(f"  {key}={val}")
                lines.append(" }")
            
            for phone in self.data.sip['PHONE']:
                lines.append(" PHONE {")
                for key, val in phone.items():
                    if val is not None and val != '':
                        if isinstance(val, bool):
                            val = 'true' if val else 'false'
                        lines.append(f"  {key}={val}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # ZAPTEL (необязательная)
        if self.zaptel_has_data():
            lines.append("ZAPTEL {")
            if self.data.zaptel.get('LOADZONE'):
                lines.append(f" LOADZONE={self.data.zaptel['LOADZONE']}")
            if self.data.zaptel.get('DEFAULTZONE'):
                lines.append(f" DEFAULTZONE={self.data.zaptel['DEFAULTZONE']}")
            if self.data.zaptel.get('FXOKS'):
                lines.append(f" FXOKS=\"{self.data.zaptel['FXOKS']}\"")
            if self.data.zaptel.get('DYNAMIC'):
                lines.append(f" DYNAMIC=\"{self.data.zaptel['DYNAMIC']}\"")
            
            for e1 in self.data.zaptel['CHAN_E1']:
                lines.append(" CHAN_E1 {")
                if 'SPAN' in e1:
                    span = e1['SPAN']
                    lines.append("  SPAN {")
                    if span.get('NUMBER'):
                        lines.append(f"   NUMBER={span['NUMBER']}")
                    if span.get('TIMING'):
                        lines.append(f"   TIMING={span['TIMING']}")
                    if span.get('LBO'):
                        lines.append(f"   LBO={span['LBO']}")
                    if span.get('FRAMING'):
                        lines.append(f"   FRAMING={span['FRAMING']}")
                    if span.get('CODING'):
                        lines.append(f"   CODING={span['CODING']}")
                    lines.append("  }")
                if e1.get('BCHAN'):
                    lines.append(f"  BCHAN=\"{e1['BCHAN']}\"")
                if e1.get('HARDHDLC'):
                    lines.append(f"  HARDHDLC={e1['HARDHDLC']}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # ZAPATA (необязательная)
        if self.zapata_has_data():
            lines.append("ZAPATA {")
            if self.data.zapata.get('CONTEXT'):
                lines.append(f" CONTEXT={self.data.zapata['CONTEXT']}")
            if self.data.zapata.get('SWITCHTYPE'):
                lines.append(f" SWITCHTYPE={self.data.zapata['SWITCHTYPE']}")
            if self.data.zapata.get('SIGNALLING'):
                lines.append(f" SIGNALLING={self.data.zapata['SIGNALLING']}")
            lines.append(f" ECHOCANCEL={'true' if self.data.zapata.get('ECHOCANCEL', True) else 'false'}")
            if self.data.zapata.get('OVERLAPDIAL') is not None:
                lines.append(f" OVERLAPDIAL={'true' if self.data.zapata['OVERLAPDIAL'] else 'false'}")
            if self.data.zapata.get('RXGAIN'):
                lines.append(f" RXGAIN={self.data.zapata['RXGAIN']}")
            if self.data.zapata.get('TXGAIN'):
                lines.append(f" TXGAIN={self.data.zapata['TXGAIN']}")
            if self.data.zapata.get('GROUP'):
                lines.append(f" GROUP={self.data.zapata['GROUP']}")
            
            for chan in self.data.zapata['CHAN']:
                lines.append(" CHAN {")
                for key, val in chan.items():
                    if val is not None and val != '':
                        lines.append(f"  {key}={val}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # EXTENSIONS (обязательная)
        lines.append("EXTENSIONS {")
        lines.append(" GENERAL {")
        for key, val in self.data.extensions['GENERAL'].items():
            lines.append(f"  {key}={'true' if val else 'false'}")
        lines.append(" }")
        
        if self.data.extensions['GLOBALS']:
            lines.append(" GLOBALS {")
            for var, value in self.data.extensions['GLOBALS']:
                lines.append(f"  {var}={value}")
            lines.append(" }")
        
        for group in self.data.extensions['EXTENGROUP']:
            lines.append(" EXTENGROUP {")
            lines.append(f"  NAME={group['NAME']}")
            for exten in group.get('EXTEN', []):
                exten_str = self._format_exten(exten)
                lines.append(f"  EXTEN=\"{exten_str}\"")
            lines.append(" }")
        
        lines.append("}")
        lines.append("")
        
        # ALARM (необязательная)
        if self.data.alarm:
            lines.append("ALARM {")
            for event in self.data.alarm:
                lines.extend(self._generate_alarm_event(event))
            lines.append("}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_exten(self, exten: dict) -> str:
        """Форматирует строку EXTEN."""
        field1 = exten.get('field1', '')
        field2 = exten.get('field2', '')
        field3 = exten.get('field3', '')
        field4 = exten.get('field4', '')
        
        return f"{field1}:{field2}:{field3}:{field4}"
    
    def _generate_tunnels(self) -> List[str]:
        """Генерирует секцию TUNNELS."""
        lines = ["TUNNELS {"]
        t = self.data.tunnels
        
        if t.get('OPTIONS'):
            lines.append(" OPTIONS {")
            opts = t['OPTIONS']
            if opts.get('PORT'):
                lines.append(f"  PORT={opts['PORT']}")
            if opts.get('IFACE_NAME'):
                lines.append(f"  IFACE_NAME={opts['IFACE_NAME']}")
            for cmd in opts.get('COMMAND', []):
                lines.append(f"  COMMAND=\"{cmd}\"")
            lines.append(" }")
        
        if t.get('DEFAULT'):
            lines.append(" DEFAULT {")
            d = t['DEFAULT']
            if d.get('COMPRESS') is not None:
                lines.append(f"  COMPRESS={'true' if d['COMPRESS'] else 'false'}")
            if d.get('SPEED'):
                lines.append(f"  SPEED=\"{d['SPEED']}\"")
            lines.append(" }")
        
        for tun in t.get('TUN', []):
            lines.append(" TUN {")
            lines.append(f"  FROM={tun.get('FROM', '')}")
            lines.append(f"  TO={tun.get('TO', '')}")
            if tun.get('PASSWD'):
                lines.append(f"  PASSWD=\"{tun['PASSWD']}\"")
            if tun.get('TYPE'):
                lines.append(f"  TYPE={tun['TYPE']}")
            if tun.get('PROTO'):
                lines.append(f"  PROTO={tun['PROTO']}")
            if tun.get('COMPRESS') is not None:
                lines.append(f"  COMPRESS={'true' if tun['COMPRESS'] else 'false'}")
            if tun.get('ENCRYPT') is not None:
                lines.append(f"  ENCRYPT={'true' if tun['ENCRYPT'] else 'false'}")
            if tun.get('KEEPALIVE') is not None:
                lines.append(f"  KEEPALIVE={'true' if tun['KEEPALIVE'] else 'false'}")
            if tun.get('PERSIST') is not None:
                lines.append(f"  PERSIST={'true' if tun['PERSIST'] else 'false'}")
            if tun.get('SPEED'):
                lines.append(f"  SPEED=\"{tun['SPEED']}\"")
            
            if tun.get('UP'):
                lines.append("  UP {")
                for run in tun['UP']:
                    escaped = run.replace('"', '\\"')
                    lines.append(f"   RUN='{escaped}'")
                lines.append("  }")
            
            if tun.get('DOWN'):
                lines.append("  DOWN {")
                for run in tun['DOWN']:
                    escaped = run.replace('"', '\\"')
                    lines.append(f"   RUN='{escaped}'")
                lines.append("  }")
            
            lines.append(" }")
        
        if t.get('SERVERS'):
            lines.append(" SERVERS {")
            for srv in t['SERVERS']:
                lines.append(f"  NAME={srv.get('NAME', '')}")
            lines.append(" }")
        
        if t.get('CLIENTS'):
            lines.append(" CLIENTS {")
            for cli in t['CLIENTS']:
                name = cli.get('NAME', '')
                addr = cli.get('ADDR', '')
                lines.append(f"  NAME={name},{addr}")
            lines.append(" }")
        
        lines.append("}")
        lines.append("")
        return lines
    
    def _generate_tc(self, tc: dict) -> List[str]:
        """Генерирует подсекцию TC."""
        lines = []
        lines.append(" QDISC {")
        lines.append(f"  IFACE_NAME={tc.get('IFACE_NAME', 'eth0')}")
        lines.append(f"  TYPE={tc.get('TYPE', 'htb')}")
        if tc.get('DEFAULT_CLASS'):
            lines.append(f"  DEFAULT_CLASS={tc['DEFAULT_CLASS']}")
        if tc.get('RATE'):
            lines.append(f"  RATE={tc['RATE']}")
        
        for cls in tc.get('CLASSES', []):
            lines.append("  CLASSES {")
            if cls.get('CLASSID'):
                lines.append(f"   CLASSID={cls['CLASSID']}")
            if cls.get('RATE'):
                lines.append(f"   RATE={cls['RATE']}")
            if cls.get('DISCIPLINE'):
                lines.append(f"   DISCIPLINE={cls['DISCIPLINE']}")
            lines.append("  }")
        
        for filt in tc.get('FILTER', []):
            lines.append("  FILTER {")
            if filt.get('TAG'):
                lines.append(f"   TAG=\"{filt['TAG']}\"")
            if filt.get('FLOWID'):
                lines.append(f"   FLOWID={filt['FLOWID']}")
            lines.append("  }")
        
        lines.append(" }")
        return lines
    
    def iptables_has_rules(self) -> bool:
        """Проверяет есть ли правила iptables."""
        for chain in ['INPUT', 'OUTPUT', 'FORWARD', 'PREROUTING', 'POSTROUTING']:
            if self.data.iptables.get(chain, []):
                return True
        if self.data.iptables.get('CHAIN', []):
            return True
        return False
    
    def _generate_iptables(self) -> List[str]:
        """Генерирует секцию IPTABLES."""
        lines = ["IPTABLES {"]
        
        for chain_name in ['INPUT', 'OUTPUT', 'FORWARD', 'PREROUTING', 'POSTROUTING']:
            rules = self.data.iptables.get(chain_name, [])
            if rules:
                lines.append(f" {chain_name} {{")
                for rule in rules:
                    lines.append("  RULE {")
                    for key, val in rule.items():
                        if val is not None and val != '':
                            lines.append(f"   {key}={val}")
                    lines.append("  }")
                lines.append(" }")
        
        for chain in self.data.iptables.get('CHAIN', []):
            lines.append(f" CHAIN {{")
            if chain.get('NAME'):
                lines.append(f"  NAME={chain['NAME']}")
            for rule in chain.get('RULES', []):
                lines.append("  RULE {")
                for key, val in rule.items():
                    if val is not None and val != '':
                        lines.append(f"   {key}={val}")
                lines.append("  }")
            lines.append(" }")
        
        lines.append("}")
        lines.append("")
        return lines
    
    def zaptel_has_data(self) -> bool:
        """Проверяет есть ли данные в ZAPTEL."""
        if self.data.zaptel.get('LOADZONE') or self.data.zaptel.get('DEFAULTZONE'):
            return True
        if self.data.zaptel.get('FXOKS') or self.data.zaptel.get('DYNAMIC'):
            return True
        if self.data.zaptel.get('CHAN_E1', []):
            return True
        return False
    
    def zapata_has_data(self) -> bool:
        """Проверяет есть ли данные в ZAPATA."""
        if self.data.zapata.get('CONTEXT'):
            return True
        if self.data.zapata.get('SIGNALLING'):
            return True
        if self.data.zapata.get('CHAN', []):
            return True
        return False
    
    def _generate_alarm_event(self, event: dict) -> List[str]:
        """Генерирует событие ALARM."""
        lines = [" EVENT {"]
        if event.get('NAME'):
            lines.append(f"  NAME={event['NAME']}")
        if event.get('SADDR'):
            lines.append(f"  SADDR={event['SADDR']}")
        if event.get('CLOSE_RELE'):
            lines.append(f"  CLOSE_RELE={event['CLOSE_RELE']}")
        if event.get('OPEN_RELE'):
            lines.append(f"  OPEN_RELE={event['OPEN_RELE']}")
        if event.get('SEND_TO_IP'):
            lines.append(f"  SEND_TO_IP={event['SEND_TO_IP']}")
        
        for log in event.get('LOG', []):
            lines.append("  LOG {")
            if log.get('NAME'):
                lines.append(f"   NAME={log['NAME']}")
            if log.get('STRING'):
                lines.append(f"   STRING=\"{log['STRING']}\"")
            lines.append("  }")
        
        for ind in event.get('INDICATOR', []):
            lines.append("  INDICATOR {")
            if ind.get('NAME'):
                lines.append(f"   NAME={ind['NAME']}")
            if ind.get('COLOR'):
                lines.append(f"   COLOR={ind['COLOR']}")
            if ind.get('FREQUENCY'):
                lines.append(f"   FREQUENCY={ind['FREQUENCY']}")
            lines.append("  }")
        
        lines.append(" }")
        return lines
