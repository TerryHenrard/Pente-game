import json
import re
import socket

import pygame
import pygame_gui
import select

# Configuration du serveur
HOST = '127.0.0.1'  # Adresse IP du serveur (localhost)
PORT = 55555  # Port du serveur
BUFFER_SIZE = 2048

# Initialisation de PyGame et du module audio
pygame.init()
pygame.mixer.init()

# Configuration de PyGame
# Configuration de l'écran
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 900
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Plateau de Pente")

# Dimensions du plateau
GRID_ROWS = 19
GRID_COLS = 19
CELL_SIZE = 45
PIECE_SIZE = 40

# Images des pions
PION_IMAGE_PLAYER1 = (
    pygame.transform.scale(
        pygame.image.load("assets/images/one_ring_pion.png"),
        (PIECE_SIZE, PIECE_SIZE)
    )
)
PION_IMAGE_PLAYER2 = (
    pygame.transform.scale(
        pygame.image.load(
            "assets/images/eye_of_sauron_pion.png"),
        (PIECE_SIZE, PIECE_SIZE)
    )
)

# Tolérance pour cliquer autour des intersections (en pixels)
TOLERANCE = 5

# Dimensions de la grille
GRID_SIZE = (GRID_COLS - 1) * CELL_SIZE

# Calculer les marges pour centrer la grille
MARGIN_X = (SCREEN_WIDTH - GRID_SIZE) // 2
MARGIN_Y = (SCREEN_HEIGHT - GRID_SIZE) // 2 + 20

# Buttons dimensions
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_LEFT_RIGHT_MARGIN = 10
BUTTON_BETWEEN_MARGIN = 10
BUTTON_BOTTOM_MARGIN = 60
BUTTON_GAME_WIDTH = SCREEN_WIDTH // 2 + 50
BUTTON_GAME_HEIGHT = 45
BUTTON_GAME_MARGIN = 10

# Labels dimensions
LABEL_WIDTH = 200
LABEL_HEIGHT = 20
LABEL_MARGIN_BOTTOM = 10
LABEL_LEFT_MARGIN = 5

# Couleurs
BACKGROUND_COLOR = (193, 176, 150)
LINE_COLOR = (0, 0, 0)
RED_PION_COLOR = (255, 0, 0, 150)
YELLOW_PION_COLOR = (255, 215, 0, 150)

# Chemins des fichiers theme
THEME_PATH = "assets/styles/theme.json"

# Chemin du fichier audio
BACKGROUND_MUSIC_PATH = "assets/audio/background-music.mp3"
YOU_SHALL_NOT_PASS_PATH = "assets/audio/login-error.wav"
LOBBY_ENTRY = "assets/audio/lobby-entry.mp3"

# Chemin des fichiers image
GANDALF_IMAGE_PATH = "assets/images/gandalf.png"

# Status de la réponse (JSON)
RESPONSE_SUCCESS_STATUS = 1
RESPONSE_FAIL_STATUS = 0

# Regex's
REGEX_CAPTURE_GAME_NAME = r"Name:\s*(.*?)\s*Status:"

# Statistiques des joueurs
score = 0
wins = 0
losses = 0
games_played = 0

# Afficher le plateau de jeu
is_grid_visible = False
board = []

# Liste des pions
pions = []


def rebuild_board(received_board):
    copy_board = []
    for y in range(0, len(received_board)):
        row = []
        for x in range(0, len(received_board[y])):
            pion_type = received_board[x][y]
            row.append(pion_type)
            pions.append((x, y, pion_type))
        board.append(row)

    return copy_board


def play_music(music_path, volume=1, fade_ms=0, is_loop=False):
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=1 if is_loop else 0, fade_ms=fade_ms)
    except pygame.error as e:
        print(f"Erreur lors de la lecture de la musique : {e}")


def stop_music(fade_ms=2000):
    try:
        pygame.mixer.music.fadeout(fade_ms)
    except pygame.error as e:
        print(f"Erreur lors de l'arrêt de l'audio : {e}")


def pause_music():
    pygame.mixer.music.pause()


