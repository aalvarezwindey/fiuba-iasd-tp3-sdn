from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
import math

log = core.getLogger()


class SwitchController:
    def __init__(self, dpid, connection, fat_tree):
        self.dpid = dpid
        self.connection = connection
        self.fat_tree = fat_tree
        # El SwitchController se agrega como handler de los eventos del switch
        self.connection.addListeners(self)

    def _handle_PacketIn(self, event):
        """
        Esta funcion es llamada cada vez que el switch recibe un paquete
        y no encuentra en su tabla una regla para rutearlo
        """
        packet = event.parsed

        self.handle_packet(packet)
        log.info("Packet arrived to switch %s from %s to %s", self.dpid, packet.src, packet.dst)
        log.info("Packet arrived to switch %s from %s to %s", self.dpid, packet.src, packet.dst)

    # https://openflow.stanford.edu/display/ONL/POX+Wiki.html#POXWiki-Workingwithpackets%3Apox.lib.packet
    def handle_packet(self, packet):
        # SUPOSICION: solo manejamos paquetes ethernet
        if packet.type == pkt.ethernet.IP_TYPE:
            ip_packet = packet.payload

            log.info("ip_packet.protocol: %s", ip_packet.protocol)
            log.info("pkt.ipv4.TCP_PROTOCOL: %s", pkt.ipv4.TCP_PROTOCOL)
            log.info("pkt.ipv4.UDP_PROTOCOL: %s", pkt.ipv4.UDP_PROTOCOL)
            if ip_packet.protocol == pkt.ipv4.TCP_PROTOCOL:
                tcp_packet = ip_packet.payload
                flow = {
                    'ip_origen': ip_packet.srcip,
                    'ip_destino': ip_packet.dstip,
                    'puerto_origen': tcp_packet.srcport,
                    'puerto_destino': tcp_packet.dstport,
                    'protocolo': pkt.ipv4.TCP_PROTOCOL
                }

                log.info("FLOW TCP GENERADO %s", flow)
                self.buscar_caminos(flow)
                # self.elegir_camino_para_flow(flow)
            elif ip_packet.protocol == pkt.ipv4.UDP_PROTOCOL:
                udp_packet = ip_packet.payload
                flow = {
                    'ip_origen': ip_packet.srcip,
                    'ip_destino': ip_packet.dstip,
                    'puerto_origen': udp_packet.srcport,
                    'puerto_destino': udp_packet.dstport,
                    'protocolo': pkt.ipv4.UDP_PROTOCOL
                }

                log.info("FLOW UDP GENERADO %s", flow)
                # self.elegir_camino_para_flow(flow)
                self.buscar_caminos(flow)
            else:
                log.info("* * * * * No se handlear este protocolo * * * * * %s", ip_packet.protocol)

    # TODO: usar los caminos minimos calculados
    def elegir_camino_para_flow(self, flow, caminos=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]):
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

        log.info("cantidad_de_caminos totales %s", len(caminos))
        log.info("cantidad_de_caminos_para_tcp %s", cantidad_de_caminos_para_tcp)
        log.info("cantidad_de_caminos_para_udp %s", cantidad_de_caminos_para_udp)

        # Nuestro balanceo de caminos lo haremos unicamente en base a los puertos origen y destino
        caminos_para_tcp = caminos[0:cantidad_de_caminos_para_tcp]
        caminos_para_udp = caminos[cantidad_de_caminos_para_tcp:len(caminos)] if resto_de_caminos else caminos_para_tcp
        log.info("caminos_para_tcp: %s", caminos_para_tcp)
        log.info("caminos_para_udp: %s", caminos_para_udp)

        suma_puertos = flow['puerto_origen'] + flow['puerto_destino']
        log.info("suma_puertos: %s", suma_puertos)

        if flow['protocolo'] == pkt.ipv4.TCP_PROTOCOL:
            camino = caminos_para_tcp[suma_puertos % len(caminos_para_tcp)]
            log.info("camino elegido para tcp: %s", camino)
            return camino
        elif flow['protocolo'] == pkt.ipv4.UDP_PROTOCOL:
            camino = caminos_para_udp[suma_puertos % len(caminos_para_udp)]
            log.info("camino elegido para udp: %s", camino)
            return camino

    def buscar_caminos(self, flow):
      print(flow)
