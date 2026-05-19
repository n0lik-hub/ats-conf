# -*- coding: utf-8 -*-
"""
Мастер конфигурации IP-АТС Т76-С - Модуль данных и генерации
Версия: 2.1
"""

import re
from typing import Dict, List, Any, Optional


def validate_ipv4(ip: str) -> bool:
    """Проверяет корректность IPv4 адреса."""
    if not ip:
        return False
    pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    match = re.match(pattern, ip)
    if not match:
        return False
    for octet in match.groups():
        if int(octet) > 255:
            return False
        # Проверка на ведущие нули (кроме самого 0)
        if len(octet) > 1 and octet.startswith('0'):
            return False
    return True


def validate_netmask(mask: str) -> bool:
    """Проверяет корректность маски подсети."""
    if not validate_ipv4(mask):
        return False
    # Маска должна быть последовательностью единиц слева
    octets = mask.split('.')
    binary = ''.join(format(int(o), '08b') for o in octets)
    # Должна быть последовательность 1 затем 0
    return '01' not in binary


def validate_mac(mac: str) -> bool:
    """Проверяет корректность MAC адреса."""
    if not mac:
        return False
    pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
    return bool(re.match(pattern, mac))


def validate_hostname(hostname: str) -> bool:
    """Проверяет корректность имени хоста."""
    if not hostname:
        return False
    if len(hostname) > 63:
        return False
    pattern = r'^[a-zA-Z0-9._-]+$'
    return bool(re.match(pattern, hostname))


def validate_integer(value: str, min_val: int = 0, max_val: int = 65535) -> bool:
    """Проверяет что значение целое число в диапазоне."""
    if not value:
        return False
    try:
        num = int(value)
        return min_val <= num <= max_val
    except ValueError:
        return False


def validate_port_range(port_range: str, min_port: int = 1, max_port: int = 65535) -> bool:
    """Проверяет диапазон портов формата '1-15,17-31'."""
    if not port_range:
        return False
    parts = port_range.split(',')
    all_ports = set()
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start < min_port or end > max_port or start > end:
                    return False
                ports = set(range(start, end + 1))
                if ports & all_ports:
                    return False  # Пересечение
                all_ports.update(ports)
            except ValueError:
                return False
        else:
            try:
                port = int(part)
                if port < min_port or port > max_port:
                    return False
                if port in all_ports:
                    return False
                all_ports.add(port)
            except ValueError:
                return False
    return len(all_ports) > 0


def validate_cidr(cidr: str) -> bool:
    """Проверяет CIDR нотацию (IP/маска)."""
    if not cidr:
        return False
    parts = cidr.split('/')
    if len(parts) != 2:
        return False
    if not validate_ipv4(parts[0]):
        return False
    try:
        prefix = int(parts[1])
        return 0 <= prefix <= 32
    except ValueError:
        return False


