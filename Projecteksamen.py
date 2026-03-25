import math
import arcade
import random

# --- KONSTANTER ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SHIP_SPEED_PIXELS = 100
SHIP_TURN_SPEED_DEGREES = 130

# SKUD & TIMERE
NORMAL_FIRE_RATE = 0.5
FAST_FIRE_RATE = 0.2
BULLET_SPEED = 20
STAR_SPAWN_RATE = 1.0  # 1 minut mellem stjerner

# POWER-UP & NOVA
NOVA_COOLDOWN = 15.0
POWER_UP_SPAWN_RATE = 10.0
FIRE_BOOST_DURATION = 5.0
INVINCIBLE_DURATION = 5.0

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        
        # Ressourcer
        try:
            self.background = arcade.load_texture("Resorces/c58d078a-856c-4aed-9ff9-0bf536e245f2.jpg")
            self.ship = arcade.Sprite("Resorces/Ship.png", scale=0.05)
        except:
            # Fallback hvis filer mangler
            self.background = None
            self.ship = arcade.SpriteSolidColor(30, 50, arcade.color.WHITE)

        self.ship.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        # Spil Status & Bane-logik
        self.level = 1
        self.stars_collected = 0
        self.lives = 3
        self.game_over = False
        self.victory = False
        
        # Sværhedsgrad variabler
        self.asteroid_speed = 5
        self.asteroid_spawn_rate = 0.5

        # Sprite Lister
        self.ship_sprite_list = arcade.SpriteList()
        self.ship_sprite_list.append(self.ship)
        self.bullet_list = arcade.SpriteList()
        self.asteroid_list = arcade.SpriteList()
        self.power_up_list = arcade.SpriteList()
        self.star_list = arcade.SpriteList()

        # Timere & Bevægelse
        self.held_keys = set()
        self.ship_direction = 0.0
        self.ship_turning = 0.0
        self.boost_timer = 3.0
        self.shoot_timer = 0.0
        self.asteroid_timer = 0.0
        self.nova_timer = 0.0
        self.star_spawn_timer = 0.0
        self.power_up_spawn_timer = 0.0
        self.fire_boost_timer = 0.0
        self.invincible_timer = 0.0

    def setup_level(self):
        """ Indstiller sværhedsgraden baseret på bane-nummer """
        self.stars_collected = 0
        self.star_spawn_timer = 0.0
        self.asteroid_list.clear()
        self.star_list.clear()
        
        if self.level == 1:
            self.asteroid_speed = 5
            self.asteroid_spawn_rate = 0.3
        elif self.level == 2:
            self.asteroid_speed = 7
            self.asteroid_spawn_rate = 0.2
        elif self.level == 3:
            self.asteroid_speed = 10
            self.asteroid_spawn_rate = 0.1

    def on_draw(self):
        self.clear()
        if self.background:
            arcade.draw_texture_rect(self.background, arcade.XYWH(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.star_list.draw()
        self.power_up_list.draw()
        self.asteroid_list.draw()
        self.bullet_list.draw()
        self.ship_sprite_list.draw()

        # UI Tekst
        arcade.draw_text(f"BANE: {self.level}   LIV: {self.lives}   STJERNER: {self.stars_collected}/3", 20, SCREEN_HEIGHT - 40, arcade.color.WHITE, 20)
        
        if self.fire_boost_timer > 0:
            arcade.draw_text("FAST FIRE!", 20, SCREEN_HEIGHT - 80, arcade.color.PURPLE, 20, bold=True)
        if self.invincible_timer > 0:
            arcade.draw_text("INVINCIBLE!", 20, SCREEN_HEIGHT - 110, arcade.color.GOLD, 20, bold=True)

        if self.game_over:
            arcade.draw_text("GAME OVER", SCREEN_WIDTH/2, SCREEN_HEIGHT/2, arcade.color.RED, 60, anchor_x="center")
        elif self.victory:
            arcade.draw_text("MISSION FULDFØRT!", SCREEN_WIDTH/2, SCREEN_HEIGHT/2, arcade.color.GOLD, 60, anchor_x="center")

        self.draw_bars()

    def draw_bars(self):
        # Boost Bar (Venstre)
        bx, by = SCREEN_WIDTH // 2 - 220, 50
        arcade.draw_rect_filled(arcade.XYWH(bx, by, 400, 20), arcade.color.GRAY)
        curr_boost = (max(0, self.boost_timer) / 3.0) * 400
        arcade.draw_rect_filled(arcade.XYWH(bx - (400 - curr_boost)/2, by, curr_boost, 20), arcade.color.CYAN)

        # Nova Bar (Højre)
        nx, ny = SCREEN_WIDTH // 2 + 220, 50
        arcade.draw_rect_filled(arcade.XYWH(nx, ny, 400, 20), arcade.color.GRAY)
        curr_nova = (min(self.nova_timer, NOVA_COOLDOWN) / NOVA_COOLDOWN) * 400
        n_color = arcade.color.GOLD if self.nova_timer >= NOVA_COOLDOWN else arcade.color.ORANGE
        arcade.draw_rect_filled(arcade.XYWH(nx - (400 - curr_nova)/2, ny, curr_nova, 20), n_color)

    def on_update(self, delta_time: float):
        if self.game_over or self.victory: return

        # 1. Timere & Power-ups
        self.nova_timer = min(NOVA_COOLDOWN, self.nova_timer + delta_time)
        self.fire_boost_timer -= delta_time
        self.invincible_timer -= delta_time
        self.ship.alpha = 150 if self.invincible_timer > 0 else 255

        # Spawning (Stjerner, Power-ups, Asteroider)
        self.handle_spawning(delta_time)

        # 2. Bevægelse og Skydning
        self.bullet_list.update()
        self.asteroid_list.update()
        
        current_rate = FAST_FIRE_RATE if self.fire_boost_timer > 0 else NORMAL_FIRE_RATE
        self.shoot_timer += delta_time
        if self.shoot_timer >= current_rate:
            self.shoot_bullet()
            self.shoot_timer = 0

        self.handle_movement(delta_time)

        # 3. Kollisioner
        self.check_collisions()

    def handle_spawning(self, delta_time):
        # Stjerner
        if len(self.star_list) + self.stars_collected < 3:
            self.star_spawn_timer += delta_time
            if self.star_spawn_timer >= STAR_SPAWN_RATE:
                star = arcade.SpriteCircle(20, arcade.color.GOLD)
                star.center_x, star.center_y = random.randint(100, SCREEN_WIDTH-100), random.randint(100, SCREEN_HEIGHT-100)
                self.star_list.append(star)
                self.star_spawn_timer = 0

        # Power-ups
        self.power_up_spawn_timer += delta_time
        if self.power_up_spawn_timer >= POWER_UP_SPAWN_RATE:
            self.spawn_power_up()
            self.power_up_spawn_timer = 0

        # Asteroider
        self.asteroid_timer += delta_time
        if self.asteroid_timer >= self.asteroid_spawn_rate:
            a = arcade.Sprite("Resorces/Astroid.png", scale=random.uniform(0.05, 0.3))
            a.center_x, a.center_y = random.randrange(SCREEN_WIDTH), SCREEN_HEIGHT + 50
            a.change_y = -self.asteroid_speed
            self.asteroid_list.append(a)
            self.asteroid_timer = 0

    def check_collisions(self):
        # Stjerner
        for s in arcade.check_for_collision_with_list(self.ship, self.star_list):
            s.remove_from_sprite_lists()
            self.stars_collected += 1
            if self.stars_collected >= 3:
                self.next_level()

        # Power-ups
        for p in arcade.check_for_collision_with_list(self.ship, self.power_up_list):
            if p.properties.get("type") == "fire": self.fire_boost_timer = FIRE_BOOST_DURATION
            else: self.invincible_timer = INVINCIBLE_DURATION
            p.remove_from_sprite_lists()

        # Asteroider (Skib)
        for a in arcade.check_for_collision_with_list(self.ship, self.asteroid_list):
            a.remove_from_sprite_lists()
            if self.invincible_timer <= 0:
                self.lives -= 1
                if self.lives <= 0: self.game_over = True

        # Asteroider (Skud)
        for b in self.bullet_list:
            hits = arcade.check_for_collision_with_list(b, self.asteroid_list)
            if hits:
                b.remove_from_sprite_lists()
                for h in hits: h.remove_from_sprite_lists()

    def next_level(self):
        if self.level < 3:
            self.level += 1
            self.setup_level()
        else:
            self.victory = True

    def spawn_power_up(self):
        t = random.choice(["fire", "shield"])
        orb = arcade.SpriteCircle(15, arcade.color.PURPLE if t=="fire" else arcade.color.WHITE)
        orb.properties["type"] = t
        orb.center_x, orb.center_y = random.randint(100, SCREEN_WIDTH-100), random.randint(100, SCREEN_HEIGHT-100)
        self.power_up_list.append(orb)

    def shoot_bullet(self, angle=None):
        angle = angle if angle is not None else self.ship.angle
        b = arcade.SpriteSolidColor(10, 40, arcade.color.YELLOW)
        b.center_x, b.center_y, b.angle = self.ship.center_x, self.ship.center_y, angle
        rad = math.radians(angle)
        b.change_x = math.sin(rad) * BULLET_SPEED
        b.change_y = math.cos(rad) * BULLET_SPEED
        self.bullet_list.append(b)

    def handle_movement(self, delta_time):
        # 1. Boost logik
        w_a_d = {arcade.key.W, arcade.key.A, arcade.key.D}.issubset(self.held_keys)
        boost = 3.0 if (w_a_d and self.boost_timer > 0) else 1.0
        
        if boost > 1.0: 
            self.boost_timer -= delta_time
        elif self.boost_timer < 3.0: 
            self.boost_timer += delta_time * 0.2

        # 2. Rotation
        self.ship.angle += (SHIP_TURN_SPEED_DEGREES * self.ship_turning * delta_time)

        # 3. Ny position med SCREEN BORDERS (Kanter)
        move_mag = self.ship_direction * SHIP_SPEED_PIXELS * delta_time * boost
        new_x = self.ship.center_x + math.sin(math.radians(self.ship.angle)) * move_mag
        new_y = self.ship.center_y + math.cos(math.radians(self.ship.angle)) * move_mag

        # Tjek grænser
        if new_x < 0: new_x = 0
        elif new_x > SCREEN_WIDTH: new_x = SCREEN_WIDTH
        if new_y < 0: new_y = 0
        elif new_y > SCREEN_HEIGHT: new_y = SCREEN_HEIGHT

        self.ship.center_x = new_x
        self.ship.center_y = new_y

    def on_key_press(self, symbol, modifiers):
        self.held_keys.add(symbol)
        if symbol == arcade.key.W: self.ship_direction += 4
        elif symbol == arcade.key.S: self.ship_direction -= 4
        elif symbol == arcade.key.A: self.ship_turning -= 3
        elif symbol == arcade.key.D: self.ship_turning += 3
        elif symbol == arcade.key.Q and self.nova_timer >= NOVA_COOLDOWN:
            for i in range(24): self.shoot_bullet((360/24)*i)
            self.nova_timer = 0

    def on_key_release(self, symbol, modifiers):
        if symbol in self.held_keys: self.held_keys.remove(symbol)
        if symbol == arcade.key.W: self.ship_direction -= 4
        elif symbol == arcade.key.S: self.ship_direction += 4
        elif symbol == arcade.key.A: self.ship_turning += 3
        elif symbol == arcade.key.D: self.ship_turning -= 3

if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Space Survival Adventure")
    view = GameView()
    view.setup_level()
    window.show_view(view)
    arcade.run()










