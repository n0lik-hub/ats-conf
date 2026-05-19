"""
Генератор конфигурационного файла для IP-АТС Т76-С.
Создает файл в соответствии с синтаксисом, описанным в ТЗ.
"""

from typing import Dict, List, Any
from config_data import ConfigData


class ConfigGenerator:
    """Класс для генерации текста конфигурационного файла."""
    
    def __init__(self, data: ConfigData):
        self.data = data
        
    def generate(self) -> str:
        """Сгенерировать полный текст конфигурационного файла."""
        lines = []
        
        # SYSTEM (обязательная)
        lines.append("SYSTEM {")
        lines.append(f" HOSTNAME={self.data.system['hostname']}")
        lines.append("}")
        lines.append("")
        
        # NTP (необязательная)
        if self.data.ntp_enabled:
            lines.append("NTP {")
            if self.data.ntp.get('ip_srv'):
                lines.append(f" IP_SRV={self.data.ntp['ip_srv']}")
            if self.data.ntp.get('interval'):
                lines.append(f" INTERVAL={self.data.ntp['interval']}")
            lines.append("}")
            lines.append("")
        
        # NETWORK (обязательная)
        if self.data.network_ifaces or self.data.network_routes or self.data.network_arp:
            lines.append("NETWORK {")
            
            # IFACE
            for iface in self.data.network_ifaces:
                lines.append(" IFACE {")
                if iface.get('iface_name'):
                    lines.append(f"  IFACE_NAME={iface['iface_name']}")
                if iface.get('ip'):
                    lines.append(f"  IP={iface['ip']}")
                if iface.get('netmask'):
                    lines.append(f"  NETMASK={iface['netmask']}")
                if iface.get('broadcast'):
                    lines.append(f"  BROADCAST={iface['broadcast']}")
                if iface.get('mtu'):
                    lines.append(f"  MTU={iface['mtu']}")
                if iface.get('metric'):
                    lines.append(f"  METRIC={iface['metric']}")
                if iface.get('speed'):
                    lines.append(f"  SPEED={iface['speed']}")
                if iface.get('duplex'):
                    lines.append(f"  DUPLEX={iface['duplex']}")
                if iface.get('autoneg'):
                    lines.append(f"  AUTONEG={iface['autoneg']}")
                lines.append(" }")
            
            # ROUTE
            for route in self.data.network_routes:
                lines.append(" ROUTE {")
                if route.get('iface_name'):
                    lines.append(f"  IFACE_NAME={route['iface_name']}")
                if route.get('net'):
                    lines.append(f"  NET={route['net']}")
                if route.get('netmask'):
                    lines.append(f"  NETMASK={route['netmask']}")
                if route.get('gateway'):
                    lines.append(f"  GATEWAY={route['gateway']}")
                if route.get('default_gw'):
                    lines.append(f"  DEFAULT_GW={'true' if route['default_gw'] else 'false'}")
                if route.get('metric'):
                    lines.append(f"  METRIC={route['metric']}")
                lines.append(" }")
            
            # ARP
            for arp in self.data.network_arp:
                lines.append(" ARP {")
                if arp.get('ip'):
                    lines.append(f"  IP={arp['ip']}")
                if arp.get('mac'):
                    lines.append(f"  MAC={arp['mac']}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # MPLS (необязательная)
        if self.data.mpls_enabled and (self.data.mpls_out or self.data.mpls_in):
            lines.append("MPLS {")
            
            for rule in self.data.mpls_out:
                lines.append(" MPLS_RULE_OUT {")
                if rule.get('ip_dest'):
                    lines.append(f"  IP_DEST={rule['ip_dest']}")
                if rule.get('label'):
                    lines.append(f"  LABEL={rule['label']}")
                if rule.get('out_iface_name'):
                    lines.append(f"  OUT_IFACE_NAME={rule['out_iface_name']}")
                if rule.get('ip_next'):
                    lines.append(f"  IP_NEXT={rule['ip_next']}")
                lines.append(" }")
            
            for rule in self.data.mpls_in:
                lines.append(" MPLS_RULE_IN {")
                if rule.get('in_iface_name'):
                    lines.append(f"  IN_IFACE_NAME={rule['in_iface_name']}")
                if rule.get('label'):
                    lines.append(f"  LABEL={rule['label']}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # TUNNELS (необязательная) - упрощенная реализация
        if self.data.tunnels_enabled:
            lines.append("TUNNELS {")
            
            # OPTIONS
            lines.append(" OPTIONS {")
            if self.data.tunnels_options.get('port'):
                lines.append(f"  PORT={self.data.tunnels_options['port']}")
            if self.data.tunnels_options.get('iface_name'):
                lines.append(f"  IFACE_NAME={self.data.tunnels_options['iface_name']}")
            for cmd in self.data.tunnels_options.get('commands', []):
                lines.append(f"  COMMAND=\"{cmd}\"")
            lines.append(" }")
            
            # DEFAULT
            if self.data.tunnels_default.get('compress') or self.data.tunnels_default.get('speed'):
                lines.append(" DEFAULT {")
                if self.data.tunnels_default.get('compress'):
                    lines.append(f"  COMPRESS=true")
                if self.data.tunnels_default.get('speed'):
                    lines.append(f"  SPEED={self.data.tunnels_default['speed']}")
                lines.append(" }")
            
            # TUN
            for tun in self.data.tunnels:
                lines.append(" TUN {")
                if tun.get('from_dev'):
                    lines.append(f"  FROM={tun['from_dev']}")
                if tun.get('to_dev'):
                    lines.append(f"  TO={tun['to_dev']}")
                if tun.get('passwd'):
                    lines.append(f"  PASSWD={tun['passwd']}")
                if tun.get('type'):
                    lines.append(f"  TYPE={tun['type']}")
                if tun.get('proto'):
                    lines.append(f"  PROTO={tun['proto']}")
                if tun.get('compress'):
                    lines.append(f"  COMPRESS={'true' if tun['compress'] else 'false'}")
                if tun.get('encrypt'):
                    lines.append(f"  ENCRYPT={'true' if tun['encrypt'] else 'false'}")
                if tun.get('keepalive'):
                    lines.append(f"  KEEPALIVE={'true' if tun['keepalive'] else 'false'}")
                if tun.get('persist'):
                    lines.append(f"  PERSIST={'true' if tun['persist'] else 'false'}")
                if tun.get('speed'):
                    lines.append(f"  SPEED={tun['speed']}")
                lines.append(" }")
            
            # SERVERS
            for server in self.data.tunnels_servers:
                lines.append(f" SERVERS {{ NAME={server} }}")
            
            # CLIENTS
            for client in self.data.tunnels_clients:
                name = client.get('name', '')
                addr = client.get('address', '')
                lines.append(f" CLIENTS {{ NAME={name},{addr} }}")
            
            lines.append("}")
            lines.append("")
        
        # TC (необязательная) - упрощенная реализация
        if self.data.tc_enabled and self.data.tc_qdiscs:
            lines.append("TC {")
            for qdisc in self.data.tc_qdiscs:
                lines.append(" QDISC {")
                if qdisc.get('iface_name'):
                    lines.append(f"  IFACE_NAME={qdisc['iface_name']}")
                if qdisc.get('discipline'):
                    lines.append(f"  DISCIPLINE={qdisc['discipline']}")
                if qdisc.get('rate'):
                    lines.append(f"  RATE={qdisc['rate']}")
                if qdisc.get('default_class'):
                    lines.append(f"  DEFAULT_CLASS={qdisc['default_class']}")
                lines.append(" }")
            lines.append("}")
            lines.append("")
        
        # IPTABLES (необязательная) - упрощенная реализация
        if self.data.iptables_enabled:
            lines.append("IPTABLES {")
            
            for chain_name, rules in self.data.iptables_rules.items():
                if rules:
                    if chain_name == 'CHAIN':
                        # Пользовательские цепочки
                        for rule in rules:
                            if rule.get('chain_name'):
                                lines.append(f" CHAIN {{ NAME={rule['chain_name']} }}")
                    else:
                        for rule in rules:
                            lines.append(f" {chain_name} {{")
                            if rule.get('action'):
                                lines.append(f"  ACTION={rule['action']}")
                            if rule.get('protocol'):
                                lines.append(f"  PROTOCOL={rule['protocol']}")
                            if rule.get('sport'):
                                lines.append(f"  SPORT={rule['sport']}")
                            if rule.get('dport'):
                                lines.append(f"  DPORT={rule['dport']}")
                            if rule.get('in_iface'):
                                lines.append(f"  IN_IFACE_NAME={rule['in_iface']}")
                            if rule.get('out_iface'):
                                lines.append(f"  OUT_IFACE_NAME={rule['out_iface']}")
                            if rule.get('saddr'):
                                lines.append(f"  SADDR={rule['saddr']}")
                            if rule.get('daddr'):
                                lines.append(f"  DADDR={rule['daddr']}")
                            if rule.get('match'):
                                lines.append(f"  MATCH={rule['match']}")
                            if rule.get('match_params'):
                                lines.append(f"  MATCH_PARAMS={rule['match_params']}")
                            if rule.get('icmp_type'):
                                lines.append(f"  ICMP_TYPE={rule['icmp_type']}")
                            if rule.get('to_dest'):
                                lines.append(f"  TO_DEST={rule['to_dest']}")
                            if rule.get('source_to'):
                                lines.append(f"  SOURCE_TO={rule['source_to']}")
                            lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # IAX (необязательная)
        if self.data.iax_enabled:
            lines.append("IAX {")
            
            # GENERAL
            lines.append(" GENERAL {")
            gen = self.data.iax_general
            lines.append(f"  AUTOKILL={'true' if gen.get('autokill') else 'false'}")
            if gen.get('bindaddr'):
                lines.append(f"  BINDADDR={gen['bindaddr']}")
            if gen.get('bandwidth'):
                lines.append(f"  BANDWIDTH={gen['bandwidth']}")
            if gen.get('codecpriority'):
                lines.append(f"  CODECPRIORITY={gen['codecpriority']}")
            lines.append(f"  JITTERBUFFER={'true' if gen.get('jitterbuffer') else 'false'}")
            lines.append(f"  FORCEJITTERBUFFER={'true' if gen.get('forcejitterbuffer') else 'false'}")
            if gen.get('maxjitterbuffer'):
                lines.append(f"  MAXJITTERBUFFER={gen['maxjitterbuffer']}")
            if gen.get('maxjitterinterps'):
                lines.append(f"  MAXJITTERINTERPS={gen['maxjitterinterps']}")
            if gen.get('resyncreshold'):
                lines.append(f"  RESYNCTHRESHOLD={gen['resyncreshold']}")
            lines.append(" }")
            
            # IAX_ROUTE
            for route in self.data.iax_routes:
                lines.append(" IAX_ROUTE {")
                if route.get('name'):
                    lines.append(f"  NAME={route['name']}")
                if route.get('type'):
                    lines.append(f"  TYPE={route['type']}")
                if route.get('host'):
                    lines.append(f"  HOST={route['host']}")
                if route.get('context'):
                    lines.append(f"  CONTEXT={route['context']}")
                lines.append(f"  TRUNK={'true' if route.get('trunk') else 'false'}")
                if route.get('trunkfreq'):
                    lines.append(f"  TRUNKFREQ={route['trunkfreq']}")
                if route.get('qualify') is not None:
                    qualify = route['qualify']
                    if isinstance(qualify, bool):
                        lines.append(f"  QUALIFY={'true' if qualify else 'false'}")
                    else:
                        lines.append(f"  QUALIFY={qualify}")
                if route.get('allow'):
                    allow_list = route['allow'] if isinstance(route['allow'], list) else [route['allow']]
                    lines.append(f"  ALLOW={','.join(allow_list)}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # SIP (необязательная)
        if self.data.sip_enabled:
            lines.append("SIP {")
            
            # GENERAL
            lines.append(" GENERAL {")
            gen = self.data.sip_general
            if gen.get('context'):
                lines.append(f"  CONTEXT={gen['context']}")
            lines.append(f"  ALLOWOVERLAP={'true' if gen.get('allowoverlap') else 'false'}")
            if gen.get('bindport'):
                lines.append(f"  BINDPORT={gen['bindport']}")
            if gen.get('bindaddr'):
                lines.append(f"  BINDADDR={gen['bindaddr']}")
            lines.append(f"  SRVLOOKUP={'true' if gen.get('srvlookup') else 'false'}")
            if gen.get('disallow'):
                lines.append(f"  DISALLOW={gen['disallow']}")
            if gen.get('allow'):
                lines.append(f"  ALLOW={gen['allow']}")
            if gen.get('register'):
                lines.append(f"  REGISTER=\"{gen['register']}\"")
            lines.append(f"  CANREINVITE={'true' if gen.get('canreinvite') else 'false'}")
            if gen.get('insecure'):
                lines.append(f"  INSECURE={gen['insecure']}")
            lines.append(" }")
            
            # PHONE
            for phone in self.data.sip_phones:
                lines.append(" PHONE {")
                if phone.get('number'):
                    lines.append(f"  NUMBER={phone['number']}")
                if phone.get('type'):
                    lines.append(f"  TYPE={phone['type']}")
                if phone.get('username'):
                    lines.append(f"  USERNAME={phone['username']}")
                if phone.get('secret'):
                    lines.append(f"  SECRET={phone['secret']}")
                if phone.get('host'):
                    lines.append(f"  HOST={phone['host']}")
                if phone.get('context'):
                    lines.append(f"  CONTEXT={phone['context']}")
                if phone.get('disallow'):
                    lines.append(f"  DISALLOW={phone['disallow']}")
                if phone.get('allow'):
                    lines.append(f"  ALLOW={phone['allow']}")
                lines.append(f"  CANREINVITE={'true' if phone.get('canreinvite') else 'false'}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # ZAPTEL (необязательная)
        if self.data.zaptel_enabled:
            lines.append("ZAPTEL {")
            z = self.data.zaptel
            if z.get('loadzone'):
                lines.append(f" LOADZONE={z['loadzone']}")
            if z.get('defaultzone'):
                lines.append(f" DEFAULTZONE={z['defaultzone']}")
            if z.get('fxoks'):
                lines.append(f" FXOKS=\"{z['fxoks']}\"")
            
            # CHAN_E1
            for e1 in self.data.zaptel_e1:
                lines.append(" CHAN_E1 {")
                span = e1.get('span', {})
                if span.get('number'):
                    lines.append(f"  SPAN {{ NUMBER={span['number']} }}")
                    if span.get('timing'):
                        lines.append(f"   TIMING={span['timing']}")
                    if span.get('lbo'):
                        lines.append(f"   LBO={span['lbo']}")
                    if span.get('framing'):
                        lines.append(f"   FRAMING={span['framing']}")
                    if span.get('coding'):
                        lines.append(f"   CODING={span['coding']}")
                if e1.get('bchan'):
                    lines.append(f"  BCHAN=\"{e1['bchan']}\"")
                if e1.get('hardhdlc'):
                    lines.append(f"  HARDHDLC={e1['hardhdlc']}")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # ZAPATA (необязательная)
        if self.data.zapata_enabled:
            lines.append("ZAPATA {")
            z = self.data.zapata_general
            if z.get('context'):
                lines.append(f" CONTEXT={z['context']}")
            if z.get('switchtype'):
                lines.append(f" SWITCHTYPE={z['switchtype']}")
            if z.get('signalling'):
                lines.append(f" SIGNALLING={z['signalling']}")
            lines.append(f" ECHOCANCEL={'true' if z.get('echocancel') else 'false'}")
            lines.append(f" OVERLAPDIAL={'true' if z.get('overlapdial') else 'false'}")
            if z.get('rxgain'):
                lines.append(f" RXGAIN={z['rxgain']}")
            if z.get('txgain'):
                lines.append(f" TXGAIN={z['txgain']}")
            if z.get('group'):
                lines.append(f" GROUP={z['group']}")
            
            # CHAN
            for chan in self.data.zapata_channels:
                lines.append(" CHAN {")
                if chan.get('context'):
                    lines.append(f"  CONTEXT={chan['context']}")
                if chan.get('group'):
                    lines.append(f"  GROUP={chan['group']}")
                if chan.get('signalling'):
                    lines.append(f"  SIGNALLING={chan['signalling']}")
                if chan.get('rxgain'):
                    lines.append(f"  RXGAIN={chan['rxgain']}")
                if chan.get('txgain'):
                    lines.append(f"  TXGAIN={chan['txgain']}")
                if chan.get('callerid'):
                    lines.append(f"  CALLERID={chan['callerid']}")
                if chan.get('channel'):
                    lines.append(f"  CHANNEL=\"{chan['channel']}\"")
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # EXTENSIONS (обязательная)
        lines.append("EXTENSIONS {")
        
        # GENERAL
        lines.append(" GENERAL {")
        ext_gen = self.data.extensions_general
        lines.append(f"  STATIC={'true' if ext_gen.get('static') else 'false'}")
        lines.append(f"  WRITEPROTECT={'true' if ext_gen.get('writeprotect') else 'false'}")
        lines.append(f"  CLEARGLOBALVARS={'true' if ext_gen.get('clearglobalvars') else 'false'}")
        lines.append(f"  AUTOFALLTHROUGH={'true' if ext_gen.get('autofallthrough') else 'false'}")
        lines.append(" }")
        
        # GLOBALS
        for glob in self.data.extensions_globals:
            var = glob.get('var', '')
            val = glob.get('value', '')
            if var:
                lines.append(f" GLOBALS {{ {var}={val} }}")
        
        # EXTENGROUP
        for group in self.data.extensions_groups:
            lines.append(" EXTENGROUP {")
            if group.get('name'):
                lines.append(f"  NAME={group['name']}")
            
            # EXTEN
            for exten in group.get('extens', []):
                field1 = exten.get('field1', '')
                field2 = exten.get('field2', '')
                field3 = exten.get('field3', '')
                field4 = exten.get('field4', '')
                
                # Формируем строку EXTEN
                exten_str = f"{field1}:{field2}"
                if field3:
                    exten_str += f":{field3}"
                if field4:
                    exten_str += f":{field4}"
                
                lines.append(f"  EXTEN=\"{exten_str}\"")
            
            lines.append(" }")
        
        lines.append("}")
        lines.append("")
        
        # ALARM (необязательная)
        if self.data.alarm_enabled and self.data.alarm_events:
            lines.append("ALARM {")
            
            for event in self.data.alarm_events:
                lines.append(" EVENT {")
                if event.get('name'):
                    lines.append(f"  NAME={event['name']}")
                if event.get('saddr'):
                    lines.append(f"  SADDR={event['saddr']}")
                if event.get('close_rele'):
                    lines.append(f"  CLOSE_RELE={event['close_rele']}")
                if event.get('open_rele'):
                    lines.append(f"  OPEN_RELE={event['open_rele']}")
                if event.get('send_to_ip'):
                    lines.append(f"  SEND_TO_IP={event['send_to_ip']}")
                
                # LOG реакции
                for log in event.get('logs', []):
                    lines.append("  LOG {")
                    if log.get('name'):
                        lines.append(f"   NAME={log['name']}")
                    if log.get('string'):
                        lines.append(f"   STRING={log['string']}")
                    lines.append("  }")
                
                # INDICATOR реакции
                for ind in event.get('indicators', []):
                    lines.append("  INDICATOR {")
                    if ind.get('name'):
                        lines.append(f"   NAME={ind['name']}")
                    if ind.get('color'):
                        lines.append(f"   COLOR={ind['color']}")
                    if ind.get('frequency'):
                        lines.append(f"   FREQUENCY={ind['frequency']}")
                    lines.append("  }")
                
                lines.append(" }")
            
            lines.append("}")
            lines.append("")
        
        # Удаляем последний пустой элемент если есть
        while lines and lines[-1] == "":
            lines.pop()
        
        return '\n'.join(lines)
