from extensions.caminos import FatTree, Switch, Link
from pox.core import core
import pox.openflow.discovery
import pox.openflow.spanning_tree
import pox.forwarding.l2_learning
from extensions.switch import SwitchController
# import pox.host_tracker


log = core.getLogger()


class Controller:
    def __init__(self):
        self.connections = set()
        self.switches = []
        self.fat_tree = FatTree()

        # Esperando que los modulos openflow y openflow_discovery esten listos
        core.call_when_ready(self.startup, ('openflow', 'openflow_discovery'))

    def _handle_HostEvent(self, event):
        """
        Listen to host_tracker events, fired up every time a host is up or down
        To fire up we must issue a pingall from mininet cli.
        Args:
            event: HostEvent listening to core.host_tracker
        Returns: nada
        """
        macaddr = event.entry.macaddr.toStr()
        port = event.entry.port
        print('macaddr', macaddr)
        print('port', port)
        print('event', event)
        # your code here

    def startup(self):
        """
        Esta funcion se encarga de inicializar el controller
        Agrega el controller como event handler para los eventos de
        openflow y openflow_discovery
        """
        core.openflow.addListeners(self)
        core.openflow_discovery.addListeners(self)
        # core.host_tracker.addListenerByName("HostEvent", self._handle_HostEvent)
        log.info('Controller initialized')

    def _handle_ConnectionUp(self, event):
        """
        Esta funcion es llamada cada vez que un nuevo switch establece conexion
        Se encarga de crear un nuevo switch controller para manejar los eventos de cada switch
        """
        # log.info("Switch %s has come up.", dpid_to_str(event.dpid))
        if event.connection not in self.connections:

            nombre = event.connection.features.ports[0].name
            switch = Switch(nombre, event.connection, event.dpid)
            self.fat_tree.agregar_switch(switch)

            self.connections.add(event.connection)
            sw = SwitchController(event.dpid, event.connection, self.fat_tree)
            self.switches.append(sw)

    def _handle_LinkEvent(self, event):
        """
        Esta funcion es llamada cada vez que openflow_discovery descubre un nuevo enlace
        """
        link = event.link
        # log.info("Link has been discovered from %s,%s to %s,%s", dpid_to_str(link.dpid1), link.port1,
        #          dpid_to_str(link.dpid2), link.port2)

        switch1 = self.fat_tree.get_switch_por_dpid(link.dpid1)
        switch2 = self.fat_tree.get_switch_por_dpid(link.dpid2)
        link = Link(switch1, switch2)

        if event.added:
            self.fat_tree.agregar_link(link)
            print("Link agregado", link)
        else:
            self.fat_tree.quitar_link(link)
            print("Link quitado", link)


def launch():
    # Inicializando el modulo openflow_discovery
    pox.openflow.discovery.launch()
    # pox.host_tracker.launch()

    # Registrando el Controller en pox.core para que sea ejecutado
    core.registerNew(Controller)

    """
    Corriendo Spanning Tree Protocol y el modulo l2_learning.
    No queremos correrlos para la resolucion del TP.
    Aqui lo hacemos a modo de ejemplo
    """
    # pox.openflow.spanning_tree.launch()
    # pox.forwarding.l2_learning.launch()