class ConfigData:
    """Хранилище всех данных конфигурации."""
    
    def __init__(self):
        # SYSTEM
        self.system: Dict[str, Any] = {'HOSTNAME': 'ats1'}
        
        # NTP
        self.ntp_enabled: bool = False
        self.ntp: Dict[str, Any] = {'IP_SRV': '', 'INTERVAL': 14400}
        
        # NETWORK
        self.interfaces: List[Dict[str, Any]] = []
        self.routes: List[Dict[str, Any]] = []
        self.arp_entries: List[Dict[str, str]] = []
        
        # MPLS
        self.mpls_enabled: bool = False
        self.mpls_out_rules: List[Dict[str, Any]] = []
        self.mpls_in_rules: List[Dict[str, Any]] = []
        
        # TUNNELS
        self.tunnels_enabled: bool = False
        self.tunnel_options: Dict[str, Any] = {'PORT': 5000, 'IFACE_NAME': '', 'COMMANDS': []}
        self.tunnel_default: Dict[str, Any] = {'COMPRESS': False, 'SPEED': ''}
        self.tunnels: List[Dict[str, Any]] = []
        self.tunnel_servers: List[str] = []
        self.tunnel_clients: List[Dict[str, str]] = []
        
        # TC
        self.tc_enabled: bool = False
        self.qdiscs: List[Dict[str, Any]] = []
        
        # IPTABLES
        self.iptables_enabled: bool = False
        self.iptables_rules: Dict[str, List[Dict[str, Any]]] = {
            'INPUT': [], 'OUTPUT': [], 'FORWARD': [],
            'PREROUTING': [], 'POSTROUTING': [], 'CHAIN': []
        }
        
        # IAX
        self.iax_enabled: bool = False
        self.iax_general: Dict[str, Any] = {
            'AUTOKILL': True, 'BINDADDR': '0.0.0.0', 'BANDWIDTH': 'low',
            'CODECPRIORITY': 'host', 'JITTERBUFFER': False,
            'FORCEJITTERBUFFER': False, 'MAXJITTERBUFFER': 500,
            'MAXJITTERINTERPS': 10, 'RESYNCTHRESHOLD': 1000
        }
        self.iax_routes: List[Dict[str, Any]] = []
        
        # SIP
        self.sip_enabled: bool = False
        self.sip_general: Dict[str, Any] = {
            'CONTEXT': 'default', 'ALLOWOVERLAP': False, 'BINDPORT': 5060,
            'BINDADDR': '0.0.0.0', 'SRVLOOKUP': False, 'DISALLOW': 'all',
            'ALLOW': 'ulaw,alaw', 'REGISTER': '', 'CANREINVITE': False,
            'INSECURE': 'no'
        }
        self.sip_phones: List[Dict[str, Any]] = []
        
        # ZAPTEL
        self.zaptel_enabled: bool = False
        self.zaptel: Dict[str, Any] = {
            'LOADZONE': 'ru', 'DEFAULTZONE': 'ru', 'FXOKS': ''
        }
        self.zaptel_e1: List[Dict[str, Any]] = []
        
        # ZAPATA
        self.zapata_enabled: bool = False
        self.zapata_general: Dict[str, Any] = {
            'CONTEXT': 'default', 'SWITCHTYPE': '', 'SIGNALLING': '',
            'ECHOCANCEL': True, 'OVERLAPDIAL': False, 'RXGAIN': 0.0,
            'TXGAIN': 0.0, 'GROUP': 0
        }
        self.zapata_channels: List[Dict[str, Any]] = []
        
        # EXTENSIONS
        self.extensions_general: Dict[str, bool] = {
            'STATIC': False, 'WRITEPROTECT': False,
            'CLEARGLOBALVARS': False, 'AUTOFALLTHROUGH': True
        }
        self.extensions_globals: Dict[str, str] = {}
        self.extension_groups: List[Dict[str, Any]] = []
        
        # ALARM
        self.alarm_enabled: bool = False
        self.alarm_events: List[Dict[str, Any]] = []
    
    def get_defined_zap_groups(self) -> List[str]:
        """Возвращает список определённых групп Zap."""
        groups = []
        for ch in self.zapata_channels:
            if ch.get('GROUP'):
                groups.append(f"g{ch['GROUP']}")
        return groups
    
    def get_defined_iax_names(self) -> List[str]:
        """Возвращает список определённых имён IAX."""
        return [r.get('NAME', '') for r in self.iax_routes if r.get('NAME')]
    
    def get_defined_sip_numbers(self) -> List[str]:
        """Возвращает список определённых SIP номеров."""
        numbers = []
        for phone in self.sip_phones:
            if phone.get('NUMBER'):
                numbers.append(phone['NUMBER'])
            if phone.get('USERNAME'):
                numbers.append(phone['USERNAME'])
        return numbers


