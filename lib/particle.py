from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty
from kivy.vector import Vector

class EnsParticle(Widget):
    vel_x = NumericProperty(0)
    vel_y = NumericProperty(0)
    vel = ReferenceListProperty(vel_x, vel_y)
    color = ListProperty([1,1,1])

    def __init__(self, pos, size, color, vel):
        super(EnsParticle, self).__init__()		
        self.width = size
        self.pos = pos
        self.vel = vel
        self.color = color

    def move(self):
        self.pos = Vector(*self.vel) + self.pos