def unpause_music():
    try:
        print("Reprise de la musique.")
        pygame.mixer.music.unpause()
    except pygame.error as e:
        print(f"Erreur lors de la reprise de l'audio : {e}")


def play_audio(sound_path, volume=0.1):
    try:
        if not pygame.mixer.get_busy():  # Vérifier si un son est déjà en cours
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(volume)
            sound.play()
    except pygame.error as e:
        print(f"Erreur lors de la lecture de l'audio : {e}")


def add_pion_to_pions_list(x, y, image):
    print("tentative d'ajout")
    # Vérifie si les indices sont valides
    if 0 <= x < GRID_COLS and 0 <= y < GRID_ROWS:
        print(f"Image ajoutée au tableau à : Ligne {y + 1}, Colonne {x + 1}")
        pions.append((x, y, image))
    else:
        print("Clic en dehors de la grille.")


def draw_pions_list():
    for pion in pions:
        # Calcul de la position en pixels de l'image
        img_x = (MARGIN_X + (pion[0] * CELL_SIZE) - (PIECE_SIZE // 2))
        img_y = (MARGIN_Y + (pion[1] * CELL_SIZE) - (PIECE_SIZE // 2))

        pion_image = None
        if pion[2] == 'x':
            pion_image = PION_IMAGE_PLAYER1
        elif pion[2] == 'o':
            pion_image = PION_IMAGE_PLAYER2

        if pion_image is not None:
            SCREEN.blit(pion_image, (img_x, img_y))


# Fonction pour dessiner la grille et les points "hoshi"
def draw_grid(surface):
    # Dessiner les lignes verticales
    for x in range(GRID_COLS):
        width = 2 if x == 9 else 1
        pygame.draw.line(
            surface,
            LINE_COLOR,
            (MARGIN_X + x * CELL_SIZE, MARGIN_Y),
            (MARGIN_X + x * CELL_SIZE, MARGIN_Y + GRID_SIZE),
            width
        )

    # Dessiner les lignes horizontales
    for y in range(GRID_ROWS):
        width = 2 if y == 9 else 1
        pygame.draw.line(
            surface,
            LINE_COLOR,
            (MARGIN_X, MARGIN_Y + y * CELL_SIZE),
            (MARGIN_X + GRID_SIZE, MARGIN_Y + y * CELL_SIZE),
            width
        )

    # Ajouter les points "hoshi"
    hoshi_points = [
        (3, 3), (3, 9), (3, 15),
        (9, 3), (9, 9), (9, 15),
        (15, 3), (15, 9), (15, 15)
    ]
    for px, py in hoshi_points:
        square_size = 8  # Taille du carré
        pygame.draw.rect(
            surface,
            LINE_COLOR,
            pygame.Rect(
                MARGIN_X + px * CELL_SIZE - square_size // 2 + 1,
                MARGIN_Y + py * CELL_SIZE - square_size // 2 + 0.5,
                square_size,
                square_size
            )
        )


def send_json(user_socket, json_message):
    try:
        print(f"Envoi du message :")
        print(json.dumps(json.loads(json_message), indent=4))
        user_socket.sendall(json_message.encode())
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")


def receive_json(s):
    try:
        data = s.recv(BUFFER_SIZE).decode()
        if not data:
            return None
        return json.loads(data)
    except json.JSONDecodeError as e:
        print(f"Erreur de décodage JSOn : {e}")
        return None
    except Exception as e:
        print(f"Erreur lors de la réception : {e}")
        return None


def connect_to_server(host, port):
    user_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    user_socket.connect((host, port))
    user_socket.setblocking(False)
    print("Connecté au serveur.")

    return user_socket


def create_ready_to_play_message():
    try:
        return json.dumps({
            "type": "ready_to_play"
        })
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def create_auth_json(username, password):
    try:
        return json.dumps({
            "type": "auth",
            "username": username,
            "password": password
        })
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def create_new_account_json(username, password, conf_password):
    try:
        return json.dumps({
            "type": "new_account",
            "username": username,
            "password": password,
            "conf_password": conf_password
        })
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def create_deconnection_json():
    try:
        return json.dumps({
            "type": "disconnect"
        })
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def create_get_lobby_json():
    try:
        return json.dumps({
            "type": "get_lobby"
        })
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def create_join_game_json(game_name):
    try:
        return json.dumps({
            "type": "join_game",
            "game_name": game_name
        })
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def create_new_game_json(game_name):
    try:
        return json.dumps({
            "type": "create_game",
            "game_name": game_name
        })
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def init_pygame():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Jeu de Pente")
    return screen


def create_background():
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background.fill(BACKGROUND_COLOR)
    return background


# Fonction pour créer le gestionnaire GUI et les éléments
def create_gui_elements_lobby_page(manager):
    return {
        "title_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 - 300,
                    SCREEN_HEIGHT // 2 - 400
                ),
                (600, 60)
            ),
            text="Menu principal",
            manager=manager,
            object_id='#lobby_title_label'
        ),
        "score_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (LABEL_LEFT_MARGIN, BUTTON_BETWEEN_MARGIN),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="score_label",
            manager=manager,
            object_id="#score_label"
        ),
        "wins_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    LABEL_LEFT_MARGIN,
                    LABEL_HEIGHT + ((3 / 2) * BUTTON_BETWEEN_MARGIN)
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="wins_label",
            manager=manager,
            object_id="#wins_label"
        ),
        "losses_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    LABEL_LEFT_MARGIN,
                    2 * (LABEL_HEIGHT + BUTTON_BETWEEN_MARGIN)
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="losses_label",
            manager=manager,
            object_id="#losses_label"
        ),
        "games_played_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    LABEL_LEFT_MARGIN,
                    3 * (LABEL_HEIGHT + BUTTON_BETWEEN_MARGIN) - (BUTTON_BETWEEN_MARGIN // 2)
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="games_played_label",
            manager=manager,
            object_id="#games_played_label"
        ),
        "create_game_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 - BUTTON_WIDTH,
                    SCREEN_HEIGHT - BUTTON_BOTTOM_MARGIN
                ),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Créer une partie",
            manager=manager
        ),
        "disconnect_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 + BUTTON_LEFT_RIGHT_MARGIN,
                    SCREEN_HEIGHT - BUTTON_BOTTOM_MARGIN
                ),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Se déconnecter",
            manager=manager
        ),
        "error_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 120),
                (400, 30)
            ),
            text="",
            manager=manager,
            object_id="#error_label"
        )
    }


