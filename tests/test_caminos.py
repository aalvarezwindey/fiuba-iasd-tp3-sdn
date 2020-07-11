from controller.extensions.caminos import FatTree, Switch, Link


class TestCaminosConTresNiveles:

    def setup_method(self, method):
        """ setup any state tied to the execution of the given method in a
        class.  setup_method is invoked for every test method of a class.
        """
        self.fat_tree = FatTree()
        switches = ['sw0_0_1', 'sw1_1_1', 'sw2_1_2', 'sw3_2_1', 'sw4_2_2', 'sw5_2_3', 'sw6_2_4']
        for switch in switches:
            self.fat_tree.agregar_switch(Switch(switch, None, switch))

        links = [('sw0_0_1', 'sw1_1_1'), ('sw0_0_1', 'sw2_1_2'),
                 ('sw1_1_1', 'sw3_2_1'), ('sw1_1_1', 'sw4_2_2'),
                 ('sw1_1_1', 'sw5_2_3'), ('sw1_1_1', 'sw6_2_4'),
                 ('sw2_1_2', 'sw3_2_1'), ('sw2_1_2', 'sw4_2_2'),
                 ('sw2_1_2', 'sw5_2_3'), ('sw2_1_2', 'sw6_2_4')]

        for sw1_nombre, sw2_nombre in links:
            sw1 = self.fat_tree.get_switch_por_dpid(sw1_nombre)
            sw2 = self.fat_tree.get_switch_por_dpid(sw2_nombre)
            self.fat_tree.agregar_link(Link(sw1, sw2))

    def test_hay_dos_caminos_desde_el_root_al_nivel_inferior(self):
        sw_root = self.fat_tree.get_switch_por_dpid('sw0_0_1')
        sw_inferior = self.fat_tree.get_switch_por_dpid('sw6_2_4')
        caminos = self.fat_tree.get_caminos(sw_root, sw_inferior)
        assert len(caminos) == 2

    def test_hay_dos_caminos_desde_el_nivel_inferior_al_root(self):
        sw_root = self.fat_tree.get_switch_por_dpid('sw0_0_1')
        sw_inferior = self.fat_tree.get_switch_por_dpid('sw6_2_4')
        caminos = self.fat_tree.get_caminos(sw_inferior, sw_root)
        assert len(caminos) == 2

    def test_hay_un_camino_desde_el_nivel_inferior_al_medio(self):
        sw_medio = self.fat_tree.get_switch_por_dpid('sw1_1_1')
        sw_inferior = self.fat_tree.get_switch_por_dpid('sw6_2_4')
        caminos = self.fat_tree.get_caminos(sw_inferior, sw_medio)
        assert len(caminos) == 1

    def test_hay_un_camino_desde_el_nivel_medio_al_nivel_inferior(self):
        sw_medio = self.fat_tree.get_switch_por_dpid('sw1_1_1')
        sw_inferior = self.fat_tree.get_switch_por_dpid('sw6_2_4')
        caminos = self.fat_tree.get_caminos(sw_medio, sw_inferior)
        assert len(caminos) == 1

    def test_hay_un_camino_desde_el_nivel_medio_al_root(self):
        sw_medio = self.fat_tree.get_switch_por_dpid('sw1_1_1')
        sw_root = self.fat_tree.get_switch_por_dpid('sw0_0_1')
        caminos = self.fat_tree.get_caminos(sw_medio, sw_root)
        assert len(caminos) == 1

    def test_hay_dos_caminos_desde_el_nivel_inferior_al_nivel_inferior(self):
        sw1 = self.fat_tree.get_switch_por_dpid('sw6_2_4')
        sw2 = self.fat_tree.get_switch_por_dpid('sw3_2_1')
        caminos = self.fat_tree.get_caminos(sw1, sw2)
        assert len(caminos) == 2


class TestCaminosConCuatroNiveles:

    def setup_method(self, method):
        """ setup any state tied to the execution of the given method in a
        class.  setup_method is invoked for every test method of a class.
        """
        self.fat_tree = FatTree()
        switches = ['sw0_0_1', 'sw1_1_1', 'sw2_1_2', 'sw3_2_1',
                    'sw4_2_2', 'sw5_2_3', 'sw6_2_4', 'sw7_3_1',
                    'sw8_3_2', 'sw9_3_3', 'sw10_3_4', 'sw11_3_5',
                    'sw12_3_6', 'sw13_3_7', 'sw14_3_8']

        for switch in switches:
            self.fat_tree.agregar_switch(Switch(switch, None, switch))

        links = [('sw0_0_1', 'sw1_1_1'), ('sw0_0_1', 'sw2_1_2'), ('sw1_1_1', 'sw3_2_1'),
                 ('sw1_1_1', 'sw4_2_2'), ('sw1_1_1', 'sw5_2_3'), ('sw1_1_1', 'sw6_2_4'),
                 ('sw2_1_2', 'sw3_2_1'), ('sw2_1_2', 'sw4_2_2'), ('sw2_1_2', 'sw5_2_3'),
                 ('sw2_1_2', 'sw6_2_4'), ('sw3_2_1', 'sw7_3_1'), ('sw3_2_1', 'sw8_3_2'),
                 ('sw3_2_1', 'sw9_3_3'), ('sw3_2_1', 'sw10_3_4'), ('sw3_2_1', 'sw11_3_5'),
                 ('sw3_2_1', 'sw12_3_6'), ('sw3_2_1', 'sw13_3_7'), ('sw3_2_1', 'sw14_3_8'),
                 ('sw4_2_2', 'sw7_3_1'), ('sw4_2_2', 'sw8_3_2'), ('sw4_2_2', 'sw9_3_3'),
                 ('sw4_2_2', 'sw10_3_4'), ('sw4_2_2', 'sw11_3_5'), ('sw4_2_2', 'sw12_3_6'),
                 ('sw4_2_2', 'sw13_3_7'), ('sw4_2_2', 'sw14_3_8'), ('sw5_2_3', 'sw7_3_1'),
                 ('sw5_2_3', 'sw8_3_2'), ('sw5_2_3', 'sw9_3_3'), ('sw5_2_3', 'sw10_3_4'),
                 ('sw5_2_3', 'sw11_3_5'), ('sw5_2_3', 'sw12_3_6'), ('sw5_2_3', 'sw13_3_7'),
                 ('sw5_2_3', 'sw14_3_8'), ('sw6_2_4', 'sw7_3_1'), ('sw6_2_4', 'sw8_3_2'),
                 ('sw6_2_4', 'sw9_3_3'), ('sw6_2_4', 'sw10_3_4'), ('sw6_2_4', 'sw11_3_5'),
                 ('sw6_2_4', 'sw12_3_6'), ('sw6_2_4', 'sw13_3_7'), ('sw6_2_4', 'sw14_3_8')]

        for sw1_nombre, sw2_nombre in links:
            sw1 = self.fat_tree.get_switch_por_dpid(sw1_nombre)
            sw2 = self.fat_tree.get_switch_por_dpid(sw2_nombre)
            self.fat_tree.agregar_link(Link(sw1, sw2))

    def test_hay_cuatro_caminos_desde_el_nivel_inferior_al_nivel_inferior(self):
        sw1 = self.fat_tree.get_switch_por_dpid('sw14_3_8')
        sw2 = self.fat_tree.get_switch_por_dpid('sw13_3_7')
        caminos = self.fat_tree.get_caminos(sw1, sw2)
        assert len(caminos) == 4
