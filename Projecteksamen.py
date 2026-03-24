import math
import arcade
from arcade.types import Point
from arcade.math import (
    get_angle_radians,
    rotate_point,
    get_angle_degrees,
)

# --- CONSTANTS ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SHIP_SPEED_PIXELS = 200
SHIP_TURN_SPEED_DEGREES = 180

# --- WINDOW ---
class RotatingSprite(arcade.Sprite):
    def rotate_around_point(self, point: Point, degrees: float):
        self.angle += degrees
        self.position = rotate_point(
            self.center_x, self.center_y,
            point[0], point[1], degrees
        )

    def face_point(self, point: Point):
        self.angle = get_angle_degrees(*self.position, *point)


class GameView(arcade.View):

    def __init__(self):
        super().__init__()

        self.window.background_color = arcade.csscolor.SEA_GREEN

        # --- SHIP BODY ---
        self.ship = arcade.Sprite("Resorces/Ship.png", scale=0.5)
        self.ship.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        # --- MOVEMENT ---
        self.ship_direction = 0.0
        self.ship_turning = 0.0
        self.mouse_pos = (0, 0)

        # --- SPRITES ---
        self.ship_sprite_list = arcade.SpriteList()
        self.ship_sprite_list.append(self.ship)

        # --- TEXT ---
        self.control_text = arcade.Text(
            "WASD to move ship, Mouse to aim",
            SCREEN_WIDTH // 2, 15,
            anchor_x='center'
        )

    def on_draw(self):
        self.clear()
        self.ship_sprite_list.draw()
        self.control_text.draw()

    def on_update(self, delta_time: float):
        self.move_ship(delta_time)

    def move_ship(self, delta_time):

        # --- ROTATE SHIP ---
        self.ship.angle += (
            SHIP_TURN_SPEED_DEGREES * self.ship_turning * delta_time
        )

        # --- MOVE SHIP ---
        move_magnitude = self.ship_direction * SHIP_SPEED_PIXELS * delta_time
        x_dir = math.sin(math.radians(self.ship.angle)) * move_magnitude
        y_dir = math.cos(math.radians(self.ship.angle)) * move_magnitude

        self.ship.center_x += x_dir
        self.ship.center_y += y_dir

        

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.W:
            self.ship_direction += 1
        elif symbol == arcade.key.S:
            self.ship_direction -= 1
        elif symbol == arcade.key.A:
            self.ship_turning -= 1
        elif symbol == arcade.key.D:
            self.ship_turning += 1

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol == arcade.key.W:
            self.ship_direction -= 1
        elif symbol == arcade.key.S:
            self.ship_direction += 1
        elif symbol == arcade.key.A:
            self.ship_turning += 1
        elif symbol == arcade.key.D:
            self.ship_turning -= 1

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.mouse_pos = (x, y)


# --- RUN GAME ---
window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Projecteksamen")
view = GameView()
window.show_view(view)
arcade.run()