def create_gui_elements_create_game_page(manager):
    return {
        "title_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 300),
                (600, 60)
            ),
            text="Créer une partie",
            manager=manager,
            object_id='#new_game_title_label'
        ),
        "game_name_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 - (BUTTON_WIDTH // 2),
                    SCREEN_HEIGHT // 2 - 115
                ),
                (200, 30)
            ),
            text="Nom de la partie",
            manager=manager,
            object_id="#game_name_label"
        ),
        "game_name_entry": pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 - (BUTTON_WIDTH // 2),
                    SCREEN_HEIGHT // 2 - 85
                ),
                (200, 30)
            ),
            manager=manager,
            object_id="#game_name_entry"
        ),
        "create_new_game_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 - (BUTTON_WIDTH // 2),
                    SCREEN_HEIGHT // 2 + 25
                ),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Créer",
            manager=manager
        ),
        "back_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 - (BUTTON_WIDTH // 2),
                    SCREEN_HEIGHT // 2 + 85
                ),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Retour",
            manager=manager
        ),
        "error_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 155),
                (300, 30)
            ),
            text="",
            manager=manager,
            object_id="#error_label"
        )
    }


def create_gui_elements_login_page(manager):
    return {
        "title_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 300),
                (600, 60)
            ),
            text="Se connecter",
            manager=manager,
            object_id='#login_title_label'
        ),
        "username_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 115),
                (200, 30)
            ),
            text="Nom d'utilisateur",
            manager=manager,
            object_id="#username_label"
        ),
        "username_entry": pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 85),
                (200, 30)
            ),
            manager=manager,
            object_id="#username_login_entry"
        ),
        "password_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 55),
                (200, 30)
            ),
            text="Mot de passe",
            manager=manager,
            object_id="#password_label"
        ),
        "password_entry": pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 25),
                (200, 30)
            ),
            manager=manager,
            object_id="#password_login_entry"
        ),
        "login_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 25),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Se connecter",
            manager=manager
        ),
        "create_account_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 85),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Créer un compte",
            manager=manager
        ),
        "error_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 155),
                (300, 30)
            ),
            text="",
            manager=manager,
            object_id="#error_label"
        )
    }


