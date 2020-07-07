#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re


class Switch:

    def __init__(self, nombre, conexion, dpid):
        self.nombre = nombre
        self.conexion = conexion
        self.dpid = dpid

    def get_nivel(self):
        return int(re.search('sw([0-9]+)_[0-9]+', self.nombre).group(1))

    def __str__(self):
        return 'Switch nombre: {}, conexion: {}, dpip: {}'.format(self.nombre, self.conexion, self.dpid)

    def __repr__(self):
        return self.__str__()


class Link:

    def __init__(self, dpid1, puerto1, dpid2, puerto2):
        self.dpid1 = dpid1
        self.puerto1 = puerto1
        self.dpid2 = dpid2
        self.puerto2 = puerto2

    def __str__(self):
        return 'Link dpid1: {}, puerto1: {}, dpip2: {}, puerto2: {}'.format(self.dpid1, self.puerto1, self.dpid2, self.puerto2)

    def __repr__(self):
        return self.__str__()


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

    def get_switches_a_nivel(self, nivel):
        switches = []
        for switch in self.switches:
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
        nuevo_camino.switches = self.switches.copy()
        return nuevo_camino

    def __str__(self):
        return 'Camino: {}'.format(self.switches)

    def __repr__(self):
        return self.__str__()


class FatTree:

    def __init__(self):
        self.niveles = {}
        self.links_por_switch = {}

    def agregar_switch(self, switch):
        nivel = self.niveles.get(switch.get_nivel(),
                                 Nivel(switch.get_nivel()))
        nivel.agregar_switch(switch)
        self.niveles[switch.get_nivel()] = nivel

    def get_switch_por_dpid(self, dpid):
        for nivel in self.niveles.values():
            switch = nivel.get_switch_por_dpid(dpid)
            if switch:
                return switch
        return False

    def agregar_link(self, link):
        switch1 = self.get_switch_por_dpid(link.dpid1)
        switch2 = self.get_switch_por_dpid(link.dpid2)
        assert switch1 is not False
        assert switch2 is not False

        links_switch1 = self.links_por_switch.get(switch1.nombre, Links())
        links_switch2 = self.links_por_switch.get(switch2.nombre, Links())

        links_switch1.agregar_switch(switch2)
        links_switch2.agregar_switch(switch1)

        self.links_por_switch[switch1.nombre] = links_switch1
        self.links_por_switch[switch2.nombre] = links_switch2

    def get_caminos(self, switch_origen, switch_destino, camino=None):
        if not camino:
            camino = Camino()

        # En principio busco ir de abajo hacia arriba unicamente
        # (despues vemos otros casos).
        links = self.links_por_switch[switch_origen.nombre]
        switches_nivel_superior = links.get_switches_a_nivel(switch_origen.get_nivel() - 1)

        if switch_origen == switch_destino:  # llegué a destino
            return [camino]

        if not switches_nivel_superior:  # no hay switches en el nivel superior (camino sin salida)
            return []

        caminos = []
        for switch in switches_nivel_superior:
            nuevo_camino = camino.copiar()
            nuevo_camino.agregar_switch(switch)
            caminos += self.get_caminos(switch, switch_destino, nuevo_camino)
        return caminos

    def __str__(self):
        return 'FatTree: \n' \
               '  Niveles: {}\n' \
               '  Links: {}'.format(self.niveles, str(self.links_por_switch))

    def __repr__(self):
        return self.__str__()

    def quitar_link(self, link):
        # TODO.
        pass

    def quitar_switch(self, switch):
        # TODO.
        pass
