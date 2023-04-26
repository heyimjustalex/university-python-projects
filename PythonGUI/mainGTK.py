import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk

from random import randrange


class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Snake")
        self.set_size_request(840, 840)

        menuBar = Gtk.MenuBar()
        menuBarPart = Gtk.Menu()
        infoButtonMenu = Gtk.MenuItem("Informacje")
        infoButtonMenu.set_submenu(menuBarPart)
        showInf = Gtk.MenuItem("Pokaż")
        showInf.connect("activate", self.informationPopupClick)
        menuBarPart.append(showInf)
        menuBar.append(infoButtonMenu)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        button = Gtk.Button.new_with_label("Start")
        button.connect("clicked", self.startGame)
        self.box.pack_start(menuBar, False, False, 0)
        self.box.pack_start(button, True, True, 0)

        provider = Gtk.CssProvider()
        provider.load_from_data(
            "button {background: #D1FFBD; color: black; border: 2px solid black;border-radius: 8px; font-size: 16px; margin:300px; } button:hover{background:#C0EEAC;}".encode()
        )

        context = button.get_style_context()
        context.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.add(self.box)

    def startGame(self, button):
        self.board = SnakeGame()
        self.board.connect("key_press_event", self.board.on_key_down)
        self.board.show_all()
        Gtk.main()

    def informationPopupClick(self, button):
        dialog = Gtk.MessageDialog(
            self, 0, Gtk.MessageType.INFO, title="Informacje o grze"
        )
        dialog.set_size_request(300, 200)
        dialog.format_secondary_text(
            "Gra Snake to prosta gra komputerowa, w której gracz kontroluje węża, \nktóry porusza się po planszy, zjada jedzenie i rośnie wraz z każdym \nzjedzonym kawałkiem. Celem gry jest zjedzenie jak największej ilości \njedzenia, aby wąż stał się coraz dłuższy. Jednocześnie gracz musi unikać \nzderzeń ze ścianami planszy oraz z własnym ogonem, który staje się coraz dłuższy w dłuższy w miarę jak wąż rośnie."
        )
        dialog.run()
        dialog.destroy()


class Square:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __eq__(self, second):
        if self.x == second.x and self.y == second.y:
            return True
        return False