def create_gui_elements_new_account_page(manager):
    return {
        "title_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 300),
                (600, 60)
            ),
            text="S'inscrire",
            manager=manager,
            object_id='#new_account_title_label'
        ),
        "username_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 115),
                (200, 30)
            ),
            text="Nom d'utilisateur",
            manager=manager,
            object_id="#username_label"
        ),
        "username_entry": pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 85),
                (200, 30)
            ),
            manager=manager,
            object_id="#username_create_account_entry"
        ),
        "password_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 55),
                (200, 30)
            ),
            text="Mot de passe",
            manager=manager,
            object_id="#password_label"
        ),
        "password_entry": pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 25),
                (200, 30)
            ),
            manager=manager,
            object_id="#password_create_account_entry"
        ),
        "conf_password_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 5),
                (200, 30)
            ),
            text="Confirmez le mot de passe",
            manager=manager,
            object_id="#conf_password_label"
        ),
        "conf_password_entry": pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 35),
                (200, 30)
            ),
            manager=manager,
            object_id="#conf_password_create_account_entry"
        ),
        "create_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 75),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Créer",
            manager=manager
        ),
        "back_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 135),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Retour",
            manager=manager
        ),
        "error_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 195),
                (400, 30)
            ),
            text="",
            manager=manager,
            object_id="#error_label"
        )
    }


def create_gui_elements_game_page(manager):
    return {
        "title_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 300, 0),
                (600, 60)
            ),
            text="",
            manager=manager,
            object_id='#new_join_game_title_label'
        ),
        "error_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (10, 10),
                (400, 30)
            ),
            text="",
            manager=manager,
            object_id="#error_label_on_game_page"
        )
    }


def print_board(board_param):
    print("   " + " ".join(f"{x + 1:2}" for x in range(len(board_param[0]))))

    for y, row in enumerate(board_param):
        # Afficher le numéro de ligne suivi de la ligne elle-même
        print(f"{y + 1:2} " + " ".join(row))


def handle_server_response(manager, user_socket, current_page_elements, current_event_handler):
    """
    Vérifie et traite la réponse du serveur de manière non bloquante.

    Args :
        s socket: Socket connecté au serveur.
    Returns :
        bool : True si la connexion reste active, False en cas d'erreur.
    """
    try:
        # Utiliser select pour vérifier si des données sont disponibles sans bloquer
        ready_to_read, _, _ = select.select([user_socket], [], [], 0.001)

        # Vérifier s'il y a des données à lire
        if user_socket not in ready_to_read:
            return True, current_page_elements, current_event_handler

        # Recevoir et décoder les données
        response_json = receive_json(user_socket)
        if not response_json:
            print("Aucune donnée reçue.")
            return False, None, None

        # Afficher la réponse de manière lisible
        print("Réponse du serveur :")
        if response_json.get("type") == "alert_start_game":
            print(f"type\": {response_json.get("type")}")
            print(f"status\": {response_json.get("status")}")
            print_board(response_json.get("board"))
        else:
            print(json.dumps(response_json, indent=4))

        response_type = response_json.get("type")
        # Traiter la réponse en fonction du type de message
        if (
                response_type == "auth_response" or
                response_type == "new_account_response"
        ):
            return handle_auth_response(
                response_json,
                current_page_elements,
                manager,
                user_socket
            )
        elif response_type == "disconnect_ack":
            return handle_disconnect_ack_response(
                response_json,
                current_page_elements,
                manager
            )
        elif response_type == "get_lobby_response":
            return handle_get_lobby_response(
                response_json,
                current_page_elements,
                manager
            )
        elif response_type == "create_game_response":
            return handle_create_game_response(
                response_json,
                current_page_elements,
                manager
            )
        elif response_type == "join_game_response":
            return handle_join_game_response(
                response_json,
                current_page_elements,
                manager,
                user_socket
            )
        elif response_type == "alert_start_game":
            return handle_alert_start_game(
                response_json,
                current_page_elements,
                manager
            )

        return True, current_page_elements, current_event_handler

    except BlockingIOError:
        # Gérer spécifiquement les erreurs de socket non bloquant
        print("Socket temporairement indisponible. Nouvelle tentative...")
        return True, current_page_elements, current_event_handler

    except Exception as e:
        # Capture des erreurs inattendues
        print(f"Erreur de communication : {e}")
        return False, None, None


