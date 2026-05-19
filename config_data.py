"""
Модуль для хранения конфигурационных данных IP-АТС Т76-С.
Все данные хранятся в словарях и списках, независимых от интерфейса.
"""

from typing import Dict, List, Any, Optional


class ConfigData:
    """Класс для хранения всех данных конфигурации."""
    
    def __init__(self):
        # Секция SYSTEM (обязательная)
        self.system: Dict[str, Any] = {
            'hostname': 'ats1'
        }
        
        # Секция NTP (необязательная)
        self.ntp_enabled: bool = False
        self.ntp: Dict[str, Any] = {
            'ip_srv': '',
            'interval': 14400
        }
        
        # Секция NETWORK (обязательная)
        self.network_ifaces: List[Dict[str, Any]] = []
        self.network_routes: List[Dict[str, Any]] = []
        self.network_arp: List[Dict[str, Any]] = []
        
        # Секция MPLS (необязательная)
        self.mpls_enabled: bool = False
        self.mpls_out: List[Dict[str, Any]] = []
        self.mpls_in: List[Dict[str, Any]] = []
        
        # Секция TUNNELS (необязательная)
        self.tunnels_enabled: bool = False
        self.tunnels_options: Dict[str, Any] = {
            'port': 5000,
            'iface_name': '',
            'commands': ['/sbin/ifconfig', '/sbin/route']
        }
        self.tunnels_default: Dict[str, Any] = {
            'compress': False,
            'speed': ''
        }
        self.tunnels: List[Dict[str, Any]] = []
        self.tunnels_servers: List[str] = []
        self.tunnels_clients: List[Dict[str, str]] = []
        
        # Секция TC (необязательная)
        self.tc_enabled: bool = False
        self.tc_qdiscs: List[Dict[str, Any]] = []
        
        # Секция IPTABLES (необязательная)
        self.iptables_enabled: bool = False
        self.iptables_rules: Dict[str, List[Dict[str, Any]]] = {
            'INPUT': [],
            'OUTPUT': [],
            'FORWARD': [],
            'PREROUTING': [],
            'POSTROUTING': [],
            'CHAIN': []
        }
        self.iptables_chains: List[str] = []
        
        # Секция IAX (необязательная)
        self.iax_enabled: bool = False
        self.iax_general: Dict[str, Any] = {
            'autokill': True,
            'bindaddr': '0.0.0.0',
            'bandwidth': 'low',
            'codecpriority': 'host',
            'jitterbuffer': False,
            'forcejitterbuffer': False,
            'maxjitterbuffer': 500,
            'maxjitterinterps': 10,
            'resyncreshold': 1000
        }
        self.iax_routes: List[Dict[str, Any]] = []
        
        # Секция SIP (необязательная)
        self.sip_enabled: bool = False
        self.sip_general: Dict[str, Any] = {
            'context': '',
            'allowoverlap': False,
            'bindport': 5060,
            'bindaddr': '0.0.0.0',
            'srvlookup': False,
            'disallow': 'all',
            'allow': 'ulaw,alaw',
            'register': '',
            'canreinvite': False,
            'insecure': 'no'
        }
        self.sip_phones: List[Dict[str, Any]] = []
        
        # Секция ZAPTEL (необязательная)
        self.zaptel_enabled: bool = False
        self.zaptel: Dict[str, Any] = {
            'loadzone': 'ru',
            'defaultzone': 'ru',
            'fxoks': ''
        }
        self.zaptel_e1: List[Dict[str, Any]] = []
        
        # Секция ZAPATA (необязательная)
        self.zapata_enabled: bool = False
        self.zapata_general: Dict[str, Any] = {
            'context': '',
            'switchtype': '',
            'signalling': '',
            'echocancel': True,
            'overlapdial': False,
            'rxgain': 0.0,
            'txgain': 0.0,
            'group': 0
        }
        self.zapata_channels: List[Dict[str, Any]] = []
        
        # Секция EXTENSIONS (обязательная)
        self.extensions_general: Dict[str, Any] = {
            'static': False,
            'writeprotect': False,
            'clearglobalvars': False,
            'autofallthrough': True
        }
        self.extensions_globals: List[Dict[str, str]] = []
        self.extensions_groups: List[Dict[str, Any]] = []
        
        # Секция ALARM (необязательная)
        self.alarm_enabled: bool = False
        self.alarm_events: List[Dict[str, Any]] = []
        
        # Справочники для проверки ссылочной целостности
        self.zapata_groups: List[int] = []  # Номера групп Zap
        self.iax_names: List[str] = []  # Имена IAX routes
        self.sip_numbers: List[str] = []  # Номера SIP телефонов
        
    def reset(self):
        """Сброс всех данных к начальным значениям."""
        self.__init__()
        
    # Методы для работы с сетевыми интерфейсами
    def add_iface(self, iface_data: Dict[str, Any]):
        """Добавить сетевой интерфейс."""
        self.network_ifaces.append(iface_data)
        
    def remove_iface(self, index: int):
        """Удалить сетевой интерфейс по индексу."""
        if 0 <= index < len(self.network_ifaces):
            del self.network_ifaces[index]
            
    def get_iface_names(self) -> List[str]:
        """Получить список имен интерфейсов."""
        return [iface['iface_name'] for iface in self.network_ifaces if 'iface_name' in iface]
    
    # Методы для работы с маршрутами
    def add_route(self, route_data: Dict[str, Any]):
        """Добавить маршрут."""
        self.network_routes.append(route_data)
        
    def remove_route(self, index: int):
        """Удалить маршрут по индексу."""
        if 0 <= index < len(self.network_routes):
            del self.network_routes[index]
            
    def check_default_gw(self) -> bool:
        """Проверить, что ровно один маршрут является шлюзом по умолчанию."""
        default_gw_count = sum(1 for r in self.network_routes if r.get('default_gw', False))
        return default_gw_count <= 1
    
    # Методы для работы с ARP
    def add_arp(self, arp_data: Dict[str, str]):
        """Добавить ARP запись."""
        self.network_arp.append(arp_data)
        
    def remove_arp(self, index: int):
        """Удалить ARP запись по индексу."""
        if 0 <= index < len(self.network_arp):
            del self.network_arp[index]
    
    # Методы для работы с расширениями
    def add_extension_group(self, group_data: Dict[str, Any]):
        """Добавить группу расширений (контекст)."""
        self.extensions_groups.append(group_data)
        
    def remove_extension_group(self, index: int):
        """Удалить группу расширений по индексу."""
        if 0 <= index < len(self.extensions_groups):
            del self.extensions_groups[index]
            
    def add_extension_to_group(self, group_index: int, exten_data: Dict[str, Any]):
        """Добавить расширение в группу."""
        if 0 <= group_index < len(self.extensions_groups):
            if 'extens' not in self.extensions_groups[group_index]:
                self.extensions_groups[group_index]['extens'] = []
            self.extensions_groups[group_index]['extens'].append(exten_data)
            
    def remove_extension_from_group(self, group_index: int, exten_index: int):
        """Удалить расширение из группы."""
        if 0 <= group_index < len(self.extensions_groups):
            group = self.extensions_groups[group_index]
            if 'extens' in group and 0 <= exten_index < len(group['extens']):
                del group['extens'][exten_index]
    
    # Методы для обновления справочников ссылочной целостности
    def update_zapata_groups(self):
        """Обновить список групп Zap из секции ZAPATA."""
        self.zapata_groups = []
        for chan in self.zapata_channels:
            if 'group' in chan and chan['group']:
                try:
                    grp = int(chan['group'])
                    if grp not in self.zapata_groups:
                        self.zapata_groups.append(grp)
                except (ValueError, TypeError):
                    pass
                    
    def update_iax_names(self):
        """Обновить список имен IAX routes."""
        self.iax_names = [route['name'] for route in self.iax_routes if 'name' in route and route['name']]
        
    def update_sip_numbers(self):
        """Обновить список номеров SIP телефонов."""
        self.sip_numbers = [phone['number'] for phone in self.sip_phones if 'number' in phone and phone['number']]
        
    def validate_extension_reference(self, tech: str, identifier: str) -> bool:
        """
        Проверить ссылочную целостность для расширения.
        tech: Zap, SIP, IAX2
        identifier: имя группы, номер телефона и т.д.
        """
        if tech == 'Zap':
            # Проверяем, является ли identifier группой (g1, g2 и т.д.) или номером порта
            if identifier.startswith('g'):
                try:
                    grp_num = int(identifier[1:])
                    return grp_num in self.zapata_groups
                except ValueError:
                    return False
            else:
                # Проверяем номер порта (1-110)
                try:
                    port = int(identifier)
                    return 1 <= port <= 110
                except ValueError:
                    return False
        elif tech == 'SIP':
            return identifier in self.sip_numbers or identifier.isdigit()  # Разрешаем любые цифры
        elif tech == 'IAX2':
            return identifier in self.iax_names or identifier.startswith('to_')
        return True
