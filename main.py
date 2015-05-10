#!usr/bin/python

from kivy import require
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivy.properties import NumericProperty, ObjectProperty, \
                            StringProperty

from math import cos, sin, atan, pi, radians
from random import randint, choice
from functools import partial

from lib.player import EnsPlayer
from lib.bullet import EnsBullet
from lib.asteroid import EnsAsteroid
from lib.particle import EnsParticle
from lib.system import lu, WIDTH, HEIGHT, platform, PY_VER

__title__ = 'EightNineSeven'
__version__ = '0.5.8'
__domain__ = 'hellux'
__android_package__ = 'ens'

__kivy_version__ = "1.9.0"

require(__kivy_version__)

class EnsDebugger(Widget):
    """if debug == True gathers variable values and displays them
       if fps == True displays fps"""
    label = ObjectProperty(None)
    debug = False
    fps = True
    label_text = StringProperty("")
    font_size = NumericProperty(lu(15))

    def update(self):
        self.label.top = HEIGHT
        self.label.right = WIDTH
        if self.debug:
            data = [
                ["fps", int(Clock.get_fps())],
                ["rfps", int(Clock.get_rfps())],
            ]
            self.label_text = "{}, {}.{} version {}".format(__title__,
                                                            __domain__,
                                                            __android_package__,
                                                            __version__)
            for element, value in data:
                self.label_text += "\n[color=888888]{}:[/color] {}".format(element,
                                                                           value)
        elif self.fps:
            self.label_text = "fps: {:.0f}".format(Clock.get_fps())

class EnsScore(Widget):
    """displays and stores score and lives"""
    label = ObjectProperty(None)
    score = NumericProperty(0)
    lives = NumericProperty(0)
    h = NumericProperty(HEIGHT)
    font_size = NumericProperty(lu(50))
    scores = {"small": 100,
              "medium": 50,
              "large": 20}
    player_models = []

    def __init__(self, **kwargs):
        super(EnsScore, self).__init__(**kwargs)

    def reset(self):
        """restore values and draw 3 player models"""
        self.lives = 3
        self.score = 0
        self.player_models = []
        for i in range(3):
            player = EnsPlayer()
            player.h = lu(20)
            player.w = player.h*0.75
            player.cpos = lu(15) + lu(25)*i, HEIGHT-self.font_size-lu(15)
            player.set_points()
            self.player_models.append(player)
            self.add_widget(player)


    def add(self, score_token):
        self.score += self.scores[score_token]

    def die(self):
        """subtract hp, remove player model"""
        self.lives -= 1
        self.remove_widget(self.player_models[self.lives])

class EnsEnd(Widget):
    """handles post game"""
    lbl_score = ObjectProperty(None)
    lbl_best = ObjectProperty(None)
    lbl_game_over = ObjectProperty(None)
    lbl_retry = ObjectProperty(None)
    lbl_exit = ObjectProperty(None)

    res_x, res_y = WIDTH, HEIGHT

    def __init__(self, score, best):
        super(EnsEnd, self).__init__()
        for lbl in self.children:
            lbl.font_size = lu(50)
            lbl.font_name = "DroidSansMono"

        self.lbl_game_over.font_size = lu(100)
        self.lbl_game_over.text = "GAME OVER"
        self.lbl_game_over.center = WIDTH/2, HEIGHT*0.8

        self.lbl_score.text = "Your score: " + str(score)
        self.lbl_score.center = WIDTH/2, HEIGHT*0.6

        self.lbl_best.text = "High score: " + str(best)
        self.lbl_best.center = WIDTH/2, HEIGHT*0.5

        self.lbl_retry.text = "Play again"
        self.lbl_exit.text = "Quit game"

class EnsStart(Widget):
    """handles pre game"""
    lbl_title = ObjectProperty(None)
    lbl_start = ObjectProperty(None)
    lbl_info = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(EnsStart, self).__init__(**kwargs)

        self.lbl_title.text = "EightNineSeven"
        self.lbl_title.font_size = lu(100)
        self.lbl_title.center = WIDTH/2, HEIGHT*0.6

        self.color = 0, 1, 1
        self.lbl_start.text = "Press anywhere to start"
        self.lbl_start.font_size = lu(40)
        self.lbl_start.center = WIDTH/2, HEIGHT*0.45

        self.lbl_info.text = "{}.{} {}\nKivy {}\nPython {}".format(__domain__,
                                                                   __package__,
                                                                   __version__,
                                                                   __kivy_version__,
                                                                   PY_VER)
        self.lbl_info.font_size = lu(15)
        self.lbl_info.halign = "center"
        self.lbl_info.center = WIDTH/2, HEIGHT/10