def add_padding(text, total_length=20, align="left", padding_char=" "):
    """
    Ajuste le texte pour qu'il ait exactement total_length caractères.

    :param text: La chaîne à ajuster.
    :param total_length: La longueur totale désirée.
    :param align: L'alignement du texte ("left", "right", "center").
    :param padding_char: Le caractère utilisé pour le padding.
    :return: La chaîne ajustée ou tronquée.
    """
    text = str(text).strip()  # Supprime les espaces inutiles
    if len(text) > total_length:
        return text[:total_length]  # Tronque si trop long
    elif align == "left":
        return text.ljust(total_length, padding_char)
    elif align == "right":
        return text.rjust(total_length, padding_char)
    elif align == "center":
        return text.center(total_length, padding_char)
    else:
        raise ValueError("align doit être 'left', 'right' ou 'center'")


def create_gui_join_game_button_element(game_json, manager, index):
    game_id = game_json.get("id", None)
    game_name = game_json.get("name", None)
    game_players = game_json.get("players", None)
    game_status = game_json.get("status", None)  # waiting 0 / ongoing 1

    if None in [game_id, game_name, game_players, game_status]:
        return None

    button_text = (
            add_padding(f"N°{index + 1}", total_length=7) +
            add_padding(f"Name: {game_name}", total_length=30) +
            add_padding(f"Status: {'waiting' if game_status == 0 else 'ongoing'}") +
            add_padding(f"Players: {', '.join(game_players)}")
    )

    return pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(
            (
                SCREEN_WIDTH // 2 - (BUTTON_GAME_WIDTH // 2),
                (100 + (BUTTON_GAME_HEIGHT * index) + 10)
            ),
            (BUTTON_GAME_WIDTH, BUTTON_GAME_HEIGHT)
        ),
        text=button_text,
        manager=manager,
        object_id=f"#button_game_{game_id}"
    )


def return_to_lobby_page_with_delay(current_page_elements, manager, ms_delay=2000):
    pygame.time.delay(ms_delay)
    clear_page(current_page_elements)
    lobby_page_elements = create_gui_elements_lobby_page(manager)
    display_player_stats(lobby_page_elements)
    return True, lobby_page_elements, handle_events_on_lobby_page


def handle_alert_start_game(response_json, current_page_elements, manager):
    global is_grid_visible, board

    response_status = response_json.get("status", None)

    if (
            response_status is None or
            not response_status == RESPONSE_SUCCESS_STATUS
    ):
        return return_to_lobby_page_with_delay(current_page_elements, manager)

    response_board = response_json.get("board", None)
    if response_board is None:
        return return_to_lobby_page_with_delay(current_page_elements, manager)

    board = rebuild_board(response_board)
    is_grid_visible = True

    return True, current_page_elements, handle_events_on_game_page


def handle_join_game_response(response_json, current_page_elements, manager, user_socket):
    response_status = response_json.get("status", None)

    if (
            response_status is None or
            not response_status == RESPONSE_SUCCESS_STATUS
    ):
        current_page_elements["error_label"].set_text("Partie complète ou impossible à rejoindre.")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    clear_page(current_page_elements)
    game_page_elements = create_gui_elements_game_page(manager)

    send_json(user_socket, create_ready_to_play_message())

    return True, game_page_elements, handle_events_on_game_page