class SnakeGame(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Snake")
        self.width = 840
        self.height = 840
        self.startX = self.width / 2
        self.startY = self.height / 2
        self.dx = 40
        self.dy = 40
        self.score = -1
        self.previousDirection = None
        self.set_size_request(840, 840)

        self.highscore = 0
        self.snake = []
        self.prevSnake = [Square(-200, -200)]

        self.currentDirection = None
        self.hasStarted = False
        self.food = None
        self.gameOver = False
        self.gameWon = False
        # self.maxScore = 5
        self.maxScore = int(self.width * self.width / self.dx / self.dx)
        self.snakeInit(self.snake, self.startX, self.startY)
        self.connect("destroy", Gtk.main_quit)

        self.game_area = Gtk.DrawingArea()
        self.game_area.connect("draw", self.draw)
        self.add(self.game_area)

        GLib.timeout_add(100, self.game_loop)

    def snakeInit(self, snakeCoordinatesArr, startX, startY):
        initSquare = Square(startX, startY)
        snakeCoordinatesArr.append(initSquare)
        return snakeCoordinatesArr

    def on_key_down(self, data, event):
        self.hasStarted = True
        if self.prevSnake[0] == self.snake[0]:
            return
        self.previousDirection = self.currentDirection

        if event.keyval == 65307:
            Gtk.main_quit()

        if event.keyval == 114:
            self.snake = []
            self.gameOver = False
            self.snakeInit(self.snake, self.startX, self.startY)
            self.score = 0
            self.gameWon = False

        if self.gameOver or self.gameWon:
            return
        # make snake not set wrong directions - from eft to right or up to down
        if event.keyval == 65361 and self.previousDirection != "RIGHT":
            self.currentDirection = "LEFT"

        elif event.keyval == 65363 and self.previousDirection != "LEFT":
            self.currentDirection = "RIGHT"

        elif event.keyval == 65364 and self.previousDirection != "UP":
            self.currentDirection = "DOWN"

        elif event.keyval == 65362 and self.previousDirection != "DOWN":
            self.currentDirection = "UP"

        self.allowDirectionChange = False
        if self.hasStarted:
            self.prevSnake[0] = self.snake[0]

    def drawFood(self, cr):
        if not self.gameOver or not self.gameWon:
            cr.set_source_rgb(0, 0, 255)

            if not self.food:
                x = randrange(20) * 40
                y = randrange(20) * 40

                new_food = Square(x, y)
                for i in self.snake:
                    if new_food.x == i.x - 20 and new_food.y == i.y - 20:
                        self.food = None
                        return

                self.food = new_food
                self.score += 1
            cr.rectangle(self.food.x, self.food.y, 40, 40)

            cr.fill()

    def moveSnake(self):
        if not self.gameOver or not self.gameWon:
            snake_len = len(self.snake)

            if self.currentDirection == "LEFT":
                self.snake = [
                    Square(self.snake[0].x - self.dx, self.snake[0].y)
                ] + self.snake[: snake_len - 1]

            elif self.currentDirection == "RIGHT":
                self.snake = [
                    Square(self.snake[0].x + self.dx, self.snake[0].y)
                ] + self.snake[: snake_len - 1]

            elif self.currentDirection == "UP":
                self.snake = [
                    Square(self.snake[0].x, self.snake[0].y - self.dy)
                ] + self.snake[: snake_len - 1]

            elif self.currentDirection == "DOWN":
                self.snake = [
                    Square(self.snake[0].x, self.snake[0].y + self.dy)
                ] + self.snake[: snake_len - 1]

    # check if collison
    def snakeStatusChecker(self):
        if not self.food:
            return

        if (
            self.snake[0].x > self.width
            or self.snake[0].x < 0
            or self.snake[0].y > self.height
            or self.snake[0].y < 0
        ) and not self.gameWon:
            self.gameOver = True

        elif (
            self.snake[0].x - 20 == self.food.x and self.snake[0].y - 20 == self.food.y
        ):
            self.snake.append(Square(self.food.x + 20, self.food.y - 20))
            self.food = False

        elif self.snake[0] in self.snake[1:]:
            self.gameOver = True

        elif self.score >= self.maxScore:
            self.gameWon = True

    def printScore(self, cr):
        cr.set_font_size(14)
        cr.set_source_rgb(0, 0, 0)
        x = 4
        y = 17
        cr.move_to(x, y)
        cr.show_text("Wynik: " + str(self.score))

    def printGameOver(self, cr):
        cr.set_font_size(14)
        cr.set_source_rgb(0, 0, 0)
        cr.move_to(self.width // 2 - 100, self.height // 2)
        cr.show_text("Koniec Gry - R aby zresetować")

    def printGameWon(self, cr):
        cr.set_font_size(14)
        cr.set_source_rgb(0, 0, 0)
        cr.move_to(self.width // 2 - 80, self.height // 2)
        cr.show_text("Wygrana - koniec gry")

    def draw(self, widget, cr):
        self.moveSnake()
        self.drawSnake(cr)
        self.drawFood(cr)
        self.snakeStatusChecker()
        self.printScore(cr)
        if self.gameOver:
            self.printGameOver(cr)
        if self.gameWon:
            self.printGameWon(cr)

    def drawSnake(self, cr):
        if self.gameOver or self.gameWon:
            return

        for i, square in enumerate(self.snake):
            if i > 0:
                cr.set_source_rgb(255, 0, 0)
                cr.rectangle(
                    square.x - self.dx / 2 + 1,
                    square.y - self.dy / 2 + 1,
                    self.width / 20 - 2,
                    self.height / 20 - 2,
                )

                cr.fill_preserve()
                cr.set_source_rgb(0, 0, 0)
                cr.set_line_width(1)
                cr.stroke()

            else:
                cr.set_source_rgb(0, 0, 0)
                cr.rectangle(
                    square.x - self.dx / 2,
                    square.y - self.dy / 2,
                    self.width / 20,
                    self.height / 20,
                )
                cr.fill()

        cr.stroke()

    def game_loop(self):
        self.game_area.queue_draw()
        return True


if __name__ == "__main__":
    win = MainWindow()

    win.show_all()
    Gtk.main()
