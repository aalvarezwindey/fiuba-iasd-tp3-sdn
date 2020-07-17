#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pox

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
import math

from pox.lib.addresses import EthAddr, IPAddr

log = core.getLogger()


class SwitchController:
    def __init__(self, dpid, connection, fat_tree, nombre):
        self.dpid = dpid
        self.connection = connection
        self.fat_tree = fat_tree
        self.nombre = nombre
        # El SwitchController se agrega como handler de los eventos del switch
        self.connection.addListeners(self)
        self.links = []
        self.niveles = 0
        
        # pox.openflow.libopenflow_01.ofp_features_reply()

        # print(self.connection.features.datapath_id)
        # for k,v in self.connection.ports.items():
        #     print(k, v)

        # pox.openflow.ConnectionIn

    def add_link(self, link):
        self.links.append(link)

    def set_levels(self, levels):
        self.niveles = levels

    def _handle_PacketIn(self, event):
        """
        Esta funcion es llamada cada vez que el switch recibe un paquete
        y no encuentra en su tabla una regla para rutearlo
        """

        packet = event.parsed

        if packet.type != pkt.ethernet.IP_TYPE:
            return

        print("********************* _HANDLE_PACKET_IN_ EN {}  *********************".format(self.nombre))
        

        flow = self.packet_to_flow(packet)
        
        if flow['protocolo'] == pkt.ipv4.ICMP_PROTOCOL:
            self._handle_ICMP_packet(event, flow)
            return   

        print("FLOW: {}".format(flow))

        print("EL PAQUETE QUE NO SE MANEJAR ME LLEGO POR EL PUERTO NÚMERO: {}".format(event.port))
        # Si soy el switch raiz, me interesa guardar en la tabla la relación:
        # Puerto por el que me llego el paquete - IP origen para retornar el mensaje
        soy_raiz = (self.nombre == 'sw0_0_1')  # Una forma tricky de darnos cuenta que somos el switch raiz
        if (soy_raiz): #
            # Grabamos la tabla del switch raiz para poder devolver el mensaje al host origen
            self.connection.send(of.ofp_flow_mod(action=of.ofp_action_output(port=event.port),
                        priority=42,
                        match=of.ofp_match(dl_type=0x800,
                                        nw_dst=flow['ip_origen'],       # Notar que invierto origen y destino
                                        tp_dst=flow['puerto_origen'],
                                        nw_src=flow['ip_destino'],
                                        tp_src=flow['puerto_destino'],
                                        nw_proto=flow['protocolo'])))

        caminos = self.buscar_caminos(packet)
        print("EXISTEN {} CAMINOS POSIBLES:".format(len(caminos)), caminos)

        camino_elegido = self.elegir_camino_para_flow(flow, caminos).switches
        print('PARA EL FLOW SE ELIGIÓ EL CAMINO {}'.format(camino_elegido))

        indice_en_vector_de_caminos = -1

        for i in range(len(camino_elegido)):
            if camino_elegido[i].dpid == self.dpid:
                indice_en_vector_de_caminos = i

        if (indice_en_vector_de_caminos == (len(camino_elegido) - 1)) and (not soy_raiz):
            print("SOY UN SWITCH HOJA, NO SE COMO LLEGAR AL HOST DE ABAJO")
            # Suponemos que siempre habrá solo un host en cada switch hoja, y su numeración en puerto de swich sera n+1 siendo n
            # la cantidad de links con switches que hay en el switch hoja
            puerto_al_host = len(self.links) + 1

            self.connection.send(of.ofp_flow_mod(action=of.ofp_action_output(port=puerto_al_host ),
                                    priority=42,
                                    match=of.ofp_match(dl_type=0x800,
                                                    nw_dst=flow['ip_destino'],
                                                    tp_dst=flow['puerto_destino'],
                                                    nw_src=flow['ip_origen'],
                                                    tp_src=flow['puerto_origen'],
                                                    nw_proto=flow['protocolo'])))
        else:
            print("NO SOY UN SWITCH HOJA")
            # Busco entre mis links, aquél que me lleva al siguiente switch según el camino que me dieron
            for link in self.links:
                if str(link.switch2) == str(camino_elegido[indice_en_vector_de_caminos+1]):
                    # Tengo identificado el link, puedo conocer los puertos
                    mi_puerto = link.port_switch_1
                    print("LLEGO AL PRÓXIMO SWITCH A TRAVÉS DE MI PUERTO NÚMERO: {}".format(mi_puerto))

                    self.connection.send(of.ofp_flow_mod(action=of.ofp_action_output(port=mi_puerto),
                                            priority=42,
                                            match=of.ofp_match(dl_type=0x800,
                                                            nw_dst=flow['ip_destino'],
                                                            tp_dst=flow['puerto_destino'],
                                                            nw_src=flow['ip_origen'],
                                                            tp_src=flow['puerto_origen'],
                                                            nw_proto=flow['protocolo'])))

    print("*********************  *********************  *********************")
    #    log.info("Packet arrived to switch %s from %s to %s", self.dpid, packet.src, packet.dst)

    def _handle_ICMP_packet(self, event, flow):
        # Se invoca cuando _handle_PacketIn detecta que es un mensaje de tipo ICMP
        # Algoritmo
        # Básicamente, las reglas para ICMP son:
        #    
        #    - Si el paquete es ICMP
        #    - Y te llegó por un puerto que te conecta para abajo
        #       --> Mandalo por un puerto que te conecte para arriba
        #
        #    - Si el paquete es ICMP
        #    - Y te llegó por un puerto que te conecte para arriba
        #       --> Mandalo por un puerto que te coencte para abajo
        #
        
        puerto_de_entrada = event.port
        soy_raiz = (self.nombre == 'sw0_0_1')  # Una forma tricky de darnos cuenta que somos el switch raiz
        soy_hoja = False
        mi_nivel = int(self.nombre[4])


        if (mi_nivel == (self.niveles-1)):
            soy_hoja = True

        # Hasta acá se si soy un switch raiz, intermedio u hoja

        if (soy_raiz):
            print("SOY UN SWITCH RAIZ.")
            # Ya puedo escribir reglas
            puertos_de_salida = []
            for link in self.links:
                puertos_de_salida.append(link.port_switch_1)

                fm = of.ofp_flow_mod()
                fm.match.in_port = link.port_switch_1
                fm.priority = 42
                fm.match.dl_type = 0x0800
                fm.match.nw_src = flow['ip_destino']
                fm.match.nw_dst = flow['ip_origen']
                fm.actions.append(of.ofp_action_output(port = puerto_de_entrada))
                self.connection.send( fm )
                
                fm = of.ofp_flow_mod()
                fm.match.in_port = link.port_switch_1
                fm.match.dl_type = 0x0806
                fm.priority = 42
                fm.actions.append(of.ofp_action_output(port = puerto_de_entrada ))
                self.connection.send(fm)

            print("SET REGLA: DE PUERTO {} A PUERTO {}".format(puerto_de_entrada, link.port_switch_1))

            fm = of.ofp_flow_mod()
            fm.match.in_port = puerto_de_entrada
            fm.priority = 42
            fm.match.dl_type = 0x0800
            fm.match.nw_src = flow['ip_origen']
            fm.match.nw_dst = flow['ip_destino']
            for puerto_de_salida in puertos_de_salida:
                fm.actions.append(of.ofp_action_output( port = puerto_de_salida ) )
            self.connection.send( fm )

            fm = of.ofp_flow_mod()
            fm.match.in_port = puerto_de_entrada
            fm.match.dl_type = 0x0806
            fm.priority = 42
            for puerto_de_salida in puertos_de_salida:
                fm.actions.append(of.ofp_action_output( port = puerto_de_salida ) )
            self.connection.send(fm)

        elif (soy_hoja):
            print("SOY UN SWITCH HOJA.")
            for link in self.links:
                print("SET REGLA: DE PUERTO {} A PUERTO {}".format(link.port_switch_1, (len(self.links) + 1)))

                fm = of.ofp_flow_mod()
                fm.match.in_port = link.port_switch_1
                fm.priority = 42
                fm.match.dl_type = 0x0800
                fm.match.nw_src = flow['ip_origen']
                fm.match.nw_dst = flow['ip_destino']
                fm.actions.append(of.ofp_action_output( port = (len(self.links) + 1)))
                self.connection.send( fm )

                fm = of.ofp_flow_mod()
                fm.match.in_port = link.port_switch_1
                fm.match.dl_type = 0x0806
                fm.priority = 42
                fm.actions.append(of.ofp_action_output( port = (len(self.links) + 1)))
                self.connection.send(fm)

                print("SET REGLA: DE PUERTO {} A PUERTO {}".format((len(self.links) + 1), link.port_switch_1))

                fm = of.ofp_flow_mod()
                fm.match.in_port = (len(self.links) + 1)
                fm.priority = 42
                fm.match.dl_type = 0x0800
                fm.match.nw_src = flow['ip_destino']
                fm.match.nw_dst = flow['ip_origen']
                fm.actions.append(of.ofp_action_output( port = link.port_switch_1))
                self.connection.send( fm )

                fm = of.ofp_flow_mod()
                fm.match.in_port = (len(self.links) + 1)
                fm.match.dl_type = 0x0806
                fm.priority = 33001
                fm.actions.append(of.ofp_action_output( port = link.port_switch_1 ))
                self.connection.send(fm)

        else:
            # Soy un switch intermedio
            mi_nivel = int(self.nombre[4])
            print("SOY UN SWITCH INTERMEDIO EN EL NIVEL {}".format(mi_nivel))
            flujo_hacia_abajo = True
            for link in self.links:
                if (link.port_switch_1 == puerto_de_entrada): # Identificamos el link por el que vino el paquete
                        if (int(link.switch2.nombre[4]) < mi_nivel):
                            # El paquete vino de arriba
                            flujo_hacia_abajo = True
                        else:
                            flujo_hacia_abajo = False
            
            if flujo_hacia_abajo:
                print("EL FLUJO ES HACIA ABAJO")
                puertos_de_salida = []
                for link in self.links:
                    if (int(link.switch2.nombre[4]) > mi_nivel):
                        puertos_de_salida.append(link.port_switch_1)
                        
                        fm = of.ofp_flow_mod()
                        fm.match.in_port = link.port_switch_1
                        fm.priority = 42
                        fm.match.dl_type = 0x0800
                        fm.match.nw_src = flow['ip_destino']
                        fm.match.nw_dst = flow['ip_origen']
                        fm.actions.append(of.ofp_action_output( port = puerto_de_entrada))
                        self.connection.send( fm )

                        fm = of.ofp_flow_mod()
                        fm.match.in_port = link.port_switch_1
                        fm.match.dl_type = 0x0806
                        fm.priority = 42
                        fm.actions.append(of.ofp_action_output( port = puerto_de_entrada))
                        self.connection.send(fm)

                fm = of.ofp_flow_mod()
                fm.match.in_port = puerto_de_entrada
                fm.priority = 42
                fm.match.dl_type = 0x0800
                fm.match.nw_src = flow['ip_origen']
                fm.match.nw_dst = flow['ip_destino']
                for puerto_de_salida in puertos_de_salida:
                    fm.actions.append(of.ofp_action_output( port = puerto_de_salida))
                self.connection.send( fm )

                fm = of.ofp_flow_mod()
                fm.match.in_port = puerto_de_entrada
                fm.match.dl_type = 0x0806
                fm.priority = 42
                for puerto_de_salida in puertos_de_salida:
                    fm.actions.append(of.ofp_action_output( port = puerto_de_salida))
                self.connection.send(fm)
                
            else:
                print("EL FLUJO ES HACIA ARRIBA")
                for link in self.links:
                    if (int(link.switch2.nombre[4]) < mi_nivel):

                        print("SET REGLA: DE PUERTO {} A PUERTO {}".format(puerto_de_entrada, link.port_switch_1))

                        fm = of.ofp_flow_mod()
                        fm.match.in_port = puerto_de_entrada
                        fm.priority = 42
                        fm.match.dl_type = 0x0800
                        fm.match.nw_src = flow['ip_destino']
                        fm.match.nw_dst = flow['ip_origen']
                        fm.actions.append(of.ofp_action_output( port = link.port_switch_1))
                        self.connection.send( fm )

                        fm = of.ofp_flow_mod()
                        fm.match.in_port = puerto_de_entrada
                        fm.match.dl_type = 0x0806
                        fm.priority = 42
                        fm.actions.append(of.ofp_action_output( port = link.port_switch_1))
                        self.connection.send(fm)

                        print("SET REGLA: DE PUERTO {} A PUERTO {}".format(link.port_switch_1, puerto_de_entrada))

                        fm = of.ofp_flow_mod()
                        fm.match.in_port = link.port_switch_1
                        fm.priority = 42
                        fm.match.dl_type = 0x0800
                        fm.match.nw_src = flow['ip_origen']
                        fm.match.nw_dst = flow['ip_destino']
                        fm.actions.append(of.ofp_action_output( port = puerto_de_entrada))
                        self.connection.send( fm )

                        fm = of.ofp_flow_mod()
                        fm.match.in_port = link.port_switch_1
                        fm.match.dl_type = 0x0806
                        fm.priority = 42
                        fm.actions.append(of.ofp_action_output( port = puerto_de_entrada))
                        self.connection.send(fm)

    # https://openflow.stanford.edu/display/ONL/POX+Wiki.html#POXWiki-Workingwithpackets%3Apox.lib.packet
    def packet_to_flow(self, packet):
        # SUPOSICION: solo manejamos paquetes ethernet
        if packet.type == pkt.ethernet.IP_TYPE:
            ip_packet = packet.payload

            #log.info("ip_packet.protocol: %s", ip_packet.protocol)
            #log.info("pkt.ipv4.TCP_PROTOCOL: %s", pkt.ipv4.TCP_PROTOCOL)
            #log.info("pkt.ipv4.UDP_PROTOCOL: %s", pkt.ipv4.UDP_PROTOCOL)
            if ip_packet.protocol == pkt.ipv4.TCP_PROTOCOL:
                tcp_packet = ip_packet.payload
                flow = {
                    'ip_origen': ip_packet.srcip,
                    'ip_destino': ip_packet.dstip,
                    'puerto_origen': tcp_packet.srcport,
                    'puerto_destino': tcp_packet.dstport,
                    'protocolo': pkt.ipv4.TCP_PROTOCOL
                }

                #log.info("FLOW TCP GENERADO %s", flow)
                return flow
            elif ip_packet.protocol == pkt.ipv4.UDP_PROTOCOL:
                udp_packet = ip_packet.payload
                flow = {
                    'ip_origen': ip_packet.srcip,
                    'ip_destino': ip_packet.dstip,
                    'puerto_origen': udp_packet.srcport,
                    'puerto_destino': udp_packet.dstport,
                    'protocolo': pkt.ipv4.UDP_PROTOCOL
                }

                #log.info("FLOW UDP GENERADO %s", flow)
                return flow
            elif ip_packet.protocol == pkt.ipv4.ICMP_PROTOCOL:
                # SUPOSICION: Asumimos puerto 7 para paquetes ICMP
                # fuente: https://networkengineering.stackexchange.com/questions/37896/ping-port-number
                flow = {
                    'ip_origen': ip_packet.srcip,
                    'ip_destino': ip_packet.dstip,
                    'puerto_origen': 7,
                    'puerto_destino': 7,
                    'protocolo': pkt.ipv4.ICMP_PROTOCOL
                }

                #log.info("FLOW ICMP GENERADO %s", flow)
                return flow
            else:
                log.info("* * * * * No se handlear este protocolo * * * * * %s", ip_packet.protocol)
                return {}

    def elegir_camino_para_flow(self, flow, caminos):
        # SUPOSICION: le damos la misma cantidad de caminos posibles a TCP y a UDP,
        # pero dependiendo el trafico de ambos protocolos en la red podriamos cambiar esas cantidades.
        # Por ejemplo: si sabemos que a nuestro Datacenter el 90% de los paquetes que llegan son TCP
        # y el 10% UDP, los paquetes TCP los repartimos de manera balanceada entre el 90% de los caminos
        # minimos posibles y lo mismo para UDP con el 10% restante.
        # SUPOSICION: Solo consideramos TCP y UDP, no tenemos en cuenta QUIC por ejemplo.
        PORCENTAJE_TCP_EN_LA_RED = 0.5  # el resto es para UDP

        cantidad_de_caminos_para_tcp = int(math.ceil(PORCENTAJE_TCP_EN_LA_RED * len(caminos)))

        # si el resto de caminos da cero, deben compartir los caminos
        resto_de_caminos = len(caminos) - cantidad_de_caminos_para_tcp

        cantidad_de_caminos_para_udp = cantidad_de_caminos_para_tcp if not resto_de_caminos else resto_de_caminos

        #log.info("cantidad_de_caminos totales %s", len(caminos))
        #log.info("cantidad_de_caminos_para_tcp %s", cantidad_de_caminos_para_tcp)
        #log.info("cantidad_de_caminos_para_udp %s", cantidad_de_caminos_para_udp)

        # Nuestro balanceo de caminos lo haremos unicamente en base a los puertos origen y destino
        caminos_para_tcp = caminos[0:cantidad_de_caminos_para_tcp]
        caminos_para_udp = caminos[cantidad_de_caminos_para_tcp:len(caminos)] if resto_de_caminos else caminos_para_tcp
        #log.info("caminos_para_tcp: %s", caminos_para_tcp)
        #log.info("caminos_para_udp: %s", caminos_para_udp)

        suma_puertos = flow['puerto_origen'] + flow['puerto_destino']
        #log.info("suma_puertos: %s", suma_puertos)

        if flow['protocolo'] == pkt.ipv4.TCP_PROTOCOL:
            camino = caminos_para_tcp[suma_puertos % len(caminos_para_tcp)]
            #log.info("camino elegido para tcp: %s", camino)
            return camino
        elif flow['protocolo'] == pkt.ipv4.UDP_PROTOCOL:
            camino = caminos_para_udp[suma_puertos % len(caminos_para_udp)]
            #log.info("camino elegido para udp: %s", camino)
            return camino
        elif flow['protocolo'] == pkt.ipv4.ICMP_PROTOCOL:
            # Suponemos que el tráfico de UDP es menor, asique compartimos los ICMP con los UDP
            camino = caminos_para_udp[suma_puertos % len(caminos_para_udp)]
            #log.info("camino elegido para icmp: %s", camino)
            return camino

    def buscar_caminos(self, paquete):
        #log.info("Packet arrived to switch %s from %s to %s with ip %s",
        #         self.dpid, paquete.src, paquete.dst, paquete.payload.dstip)

        host = paquete.payload.dstip.toSigned() - IPAddr("10.0.0.0").toSigned()
        #print("host:", host)

        nivel_inferior = self.fat_tree.get_nivel_inferior()
        switch_destino = None
        for switch in nivel_inferior.switches:
            if switch.get_indice() == host:
                switch_destino = switch

        # Si no es un host que esté en el nivel inferior, entonces está en el root
        if switch_destino is None:
            try:
                switch_destino = self.fat_tree.niveles[0].switches[0]
            except (IndexError, KeyError):
                # El switch root no esta.
                return []

        switch_origen = self.fat_tree.get_switch_por_dpid(self.dpid)
        #print("switch origen", switch_origen)
        #print("switch destino", switch_destino)

        return self.fat_tree.get_caminos(switch_origen, switch_destino)