def handle_create_game_response(response_json, current_page_elements, manager):
    global is_grid_visible

    response_status = response_json.get("status", None)

    if (
            response_status is None or
            not response_status == RESPONSE_SUCCESS_STATUS
    ):
        current_page_elements["error_label"].set_text("Une partie contenant ce nom existe déjà.")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    clear_page(current_page_elements)
    game_page_elements = create_gui_elements_game_page(manager)
    game_page_elements["title_label"].set_text("En attente d'un autre joueur...")

    is_grid_visible = True

    return True, game_page_elements, handle_events_on_game_page


def handle_get_lobby_response(response_json, current_page_elements, manager):
    response_status = response_json.get("status", None)

    if response_status is None or not response_status == RESPONSE_SUCCESS_STATUS:
        current_page_elements["error_label"].set_text("Erreur lors de la récupération des parties.")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    game_list = response_json.get("games", [])
    if not game_list:
        current_page_elements["error_label"].set_text("Aucune partie disponible.")
        return True, current_page_elements, handle_events_on_lobby_page

    # Supprimer l'ancienne liste de boutons si elle existe
    if "game_buttons" not in current_page_elements:
        current_page_elements["game_buttons"] = []
        clear_page(current_page_elements)
        current_page_elements = create_gui_elements_lobby_page(manager)
        display_player_stats(current_page_elements)

    # Ajouter les nouveaux boutons dans un tableau
    buttons = []
    for index, game_json in enumerate(game_list):
        button = create_gui_join_game_button_element(game_json, manager, index)
        if button:
            buttons.append(button)

    # Stocker le tableau des boutons dans current_page_elements
    buttons.reverse()
    current_page_elements["game_buttons"] = buttons

    return True, current_page_elements, handle_events_on_lobby_page


def handle_disconnect_ack_response(response_json, current_page_elements, manager):
    response_status = response_json.get("status", None)

    if response_status is None or not response_status == RESPONSE_SUCCESS_STATUS:
        current_page_elements["error_label"].set_text("Déconnexion échouée !")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    print(current_page_elements)
    clear_page(current_page_elements)
    login_page_elements = create_gui_elements_login_page(manager)

    return True, login_page_elements, handle_events_on_login_page


def display_player_stats(next_page_elements):
    next_page_elements["score_label"].set_text(f"Score: {score}")
    next_page_elements["wins_label"].set_text(f"Victoires: {wins}")
    next_page_elements["losses_label"].set_text(f"Défaites: {losses}")
    next_page_elements["games_played_label"].set_text(f"Parties jouées: {games_played}")


def handle_auth_response(response_json, current_page_elements, manager, user_socket):
    global score, wins, losses, games_played

    response_status = response_json.get("status", None)

    if response_status is None or not response_status == RESPONSE_SUCCESS_STATUS:
        current_page_elements["error_label"].set_text("Mot de passe incorrect !")
        # play_audio(YOU_SHALL_NOT_PASS_PATH)
        return response_status is not None, current_page_elements, handle_events_on_login_page

    clear_page(current_page_elements)
    lobby_page_elements = create_gui_elements_lobby_page(manager)

    # Afficher les informations du JSON
    player_stats = response_json.get("player_stats", {})
    score = player_stats.get("score", 0)
    wins = player_stats.get("wins", 0)
    losses = player_stats.get("losses", 0)
    games_played = player_stats.get("games_played", 0)
    display_player_stats(lobby_page_elements)

    # play_audio(LOBBY_ENTRY)

    send_json(user_socket, create_get_lobby_json())

    return True, lobby_page_elements, handle_events_on_lobby_page


