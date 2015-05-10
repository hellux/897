from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty
from kivy.vector import Vector

from lib.system import lu

class EnsBullet(Widget):
    vel_x, vel_y = NumericProperty(0), NumericProperty(0)
    vel_m = lu(10)
    vel = ReferenceListProperty(vel_x, vel_y)

    def __init__(self, player):
        super(EnsBullet, self).__init__()
        self.width = lu(3)
        self.height = self.width
        self.center = player.points[0], player.points[1]
        self.vel = self.vel_m*player.cosv, self.vel_m*player.sinv

    def move(self):
        self.pos = Vector(*self.vel) + self.pos
        if not 0 < self.x < self.parent.width:
            self.x = self.parent.width - self.x
        if not 0 < self.y < self.parent.height:
            self.y = self.parent.height - self.y
        self.canvas.ask_update()