#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re


class Switch:

    def __init__(self, nombre, conexion, dpid):
        self.nombre = nombre
        self.conexion = conexion
        self.dpid = dpid

    def get_nivel(self):
        return int(re.search('sw[0-9]+_([0-9]+)_[0-9]+', self.nombre).group(1))

    def get_indice(self):
        return int(re.search('sw[0-9]+_[0-9]+_([0-9]+)', self.nombre).group(1))

    def __str__(self):
        return 'Switch {}'.format(self.nombre)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.nombre == other.nombre and \
                self.dpid == other.dpid

class Link:

    def __init__(self, switch1, switch2, link_info):
        self.switch1 = switch1
        self.switch2 = switch2
        self.port_switch_1 = link_info.port1
        self.port_switch_2 = link_info.port2

    def __str__(self):
        return 'Link switch1: {}, switch2: {} port1: {} port2: {}'.format(self.switch1, self.switch2, self.port_switch_1, self.port_switch_2)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.switch1 == other.switch1 and \
                self.switch2 == other.switch2 and \
                self.port_switch_1 == other.port_switch_1 and \
                self.port_switch_2 == other.port_switch_2


class Nivel:

    def __init__(self, nivel):
        self.switches = []
        self.nivel = nivel

    def agregar_switch(self, switch):
        self.switches.append(switch)

    def get_switch_por_dpid(self, dpid):
        for switch in self.switches:
            if switch.dpid == dpid:
                return switch
        return False

    def quitar_switch(self, switch):
        self.switches.remove(switch)

    def __str__(self):
        return 'Nivel {}: {}'.format(self.nivel, self.switches)

    def __repr__(self):
        return self.__str__()


class Links:
    """Modela los links que salen de un switch"""

    def __init__(self):
        self.switches = {}

    def agregar_switch(self, switch):
        self.switches[switch.nombre] = switch

    def quitar_switch(self, switch):
        if switch.nombre in self.switches:
            del self.switches[switch.nombre]

    def get_switches_a_nivel(self, nivel):
        switches = []
        for switch in self.switches.values():
            if switch.get_nivel() == nivel:
                switches.append(switch)
        return switches

    def __str__(self):
        return 'Links: {}'.format(self.switches)

    def __repr__(self):
        return self.__str__()


class Camino:

    def __init__(self):
        self.switches = []

    def agregar_switch(self, switch):
        self.switches.append(switch)

    def copiar(self):
        nuevo_camino = Camino()
        nuevo_camino.switches = list(self.switches)
        return nuevo_camino

    def invertir(self):
        self.switches = list(reversed(self.switches))

    def __add__(self, otro):
        nuevo = Camino()
        nuevo.switches = self.switches + otro.switches
        return nuevo

    def __str__(self):
        return 'Camino: {}'.format(self.switches)

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self.switches)