def handle_login_event(login_page_elements, user_socket):
    username = login_page_elements["username_entry"].get_text()
    password = login_page_elements["password_entry"].get_text()

    if not username or not password:
        print("Nom d'utilisateur ou mot de passe vide !")
        login_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe vide !")
        # play_audio(YOU_SHALL_NOT_PASS_PATH)
        return

    print(f"Tentative de connexion : {username}, {password}")
    json_authencation_message = create_auth_json(username, password)

    if not json_authencation_message:
        print("Erreur lors de la création du message.")
        return

    send_json(user_socket, json_authencation_message)


def handle_create_new_account_event(new_account_page_elements, user_socket):
    username = new_account_page_elements["username_entry"].get_text()
    password = new_account_page_elements["password_entry"].get_text()
    conf_password = new_account_page_elements["conf_password_entry"].get_text()

    if not username or not password:
        new_account_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe vide !")
        # play_audio(YOU_SHALL_NOT_PASS_PATH)
        return

    if len(password) < 12:
        new_account_page_elements["error_label"].set_text("Le mot de passe doit contenir au moins 12 caractères.")
        # play_audio(YOU_SHALL_NOT_PASS_PATH)
        return

    if password != conf_password:
        new_account_page_elements["error_label"].set_text("Les mots de passe ne correspondent pas.")
        # play_audio(YOU_SHALL_NOT_PASS_PATH)
        return

    print(f"Tentative de création de compte : {username}, {password}")
    json_new_account_message = create_new_account_json(username, password, conf_password)

    if not json_new_account_message:
        print("Erreur lors de la création du message.")
        return

    send_json(user_socket, json_new_account_message)


def handle_create_new_game_event(new_game_page_elements, user_socket):
    game_name = new_game_page_elements["game_name_entry"].get_text()

    if not game_name:
        new_game_page_elements["error_label"].set_text("Veuillez donner un nom à la partie")
        return

    if len(game_name) >= 20:
        new_game_page_elements["error_label"].set_text("Maximum 20 caractères")
        return

    print(f"Tentative de création de la partie : {game_name}")
    json_new_game_message = create_new_game_json(game_name)
    if not json_new_game_message:
        print("Erreur lors de la création de la partie")
        return

    send_json(user_socket, json_new_game_message)


def handle_events_on_create_new_game_page(manager, new_game_page_elements, user_socket):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, None, None

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == new_game_page_elements["create_new_game_button"]:
                print("Création de la partie")
                handle_create_new_game_event(new_game_page_elements, user_socket)

            elif event.ui_element == new_game_page_elements["back_button"]:
                print("Retour au lobby")
                send_json(user_socket, create_get_lobby_json())

        manager.process_events(event)
    return True, new_game_page_elements, handle_events_on_create_new_game_page


def get_grid_coordinates(x, y):
    # Ajustement avec les décalages
    adjusted_x = x - MARGIN_X
    adjusted_y = y - MARGIN_Y

    # Vérifie si le clic est dans la zone étendue avec tolérance
    if not (
            -TOLERANCE <= adjusted_x <= GRID_SIZE + TOLERANCE and
            -TOLERANCE <= adjusted_y <= GRID_SIZE + TOLERANCE
    ):
        return -1, -1

    # Calcul des indices de la grille
    col = round(adjusted_x / CELL_SIZE)
    row = round(adjusted_y / CELL_SIZE)

    # Vérifie si les indices sont dans les limites de la grille
    if not (0 <= col < GRID_COLS and 0 <= row < GRID_ROWS):
        return -1, -1

    return col, row


i = 0


def handle_events_on_game_page(manager, page_game_elements, user_socket):
    global i
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, None, None

        elif event.type == pygame.MOUSEBUTTONDOWN:
            col, row = get_grid_coordinates(*event.pos)

            if (col, row) == (-1, -1):
                print("Clic en dehors de la grille.")
                page_game_elements["error_label"].set_text("Clic en dehors de la grille.")
                return True, page_game_elements, handle_events_on_game_page

            print("Placement du pion")
            i += 1
            add_pion_to_pions_list(col, row, PION_IMAGE_PLAYER1 if i % 2 == 0 else PION_IMAGE_PLAYER2)

        manager.process_events(event)

    return True, page_game_elements, handle_events_on_game_page


