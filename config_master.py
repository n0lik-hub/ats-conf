# -*- coding: utf-8 -*-
"""
Мастер конфигурации IP-АТС Т76-С - Хранение данных и генерация конфигурации
Версия: 2.1
"""

from typing import Dict, List, Any, Optional
import re


# ============================================================================
# КЛАСС ДЛЯ ХРАНЕНИЯ ДАННЫХ КОНФИГУРАЦИИ
# ============================================================================

class ConfigData:
    """Контейнер для всех данных конфигурации."""
    
    def __init__(self):
        # SYSTEM
        self.system: Dict[str, Any] = {'HOSTNAME': 'ats1'}
        
        # NTP
        self.ntp_enabled: bool = False
        self.ntp: Dict[str, Any] = {
            'IP_SRV': '',
            'INTERVAL': 14400
        }
        
        # NETWORK
        self.network: Dict[str, List[Dict]] = {
            'IFACE': [],
            'ROUTE': [],
            'ARP': []
        }
        
        # MPLS
        self.mpls_enabled: bool = False
        self.mpls: Dict[str, List[Dict]] = {
            'MPLS_RULE_OUT': [],
            'MPLS_RULE_IN': []
        }
        
        # TUNNELS
        self.tunnels_enabled: bool = False
        self.tunnels: Dict[str, Any] = {
            'OPTIONS': {'PORT': 5000, 'IFACE_NAME': '', 'COMMANDS': []},
            'DEFAULT': {'COMPRESS': False, 'SPEED': ''},
            'TUN': [],
            'SERVERS': [],
            'CLIENTS': []
        }
        
        # TC
        self.tc_enabled: bool = False
        self.tc: List[Dict] = []
        
        # IPTABLES
        self.iptables_enabled: bool = False
        self.iptables: Dict[str, List[Dict]] = {
            'INPUT': [],
            'OUTPUT': [],
            'FORWARD': [],
            'PREROUTING': [],
            'POSTROUTING': [],
            'CHAIN': []
        }
        
        # IAX
        self.iax_enabled: bool = False
        self.iax: Dict[str, Any] = {
            'GENERAL': {
                'AUTOKILL': True,
                'BINDADDR': '0.0.0.0',
                'BANDWIDTH': 'low',
                'CODECPRIORITY': 'host',
                'JITTERBUFFER': False,
                'FORCEJITTERBUFFER': False,
                'MAXJITTERBUFFER': 500,
                'MAXJITTERINTERPS': 10,
                'RESYNCTHRESHOLD': 1000
            },
            'IAX_ROUTE': []
        }
        
        # SIP
        self.sip_enabled: bool = False
        self.sip: Dict[str, Any] = {
            'GENERAL': {
                'CONTEXT': '',
                'ALLOWOVERLAP': False,
                'BINDPORT': 5060,
                'BINDADDR': '0.0.0.0',
                'SRVLOOKUP': False,
                'DISALLOW': 'all',
                'ALLOW': '',
                'REGISTER': '',
                'CANREINVITE': False,
                'INSECURE': 'no'
            },
            'PHONE': []
        }
        
        # ZAPTEL
        self.zaptel_enabled: bool = False
        self.zaptel: Dict[str, Any] = {
            'LOADZONE': 'ru',
            'DEFAULTZONE': 'ru',
            'FXOKS': '',
            'DYNAMIC': '',
            'CHAN_E1': []
        }
        
        # ZAPATA
        self.zapata_enabled: bool = False
        self.zapata: Dict[str, Any] = {
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
        
        # EXTENSIONS
        self.extensions: Dict[str, Any] = {
            'GENERAL': {
                'STATIC': False,
                'WRITEPROTECT': False,
                'CLEARGLOBALVARS': False,
                'AUTOFALLTHROUGH': True
            },
            'GLOBALS': [],
            'EXTENGROUP': []
        }
        
        # ALARM
        self.alarm_enabled: bool = False
        self.alarm: List[Dict] = []
        
        # Справочники для проверки ссылочной целостности
        self.zap_groups: List[str] = []  # Группы Zap (g1, g2, ...)
        self.iax_names: List[str] = []   # Имена IAX_ROUTE
        self.sip_numbers: List[str] = [] # Номера SIP PHONE
    
    def reset(self):
        """Сбрасывает все данные к значениям по умолчанию."""
        self.__init__()


# ============================================================================
# ГЕНЕРАТОР КОНФИГУРАЦИОННОГО ФАЙЛА
# ============================================================================

class ConfigGenerator:
    """Генерирует текст конфигурационного файла на основе ConfigData."""
    
    def __init__(self, config_data: ConfigData):
        self.data = config_data
    
    def generate(self) -> str:
        """Генерирует полный текст конфигурации."""
        lines = []
        
        # SYSTEM (всегда)
        lines.extend(self._generate_system())
        
        # NTP (если включена)
        if self.data.ntp_enabled:
            lines.extend(self._generate_ntp())
        
        # NETWORK (всегда, если есть интерфейсы)
        if self.data.network['IFACE']:
            lines.extend(self._generate_network())
        
        # MPLS (если включена)
        if self.data.mpls_enabled and (self.data.mpls['MPLS_RULE_OUT'] or self.data.mpls['MPLS_RULE_IN']):
            lines.extend(self._generate_mpls())
        
        # TUNNELS (если включена)
        if self.data.tunnels_enabled:
            lines.extend(self._generate_tunnels())
        
        # TC (если включена)
        if self.data.tc_enabled and self.data.tc:
            lines.extend(self._generate_tc())
        
        # IPTABLES (если включена)
        if self.data.iptables_enabled:
            lines.extend(self._generate_iptables())
        
        # IAX (если включена)
        if self.data.iax_enabled:
            lines.extend(self._generate_iax())
        
        # SIP (если включена)
        if self.data.sip_enabled:
            lines.extend(self._generate_sip())
        
        # ZAPTEL (если включена)
        if self.data.zaptel_enabled:
            lines.extend(self._generate_zaptel())
        
        # ZAPATA (если включена)
        if self.data.zapata_enabled:
            lines.extend(self._generate_zapata())
        
        # EXTENSIONS (всегда)
        lines.extend(self._generate_extensions())
        
        # ALARM (если включена)
        if self.data.alarm_enabled and self.data.alarm:
            lines.extend(self._generate_alarm())
        
        return '\n'.join(lines)
    
    def _generate_system(self) -> List[str]:
        lines = ['SYSTEM {']
        lines.append(f" HOSTNAME={self.data.system.get('HOSTNAME', 'ats1')}")
        lines.append('}')
        return lines
    
    def _generate_ntp(self) -> List[str]:
        lines = ['NTP {']
        if self.data.ntp.get('IP_SRV'):
            lines.append(f" IP_SRV={self.data.ntp['IP_SRV']}")
        lines.append(f" INTERVAL={self.data.ntp.get('INTERVAL', 14400)}")
        lines.append('}')
        return lines
    
    def _generate_network(self) -> List[str]:
        lines = ['NETWORK {']
        
        # IFACE
        for iface in self.data.network['IFACE']:
            lines.append(' IFACE {')
            lines.append(f"  IFACE_NAME={iface.get('IFACE_NAME', '')}")
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
            lines.append(' }')
        
        # ROUTE
        for route in self.data.network['ROUTE']:
            lines.append(' ROUTE {')
            if route.get('IFACE_NAME'):
                lines.append(f"  IFACE_NAME={route['IFACE_NAME']}")
            if route.get('NET'):
                lines.append(f"  NET={route['NET']}")
            if route.get('NETMASK'):
                lines.append(f"  NETMASK={route['NETMASK']}")
            if route.get('GATEWAY'):
                lines.append(f"  GATEWAY={route['GATEWAY']}")
            lines.append(f"  DEFAULT_GW={'true' if route.get('DEFAULT_GW') else 'false'}")
            if route.get('METRIC'):
                lines.append(f"  METRIC={route['METRIC']}")
            lines.append(' }')
        
        # ARP
        for arp in self.data.network['ARP']:
            lines.append(' ARP {')
            if arp.get('IP'):
                lines.append(f"  IP={arp['IP']}")
            if arp.get('MAC'):
                lines.append(f"  MAC={arp['MAC']}")
            lines.append(' }')
        
        lines.append('}')
        return lines
    
    def _generate_mpls(self) -> List[str]:
        lines = ['MPLS {']
        
        for rule in self.data.mpls['MPLS_RULE_OUT']:
            lines.append(' MPLS_RULE_OUT {')
            if rule.get('IP_DEST'):
                lines.append(f"  IP_DEST={rule['IP_DEST']}")
            if rule.get('LABEL'):
                lines.append(f"  LABEL={rule['LABEL']}")
            if rule.get('OUT_IFACE_NAME'):
                lines.append(f"  OUT_IFACE_NAME={rule['OUT_IFACE_NAME']}")
            if rule.get('IP_NEXT'):
                lines.append(f"  IP_NEXT={rule['IP_NEXT']}")
            lines.append(' }')
        
        for rule in self.data.mpls['MPLS_RULE_IN']:
            lines.append(' MPLS_RULE_IN {')
            if rule.get('IN_IFACE_NAME'):
                lines.append(f"  IN_IFACE_NAME={rule['IN_IFACE_NAME']}")
            if rule.get('LABEL'):
                lines.append(f"  LABEL={rule['LABEL']}")
            lines.append(' }')
        
        lines.append('}')
        return lines
    
    def _generate_tunnels(self) -> List[str]:
        lines = ['TUNNELS {']
        
        # OPTIONS
        opts = self.data.tunnels.get('OPTIONS', {})
        lines.append(' OPTIONS {')
        if opts.get('PORT'):
            lines.append(f"  PORT={opts['PORT']}")
        if opts.get('IFACE_NAME'):
            lines.append(f"  IFACE_NAME={opts['IFACE_NAME']}")
        for cmd in opts.get('COMMANDS', []):
            lines.append(f'  COMMAND="{cmd}"')
        lines.append(' }')
        
        # DEFAULT
        default = self.data.tunnels.get('DEFAULT', {})
        if default.get('COMPRESS') is not None or default.get('SPEED'):
            lines.append(' DEFAULT {')
            if default.get('COMPRESS') is not None:
                lines.append(f"  COMPRESS={'true' if default['COMPRESS'] else 'false'}")
            if default.get('SPEED'):
                lines.append(f"  SPEED={default['SPEED']}")
            lines.append(' }')
        
        # TUN
        for tun in self.data.tunnels.get('TUN', []):
            lines.append(' TUN {')
            if tun.get('FROM'):
                lines.append(f"  FROM={tun['FROM']}")
            if tun.get('TO'):
                lines.append(f"  TO={tun['TO']}")
            if tun.get('PASSWD'):
                lines.append(f"  PASSWD={tun['PASSWD']}")
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
                lines.append(f"  SPEED={tun['SPEED']}")
            
            # UP команды
            for up_cmd in tun.get('UP', []):
                lines.append(f"  UP RUN='{up_cmd}'")
            
            # DOWN команды
            for down_cmd in tun.get('DOWN', []):
                lines.append(f"  DOWN RUN='{down_cmd}'")
            
            lines.append(' }')
        
        # SERVERS
        for srv in self.data.tunnels.get('SERVERS', []):
            lines.append(' SERVERS {')
            if srv.get('NAME'):
                lines.append(f"  NAME={srv['NAME']}")
            lines.append(' }')
        
        # CLIENTS
        for cli in self.data.tunnels.get('CLIENTS', []):
            lines.append(' CLIENTS {')
            if cli.get('NAME'):
                lines.append(f"  NAME={cli['NAME']}")
            if cli.get('ADDRESS'):
                lines.append(f"  ADDRESS={cli['ADDRESS']}")
            lines.append(' }')
        
        lines.append('}')
        return lines
    
    def _generate_tc(self) -> List[str]:
        lines = ['TC {']
        
        for qdisc in self.data.tc:
            lines.append(' QDISC {')
            if qdisc.get('IFACE_NAME'):
                lines.append(f"  IFACE_NAME={qdisc['IFACE_NAME']}")
            if qdisc.get('DISCIPLINE'):
                lines.append(f"  DISCIPLINE={qdisc['DISCIPLINE']}")
            if qdisc.get('RATE'):
                lines.append(f"  RATE={qdisc['RATE']}")
            if qdisc.get('DEFAULT_CLASS'):
                lines.append(f"  DEFAULT_CLASS={qdisc['DEFAULT_CLASS']}")
            
            # CLASSES
            for cls in qdisc.get('CLASSES', []):
                lines.append('  CLASSES {')
                if cls.get('CLASSID'):
                    lines.append(f"   CLASSID={cls['CLASSID']}")
                if cls.get('RATE'):
                    lines.append(f"   RATE={cls['RATE']}")
                if cls.get('DISCIPLINE'):
                    lines.append(f"   DISCIPLINE={cls['DISCIPLINE']}")
                lines.append('  }')
            
            # FILTER
            for flt in qdisc.get('FILTER', []):
                lines.append('  FILTER {')
                if flt.get('TAG'):
                    lines.append(f"   TAG={flt['TAG']}")
                if flt.get('FLOWID'):
                    lines.append(f"   FLOWID={flt['FLOWID']}")
                lines.append('  }')
            
            lines.append(' }')
        
        lines.append('}')
        return lines
    
    def _generate_iptables(self) -> List[str]:
        lines = ['IPTABLES {']
        
        for chain_name in ['INPUT', 'OUTPUT', 'FORWARD', 'PREROUTING', 'POSTROUTING']:
            rules = self.data.iptables.get(chain_name, [])
            for rule in rules:
                lines.append(f' {chain_name} {{')
                if rule.get('ACTION'):
                    lines.append(f"  ACTION={rule['ACTION']}")
                if rule.get('PROTOCOL'):
                    lines.append(f"  PROTOCOL={rule['PROTOCOL']}")
                if rule.get('SPORT'):
                    lines.append(f"  SPORT={rule['SPORT']}")
                if rule.get('DPORT'):
                    lines.append(f"  DPORT={rule['DPORT']}")
                if rule.get('IN_IFACE_NAME'):
                    lines.append(f"  IN_IFACE_NAME={rule['IN_IFACE_NAME']}")
                if rule.get('OUT_IFACE_NAME'):
                    lines.append(f"  OUT_IFACE_NAME={rule['OUT_IFACE_NAME']}")
                if rule.get('SADDR'):
                    lines.append(f"  SADDR={rule['SADDR']}")
                if rule.get('DADDR'):
                    lines.append(f"  DADDR={rule['DADDR']}")
                if rule.get('MATCH'):
                    lines.append(f"  MATCH={rule['MATCH']}")
                if rule.get('MATCH_PARAMS'):
                    lines.append(f"  MATCH_PARAMS={rule['MATCH_PARAMS']}")
                if rule.get('ICMP_TYPE'):
                    lines.append(f"  ICMP_TYPE={rule['ICMP_TYPE']}")
                if rule.get('TO_DEST'):
                    lines.append(f"  TO_DEST={rule['TO_DEST']}")
                if rule.get('SOURCE_TO'):
                    lines.append(f"  SOURCE_TO={rule['SOURCE_TO']}")
                if rule.get('EVENT'):
                    lines.append(f"  EVENT={rule['EVENT']}")
                if rule.get('GOTO'):
                    lines.append(f"  GOTO={rule['GOTO']}")
                lines.append(' }')
        
        # Пользовательские цепочки
        for chain in self.data.iptables.get('CHAIN', []):
            lines.append(f' CHAIN {{')
            if chain.get('NAME'):
                lines.append(f"  NAME={chain['NAME']}")
            for rule in chain.get('RULES', []):
                lines.append('  RULE {')
                if rule.get('ACTION'):
                    lines.append(f"   ACTION={rule['ACTION']}")
                if rule.get('PROTOCOL'):
                    lines.append(f"   PROTOCOL={rule['PROTOCOL']}")
                if rule.get('DPORT'):
                    lines.append(f"   DPORT={rule['DPORT']}")
                lines.append('  }')
            lines.append(' }')
        
        lines.append('}')
        return lines
    
    def _generate_iax(self) -> List[str]:
        lines = ['IAX {']
        
        # GENERAL
        gen = self.data.iax.get('GENERAL', {})
        lines.append(' GENERAL {')
        if gen.get('AUTOKILL') is not None:
            val = gen['AUTOKILL']
            lines.append(f"  AUTOKILL={'true' if val is True else ('false' if val is False else val)}")
        if gen.get('BINDADDR'):
            lines.append(f"  BINDADDR={gen['BINDADDR']}")
        if gen.get('BANDWIDTH'):
            lines.append(f"  BANDWIDTH={gen['BANDWIDTH']}")
        if gen.get('CODECPRIORITY'):
            lines.append(f"  CODECPRIORITY={gen['CODECPRIORITY']}")
        if gen.get('JITTERBUFFER') is not None:
            lines.append(f"  JITTERBUFFER={'true' if gen['JITTERBUFFER'] else 'false'}")
        if gen.get('FORCEJITTERBUFFER') is not None:
            lines.append(f"  FORCEJITTERBUFFER={'true' if gen['FORCEJITTERBUFFER'] else 'false'}")
        if gen.get('MAXJITTERBUFFER'):
            lines.append(f"  MAXJITTERBUFFER={gen['MAXJITTERBUFFER']}")
        if gen.get('MAXJITTERINTERPS'):
            lines.append(f"  MAXJITTERINTERPS={gen['MAXJITTERINTERPS']}")
        if gen.get('RESYNCTHRESHOLD'):
            lines.append(f"  RESYNCTHRESHOLD={gen['RESYNCTHRESHOLD']}")
        lines.append(' }')
        
        # IAX_ROUTE
        for route in self.data.iax.get('IAX_ROUTE', []):
            lines.append(' IAX_ROUTE {')
            if route.get('NAME'):
                lines.append(f"  NAME={route['NAME']}")
            if route.get('TYPE'):
                lines.append(f"  TYPE={route['TYPE']}")
            if route.get('HOST'):
                lines.append(f"  HOST={route['HOST']}")
            if route.get('CONTEXT'):
                lines.append(f"  CONTEXT={route['CONTEXT']}")
            if route.get('TRUNK') is not None:
                lines.append(f"  TRUNK={'true' if route['TRUNK'] else 'false'}")
            if route.get('TRUNKFREQ'):
                lines.append(f"  TRUNKFREQ={route['TRUNKFREQ']}")
            if route.get('QUALIFY') is not None:
                val = route['QUALIFY']
                lines.append(f"  QUALIFY={'true' if val is True else ('false' if val is False else val)}")
            if route.get('QUALIFYFREQOK'):
                lines.append(f"  QUALIFYFREQOK={route['QUALIFYFREQOK']}")
            if route.get('QUALIFYFREQNOTOK'):
                lines.append(f"  QUALIFYFREQNOTOK={route['QUALIFYFREQNOTOK']}")
            if route.get('QUALIFYSMOOTHING') is not None:
                lines.append(f"  QUALIFYSMOOTHING={'true' if route['QUALIFYSMOOTHING'] else 'false'}")
            if route.get('ALLOW'):
                allow_str = ','.join(route['ALLOW']) if isinstance(route['ALLOW'], list) else route['ALLOW']
                lines.append(f"  ALLOW={allow_str}")
            lines.append(' }')
        
        lines.append('}')
        return lines
    
    def _generate_sip(self) -> List[str]:
        lines = ['SIP {']
        
        # GENERAL
        gen = self.data.sip.get('GENERAL', {})
        lines.append(' GENERAL {')
        if gen.get('CONTEXT'):
            lines.append(f"  CONTEXT={gen['CONTEXT']}")
        if gen.get('ALLOWOVERLAP') is not None:
            lines.append(f"  ALLOWOVERLAP={'true' if gen['ALLOWOVERLAP'] else 'false'}")
        if gen.get('BINDPORT'):
            lines.append(f"  BINDPORT={gen['BINDPORT']}")
        if gen.get('BINDADDR'):
            lines.append(f"  BINDADDR={gen['BINDADDR']}")
        if gen.get('SRVLOOKUP') is not None:
            lines.append(f"  SRVLOOKUP={'true' if gen['SRVLOOKUP'] else 'false'}")
        if gen.get('DISALLOW'):
            lines.append(f"  DISALLOW={gen['DISALLOW']}")
        if gen.get('ALLOW'):
            lines.append(f"  ALLOW={gen['ALLOW']}")
        if gen.get('REGISTER'):
            lines.append(f"  REGISTER={gen['REGISTER']}")
        if gen.get('CANREINVITE') is not None:
            lines.append(f"  CANREINVITE={'true' if gen['CANREINVITE'] else 'false'}")
        if gen.get('INSECURE'):
            lines.append(f"  INSECURE={gen['INSECURE']}")
        lines.append(' }')
        
        # PHONE
        for phone in self.data.sip.get('PHONE', []):
            lines.append(' PHONE {')
            if phone.get('NUMBER'):
                lines.append(f"  NUMBER={phone['NUMBER']}")
            if phone.get('TYPE'):
                lines.append(f"  TYPE={phone['TYPE']}")
            if phone.get('USERNAME'):
                lines.append(f"  USERNAME={phone['USERNAME']}")
            if phone.get('SECRET'):
                lines.append(f"  SECRET={phone['SECRET']}")
            if phone.get('HOST'):
                lines.append(f"  HOST={phone['HOST']}")
            if phone.get('CONTEXT'):
                lines.append(f"  CONTEXT={phone['CONTEXT']}")
            if phone.get('DISALLOW'):
                lines.append(f"  DISALLOW={phone['DISALLOW']}")
            if phone.get('ALLOW'):
                lines.append(f"  ALLOW={phone['ALLOW']}")
            if phone.get('CANREINVITE') is not None:
                lines.append(f"  CANREINVITE={'true' if phone['CANREINVITE'] else 'false'}")
            lines.append(' }')
        
        lines.append('}')
        return lines
    
    def _generate_zaptel(self) -> List[str]:
        lines = ['ZAPTEL {']
        
        if self.data.zaptel.get('LOADZONE'):
            lines.append(f" LOADZONE={self.data.zaptel['LOADZONE']}")
        if self.data.zaptel.get('DEFAULTZONE'):
            lines.append(f" DEFAULTZONE={self.data.zaptel['DEFAULTZONE']}")
        if self.data.zaptel.get('FXOKS'):
            lines.append(f" FXOKS={self.data.zaptel['FXOKS']}")
        if self.data.zaptel.get('DYNAMIC'):
            lines.append(f" DYNAMIC={self.data.zaptel['DYNAMIC']}")
        
        # CHAN_E1
        for e1 in self.data.zaptel.get('CHAN_E1', []):
            lines.append(' CHAN_E1 {')
            
            span = e1.get('SPAN', {})
            if span:
                lines.append('  SPAN {')
                if span.get('NUMBER'):
                    lines.append(f"   NUMBER={span['NUMBER']}")
                if span.get('TIMING') is not None:
                    lines.append(f"   TIMING={span['TIMING']}")
                if span.get('LBO') is not None:
                    lines.append(f"   LBO={span['LBO']}")
                if span.get('FRAMING'):
                    lines.append(f"   FRAMING={span['FRAMING']}")
                if span.get('CODING'):
                    lines.append(f"   CODING={span['CODING']}")
                lines.append('  }')
            
            if e1.get('BCHAN'):
                lines.append(f"  BCHAN={e1['BCHAN']}")
            if e1.get('HARDHDLC'):
                lines.append(f"  HARDHDLC={e1['HARDHDLC']}")
            
            lines.append(' }')
        
        lines.append('}')
        return lines
    
    def _generate_zapata(self) -> List[str]:
        lines = ['ZAPATA {']
        
        if self.data.zapata.get('CONTEXT'):
            lines.append(f" CONTEXT={self.data.zapata['CONTEXT']}")
        if self.data.zapata.get('SWITCHTYPE'):
            lines.append(f" SWITCHTYPE={self.data.zapata['SWITCHTYPE']}")
        if self.data.zapata.get('SIGNALLING'):
            lines.append(f" SIGNALLING={self.data.zapata['SIGNALLING']}")
        if self.data.zapata.get('ECHOCANCEL') is not None:
            lines.append(f" ECHOCANCEL={'true' if self.data.zapata['ECHOCANCEL'] else 'false'}")
        if self.data.zapata.get('OVERLAPDIAL') is not None:
            lines.append(f" OVERLAPDIAL={'true' if self.data.zapata['OVERLAPDIAL'] else 'false'}")
        if self.data.zapata.get('RXGAIN'):
            lines.append(f" RXGAIN={self.data.zapata['RXGAIN']}")
        if self.data.zapata.get('TXGAIN'):
            lines.append(f" TXGAIN={self.data.zapata['TXGAIN']}")
        if self.data.zapata.get('GROUP'):
            lines.append(f" GROUP={self.data.zapata['GROUP']}")
        
        # CHAN
        for chan in self.data.zapata.get('CHAN', []):
            lines.append(' CHAN {')
            if chan.get('CONTEXT'):
                lines.append(f"  CONTEXT={chan['CONTEXT']}")
            if chan.get('GROUP'):
                lines.append(f"  GROUP={chan['GROUP']}")
            if chan.get('SIGNALLING'):
                lines.append(f"  SIGNALLING={chan['SIGNALLING']}")
            if chan.get('RXGAIN'):
                lines.append(f"  RXGAIN={chan['RXGAIN']}")
            if chan.get('TXGAIN'):
                lines.append(f"  TXGAIN={chan['TXGAIN']}")
            if chan.get('CALLERID'):
                lines.append(f"  CALLERID={chan['CALLERID']}")
            if chan.get('CHANNEL'):
                lines.append(f"  CHANNEL={chan['CHANNEL']}")
            lines.append(' }')
        
        lines.append('}')
        return lines
    
    def _generate_extensions(self) -> List[str]:
        lines = ['EXTENSIONS {']
        
        # GENERAL
        gen = self.data.extensions.get('GENERAL', {})
        lines.append(' GENERAL {')
        lines.append(f"  STATIC={'true' if gen.get('STATIC') else 'false'}")
        lines.append(f"  WRITEPROTECT={'true' if gen.get('WRITEPROTECT') else 'false'}")
        lines.append(f"  CLEARGLOBALVARS={'true' if gen.get('CLEARGLOBALVARS') else 'false'}")
        lines.append(f"  AUTOFALLTHROUGH={'true' if gen.get('AUTOFALLTHROUGH') else 'false'}")
        lines.append(' }')
        
        # GLOBALS
        for glob in self.data.extensions.get('GLOBALS', []):
            if glob.get('VAR') and glob.get('VALUE'):
                lines.append(f" {glob['VAR']}={glob['VALUE']}")
        
        # EXTENGROUP
        for group in self.data.extensions.get('EXTENGROUP', []):
            lines.append(' EXTENGROUP {')
            if group.get('NAME'):
                lines.append(f"  NAME={group['NAME']}")
            
            for exten in group.get('EXTEN', []):
                field1 = exten.get('field1', '')
                field2 = exten.get('field2', '')
                field3 = exten.get('field3', '')
                field4 = exten.get('field4', '')
                
                exten_str = f"{field1}:{field2}"
                if field3:
                    exten_str += f":{field3}"
                if field4:
                    exten_str += f":{field4}"
                
                lines.append(f'  EXTEN="{exten_str}"')
            
            lines.append(' }')
        
        lines.append('}')
        return lines
    
    def _generate_alarm(self) -> List[str]:
        lines = ['ALARM {']
        
        for event in self.data.alarm:
            lines.append(' EVENT {')
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
            
            # LOG реакции
            for log in event.get('LOG', []):
                lines.append('  LOG {')
                if log.get('NAME'):
                    lines.append(f"   NAME={log['NAME']}")
                if log.get('STRING'):
                    lines.append(f"   STRING={log['STRING']}")
                lines.append('  }')
            
            # INDICATOR реакции
            for ind in event.get('INDICATOR', []):
                lines.append('  INDICATOR {')
                if ind.get('NAME'):
                    lines.append(f"   NAME={ind['NAME']}")
                if ind.get('COLOR'):
                    lines.append(f"   COLOR={ind['COLOR']}")
                if ind.get('FREQUENCY'):
                    lines.append(f"   FREQUENCY={ind['FREQUENCY']}")
                lines.append('  }')
            
            lines.append(' }')
        
        lines.append('}')
        return lines


# ============================================================================
# ФУНКЦИИ ВАЛИДАЦИИ
# ============================================================================

def validate_ipv4(ip: str) -> bool:
    """Проверяет корректность IPv4 адреса."""
    if not ip:
        return False
    
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    
    for part in parts:
        if not part:
            return False
        # Проверка на ведущие нули (кроме самого нуля)
        if len(part) > 1 and part[0] == '0':
            return False
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False
        except ValueError:
            return False
    
    return True


def validate_netmask(mask: str) -> bool:
    """Проверяет корректность маски подсети."""
    if not validate_ipv4(mask):
        return False
    
    # Преобразуем в бинарный вид
    parts = mask.split('.')
    binary = ''.join(format(int(p), '08b') for p in parts)
    
    # Маска должна быть последовательностью единиц слева
    if '01' in binary:
        return False
    
    return True


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


def validate_iface_name(name: str) -> bool:
    """Проверяет корректность имени интерфейса."""
    valid_names = ['eth0', 'eth1']
    for i in range(10):
        valid_names.append(f'eth0:{i}')
        valid_names.append(f'eth1:{i}')
    
    return name in valid_names


def validate_port_range(port_range: str, min_port: int = 1, max_port: int = 65535) -> bool:
    """Проверяет диапазон портов вида '1-15,17-31'."""
    if not port_range:
        return False
    
    parts = port_range.split(',')
    all_ports = set()
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            try:
                start_port = int(start)
                end_port = int(end)
                if start_port < min_port or end_port > max_port or start_port > end_port:
                    return False
                ports = set(range(start_port, end_port + 1))
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
                    return False  # Дубликат
                all_ports.add(port)
            except ValueError:
                return False
    
    return True


def validate_cidr(cidr: str) -> bool:
    """Проверяет CIDR нотацию (например, 192.168.1.0/24)."""
    if not cidr:
        return False
    
    parts = cidr.split('/')
    if len(parts) != 2:
        return False
    
    ip, prefix = parts
    if not validate_ipv4(ip):
        return False
    
    try:
        prefix_num = int(prefix)
        if prefix_num < 0 or prefix_num > 32:
            return False
    except ValueError:
        return False
    
    return True


def validate_integer(value: str, min_val: int = 0, max_val: int = 65535) -> bool:
    """Проверяет целое число в диапазоне."""
    if not value:
        return False
    try:
        num = int(value)
        return min_val <= num <= max_val
    except ValueError:
        return False


def validate_exten_mask(mask: str) -> bool:
    """Проверяет маску расширения Asterisk."""
    if not mask:
        return False
    
    # Простая проверка: номер или маска с _
    if mask.startswith('_'):
        # Маска может содержать X, Z, N, [, ], ., цифры
        pattern = r'^_[XZN0-9.\[\]-]+$'
        return bool(re.match(pattern, mask))
    else:
        # Просто номер
        return mask.isdigit() or bool(re.match(r'^[0-9*#]+$', mask))
