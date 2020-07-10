from mininet.topo import Topo
import math


class FatTree(Topo):
    """
    Crea una topologia fat tree (los nodos del nivel N del
    arbol estan conectados todos con todos con los nodos del nivel N-1).
    Ademas aniade 3 hosts a la raiz y un host a cada uno de los nodos hoja.
    """

    def __init__(self, tree_levels=3, **opts):
        Topo.__init__(self, **opts)

        print("Creating FAT TREE topology with {} levels".format(tree_levels))

        HOSTS_IN_ROOT = 3
        switches = []
        hosts = []
        previous_level_switches = []
        new_level_switches = []
        AMOUNT_OF_SWITCHES_FOR_LAST_LEVEL = int(math.pow(2, tree_levels - 1))
        
        for level in range(0, tree_levels):
            # clear list
            new_level_switches = []

            for level in range(0, tree_levels):
                # clear list
                new_level_switches = []
                switches_amount_for_level = int(math.pow(2, level))
                print('LEVEL: {}. new_level_switches = {}'.format(level, new_level_switches))
                print('LEVEL: {}. previous_level_switches = {}'.format(level, previous_level_switches))

                print('{} switches for level {}'.format(switches_amount_for_level, level))

                for _ in range(0, switches_amount_for_level):
                    sw_unique_id = len(switches)
                    sw = self.addSwitch('sw{}_{}'.format(sw_unique_id, level))
                    switches.append(sw)
                    new_level_switches.append(sw)

            # Agregamos los hosts a cada una de las hojas si es el ultimo nivel
            if level == tree_levels - 1:
                print('adding hosts to leaf switches')
                new_host_id = 1
                for switch_in_new_level in new_level_switches:
                    host_id = new_host_id
                    new_host_id += 1
                    print('adding host  h{} to leaf switch {}'.format(host_id, switch_in_new_level))
                    host = self.addHost('h{}'.format(host_id))
                    hosts.append(host)
                    self.addLink(switch_in_new_level, host)

            # Agregamos los tres hosts si es la raiz
            if level == 0:
                print('adding hosts to root switch')
                for host_id in range(AMOUNT_OF_SWITCHES_FOR_LAST_LEVEL + 1, AMOUNT_OF_SWITCHES_FOR_LAST_LEVEL + HOSTS_IN_ROOT + 1):
                    print('adding host  h{} to root'.format(host_id))
                    hosts.append(self.addHost('h{}'.format(host_id)))

                # Agregamos los tres hosts si es la raiz
                if level == 0:
                    print('adding hosts to root switch')
                    for host_id in range(1, HOSTS_IN_ROOT + 1):
                        print('adding host  h{} to root'.format(host_id))
                        hosts.append(self.addHost('h{}'.format(host_id)))


                # Agregamos los hosts a cada una de las hojas si es el ultimo nivel
                if level == tree_levels - 1:
                    print('adding hosts to leaf switches')
                    for switch_in_new_level in new_level_switches:
                        host_id = len(hosts) + 1
                        print('adding host  h{} to leaf switch {}'.format(host_id, switch_in_new_level))
                        host = self.addHost('h{}'.format(host_id))
                        hosts.append(host)
                        self.addLink(switch_in_new_level, host)

                previous_level_switches = new_level_switches


topos = {'fat_tree': FatTree}