def handle_events_on_lobby_page(manager, lobby_page_elements, user_socket):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, None, None

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == lobby_page_elements["create_game_button"]:
                print("Création d'une partie.")
                clear_page(lobby_page_elements)
                create_new_game_elements = create_gui_elements_create_game_page(manager)
                return True, create_new_game_elements, handle_events_on_create_new_game_page

            # FIXED : vérification de 'game_buttons' avant d'y accéder
            elif (
                    "game_buttons" in lobby_page_elements and
                    event.ui_element in lobby_page_elements["game_buttons"]
            ):
                clicked_button_index = lobby_page_elements["game_buttons"].index(event.ui_element)
                button_text = lobby_page_elements["game_buttons"][clicked_button_index].text
                match = re.search(REGEX_CAPTURE_GAME_NAME, button_text)
                send_json(user_socket, create_join_game_json(match.group(1)))

            elif event.ui_element == lobby_page_elements["disconnect_button"]:
                print("Déconnexion.")
                send_json(user_socket, create_deconnection_json())

        manager.process_events(event)

    return True, lobby_page_elements, handle_events_on_lobby_page


def handle_events_on_new_account_page(manager, create_account_elements, user_socket):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, None, None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                handle_create_new_account_event(create_account_elements, user_socket)
            else:
                create_account_elements["error_label"].set_text("")

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == create_account_elements["create_button"]:
                handle_create_new_account_event(create_account_elements, user_socket)

            elif event.ui_element == create_account_elements["back_button"]:
                clear_page(create_account_elements)
                login_page_elements = create_gui_elements_login_page(manager)
                return True, login_page_elements, handle_events_on_login_page

        manager.process_events(event)

    return True, create_account_elements, handle_events_on_new_account_page


# Fonction pour gérer les événements
def handle_events_on_login_page(manager, login_page_elements, user_socket):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, None, None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                handle_login_event(login_page_elements, user_socket)
            else:
                login_page_elements["error_label"].set_text("")

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == login_page_elements["login_button"]:
                handle_login_event(login_page_elements, user_socket)

            elif event.ui_element == login_page_elements["create_account_button"]:
                clear_page(login_page_elements)
                create_account_elements = create_gui_elements_new_account_page(manager)
                return True, create_account_elements, handle_events_on_new_account_page

        elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            login_page_elements["error_label"].set_text("")

        manager.process_events(event)

    return True, login_page_elements, handle_events_on_login_page


def clear_page(elements):
    for key, element in elements.items():
        if isinstance(element, list):
            for sub_element in element:
                if hasattr(sub_element, "kill"):
                    sub_element.kill()
        elif hasattr(element, "kill"):
            element.kill()
        else:
            print(f"Warning: Element {element} has no kill() method.")

    elements.clear()


def main():
    # play_music(BACKGROUND_MUSIC_PATH, 1, 5000, True)

    screen = init_pygame()
    background = create_background()
    manager = pygame_gui.UIManager(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        THEME_PATH
    )

    clock = pygame.time.Clock()
    running = True

    user_socket = None

    try:
        current_page_elements = create_gui_elements_login_page(manager)
        current_event_handler = handle_events_on_login_page

        user_socket = connect_to_server(HOST, PORT)
        while running:
            time_delta = clock.tick(60) / 1000.0

            # Handle events and update the current page elements and event handler
            # based on the current event handler's return values
            (
                current_handler_running,
                current_page_elements,
                current_event_handler
            ) = current_event_handler(
                manager,
                current_page_elements,
                user_socket
            )

            (
                server_running,
                current_page_elements,
                current_event_handler
            ) = handle_server_response(
                manager,
                user_socket,
                current_page_elements,
                current_event_handler
            )

            running = current_handler_running and server_running

            manager.update(time_delta)
            screen.blit(background, (0, 0))

            manager.draw_ui(screen)

            if is_grid_visible:
                draw_grid(SCREEN)
                draw_pions_list()

            pygame.display.update()
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        print("Fermeture de la connexion.")
        user_socket.close()
        pygame.quit()


if __name__ == "__main__":
    main()