class EnsGame(Widget):
    """main game widget"""
    player = ObjectProperty(None)
    debugger = ObjectProperty(None)
    score = ObjectProperty(None)

    storage = JsonStore("ens.json")
    if not storage.exists("high_score"):
        storage.put("high_score", score=0)

    start = None
    end = None

    current_round = 0
    game_mode = "start"
    bullets = [] #list of EnsBullet instances
    asteroids = []
    particles = []

    def __init__(self, **kwargs):
        """initialize keyboard if not mobile"""
        super(EnsGame, self).__init__(**kwargs)
        if platform() == "pc":
            self._keyboard = Window.request_keyboard(self._keyboard_closed,
                                                     self,
                                                     'text')
            self._keyboard.bind(on_key_down=self.on_keyboard_down)
            self._keyboard.bind(on_key_up=self.on_keyboard_up)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self.on_keyboard_down)
        self._keyboard = None

    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """handles key pressess"""
        if keycode[1] == "f3":
            self.debugger.debug = not self.debugger.debug
            self.debugger.debug_label = ""
        if self.game_mode == "ingame":
            if keycode[1] in ["left", "a"]:
                self.player.turn = True
                self.player.turn_direction = True
            if keycode[1] in ["right", "d"]:
                self.player.turn = True
                self.player.turn_direction = False
            if keycode[1] in ["up", "w", "shift"]:
                self.player.boost = True
            if keycode[1] in ["spacebar", "rshift"]:
                self.shoot()
        return True

    def on_keyboard_up(self, keyboard, keycode):
        """handles key releases"""
        if self.game_mode == "ingame":
            if keycode[1] in ["left", "right", "a", "d"]:
                self.player.turn = False
            if keycode[1] in ["up", "shift", "w"]:
                self.player.boost = False
        return True

    def on_touch_down(self, touch):
        """handles touch down events"""
        if self.game_mode == "ingame":
            if touch.x < self.center_x:#turn
                self.player.turn = True
                self.player.turn_touch_id = touch.id
                if touch.x < self.width/4:
                    self.player.turn_direction = True #left
                else:
                    self.player.turn_direction = False #right
            else:
                if touch.x < self.width*3/4: #boost
                    self.player.boost = True
                    self.player.boost_touch_id = touch.id
                else: #shoot
                    self.shoot()
        if self.game_mode == "end":
            if self.end in self.children:
                if self.end.lbl_retry.collide_point(*touch.pos):
                    self.new_game()
                if self.end.lbl_exit.collide_point(*touch.pos):
                    EnsApp().stop()
        if self.game_mode == "start":
            self.new_game()

    def on_touch_up(self, touch):
        """handles touch release events"""
        if touch.id == self.player.turn_touch_id:
            self.player.turn = False #stop turn
        if touch.id == self.player.boost_touch_id:
            self.player.boost = False #stop boost

    def shoot(self):
        """spawns bullets and sets cooldown on shooting"""
        if self.player.alive and self.player.shoot_allowed:
            if self.player.safe_mode:
                self.player.remove_safe_mode(None)
            bullet = EnsBullet(self.player)
            self.add_widget(bullet, 1)
            self.bullets.append(bullet)
            self.player.shoot_allowed = False
            Clock.schedule_once(self.player.allow_shoot,
                                0.15)
            Clock.schedule_once(partial(self.remove_entity,
                                        bullet,
                                        self.bullets),
                                1)

    def animate_explosion(self, pos):
        """spawns particles going in random directions and sets timer for removal"""
        size = lu(3)
        color = 1, 1, 1
        for _ in xrange(3):
            vel_m = lu(randint(0, 10)/2.0 + 1)
            lifetime = randint(10, 20)/60.0
            pivot = radians(randint(0, 360))
            vel = vel_m*cos(pivot), vel_m*sin(pivot)
            particle = EnsParticle(pos, size, color, vel)
            self.add_widget(particle, 1)
            self.particles.append(particle)
            Clock.schedule_once(partial(self.remove_entity,
                                        particle,
                                        self.particles),
                                lifetime)

    def new_round(self):
        """spawns new asteroids"""
        for _ in xrange(4+self.current_round*2):
            #pos
            rand_x = randint(0, self.width)
            rand_y = randint(0, self.height)
            pos = choice([[rand_x, 0],
                          [rand_x, self.height],
                          [0, rand_y],
                          [self.width, rand_y]])
            if pos[0] != self.center_x:
                pivot = atan((self.center_y - pos[1]) / (self.center_x - pos[0]))
            else:
                pivot = 0
            if pos[0] > self.center_x:
                pivot += pi
            #vel
            pivot += radians(randint(-30, 30))
            vel_m = lu(randint(1, 5)/2.0)
            vel = vel_m*cos(pivot), vel_m*sin(pivot)
            #col
            gray = randint(100, 150)/255.0
            color = [gray+randint(-25, 25)/255.0, gray, gray]
            #create ast
            asteroid = EnsAsteroid(pos, "large", vel, color)
            asteroid.move()
            self.create_entity(asteroid, self.asteroids)
        self.current_round += 1

    def destroy_asteroid(self, asteroid):
        """removes asteroid entity and if bigger than small creates a smaller one"""
        Clock.create_trigger(self.remove_entity(asteroid, self.asteroids))
        if asteroid.diameter == "large": diameter = "medium"
        elif asteroid.diameter == "medium": diameter = "small"
        else: return
        pivot = radians(randint(0, 360))
        vel_m = lu(2)
        vel_x = vel_m*cos(pivot)
        vel_y = vel_m*sin(pivot)
        for mul in [-1, 1]:
            asteroid = EnsAsteroid([asteroid.center_x+5*mul*vel_x,
                                    asteroid.center_y+5*mul*vel_y],
                                   diameter,
                                   [asteroid.vel_x+vel_x*mul,
                                    asteroid.vel_y+vel_y*mul],
                                   asteroid.color)
            self.asteroids.append(asteroid)
            self.add_widget(asteroid)

    def new_game(self):
        """resets all variables and initiates new game"""
        self.game_mode = "ingame"
        if not self.player in self.children: self.add_widget(self.player)
        if not self.score in self.children: self.add_widget(self.score, 0)
        self.current_round = 0
        for asteroid in self.asteroids:
            Clock.schedule_once(partial(self.remove_entity,
                                        asteroid,
                                        self.asteroids),
                                0)
        self.handle_widgets()
        self.score.reset()
        self.player.reset()
        if self.end in self.children: self.remove_widget(self.end)
        if self.start in self.children: self.remove_widget(self.start)

    def update(self, *largs):
        """main loop that runs 60 times a second"""
        self.debugger.update()
        if self.game_mode == "ingame":
            self.player.move()
        self.handle_widgets()

    def handle_widgets(self):
        """handle all movement and collision for all entities"""
        if not len(self.asteroids):
            self.new_round()

        for bullet in self.bullets:
            bullet.move()

        for asteroid in self.asteroids:
            asteroid.move()
            if self.player.alive and not self.player.safe_mode:
                for bullet in self.bullets:
                    if asteroid.collide_point(*bullet.pos): #bullet collision
                        self.animate_explosion(asteroid.center)
                        self.destroy_asteroid(asteroid)
                        self.score.add(asteroid.diameter)
                        Clock.schedule_once(partial(self.remove_entity,
                                                    bullet,
                                                    self.bullets),
                                            0)
                        Clock.schedule_once(partial(self.remove_entity,
                                                    bullet,
                                                    self.bullets),
                                            0)
                if asteroid.collide_widget(self.player): #player collision
                    self.animate_explosion(asteroid.center)
                    self.player.die()
                    self.destroy_asteroid(asteroid)
                    if self.score.lives > 0:
                        Clock.schedule_once(self.respawn_player, 3)
                    else:
                        Clock.schedule_once(self.game_over, 2)

        for particle in self.particles:
            particle.move()

    #callbacks
    def respawn_player(self, dt):
        """reset player position and set safe mode"""
        self.score.die()
        self.player.reset()
        self.player.color[3] = 0.5
        self.player.safe_mode = True
        Clock.schedule_once(self.player.remove_safe_mode, 3)

    def create_entity(self, entity, ent_list, *largs):
        if entity not in ent_list:
            ent_list.append(entity)
            self.add_widget(entity)

    def remove_entity(self, entity, ent_list, *largs):
        if entity in ent_list:
            ent_list.remove(entity)
            self.remove_widget(entity)

    def game_over(self, dt):
        """replace high score and initiate end screen"""
        self.game_mode = "end"
        if self.score.score > self.storage.get("high_score")["score"]:
            self.storage.put("high_score", score=self.score.score)
        self.end = EnsEnd(self.score.score, self.storage.get("high_score")["score"])
        self.remove_widget(self.score)
        self.add_widget(self.end)

class EnsApp(App):
    """application"""
    def on_pause(self):
        """makes sure game resumes on minimize"""
        return True

    def on_resume(self):
        pass

    def build(self):
        Window.clearcolor = (0.00, 0.00, 0.05, 1.00)
        game = EnsGame()
        game.remove_widget(game.player)
        game.remove_widget(game.score)
        game.start = EnsStart()
        game.add_widget(game.start, 0)
        Clock.schedule_interval(game.update, 1/60.0)
        return game

if __name__ == '__main__':
    APP = EnsApp()
    APP.run()