class FatTree:

    def __init__(self):
        self.niveles = {}
        self.links_por_switch = {}

    def get_nivel_inferior(self):
        return self.niveles[max(self.niveles.keys())]

    def agregar_switch(self, switch):
        nivel = self.niveles.get(switch.get_nivel(), Nivel(switch.get_nivel()))
        nivel.agregar_switch(switch)
        self.niveles[switch.get_nivel()] = nivel

    def get_switch_por_dpid(self, dpid):
        for nivel in self.niveles.values():
            switch = nivel.get_switch_por_dpid(dpid)
            if switch:
                return switch
        return False

    def agregar_link(self, link):
        switch1 = link.switch1
        switch2 = link.switch2
        assert switch1 is not False
        assert switch2 is not False

        links_switch1 = self.links_por_switch.get(switch1.nombre, Links())
        links_switch2 = self.links_por_switch.get(switch2.nombre, Links())

        links_switch1.agregar_switch(switch2)
        links_switch2.agregar_switch(switch1)

        self.links_por_switch[switch1.nombre] = links_switch1
        self.links_por_switch[switch2.nombre] = links_switch2

    def get_caminos(self, switch_origen, switch_destino):
        if switch_origen.get_nivel() != switch_destino.get_nivel():
            return self.get_caminos_distinto_nivel(switch_origen, switch_destino)
        return self.get_caminos_mismo_nivel(switch_origen, switch_destino)

    def get_caminos_mismo_nivel(self, switch_origen, switch_destino):
        """
        Obtengo los caminos para switches que van desde el nivel
        inferior al nivel inferior.
        """
        # Creo el camino agregando el origen.
        camino = Camino()
        camino.agregar_switch(switch_origen)
        return self._get_caminos_mismo_nivel(switch_origen, switch_destino, camino)

    def _get_caminos_mismo_nivel(self, switch_origen, switch_destino, camino):
        caminos_encontrados = self.get_caminos_distinto_nivel(switch_origen, switch_destino)
        # Si encontré caminos, entonces los concateno con el camino actual.
        if caminos_encontrados:
            caminos = []
            for camino_encontrado in caminos_encontrados:
                camino_nuevo = camino.copiar()
                camino_nuevo.switches += camino_encontrado.switches[1:]
                caminos.append(camino_nuevo)
            return caminos

        links = self.links_por_switch[switch_origen.nombre]
        switches_nivel_superior = links.get_switches_a_nivel(switch_origen.get_nivel() - 1)

        # No hay switches en el nivel superior (camino sin salida).
        if not switches_nivel_superior:
            return []

        caminos = []
        for switch in switches_nivel_superior:
            nuevo_camino = camino.copiar()
            nuevo_camino.agregar_switch(switch)
            caminos += self._get_caminos_mismo_nivel(switch, switch_destino, nuevo_camino)
        return caminos

    def get_caminos_distinto_nivel(self, switch_origen, switch_destino):
        """
        Obtengo los caminos para switches que van desde el root al
        nivel inferior o viceversa.
        """
        # Si voy desde la raiz hacia niveles inferiores, invierto el orden
        # y luego invierto el resultado.
        invertir = False
        if switch_origen.get_nivel() < switch_destino.get_nivel():
            switch_origen, switch_destino = switch_destino, switch_origen
            invertir = True

        # Creo el camino agregando el origen.
        camino = Camino()
        camino.agregar_switch(switch_origen)

        caminos = self._get_caminos_distinto_nivel(switch_origen, switch_destino, camino)
        if invertir:
            for camino in caminos:
                camino.invertir()
        return caminos

    def _get_caminos_distinto_nivel(self, switch_origen, switch_destino, camino):
        """
        Obtengo los caminos para switches que van desde el nivel
        inferior al root.
        """
        # Llegué a destino.
        if switch_origen == switch_destino:
            return [camino]

        links = self.links_por_switch[switch_origen.nombre]
        switches_nivel_superior = links.get_switches_a_nivel(switch_origen.get_nivel() - 1)

        # No hay switches en el nivel superior (camino sin salida).
        if not switches_nivel_superior:
            return []

        caminos = []
        for switch in switches_nivel_superior:
            nuevo_camino = camino.copiar()
            nuevo_camino.agregar_switch(switch)
            caminos += self._get_caminos_distinto_nivel(switch, switch_destino, nuevo_camino)
        return caminos

    def __str__(self):
        return 'FatTree: \n' \
               '  Niveles: {}\n' \
               '  Links: {}'.format(self.niveles, str(self.links_por_switch))

    def __repr__(self):
        return self.__str__()

    def quitar_link(self, link):
        switch1 = link.switch1
        switch2 = link.switch2
        assert switch1 is not False
        assert switch2 is not False

        links_switch1 = self.links_por_switch[switch1.nombre]
        links_switch2 = self.links_por_switch[switch2.nombre]

        links_switch1.quitar_switch(switch2)
        links_switch2.quitar_switch(switch1)

    def quitar_switch(self, switch):
        nivel = self.niveles.get(switch.get_nivel(), Nivel(switch.get_nivel()))
        nivel.quitar_switch(switch)
