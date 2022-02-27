import arcade
import random
from noise import pnoise1
from PIL.Image import open as open_image

import game_ai

with open_image("sprites/background.png") as img:
    background_width, background_height = img.size

SCALE = 1
WINDOW_WIDTH, WINDOW_HEIGHT = background_width * SCALE, background_height * SCALE
TUBE_INTERVAL = WINDOW_WIDTH / 4


class GUI(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)

        self.started = False
        self.dead = False
        self.ai = False

        self.tick = 0
        self.jump_start = 0
        self.falling = 0

        self.score = 0
        self.delta_y = 0
        self.ground_height = 0

        self.total_tube_count = 5
        self.sound_offset = random.randint(0, 100)

        self.background = None
        self.player = arcade.SpriteList()
        self.tubes = arcade.SpriteList()
        self.ground = arcade.SpriteList()

    def sound_pattern(self):
        points = 5
        span = 0.1

        top = WINDOW_HEIGHT
        bottom = self.ground_height

        x = float(self.total_tube_count) * span / points - 0.5 * span
        y = pnoise1(x, octaves=10, persistence=100, lacunarity=2.0, repeat=1024, base=self.sound_offset) \
            * (top - bottom) / 2
        y = int(y + (top + bottom) / 2)

        self.total_tube_count += 1
        gap_size = 150 * SCALE

        return y + (WINDOW_HEIGHT - self.ground_height) / 2 + gap_size / 2, \
            y - (WINDOW_HEIGHT - self.ground_height) / 2 - gap_size / 2

    def setup(self):
        self.background = arcade.Sprite("sprites/background.png", SCALE)
        self.background.center_x = WINDOW_WIDTH / 2
        self.background.center_y = WINDOW_HEIGHT / 2

        for i in range(3):
            bird = arcade.Sprite(f"sprites/bird{i}.png", SCALE)
            bird.center_x = WINDOW_WIDTH / 4
            bird.center_y = WINDOW_HEIGHT / 2
            self.player.append(bird)

        for i in range(2):
            ground = arcade.Sprite("sprites/ground.png", SCALE)
            ground.center_x = (WINDOW_WIDTH / 2) - (ground.width * i)
            ground.center_y = ground.height - 200 * SCALE
            self.ground.append(ground)
        self.ground_height = self.ground[0].center_y + self.ground[0].height / 2

        for i in range(0, 10, 2):
            top_tube = arcade.Sprite("sprites/top_tube.png", SCALE)
            bottom_tube = arcade.Sprite("sprites/bottom_tube.png", SCALE)
            top_tube.center_x = bottom_tube.center_x = 2*WINDOW_WIDTH + TUBE_INTERVAL*i

            top_tube.center_y, bottom_tube.center_y = self.sound_pattern()

            self.tubes.append(top_tube)
            self.tubes.append(bottom_tube)

    def on_draw(self):
        arcade.start_render()
        self.background.draw()
        self.tubes.draw()
        self.ground.draw()

        if self.ai:
            arcade.draw_circle_filled(5, WINDOW_HEIGHT-5, 4, arcade.color.WINE)

        if self.started:
            for player in self.player:
                if self.delta_y > -10:
                    player.turn_left(15 - player.angle)
                elif player.angle <= -90:
                    pass
                elif self.delta_y <= -10:
                    player.turn_left(15 + 6 * (self.delta_y + 10) - player.angle)

            self.player[(self.tick // 5) % 3].draw()  # flap the wings
        else:
            self.player[1].draw()  # normal wings

    def update(self, delta_time):
        self.tick += 1
        speed = 2
        if self.dead:
            return

        elif self.falling:
            x = self.falling - self.tick
            self.delta_y = 0.8 * x

        elif not self.started:
            x = self.tick % 40
            if x < 20:
                self.delta_y = -0.08 * x + 0.8
            if x >= 20:
                self.delta_y = 0.08 * x - 2.4

        elif self.jump_start:
            x = self.tick - self.jump_start
            if x <= 100:
                self.delta_y = -0.8 * x + 11
            else:
                self.jump_start = 0

        for player in self.player:
            player.center_y += self.delta_y * SCALE

        if self.player[1].center_y <= self.ground_height + self.player[1].height / 2:
            self.game_over()

        if self.started:
            for i in range(0, 10, 2):
                self.tubes[i].center_x -= speed if not self.falling else 0
                self.tubes[i + 1].center_x -= speed if not self.falling else 0

                if self.player[1].center_x - 1 <= self.tubes[i].center_x <= self.player[1].center_x:
                    self.score += 1

                if self.tubes[i].center_x < 0 - self.tubes[i].width \
                        and self.tubes[i + 1].center_x < 0 - self.tubes[i + 1].width:
                    self.tubes[i].center_x = self.tubes[i - 2].center_x + 2 * TUBE_INTERVAL
                    self.tubes[i + 1].center_x = self.tubes[i - 1].center_x + 2 * TUBE_INTERVAL
                    self.tubes[i].center_y, self.tubes[i + 1].center_y = self.sound_pattern()

            if arcade.check_for_collision_with_list(self.player[1], self.tubes):
                self.falling = self.tick if not self.falling else self.falling

        for ground in self.ground:
            ground.center_x -= speed if not self.falling else 0
            if ground.center_x <= -1 * ground.width / 2:
                ground.center_x += WINDOW_WIDTH + ground.width

        if self.ai:
            tube_y = 0
            distance_to_tube = WINDOW_WIDTH
            for i in range(0, 10, 2):
                distance = (self.tubes[i].center_x + self.tubes[i].width / 2) - (self.player[1].center_x - self.player[1].width / 2)
                if 0 <= distance < distance_to_tube:
                    tube_y = self.tubes[i+1].center_y + self.tubes[i+1].height / 2
                    distance_to_tube = distance
            if game_ai.jump(self.player[1].center_y - self.player[1].height / 2, tube_y, self.ground_height):
                self.jump_start = self.tick

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.exit()
            exit()
        if key == arcade.key.SPACE:
            if self.dead:
                self.tick = 0
                self.dead = False
                self.score = 0

                for player in self.player:
                    player.center_y = WINDOW_HEIGHT / 2
                    player.turn_right(player.angle)
                for i in range(0, 10, 2):
                    self.tubes[i].center_x = self.tubes[i + 1].center_x = 2*WINDOW_WIDTH + TUBE_INTERVAL*i
            else:
                if not self.started:
                    self.started = True
                    self.jump_start = self.tick
                elif not self.ai:
                    self.jump_start = self.tick
        if key == arcade.key.A:
            self.ai = not self.ai

    def game_over(self):
        self.started = False
        self.dead = True

        self.falling = 0


def main():
    game = GUI(WINDOW_WIDTH, WINDOW_HEIGHT, "Flappy Bird")
    game.setup()

    arcade.run()


if __name__ == '__main__':
    main()
