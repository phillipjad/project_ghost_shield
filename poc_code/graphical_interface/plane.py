from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from panda3d.core import load_prc_file
import simplepbr


class Enviroment(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        simplepbr.init()

        self.enviroment = self.loader.loadModel('model/enviroment.glb')
        self.enviroment.setPos(0, 5, 0)
        self.enviroment.reparentTo(self.render)


app = Enviroment()
app.run()
