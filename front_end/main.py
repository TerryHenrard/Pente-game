import json
import socket

import pygame
import pygame_gui
import select

# Configuration du serveur
HOST = '127.0.0.1'  # Adresse IP du serveur (localhost)
PORT = 55555  # Port du serveur
BUFFER_SIZE = 1024

# Initialisation de PyGame et du module audio
pygame.init()
pygame.mixer.init()

# Configuration de PyGame
# Configuration de l'écran
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Plateau de Pente")

# Dimensions du plateau
GRID_ROWS = 19
GRID_COLS = 19
CASE_SIZE = 40
PIECE_SIZE = 36

# Couleurs
BACKGROUND_COLOR = (193, 176, 150)
LINE_COLOR = (0, 0, 0)
RED_PION_COLOR = (255, 0, 0, 150)
YELLOW_PION_COLOR = (255, 215, 0, 150)

# Chemins des fichiers theme
THEME_PATH = "assets/styles/theme.json"

# Chemin du fichier audio
BACKGROUND_MUSIC_PATH = "assets/audio/background_music.mp3"
YOU_SHALL_NOT_PASS_PATH = "assets/audio/login-error.wav"

# Chemin des fichiers image
GANDALF_IMAGE_PATH = "assets/images/gandalf.png"

# Status de la réponse (JSON)
RESPONSE_SUCCESS_STATUS = 1
RESPONSE_FAIL_STATUS = 0


def play_music(music_path, volume=1, fade_ms=0, is_loop=False):
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=1 if is_loop else 0, fade_ms=fade_ms)
    except pygame.error as e:
        print(f"Erreur lors de la lecture de l'audio : {e}")


def stop_music(fade_ms=2000):
    try:
        pygame.mixer.music.fadeout(fade_ms)
    except pygame.error as e:
        print(f"Erreur lors de l'arrêt de l'audio : {e}")


def pause_music():
    try:
        pygame.mixer.music.pause()
    except pygame.error as e:
        print(f"Erreur lors de la mise en pause de l'audio : {e}")


def unpause_music():
    try:
        pygame.mixer.music.unpause()
    except pygame.error as e:
        print(f"Erreur lors de la reprise de l'audio : {e}")


def play_audio(sound_path, volume=0.1, fade_ms=0, is_loop=False):
    try:
        # Check if the sound is already playing
        if not pygame.mixer.get_busy():
            # Load and play the sound
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(volume)
            sound.play(loops=1 if is_loop else 0, fade_ms=fade_ms)
    except pygame.error as e:
        print(f"Erreur lors de la lecture de l'audio : {e}")


def draw_image(surface, image_path, position):
    try:
        image = pygame.image.load(image_path)
        surface.blit(image, position)
    except pygame.error as e:
        print(f"Erreur lors du chargement de l'image : {e}")


# Fonction pour dessiner la grille
def draw_grid(surface):
    for x in range(GRID_COLS):
        pygame.draw.line(
            surface,
            LINE_COLOR,
            (x * CASE_SIZE, 0),
            (x * CASE_SIZE, CASE_SIZE * GRID_ROWS)
        )
    for y in range(GRID_ROWS):
        pygame.draw.line(
            surface,
            LINE_COLOR,
            (0, y * CASE_SIZE),
            (CASE_SIZE * GRID_COLS, y * CASE_SIZE)
        )


# Fonction pour dessiner un pion
def draw_pion(surface, color, position, size):
    pion_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(
        pion_surface,
        color,
        (size // 2, size // 2),
        size // 2
    )
    surface.blit(pion_surface, position)


def send_json(s, json_message):
    try:
        print(f"Envoi du message :")
        print(json_message)
        s.sendall(json_message.encode())
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
                manager
            )
        elif response_type == "disconnect_ack":
            return False, None, None

        return True, current_page_elements, current_event_handler

    except BlockingIOError:
        # Gérer spécifiquement les erreurs de socket non bloquant
        print("Socket temporairement indisponible. Nouvelle tentative...")
        return True, current_page_elements, current_event_handler

    except Exception as e:
        # Capture des erreurs inattendues
        print(f"Erreur de communication : {e}")
        return False, None, None


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