class ConfigGenerator:
    """Генератор конфигурационного файла."""
    
    def __init__(self, config_data: ConfigData):
        self.config_data = config_data
    
    def generate(self) -> str:
        """Генерирует полный текст конфигурационного файла."""
        lines = []
        
        # SYSTEM (обязательная)
        lines.append("SYSTEM {")
        lines.append(f" HOSTNAME={self.config_data.system.get('HOSTNAME', 'ats1')}")
        lines.append("}")
        lines.append("")
        
        # NTP
        if self.config_data.ntp_enabled and self.config_data.ntp.get('IP_SRV'):
            lines.append("NTP {")
            lines.append(f" IP_SRV={self.config_data.ntp['IP_SRV']}")
            lines.append(f" INTERVAL={self.config_data.ntp.get('INTERVAL', 14400)}")
            lines.append("}")
            lines.append("")
        
        # NETWORK (обязательная)
        lines.append("NETWORK {")
        for iface in self.config_data.interfaces:
            lines.append(" IFACE {")
            lines.append(f"  IFACE_NAME={iface.get('IFACE_NAME', 'eth0')}")
            lines.append(f"  IP={iface.get('IP', '')}")
            lines.append(f"  NETMASK={iface.get('NETMASK', '255.255.255.0')}")
            if iface.get('BROADCAST'):
                lines.append(f"  BROADCAST={iface['BROADCAST']}")
            lines.append(f"  MTU={iface.get('MTU', 1500)}")
            lines.append(f"  METRIC={iface.get('METRIC', 1)}")
            if iface.get('SPEED'):
                lines.append(f"  SPEED={iface['SPEED']}")
            if iface.get('DUPLEX'):
                lines.append(f"  DUPLEX={iface['DUPLEX']}")
            lines.append(f"  AUTONEG={iface.get('AUTONEG', 'on')}")
            lines.append(" }")
        
        for route in self.config_data.routes:
            lines.append(" ROUTE {")
            lines.append(f"  IFACE_NAME={route.get('IFACE_NAME', '')}")
            if route.get('NET'):
                lines.append(f"  NET={route['NET']}")
            if route.get('NETMASK'):
                lines.append(f"  NETMASK={route['NETMASK']}")
            lines.append(f"  GATEWAY={route.get('GATEWAY', '')}")
            lines.append(f"  DEFAULT_GW={'true' if route.get('DEFAULT_GW') else 'false'}")
            if route.get('METRIC'):
                lines.append(f"  METRIC={route['METRIC']}")
            lines.append(" }")
        
        for arp in self.config_data.arp_entries:
            lines.append(" ARP {")
            lines.append(f"  IP={arp.get('IP', '')}")
            lines.append(f"  MAC={arp.get('MAC', '').lower()}")
            lines.append(" }")
        
        lines.append("}")
        lines.append("")
        
        # MPLS
        if self.config_data.mpls_enabled:
            lines.append("MPLS {")
            for rule in self.config_data.mpls_out_rules:
                lines.append(" MPLS_RULE_OUT {")
                lines.append(f"  IP_DEST={rule.get('IP_DEST', '')}")
                lines.append(f"  LABEL={rule.get('LABEL', '')}")
                lines.append(f"  OUT_IFACE_NAME={rule.get('OUT_IFACE_NAME', '')}")
                lines.append(f"  IP_NEXT={rule.get('IP_NEXT', '')}")
                lines.append(" }")
            for rule in self.config_data.mpls_in_rules:
                lines.append(" MPLS_RULE_IN {")
                lines.append(f"  IN_IFACE_NAME={rule.get('IN_IFACE_NAME', '')}")
                lines.append(f"  LABEL={rule.get('LABEL', '')}")
                lines.append(" }")
            lines.append("}")
            lines.append("")
        
        # TUNNELS
        if self.config_data.tunnels_enabled:
            lines.append("TUNNELS {")
            lines.append(" OPTIONS {")
            lines.append(f"  PORT={self.config_data.tunnel_options.get('PORT', 5000)}")
            if self.config_data.tunnel_options.get('IFACE_NAME'):
                lines.append(f"  IFACE_NAME={self.config_data.tunnel_options['IFACE_NAME']}")
            for cmd in self.config_data.tunnel_options.get('COMMANDS', []):
                lines.append(f"  COMMAND=\"{cmd}\"")
            lines.append(" }")
            
            if self.config_data.tunnel_default.get('COMPRESS') or self.config_data.tunnel_default.get('SPEED'):
                lines.append(" DEFAULT {")
                lines.append(f"  COMPRESS={'true' if self.config_data.tunnel_default.get('COMPRESS') else 'false'}")
                if self.config_data.tunnel_default.get('SPEED'):
                    lines.append(f"  SPEED={self.config_data.tunnel_default['SPEED']}")
                lines.append(" }")
            
            for tun in self.config_data.tunnels:
                lines.append(" TUN {")
                lines.append(f"  FROM={tun.get('FROM', '')}")
                lines.append(f"  TO={tun.get('TO', '')}")
                lines.append(f"  PASSWD={tun.get('PASSWD', '')}")
                lines.append(f"  TYPE={tun.get('TYPE', 'tun')}")
                lines.append(f"  PROTO={tun.get('PROTO', 'udp')}")
                lines.append(f"  COMPRESS={'true' if tun.get('COMPRESS') else 'false'}")
                lines.append(f"  ENCRYPT={'true' if tun.get('ENCRYPT') else 'false'}")
                lines.append(f"  KEEPALIVE={'true' if tun.get('KEEPALIVE') else 'false'}")
                lines.append(f"  PERSIST={'true' if tun.get('PERSIST') else 'false'}")
                if tun.get('SPEED'):
                    lines.append(f"  SPEED={tun['SPEED']}")
                
                for up_cmd in tun.get('UP_COMMANDS', []):
                    lines.append(f"  UP {{ RUN='{up_cmd}' }}")
                for down_cmd in tun.get('DOWN_COMMANDS', []):
                    lines.append(f"  DOWN {{ RUN='{down_cmd}' }}")
                
                lines.append(" }")
            
            for server in self.config_data.tunnel_servers:
                lines.append(" SERVERS {")
                lines.append(f"  NAME={server}")
                lines.append(" }")
            
            for client in self.config_data.tunnel_clients:
                lines.append(" CLIENTS {")
                lines.append(f"  NAME={client.get('NAME', '')},{client.get('ADDRESS', '')}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # TC
        if self.config_data.tc_enabled:
            lines.append("TC {")
            for qdisc in self.config_data.qdiscs:
                lines.append(" QDISC {")
                lines.append(f"  IFACE_NAME={qdisc.get('IFACE_NAME', '')}")
                lines.append(f"  TYPE={qdisc.get('TYPE', 'htb')}")
                if qdisc.get('TYPE') == 'htb':
                    lines.append(f"  DEFAULT_CLASS={qdisc.get('DEFAULT_CLASS', 1)}")
                    lines.append(f"  RATE={qdisc.get('RATE', 1000)}")
                    for cls in qdisc.get('CLASSES', []):
                        lines.append("  CLASSES {")
                        lines.append(f"   CLASSID={cls.get('CLASSID', '')}")
                        lines.append(f"   RATE={cls.get('RATE', '')}")
                        if cls.get('DISCIPLINE'):
                            lines.append(f"   DISCIPLINE={cls['DISCIPLINE']}")
                        lines.append("  }")
                    for filt in qdisc.get('FILTERS', []):
                        lines.append("  FILTER {")
                        lines.append(f"   TAG={filt.get('TAG', '')}")
                        lines.append(f"   FLOWID={filt.get('FLOWID', '')}")
                        lines.append("  }")
                lines.append(" }")
            lines.append("}")
            lines.append("")
        
        # IPTABLES
        if self.config_data.iptables_enabled:
            lines.append("IPTABLES {")
            for chain_name, rules in self.config_data.iptables_rules.items():
                if rules:
                    if chain_name == 'CHAIN':
                        for rule in rules:
                            lines.append(f" CHAIN {{")
                            lines.append(f"  NAME={rule.get('NAME', '')}")
                            if rule.get('RULES'):
                                for r in rule['RULES']:
                                    self._add_iptable_rule(lines, r, indent=2)
                            lines.append(" }")
                    else:
                        for rule in rules:
                            self._add_iptable_rule(lines, rule, chain_name=chain_name)
            lines.append("}")
            lines.append("")
        
        # IAX
        if self.config_data.iax_enabled:
            lines.append("IAX {")
            lines.append(" GENERAL {")
            gen = self.config_data.iax_general
            lines.append(f"  AUTOKILL={'true' if gen.get('AUTOKILL') else 'false'}")
            lines.append(f"  BINDADDR={gen.get('BINDADDR', '0.0.0.0')}")
            lines.append(f"  BANDWIDTH={gen.get('BANDWIDTH', 'low')}")
            lines.append(f"  CODECPRIORITY={gen.get('CODECPRIORITY', 'host')}")
            lines.append(f"  JITTERBUFFER={'true' if gen.get('JITTERBUFFER') else 'false'}")
            lines.append(f"  FORCEJITTERBUFFER={'true' if gen.get('FORCEJITTERBUFFER') else 'false'}")
            lines.append(f"  MAXJITTERBUFFER={gen.get('MAXJITTERBUFFER', 500)}")
            lines.append(f"  MAXJITTERINTERPS={gen.get('MAXJITTERINTERPS', 10)}")
            lines.append(f"  RESYNCTHRESHOLD={gen.get('RESYNCTHRESHOLD', 1000)}")
            lines.append(" }")
            
            for route in self.config_data.iax_routes:
                lines.append(" IAX_ROUTE {")
                lines.append(f"  NAME={route.get('NAME', '')}")
                lines.append(f"  TYPE={route.get('TYPE', 'user')}")
                lines.append(f"  HOST={route.get('HOST', 'dynamic')}")
                if route.get('CONTEXT'):
                    lines.append(f"  CONTEXT={route['CONTEXT']}")
                lines.append(f"  TRUNK={'true' if route.get('TRUNK') else 'false'}")
                if route.get('TRUNKFREQ'):
                    lines.append(f"  TRUNKFREQ={route['TRUNKFREQ']}")
                if route.get('QUALIFY') is not None:
                    lines.append(f"  QUALIFY={route['QUALIFY']}")
                if route.get('ALLOW'):
                    for codec in route['ALLOW']:
                        lines.append(f"  ALLOW={codec}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # SIP
        if self.config_data.sip_enabled:
            lines.append("SIP {")
            lines.append(" GENERAL {")
            gen = self.config_data.sip_general
            lines.append(f"  CONTEXT={gen.get('CONTEXT', 'default')}")
            lines.append(f"  ALLOWOVERLAP={'true' if gen.get('ALLOWOVERLAP') else 'false'}")
            lines.append(f"  BINDPORT={gen.get('BINDPORT', 5060)}")
            lines.append(f"  BINDADDR={gen.get('BINDADDR', '0.0.0.0')}")
            lines.append(f"  SRVLOOKUP={'true' if gen.get('SRVLOOKUP') else 'false'}")
            lines.append(f"  DISALLOW={gen.get('DISALLOW', 'all')}")
            lines.append(f"  ALLOW={gen.get('ALLOW', 'ulaw,alaw')}")
            if gen.get('REGISTER'):
                lines.append(f"  REGISTER=\"{gen['REGISTER']}\"")
            lines.append(f"  CANREINVITE={'true' if gen.get('CANREINVITE') else 'false'}")
            lines.append(f"  INSECURE={gen.get('INSECURE', 'no')}")
            lines.append(" }")
            
            for phone in self.config_data.sip_phones:
                lines.append(" PHONE {")
                lines.append(f"  NUMBER={phone.get('NUMBER', '')}")
                lines.append(f"  TYPE={phone.get('TYPE', 'friend')}")
                lines.append(f"  USERNAME={phone.get('USERNAME', '')}")
                lines.append(f"  SECRET={phone.get('SECRET', '')}")
                lines.append(f"  HOST={phone.get('HOST', 'dynamic')}")
                lines.append(f"  CONTEXT={phone.get('CONTEXT', 'default')}")
                lines.append(f"  DISALLOW={phone.get('DISALLOW', '')}")
                lines.append(f"  ALLOW={phone.get('ALLOW', '')}")
                lines.append(f"  CANREINVITE={'true' if phone.get('CANREINVITE') else 'false'}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # ZAPTEL
        if self.config_data.zaptel_enabled:
            lines.append("ZAPTEL {")
            z = self.config_data.zaptel
            lines.append(f" LOADZONE={z.get('LOADZONE', 'ru')}")
            lines.append(f" DEFAULTZONE={z.get('DEFAULTZONE', 'ru')}")
            if z.get('FXOKS'):
                lines.append(f" FXOKS=\"{z['FXOKS']}\"")
            
            for e1 in self.config_data.zaptel_e1:
                lines.append(" CHAN_E1 {")
                span = e1.get('SPAN', {})
                lines.append("  SPAN {")
                lines.append(f"   NUMBER={span.get('NUMBER', 1)}")
                lines.append(f"   TIMING={span.get('TIMING', 0)}")
                lines.append(f"   LBO={span.get('LBO', 0)}")
                lines.append(f"   FRAMING={span.get('FRAMING', 'ccs')}")
                lines.append(f"   CODING={span.get('CODING', 'hdb3')}")
                lines.append("  }")
                lines.append(f"  BCHAN=\"{e1.get('BCHAN', '')}\"")
                lines.append(f"  HARDHDLC={e1.get('HARDHDLC', 16)}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # ZAPATA
        if self.config_data.zapata_enabled:
            lines.append("ZAPATA {")
            z = self.config_data.zapata_general
            lines.append(f" CONTEXT={z.get('CONTEXT', 'default')}")
            if z.get('SWITCHTYPE'):
                lines.append(f" SWITCHTYPE={z['SWITCHTYPE']}")
            if z.get('SIGNALLING'):
                lines.append(f" SIGNALLING={z['SIGNALLING']}")
            lines.append(f" ECHOCANCEL={'true' if z.get('ECHOCANCEL') else 'false'}")
            lines.append(f" OVERLAPDIAL={'true' if z.get('OVERLAPDIAL') else 'false'}")
            lines.append(f" RXGAIN={z.get('RXGAIN', 0.0)}")
            lines.append(f" TXGAIN={z.get('TXGAIN', 0.0)}")
            if z.get('GROUP'):
                lines.append(f" GROUP={z['GROUP']}")
            
            for ch in self.config_data.zapata_channels:
                lines.append(" CHAN {")
                lines.append(f"  CONTEXT={ch.get('CONTEXT', 'default')}")
                if ch.get('GROUP'):
                    lines.append(f"  GROUP={ch['GROUP']}")
                if ch.get('SIGNALLING'):
                    lines.append(f"  SIGNALLING={ch['SIGNALLING']}")
                lines.append(f"  RXGAIN={ch.get('RXGAIN', 0.0)}")
                lines.append(f"  TXGAIN={ch.get('TXGAIN', 0.0)}")
                if ch.get('CALLERID'):
                    lines.append(f"  CALLERID=\"{ch['CALLERID']}\"")
                lines.append(f"  CHANNEL=\"{ch.get('CHANNEL', '')}\"")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # EXTENSIONS (обязательная)
        lines.append("EXTENSIONS {")
        lines.append(" GENERAL {")
        gen = self.config_data.extensions_general
        lines.append(f"  STATIC={'true' if gen.get('STATIC') else 'false'}")
        lines.append(f"  WRITEPROTECT={'true' if gen.get('WRITEPROTECT') else 'false'}")
        lines.append(f"  CLEARGLOBALVARS={'true' if gen.get('CLEARGLOBALVARS') else 'false'}")
        lines.append(f"  AUTOFALLTHROUGH={'true' if gen.get('AUTOFALLTHROUGH') else 'false'}")
        lines.append(" }")
        
        if self.config_data.extensions_globals:
            lines.append(" GLOBALS {")
            for var, val in self.config_data.extensions_globals.items():
                lines.append(f"  {var}={val}")
            lines.append(" }")
        
        for group in self.config_data.extension_groups:
            lines.append(" EXTENGROUP {")
            lines.append(f"  NAME={group.get('NAME', '')}")
            for exten in group.get('EXTENSIONS', []):
                field1 = exten.get('FIELD1', '')
                field2 = exten.get('FIELD2', '')
                field3 = exten.get('FIELD3', '')
                field4 = exten.get('FIELD4', '')
                exten_str = f"{field1}:{field2}"
                if field3:
                    exten_str += f":{field3}"
                if field4:
                    exten_str += f":{field4}"
                lines.append(f"  EXTEN=\"{exten_str}\"")
            lines.append(" }")
        
        lines.append("}")
        lines.append("")
        
        # ALARM
        if self.config_data.alarm_enabled:
            lines.append("ALARM {")
            for event in self.config_data.alarm_events:
                lines.append(" EVENT {")
                lines.append(f"  NAME={event.get('NAME', '')}")
                if event.get('SADDR'):
                    lines.append(f"  SADDR={event['SADDR']}")
                if event.get('CLOSE_RELE'):
                    lines.append(f"  CLOSE_RELE={event['CLOSE_RELE']}")
                if event.get('OPEN_RELE'):
                    lines.append(f"  OPEN_RELE={event['OPEN_RELE']}")
                if event.get('SEND_TO_IP'):
                    lines.append(f"  SEND_TO_IP={event['SEND_TO_IP']}")
                
                for log in event.get('LOGS', []):
                    lines.append("  LOG {")
                    lines.append(f"   NAME={log.get('NAME', 'fail')}")
                    lines.append(f"   STRING=\"{log.get('STRING', '')}\"")
                    lines.append("  }")
                
                for ind in event.get('INDICATORS', []):
                    lines.append("  INDICATOR {")
                    lines.append(f"   NAME={ind.get('NAME', 'fail')}")
                    lines.append(f"   COLOR={ind.get('COLOR', 'red')}")
                    lines.append(f"   FREQUENCY={ind.get('FREQUENCY', 'low')}")
                    lines.append("  }")
                
                lines.append(" }")
            lines.append("}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _add_iptable_rule(self, lines: List[str], rule: Dict[str, Any], 
                          chain_name: str = '', indent: int = 1):
        """Добавляет правило iptables в список строк."""
        prefix = " " * indent
        if chain_name and chain_name != 'CHAIN':
            lines.append(f"{prefix}{chain_name} {{")
        else:
            lines.append(f"{prefix}RULE {{")
        
        if rule.get('ACTION'):
            lines.append(f"{prefix} ACTION={rule['ACTION']}")
        if rule.get('PROTOCOL'):
            lines.append(f"{prefix} PROTOCOL={rule['PROTOCOL']}")
        if rule.get('SPORT'):
            lines.append(f"{prefix} SPORT={rule['SPORT']}")
        if rule.get('DPORT'):
            lines.append(f"{prefix} DPORT={rule['DPORT']}")
        if rule.get('IN_IFACE_NAME'):
            lines.append(f"{prefix} IN_IFACE_NAME={rule['IN_IFACE_NAME']}")
        if rule.get('OUT_IFACE_NAME'):
            lines.append(f"{prefix} OUT_IFACE_NAME={rule['OUT_IFACE_NAME']}")
        if rule.get('SADDR'):
            lines.append(f"{prefix} SADDR={rule['SADDR']}")
        if rule.get('DADDR'):
            lines.append(f"{prefix} DADDR={rule['DADDR']}")
        if rule.get('MATCH'):
            lines.append(f"{prefix} MATCH={rule['MATCH']}")
        if rule.get('MATCH_PARAMS'):
            lines.append(f"{prefix} MATCH_PARAMS=\"{rule['MATCH_PARAMS']}\"")
        if rule.get('ICMP_TYPE'):
            lines.append(f"{prefix} ICMP_TYPE={rule['ICMP_TYPE']}")
        if rule.get('TO_DEST'):
            lines.append(f"{prefix} TO_DEST={rule['TO_DEST']}")
        if rule.get('SOURCE_TO'):
            lines.append(f"{prefix} SOURCE_TO={rule['SOURCE_TO']}")
        if rule.get('EVENT'):
            lines.append(f"{prefix} EVENT={rule['EVENT']}")
        
        if chain_name and chain_name != 'CHAIN':
            lines.append(f"{prefix}}}")
        else:
            lines.append(f"{prefix}}}")