def create_gui_elements_lobby_page(manager):
    return {
        "title_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 300),
                (600, 60)
            ),
            text="Menu principal",
            manager=manager,
            object_id='#lobby_title_label'
        ),
        "score_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 220),
                (400, 30)
            ),
            text="Score: 0",
            manager=manager,
            object_id="#score_label"
        ),
        "wins_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 190),
                (400, 30)
            ),
            text="Victoires: 0",
            manager=manager,
            object_id="#wins_label"
        ),
        "losses_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 160),
                (400, 30)
            ),
            text="Défaites: 0",
            manager=manager,
            object_id="#losses_label"
        ),
        "games_played_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 130),
                (400, 30)
            ),
            text="Parties jouées: 0",
            manager=manager,
            object_id="#games_played_label"
        ),
        "create_game_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 60),
                (200, 50)
            ),
            text="Créer une partie",
            manager=manager
        ),
        "join_game_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2),
                (200, 50)
            ),
            text="Rejoindre une partie",
            manager=manager
        ),
        "disconnect_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 60),
                (200, 50)
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


# Fonction pour créer le gestionnaire GUI et les éléments
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
                (200, 50)
            ),
            text="Se connecter",
            manager=manager
        ),
        "create_account_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 85),
                (200, 50)
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
                (200, 50)
            ),
            text="Créer",
            manager=manager
        ),
        "back_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 135),
                (200, 50)
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


def handle_auth_response(response_json, current_page_elements, manager):
    response_status = response_json.get("status")
    if response_status != RESPONSE_SUCCESS_STATUS:
        return response_status is not None, current_page_elements, handle_events_on_login_page

    clear_page(current_page_elements)
    next_page_elements = create_gui_elements_lobby_page(manager)

    # Afficher les informations du JSON
    player_stats = response_json.get("player_stats", {})
    next_page_elements["score_label"].set_text(f"Score: {player_stats.get('score', 0)}")
    next_page_elements["wins_label"].set_text(f"Victoires: {player_stats.get('wins', 0)}")
    next_page_elements["losses_label"].set_text(f"Défaites: {player_stats.get('losses', 0)}")
    next_page_elements["games_played_label"].set_text(f"Parties jouées: {player_stats.get('games_played', 0)}")

    return True, next_page_elements, handle_events_on_lobby_page


def handle_login_event(login_page_elements, user_socket):
    username = login_page_elements["username_entry"].get_text()
    password = login_page_elements["password_entry"].get_text()

    if not username or not password:
        print("Nom d'utilisateur ou mot de passe vide !")
        login_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe vide !")
        play_audio(YOU_SHALL_NOT_PASS_PATH)
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
        play_audio(YOU_SHALL_NOT_PASS_PATH)
        return

    if len(password) < 12:
        new_account_page_elements["error_label"].set_text("Le mot de passe doit contenir au moins 12 caractères.")
        play_audio(YOU_SHALL_NOT_PASS_PATH)
        return

    if password != conf_password:
        new_account_page_elements["error_label"].set_text("Les mots de passe ne correspondent pas.")
        play_audio(YOU_SHALL_NOT_PASS_PATH)
        return

    print(f"Tentative de création de compte : {username}, {password}")
    json_new_account_message = create_new_account_json(username, password, conf_password)

    if not json_new_account_message:
        print("Erreur lors de la création du message.")
        return

    send_json(user_socket, json_new_account_message)


def handle_events_on_lobby_page(manager, lobby_page_elements, user_socket):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, None, None

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == lobby_page_elements["create_game_button"]:
                print("Création d'une partie.")

        manager.process_events(event)

    return True, lobby_page_elements, handle_events_on_lobby_page


def handle_events_on_new_account_page(manager, create_account_elements, user_socket):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, None, None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                handle_create_new_account_event(create_account_elements, user_socket)
            else:
                create_account_elements["error_label"].set_text("")

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
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

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                handle_login_event(login_page_elements, user_socket)
            else:
                login_page_elements["error_label"].set_text("")

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
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
    for element in elements.values():
        element.kill()

    elements.clear()


def main():
    play_music(BACKGROUND_MUSIC_PATH, 1, 5000, True)

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
            pygame.display.update()
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        print("Fermeture de la connexion.")
        user_socket.close()
        pygame.quit()


if __name__ == "__main__":
    main()
