import json
import re
import socket

import pygame
import pygame_gui
import select
from pygame_gui.elements import UIButton

# Configuration du serveur
HOST = '127.0.0.1'  # Adresse IP du serveur (localhost)
PORT = 55555  # Port du serveur
BUFFER_SIZE = 1048

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
GRID_SIZE = GRID_ROWS * GRID_COLS
CELL_SIZE = 45
PIECE_SIZE = 40
LINE_WIDTH_DEFAULT = 1
LINE_WIDTH_CENTER = 2

# Points "hoshi" (points spéciaux sur le plateau)
HOSHI_POINTS = [
    (3, 3), (3, 9), (3, 15),
    (9, 3), (9, 9), (9, 15),
    (15, 3), (15, 9), (15, 15)
]
HOSHI_POINTS_SIZE = 8

# Caractères des pions
HOST_CHAR = 'x'
OPPONENT_CHAR = 'o'
EMPTY_CHAR = '-'

# Tolérance pour cliquer autour des intersections (en pixels)
TOLERANCE = 5

# Dimensions de la grille
GRID_DIMENSIONS = (GRID_COLS - 1) * CELL_SIZE

# Calculer les marges pour centrer la grille
MARGIN_X = (SCREEN_WIDTH - GRID_DIMENSIONS) // 2
MARGIN_Y = (SCREEN_HEIGHT - GRID_DIMENSIONS) // 2 + 20

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
LABEL_WIDTH = 300
LABEL_HEIGHT = 25
LABEL_MARGIN_BOTTOM = 10
LABEL_LEFT_MARGIN = 5

# Couleurs
BACKGROUND_COLOR = (193, 176, 150)
LINE_COLOR = (0, 0, 0)

# Chemins des fichiers theme
THEME_PATH = "assets/styles/theme.json"

# Chemin du fichier audio
BACKGROUND_MUSIC_PATH = "assets/audio/background-music.mp3"
ERROR_SOUND_PATH = "assets/audio/login-error.wav"
LOBBY_ENTRY_SOUND_PATH = "assets/audio/lobby-entry.mp3"
START_GAME_OPPONENT_SOUND_PATH = "assets/audio/starting-game-opponent.mp3"
START_GAME_HOST_SOUND_PATH = "assets/audio/starting-game-host.mp3"
MOVE_FAILED_PATH = "assets/audio/move-fail.wav"
VICTORY_SOUND_PATH = "assets/audio/victory.mp3"
DEFEAT_SOUND_PATH = "assets/audio/defeat.mp3"
CAPTURE_SOUND_PATH = "assets/audio/capture.mp3"
FORFEIT_SOUND_PATH = "assets/audio/forfeit.mp3"

# Chemin des fichiers image
GANDALF_IMAGE_PATH = "assets/images/gandalf.png"
EYE_OF_SAURON_IMAGE_PATH = "assets/images/eye_of_sauron_pion.png"
GOLLUM_IMAGE_PATH = "assets/images/gollum.png"
ONE_RING_IMAGE_PATH = "assets/images/one_ring_pion.png"
SAURON_IMAGE_PATH = "assets/images/sauron.png"
NAZGUL_IMAGE_PATH = "assets/images/nazgul.png"
KING_WITCH_OF_ANGMAR_IMAGE_PATH = "assets/images/king_witch_of_angmar.png"
YOUNG_BILBO_IMAGE_PATH = "assets/images/young_bilbo.png"
OLD_BILBO_IMAGE_PATH = "assets/images/old_bilbo.png"
SOUND_ON_IMAGE_PATH = "assets/images/sound-on.png"
SOUND_OFF_IMAGE_PATH = "assets/images/sound-off.png"

# Charger les images
GANDALF_IMAGE = pygame.image.load(GANDALF_IMAGE_PATH)
SAURON_IMAGE = pygame.image.load(SAURON_IMAGE_PATH)
GOLLUM_IMAGE = pygame.image.load(GOLLUM_IMAGE_PATH)
NAZGUL_IMAGE = pygame.image.load(NAZGUL_IMAGE_PATH)
KING_WITCH_OF_ANGMAR_IMAGE = pygame.image.load(KING_WITCH_OF_ANGMAR_IMAGE_PATH)
YOUNG_BILBO_IMAGE = pygame.image.load(YOUNG_BILBO_IMAGE_PATH)
OLD_BILBO_IMAGE = pygame.image.load(OLD_BILBO_IMAGE_PATH)
PION_IMAGE_HOST = pygame.image.load(ONE_RING_IMAGE_PATH)
SOUND_ON_IMAGE = pygame.image.load(SOUND_ON_IMAGE_PATH)
SOUND_OFF_IMAGE = pygame.image.load(SOUND_OFF_IMAGE_PATH)
PION_IMAGE_OPPONENT = pygame.image.load(EYE_OF_SAURON_IMAGE_PATH)
PION_IMAGE_OPPONENT_SCALED = (
    pygame.transform.scale(
        PION_IMAGE_OPPONENT,
        (PIECE_SIZE, PIECE_SIZE)
    )
)
PION_IMAGE_HOST_SCALED = (
    pygame.transform.scale(
        PION_IMAGE_HOST,
        (PIECE_SIZE, PIECE_SIZE)
    )
)
SOUND_ON_IMAGE_SCALED = (
    pygame.transform.scale(
        SOUND_ON_IMAGE,
        (40, 40)
    )
)
SOUND_OFF_IMAGE_SCALED = (
    pygame.transform.scale(
        SOUND_OFF_IMAGE,
        (40, 40)
    )
)

# Coordonées & dimensions des images
GANDALF_IMAGE_X = 10
GANDALF_IMAGE_Y = 200
GANDALF_IMAGE_WIDTH = 600
GANDALF_IMAGE_HEIGHT = 900

SAURON_IMAGE_X = 640
SAURON_IMAGE_Y = 200
SAURON_IMAGE_WIDTH = 592
SAURON_IMAGE_HEIGHT = 900

GOLLUM_IMAGE_WIDTH = 415
GOLLUM_IMAGE_HEIGHT = 640
GOLLUM_IMAGE_X = -35
GOLLUM_IMAGE_Y = SCREEN_HEIGHT - GOLLUM_IMAGE_HEIGHT

NAZGUL_IMAGE_WIDTH = 311
NAZGUL_IMAGE_HEIGHT = 761
NAZGUL_IMAGE_X = SCREEN_WIDTH // 2 - 470
NAZGUL_IMAGE_Y = 350

KING_WITCH_OF_ANGMAR_IMAGE_WIDTH = 400
KING_WITCH_OF_ANGMAR_IMAGE_HEIGHT = 812
KING_WITCH_OF_ANGMAR_IMAGE_X = SCREEN_WIDTH // 2 + 130
KING_WITCH_OF_ANGMAR_IMAGE_Y = 300

YOUNG_BILBO_IMAGE_WIDTH = 246
YOUNG_BILBO_IMAGE_HEIGHT = 640
YOUNG_BILBO_IMAGE_X = 0
YOUNG_BILBO_IMAGE_Y = 430

OLD_BILBO_IMAGE_WIDTH = 237
OLD_BILBO_IMAGE_HEIGHT = 640
OLD_BILBO_IMAGE_X = SCREEN_WIDTH - OLD_BILBO_IMAGE_WIDTH
OLD_BILBO_IMAGE_Y = 430

# Status de la réponse (JSON)
RESPONSE_SUCCESS_STATUS = 1
RESPONSE_FAIL_STATUS = 0

# Status de fin de partie
VICTORY_STATUS = 0
DEFEAT_STATUS = 1
WITHDRAW_STATUS = 2

# Regex's
REGEX_CAPTURE_GAME_NAME = r"Name:\s*(.*?)\s*Status:"

# Logo de l'hôte
HOST_PION_LOGO_X = 10
HOST_PION_LOGO_Y = 270
HOST_PION_LOGO_WIDTH = 200
HOST_PION_LOGO_HEIGHT = 200

# Logo de l'adversaire
OPPONENT_PION_LOGO_WIDTH = 200
OPPONENT_PION_LOGO_HEIGHT = 200
OPPONENT_PION_LOGO_X = SCREEN_WIDTH - OPPONENT_PION_LOGO_WIDTH - BUTTON_LEFT_RIGHT_MARGIN
OPPONENT_PION_LOGO_Y = 270

# Statistiques du joueur connecté
score = 0
wins = 0
losses = 0
forfeits = 0
games_played = 0

# Afficher le plateau de jeu
is_grid_visible = False
is_board_visible = False
board = ""

# Info de la partie
game_name = ""
player_name = ""
opponent_name = ""
is_host = False
is_my_turn = False

# État initial du son (active par défaut)
sound_enabled = True


def toggle_sound(sound_enabled_param: bool) -> bool:
    """
    Active ou désactive le son.

    Params:
        sound_enabled_param (bool) : L'état actuel du son (True pour activé, False pour désactivé).

    Returns:
        bool: Le nouvel état du son (True pour activé, False pour désactivé).

    Raises:
        RuntimeError: Si le mixeur de pygame n'est pas initialisé.
    """
    try:
        # Inverse l'état actuel du son
        sound_enabled_param = not sound_enabled_param

        # Vérifie si le mixeur de pygame est initialisé
        if not pygame.mixer.get_init():
            raise RuntimeError(
                "pygame.mixer n'est pas initialisé. Assurez-vous que pygame.mixer.init() est appelé avant de basculer le son."
            )

        # Ajuste le volume en fonction du nouvel état
        pygame.mixer.music.set_volume(1 if sound_enabled_param else 0)

        # Retourne le nouvel état du son
        return sound_enabled_param
    except Exception as e:
        # Relève toute exception rencontrée
        raise Exception(f"Erreur lors de la bascule du son : {e}") from e


def update_sound_button(
        sound_button: UIButton,
        sound_enabled_param: bool
) -> None:
    """
    Met à jour le texte du bouton en fonction de l'état du son.

    Params:
        sound_button (UIButton): Objet du bouton à modifier (doit implémenter la méthode `set_text`).
        sound_enabled_param (bool): État actuel du son (True pour activé, False pour désactivé).

    Returns:
        None

    Raises:
        ValueError: Si le bouton fourni est invalide ou ne contient pas la méthode `set_text`.
        Exception: Pour toute erreur inattendue lors de la mise à jour du texte.
    """
    try:
        # Vérifie que le bouton est valide
        if not sound_button or not hasattr(sound_button, "set_text"):
            raise ValueError("Le bouton fourni est invalide ou ne possède pas de méthode `set_text`.")

        # Détermine le texte du bouton en fonction de l'état du son
        text: str = "Désactiver le son" if sound_enabled_param else "Activer le son"

        # Met à jour le texte du bouton
        sound_button.set_text(text)

    except ValueError as ve:
        raise ValueError(f"Erreur de validation des paramètres : {ve}") from ve
    except AttributeError as ae:
        raise AttributeError(f"Erreur d'attribut sur le bouton fourni : {ae}") from ae
    except Exception as ex:
        raise Exception(f"Erreur inattendue lors de la mise à jour du bouton : {ex}") from ex


def play_music(
        music_path: str,
        volume: float = 1.0,
        fade_ms: int = 0,
        is_loop: bool = False
) -> None:
    """
    Jouer un fichier musical.

    Params:
        music_path (str): Chemin du fichier audio.
        volume (float): Niveau du volume (valeurs entre 0.0 et 1.0). Par défaut, 1.0.
        fade_ms (int): Durée de transition (en millisecondes) pour l'apparition progressive de la musique. Par défaut, 0.
        is_loop (bool): Si vrai, boucle la musique indéfiniment. Par défaut, False.

    Returns:
        None

    Raises:
        ValueError: Si le volume est hors de l'intervalle [0.0, 1.0].
        FileNotFoundError: Si le fichier audio spécifié n'existe pas.
        pygame.error: Si une erreur Pygame survient.
        Exception: Pour toute autre erreur inattendue.
    """
    try:
        # Vérifie si le fichier existe
        if not music_path or not isinstance(music_path, str):
            raise ValueError("Le chemin de la musique doit être une chaîne non vide.")

        # Charge le fichier audio
        pygame.mixer.music.load(music_path)

        # Configure le volume
        if 0.0 <= volume <= 1.0:
            pygame.mixer.music.set_volume(volume)
        else:
            raise ValueError("Le volume doit être compris entre 0.0 et 1.0")

        # Lance la lecture avec ou sans boucle
        pygame.mixer.music.play(loops=-1 if is_loop else 0, fade_ms=fade_ms)

    except pygame.error as pe:
        raise pygame.error(f"Erreur Pygame lors de la lecture de la musique : {pe}") from pe
    except ValueError as ve:
        raise ValueError(f"Erreur de validation des paramètres : {ve}") from ve
    except Exception as ex:
        raise Exception(f"Erreur inattendue : {ex}") from ex


def pause_music() -> None:
    """
    Mets en pause la musique en cours de lecture.

    Exceptions:
        pygame.error: Si une erreur se produit lors de la tentative de mise en pause de la musique.
        Exception: Pour toute autre erreur inattendue.
    """
    try:
        # Met la musique en pause
        pygame.mixer.music.pause()

    except pygame.error as pe:
        raise pygame.error(f"Erreur Pygame lors de la mise en pause de la musique : {pe}") from pe
    except Exception as ex:
        raise Exception(f"Erreur inattendue lors de la mise en pause de la musique : {ex}") from ex


def unpause_music() -> None:
    """
    Reprends la musique en cours de pause.

    Exceptions:
        pygame.error: Si une erreur se produit lors de la reprise de la musique.
        Exception: Pour toute autre erreur imprévue.
    """
    try:
        # Reprend la musique en pause
        pygame.mixer.music.unpause()

    except pygame.error as pe:
        raise pygame.error(f"Erreur Pygame lors de la reprise de la musique : {pe}") from pe
    except Exception as ex:
        raise Exception(f"Erreur inattendue lors de la reprise de la musique : {ex}") from ex


def play_audio(
        sound_path: str,
        volume: float = 0.1
) -> None:
    """
    Joue un fichier audio.

    Params:
        sound_path (str): Chemin vers le fichier audio à jouer.
        volume (float): Niveau du volume (valeurs entre 0.0 et 1.0). Par défaut, 0.1.

    Returns:
        None

    Exceptions:
        pygame.error: Si une erreur se produit lors de la lecture audio.
        ValueError: Si le volume est hors des limites acceptables.
        Exception: Pour toute autre erreur inattendue.
    """
    try:
        # Vérifie si le volume est dans les limites acceptables
        if not 0.0 <= volume <= 1.0:
            raise ValueError("Le volume doit être compris entre 0.0 et 1.0.")

        # Vérifie si le son est activé et qu'aucun autre son n'est en cours de lecture
        if sound_enabled and not pygame.mixer.get_busy():
            # Charge et joue le son
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(volume)
            sound.play()
        else:
            print("Lecture audio ignorée : le son est désactivé ou un autre son est en cours.")

    except pygame.error as pe:
        raise pygame.error(f"Erreur Pygame lors de la lecture de l'audio : {pe}") from pe
    except ValueError as ve:
        raise ValueError(f"Erreur de validation des paramètres : {ve}") from ve
    except Exception as ex:
        raise Exception(f"Erreur inattendue lors de la lecture de l'audio : {ex}") from ex


def draw_board() -> None:
    """
    Dessine le plateau de jeu en affichant les pièces à leurs positions respectives.

    Exceptions:
        NameError: Si des constantes ou variables utilisées ne sont pas définies.
        TypeError: Si le tableau `board` ou ses éléments sont mal définis.
    """
    try:
        # Parcourt chaque rangée de la grille
        for y in range(GRID_ROWS):
            # Parcourt chaque colonne de la grille
            for x in range(GRID_COLS):
                # Récupère l'état de la case actuelle
                cell = board[y * GRID_COLS + x]

                # Calcul de la position en pixels de l'image
                img_x = (MARGIN_X + (x * CELL_SIZE) - (PIECE_SIZE // 2))
                img_y = (MARGIN_Y + (y * CELL_SIZE) - (PIECE_SIZE // 2))

                # Détermine l'image à utiliser en fonction du caractère dans la case
                pion_image = {
                    HOST_CHAR: PION_IMAGE_HOST_SCALED,
                    OPPONENT_CHAR: PION_IMAGE_OPPONENT_SCALED
                }.get(cell)

                # Dessine l'image si elle est définie
                if pion_image:
                    SCREEN.blit(pion_image, (img_x, img_y))

    except NameError as ne:
        raise NameError(f"Erreur : une constante ou une variable n'est pas définie correctement : {ne}") from ne
    except TypeError as te:
        raise TypeError(f"Erreur : le tableau `board` ou ses éléments sont mal définis : {te}") from te
    except Exception as ex:
        raise Exception(f"Erreur inattendue lors du dessin du plateau : {ex}") from ex


def draw_grid(surface: pygame.Surface) -> None:
    """
    Dessine la grille du plateau et les points "hoshi" sur la surface donnée.

    Args:
        surface (pygame.Surface): Surface sur laquelle la grille et les points doivent être dessinés.

    Exceptions:
        ValueError: Si la surface n'est pas valide.
        Exception: Pour toute erreur inattendue.
    """
    try:
        # Vérifie que la surface est valide
        if not isinstance(surface, pygame.Surface):
            raise ValueError("La surface fournie n'est pas valide.")

        # Dessiner les lignes verticales
        for x in range(GRID_COLS):
            pygame.draw.line(
                surface,
                LINE_COLOR,
                (MARGIN_X + x * CELL_SIZE, MARGIN_Y),
                (MARGIN_X + x * CELL_SIZE, MARGIN_Y + GRID_DIMENSIONS),
                LINE_WIDTH_CENTER if x == GRID_COLS // 2 else LINE_WIDTH_DEFAULT
            )

        # Dessiner les lignes horizontales
        for y in range(GRID_ROWS):
            pygame.draw.line(
                surface,
                LINE_COLOR,
                (MARGIN_X, MARGIN_Y + y * CELL_SIZE),
                (MARGIN_X + GRID_DIMENSIONS, MARGIN_Y + y * CELL_SIZE),
                LINE_WIDTH_CENTER if y == GRID_ROWS // 2 else LINE_WIDTH_DEFAULT
            )

        # Ajouter les points "hoshi" sur le plateau
        for px, py in HOSHI_POINTS:
            pygame.draw.rect(
                surface,
                LINE_COLOR,
                pygame.Rect(
                    MARGIN_X + px * CELL_SIZE - HOSHI_POINTS_SIZE // 2,
                    MARGIN_Y + py * CELL_SIZE - HOSHI_POINTS_SIZE // 2,
                    HOSHI_POINTS_SIZE,
                    HOSHI_POINTS_SIZE
                )
            )
    except ValueError as ve:
        raise ValueError(f"Erreur de validation : {ve}") from ve
    except Exception as ex:
        raise Exception(f"Erreur inattendue lors du dessin de la grille : {ex}") from ex


def send_json(user_socket: socket.socket, json_message: str) -> None:
    """
    Envoie un message JSON via un socket utilisateur.

    Args:
        user_socket (socket.socket): Le socket à utiliser pour l'envoi.
        json_message (str): Le message JSON à envoyer sous forme de chaîne.

    Exceptions:
        ValueError: Si le message JSON est invalide.
        ConnectionError: Si une erreur de connexion survient lors de l'envoi.
        Exception: Pour toute autre erreur inattendue.
    """
    try:
        # Valide et formate le message JSON avant l'envoi
        parsed_json = json.loads(json_message)  # Vérifie si le JSON est valide
        print("Envoi du message JSON formaté :")
        print(json.dumps(parsed_json, indent=4))  # Affiche le JSON sous une forme lisible pour le débogage

        # Envoie le message via le socket
        user_socket.sendall(json_message.encode('utf-8'))  # Encodage explicite en UTF-8

    except json.JSONDecodeError as je:
        raise ValueError(f"Le message fourni n'est pas un JSON valide : {je}") from je
    except socket.error as se:
        raise ConnectionError(f"Erreur de connexion lors de l'envoi du message : {se}") from se
    except Exception as ex:
        raise Exception(f"Erreur inattendue lors de l'envoi du message JSON : {ex}") from ex


def receive_json(user_scocket: socket.socket) -> dict:
    """
    Reçoit un message JSON via un socket et le décode.

    Args:
        user_scocket (socket.socket): Le socket à utiliser pour recevoir les données.

    Returns:
        dict: Le message JSON décodé sous forme de dictionnaire.

    Raises:
        ConnectionError: Si aucune donnée n'est reçue ou si une erreur de connexion survient.
        json.JSONDecodeError: Si le message reçu n'est pas un JSON valide.
        Exception: Pour toute autre erreur inattendue.
    """
    try:
        # Réception des données depuis le socket
        data = user_scocket.recv(BUFFER_SIZE).decode("utf-8")

        # Vérifie si des données ont été reçues
        if not data:
            raise ConnectionError("Aucune donnée reçue ou le socket est fermé.")

        # Tente de charger les données en tant que JSON
        return json.loads(data)

    except json.JSONDecodeError as jde:
        raise json.JSONDecodeError(f"Erreur de décodage JSON : {jde.msg}", jde.doc, jde.pos) from jde
    except socket.error as se:
        raise ConnectionError(f"Erreur de connexion au socket : {se}") from se
    except Exception as e:
        raise Exception(f"Erreur inattendue lors de la réception des données : {e}") from e


def connect_to_server(host: str, port: int) -> socket.socket:
    """
    Établit une connexion avec un serveur via un socket.

    Args:
        host (str): L'adresse du serveur (nom d'hôte ou IP).
        port (int): Le numéro de port du serveur.

    Returns:
        socket.socket: Le socket connecté au serveur.

    Raises:
        ConnectionError: Si la connexion au serveur échoue.
        ValueError: Si le port ou l'hôte est invalide.
        Exception: Pour toute autre erreur inattendue.
    """
    try:
        # Création d'un socket TCP/IP
        user_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Établit la connexion au serveur
        user_socket.connect((host, port))

        # Définit le socket en mode non bloquant
        user_socket.setblocking(False)

        print(f"Connecté au serveur {host}:{port}.")
        return user_socket

    except socket.gaierror as ge:
        raise ValueError(f"Adresse du serveur invalide : {ge}") from ge
    except socket.error as se:
        raise ConnectionError(f"Échec de la connexion au serveur {host}:{port} : {se}") from se
    except Exception as ex:
        raise Exception(f"Erreur inattendue lors de la connexion au serveur : {ex}") from ex


def create_play_move_json(x, y):
    try:
        return json.dumps({
            "type": "play_move",
            "x": x,
            "y": y
        })
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def create_quit_game_json():
    try:
        return json.dumps({
            "type": "quit_game"
        })
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


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


def create_join_game_json(game_name_param):
    try:
        return json.dumps({
            "type": "join_game",
            "game_name": game_name_param
        })
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def create_new_game_json(game_name_param):
    try:
        return json.dumps({
            "type": "create_game",
            "game_name": game_name_param
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


def draw_pion(x, y, width, heigth, image_surface, manager):
    return pygame_gui.elements.UIImage(
        relative_rect=pygame.Rect((x, y), (width, heigth)),  # Position et taille
        image_surface=image_surface,
        manager=manager
    )


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
        "forfeits_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    LABEL_LEFT_MARGIN,
                    3 * (LABEL_HEIGHT + BUTTON_BETWEEN_MARGIN) - (BUTTON_BETWEEN_MARGIN // 2)
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="",
            manager=manager,
            object_id="#forfeits_label"
        ),
        "games_played_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    LABEL_LEFT_MARGIN,
                    4 * (LABEL_HEIGHT + BUTTON_BETWEEN_MARGIN) - BUTTON_BETWEEN_MARGIN
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="games_played_label",
            manager=manager,
            object_id="#games_played_label"
        ),
        "young_bilbo_image": pygame_gui.elements.UIImage(
            relative_rect=pygame
            .Rect(
                (YOUNG_BILBO_IMAGE_X, YOUNG_BILBO_IMAGE_Y),
                (YOUNG_BILBO_IMAGE_WIDTH, YOUNG_BILBO_IMAGE_HEIGHT)
            ),
            image_surface=YOUNG_BILBO_IMAGE,
            manager=manager
        ),
        "old_bilbo_image": pygame_gui.elements.UIImage(
            relative_rect=pygame
            .Rect(
                (OLD_BILBO_IMAGE_X, OLD_BILBO_IMAGE_Y),
                (OLD_BILBO_IMAGE_WIDTH, OLD_BILBO_IMAGE_HEIGHT)
            ),
            image_surface=OLD_BILBO_IMAGE,
            manager=manager
        ),
        "create_game_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 - ((3 * BUTTON_WIDTH) // 2) - BUTTON_LEFT_RIGHT_MARGIN,
                    SCREEN_HEIGHT - BUTTON_BOTTOM_MARGIN
                ),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Créer une partie",
            manager=manager
        ),
        "refresh_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 - (BUTTON_WIDTH // 2),
                    SCREEN_HEIGHT - BUTTON_BOTTOM_MARGIN
                ),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Rafraîchir",
            manager=manager
        ),
        "disconnect_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 + (BUTTON_WIDTH // 2) + BUTTON_LEFT_RIGHT_MARGIN,
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
        ),
        "sound_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH - 160,
                    10
                ),
                (150, 40)
            ),
            text="Désactiver le son",
            manager=manager
        )
    }


def create_gui_elements_create_game_page(manager):
    return {
        "title_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH // 2 - 300,
                    SCREEN_HEIGHT // 2 - 400
                ),
                (600, 60)
            ),
            text="Créer une partie",
            manager=manager,
            object_id='#new_game_title_label'
        ),
        "nazgul_image": pygame_gui.elements.UIImage(
            relative_rect=pygame
            .Rect(
                (NAZGUL_IMAGE_X, NAZGUL_IMAGE_Y),
                (NAZGUL_IMAGE_WIDTH, NAZGUL_IMAGE_HEIGHT)
            ),
            image_surface=NAZGUL_IMAGE,
            manager=manager
        ),
        "king_witch_of_angmar_image": pygame_gui.elements.UIImage(
            relative_rect=pygame
            .Rect(
                (KING_WITCH_OF_ANGMAR_IMAGE_X, KING_WITCH_OF_ANGMAR_IMAGE_Y),
                (KING_WITCH_OF_ANGMAR_IMAGE_WIDTH, KING_WITCH_OF_ANGMAR_IMAGE_HEIGHT)
            ),
            image_surface=KING_WITCH_OF_ANGMAR_IMAGE,
            manager=manager
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
                (
                    SCREEN_WIDTH // 2 - 300,
                    SCREEN_HEIGHT // 2 - 200
                ),
                (600, 60)
            ),
            text="Se connecter",
            manager=manager,
            object_id='#login_title_label'
        ),
        "gandalf_image": pygame_gui.elements.UIImage(
            relative_rect=pygame
            .Rect(
                (GANDALF_IMAGE_X, GANDALF_IMAGE_Y),
                (GANDALF_IMAGE_WIDTH, GANDALF_IMAGE_HEIGHT)
            ),
            image_surface=GANDALF_IMAGE,
            manager=manager
        ),
        "sauron_image": pygame_gui.elements.UIImage(
            relative_rect=pygame
            .Rect(
                (SAURON_IMAGE_X, SAURON_IMAGE_Y),
                (SAURON_IMAGE_WIDTH, SAURON_IMAGE_HEIGHT)
            ),
            image_surface=SAURON_IMAGE,
            manager=manager
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
                (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 + 155),
                (600, 30)
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
                (
                    SCREEN_WIDTH // 2 - 300,
                    SCREEN_HEIGHT // 2 - 200
                ),
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
        "gollum_image": pygame_gui.elements.UIImage(
            relative_rect=pygame
            .Rect(
                (GOLLUM_IMAGE_X, GOLLUM_IMAGE_Y),
                (GOLLUM_IMAGE_WIDTH, GOLLUM_IMAGE_HEIGHT)
            ),
            image_surface=GOLLUM_IMAGE,
            manager=manager
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
                (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 + 195),
                (600, 30)
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
                (
                    SCREEN_WIDTH // 2 - 300,
                    0
                ),
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
        ),
        "player1_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    MARGIN_X // 11,
                    MARGIN_Y
                ),
                (200, 30)
            ),
            text="Player 1: ",
            manager=manager,
            object_id="#player1_label"
        ),
        "player2_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    MARGIN_X + GRID_DIMENSIONS + (MARGIN_X // 10),
                    MARGIN_Y
                ),
                (200, 30)
            ),
            text="",
            manager=manager,
            object_id="#player2_label"
        ),
        "quit_button": pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH - BUTTON_WIDTH - BUTTON_LEFT_RIGHT_MARGIN,
                    SCREEN_HEIGHT - BUTTON_BOTTOM_MARGIN
                ),
                (BUTTON_WIDTH, BUTTON_HEIGHT)
            ),
            text="Quitter la partie",
            manager=manager,
            object_id="#quit_button"
        ),
        "score_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    LABEL_LEFT_MARGIN,
                    BUTTON_BETWEEN_MARGIN + 100
                ),
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
                    LABEL_HEIGHT + ((3 / 2) * BUTTON_BETWEEN_MARGIN) + 100
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
                    2 * (LABEL_HEIGHT + BUTTON_BETWEEN_MARGIN) + 100
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="losses_label",
            manager=manager,
            object_id="#losses_label"
        ),
        "forfeits_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    LABEL_LEFT_MARGIN,
                    3 * (LABEL_HEIGHT + BUTTON_BETWEEN_MARGIN) - (BUTTON_BETWEEN_MARGIN // 2) + 100
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
                    4 * (LABEL_HEIGHT + BUTTON_BETWEEN_MARGIN) - (BUTTON_BETWEEN_MARGIN // 2) + 90
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="games_played_label",
            manager=manager,
            object_id="#games_played_label"
        ),
        "opponent_score_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH - LABEL_LEFT_MARGIN - LABEL_WIDTH,
                    BUTTON_BETWEEN_MARGIN + 100
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="",
            manager=manager,
            object_id="#opponent_score_label"
        ),
        "opponent_wins_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH - LABEL_LEFT_MARGIN - LABEL_WIDTH,
                    LABEL_HEIGHT + ((3 / 2) * BUTTON_BETWEEN_MARGIN) + 100
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="",
            manager=manager,
            object_id="#opponent_wins_label"
        ),
        "opponent_losses_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH - LABEL_LEFT_MARGIN - LABEL_WIDTH,
                    2 * (LABEL_HEIGHT + BUTTON_BETWEEN_MARGIN) + 100
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="",
            manager=manager,
            object_id="#opponent_losses_label"
        ),
        "opponent_forfeits_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH - LABEL_LEFT_MARGIN - LABEL_WIDTH,
                    3 * (LABEL_HEIGHT + BUTTON_BETWEEN_MARGIN) - (BUTTON_BETWEEN_MARGIN // 2) + 100
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="",
            manager=manager,
            object_id="#opponent_losses_label"
        ),
        "opponent_games_played_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (
                    SCREEN_WIDTH - LABEL_LEFT_MARGIN - LABEL_WIDTH,
                    4 * (LABEL_HEIGHT + BUTTON_BETWEEN_MARGIN) - (BUTTON_BETWEEN_MARGIN // 2) + 90
                ),
                (LABEL_WIDTH, LABEL_HEIGHT)
            ),
            text="",
            manager=manager,
            object_id="#opponent_games_played_label"
        ),
        "instruction_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (SCREEN_WIDTH - LABEL_LEFT_MARGIN - LABEL_WIDTH, 10),
                (LABEL_WIDTH, 30)
            ),
            text="",
            manager=manager,
            object_id="#instruction_label_on_game_page"
        ),
        "captures_label": pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (10, SCREEN_HEIGHT // 2 + 30),
                (LABEL_WIDTH, 30)
            ),
            text="Captures: 0",
            manager=manager,
            object_id="#captures_label_on_game_page"
        ),
    }


def print_board(board_param):
    print("  " + " ".join(f"{x + 1:2}" for x in range(19)))

    for y in range(19):
        # Afficher le numéro de ligne suivi de la ligne elle-même
        print(f"{y + 1:2} " + "  ".join(board_param[y * 19:(y + 1) * 19]))


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
            print(f"type: {response_json.get('type')}")
            print(f"status: {response_json.get('status')}")
            print(f"opponent_info: \n")
            print(response_json.get("opponent_info"))
            print_board(response_json.get("board"))
        else:
            print(json.dumps(response_json, indent=4))

        response_type = response_json.get("type")
        # Traiter la réponse en fonction du type de message
        if response_type in ("auth_response", "new_account_response"):
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
        elif response_type == "quit_game_response":
            return handle_quit_game_response(
                response_json,
                current_page_elements,
                manager
            )
        elif response_type in ("move_response", "new_board_state"):
            return handle_move_response(
                response_json,
                current_page_elements,
                response_type
            )
        elif response_type == "game_over":
            return handle_game_over_response(
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
    game_button_id = game_json.get("id", None)
    game_button_name = game_json.get("name", None)
    game_button_players = game_json.get("players", None)
    game_button_status = game_json.get("status", None)  # waiting 0 / ongoing 1

    if None in [game_button_id, game_button_name, game_button_players, game_button_status]:
        return None

    button_text = (
            add_padding(f"N°{index + 1}", total_length=7) +
            add_padding(f"Name: {game_button_name}", total_length=20) +
            add_padding(f"Status: {'waiting' if game_button_status == 0 else 'ongoing'}") +
            add_padding(f"Players: {', '.join(game_button_players)}", total_length=30)
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
        object_id=f"#button_game_{game_button_id}"
    )


def return_to_lobby(current_page_elements, manager):
    clear_page(current_page_elements)
    lobby_page_elements = create_gui_elements_lobby_page(manager)
    display_player_stats(lobby_page_elements)
    return True, lobby_page_elements, handle_events_on_lobby_page


def handle_quit_game_response(response_json, current_page_elements, manager):
    global is_grid_visible, is_board_visible, is_host, board

    response_status = response_json.get("status", None)
    if (
            response_status is None or
            not response_status == RESPONSE_SUCCESS_STATUS
    ):
        return return_to_lobby(current_page_elements, manager)

    is_grid_visible = False
    is_board_visible = False
    is_host = False
    board = ""

    play_audio(FORFEIT_SOUND_PATH)
    update_player_stats(response_json.get("player_stats", {}))

    return return_to_lobby(current_page_elements, manager)


def handle_move_response(response_json, current_page_elements, response_type):
    global board, is_my_turn

    response_status = response_json.get("status", None)
    response_board = response_json.get("board_state", None)
    if (
            response_status is None or
            response_board is None or
            not response_status == RESPONSE_SUCCESS_STATUS
    ):
        current_page_elements["error_label"].set_text("Placement invalide ou pas votre tour.")
        play_audio(MOVE_FAILED_PATH)
        return True, current_page_elements, handle_events_on_game_page

    current_page_elements["error_label"].set_text("")

    # Compare the number of captures to determine if a capture has been made
    print("Comparing captures")
    print(current_page_elements["captures_label"])
    previous_captures = int(current_page_elements["captures_label"].text.split(":")[1].strip())
    new_captures = response_json.get("captures", 0)
    if new_captures > previous_captures:
        play_audio(CAPTURE_SOUND_PATH)
        current_page_elements["captures_label"].set_text(f"Captures: {new_captures}")

    if response_type == "move_response":
        current_page_elements["instruction_label"].set_text(f"Attendez que {opponent_name} joue.")
    else:
        current_page_elements["instruction_label"].set_text(f"À vous de jouer, {player_name} !")

    is_my_turn = not is_my_turn
    board = response_board
    print_board(board)

    return True, current_page_elements, handle_events_on_game_page


def update_player_stats(player_stats):
    global score, wins, losses, games_played, forfeits

    score = player_stats.get("score", 0)
    wins = player_stats.get("wins", 0)
    losses = player_stats.get("losses", 0)
    games_played = player_stats.get("games_played", 0)
    forfeits = player_stats.get("forfeits", 0)


def handle_game_over_response(response_json, current_page_elements, manager):
    global is_board_visible, is_grid_visible, board, is_host
    response_status = response_json.get("status", None)

    if response_status is None:
        is_running, next_page_element, next_page_handler = return_to_lobby(current_page_elements, manager)
        next_page_element["error_label"].set_text("Une erreur est survenue, partie finie.")
        return is_running, next_page_element, next_page_handler

    temp_board = response_json.get("board", "")
    if temp_board != "":
        board = temp_board
        print_board(board)

    if response_status == VICTORY_STATUS:
        current_page_elements["instruction_label"].set_text("Vous avez gagné la partie!")
        play_audio(VICTORY_SOUND_PATH)
    elif response_status == DEFEAT_STATUS:
        current_page_elements["instruction_label"].set_text("Vous avez perdu la partie !")
        play_audio(DEFEAT_SOUND_PATH)
    elif response_status == WITHDRAW_STATUS:
        current_page_elements["instruction_label"].set_text("Vous avez abandoné la partie!")

    player_stat = response_json.get("player_stats", None)
    if player_stat is None:
        is_board_visible = False
        is_grid_visible = False
        display_player_stats(current_page_elements)
        return return_to_lobby(current_page_elements, manager)

    update_player_stats(player_stat)

    print("Fin de la partie")
    is_grid_visible = False
    is_board_visible = False
    is_host = False
    return return_to_lobby(current_page_elements, manager)


def handle_alert_start_game(response_json, current_page_elements, manager):
    global is_board_visible, is_grid_visible, board, opponent_name, is_my_turn

    response_status = response_json.get("status", None)
    if (
            response_status is None or
            not response_status == RESPONSE_SUCCESS_STATUS
    ):
        return return_to_lobby(current_page_elements, manager)

    response_board = response_json.get("board", None)
    if response_board is None:
        return return_to_lobby(current_page_elements, manager)

    board = response_board
    is_board_visible = True
    is_grid_visible = True

    opponent_info = response_json.get("opponent_info", None)
    if opponent_info is None:
        return return_to_lobby(current_page_elements, manager)

    opponent_name = opponent_info.get("name", "Nom inconnu")

    current_page_elements["title_label"].set_text(response_json.get("game_name", "Nom inconnu"))
    current_page_elements["player1_label"].set_text(player_name)
    current_page_elements["player2_label"].set_text(opponent_info.get("name", "Nom inconnu"))

    if not is_host:
        opponent_pion_logo = draw_pion(
            HOST_PION_LOGO_X,
            HOST_PION_LOGO_Y,
            HOST_PION_LOGO_WIDTH,
            HOST_PION_LOGO_HEIGHT,
            PION_IMAGE_OPPONENT,
            manager
        )
        host_pion_logo = draw_pion(
            OPPONENT_PION_LOGO_X,
            OPPONENT_PION_LOGO_Y,
            OPPONENT_PION_LOGO_WIDTH,
            OPPONENT_PION_LOGO_HEIGHT,
            PION_IMAGE_HOST,
            manager
        )
        current_page_elements["host_pion_logo"] = host_pion_logo
        current_page_elements["oppenent_pion_logo"] = opponent_pion_logo
        current_page_elements["instruction_label"].set_text(f"À vous de jouer, {player_name} !")
        is_my_turn = not is_my_turn
        play_audio(START_GAME_OPPONENT_SOUND_PATH)
    else:
        opponent_pion_logo = draw_pion(
            OPPONENT_PION_LOGO_X,
            OPPONENT_PION_LOGO_Y,
            OPPONENT_PION_LOGO_WIDTH,
            OPPONENT_PION_LOGO_HEIGHT,
            PION_IMAGE_OPPONENT,
            manager
        )
        current_page_elements["oppenent_pion_logo"] = opponent_pion_logo
        current_page_elements["instruction_label"].set_text(f"Attendez que {opponent_name} joue.")
        play_audio(START_GAME_HOST_SOUND_PATH)

    display_player_stats(current_page_elements)
    display_opponent_stats(current_page_elements, opponent_info)

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
    global is_grid_visible, is_host, game_name, player_name

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
    game_page_elements["player1_label"].set_text(f"{player_name}")
    display_player_stats(game_page_elements)

    game_name = response_json.get("game", {}).get("name", "")

    is_grid_visible = True
    is_host = True

    host_pion_logo = draw_pion(
        HOST_PION_LOGO_X,
        HOST_PION_LOGO_Y,
        HOST_PION_LOGO_WIDTH,
        HOST_PION_LOGO_HEIGHT,
        PION_IMAGE_HOST,
        manager
    )
    game_page_elements["host_pion_logo"] = host_pion_logo

    return True, game_page_elements, handle_events_on_game_page


def handle_get_lobby_response(response_json, current_page_elements, manager):
    response_status = response_json.get("status", None)

    if response_status is None or not response_status == RESPONSE_SUCCESS_STATUS:
        current_page_elements["error_label"].set_text("Erreur lors de la récupération des parties.")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    game_list = response_json.get("games", [])
    if not game_list:
        if "game_buttons" in current_page_elements:
            for button in current_page_elements["game_buttons"]:
                button.kill()

        current_page_elements["error_label"].set_text("Aucune partie disponible.")
        return True, current_page_elements, handle_events_on_lobby_page

    # Supprimer l'ancienne liste de boutons si elle existe quand on vient d'une autre page
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


def set_stat_label(page_elements, label_prefix, stats):
    """
    Met à jour les labels de statistiques pour un joueur ou un adversaire.

    Args:
        page_elements (dict) : Dictionnaire des éléments de la page.
        label_prefix (str) : Préfixe pour différencier les labels (ex : "opponent_" ou "").
        stats (dict) : Dictionnaire contenant les statistiques à afficher.
    """
    page_elements[f"{label_prefix}score_label"].set_text(f"Score: {stats.get('score', 'Unknown')}")
    page_elements[f"{label_prefix}wins_label"].set_text(f"Victoires: {stats.get('wins', 'Unknown')}")
    page_elements[f"{label_prefix}losses_label"].set_text(f"Défaites: {stats.get('losses', 'Unknown')}")
    page_elements[f"{label_prefix}forfeits_label"].set_text(f"Forfaits: {stats.get('forfeits', 'Unknown')}")
    page_elements[f"{label_prefix}games_played_label"].set_text(
        f"Parties jouées: {stats.get('games_played', 'Unknown')}")


def display_player_stats(page_elements):
    player_stats = {
        "score": score,
        "wins": wins,
        "losses": losses,
        "forfeits": forfeits,
        "games_played": games_played,
    }
    set_stat_label(page_elements, "", player_stats)


def display_opponent_stats(page_elements, opponent_stats):
    opponent_stats_dict = {
        "score": opponent_stats["score"],
        "wins": opponent_stats["wins"],
        "losses": opponent_stats["losses"],
        "forfeits": opponent_stats["forfeits"],
        "games_played": opponent_stats["games_played"],
    }
    set_stat_label(page_elements, "opponent_", opponent_stats_dict)


def handle_auth_response(response_json, current_page_elements, manager, user_socket):
    global score, wins, losses, forfeits, games_played, player_name

    response_status = response_json.get("status", None)

    if response_status is None or not response_status == RESPONSE_SUCCESS_STATUS:
        player_name = ""
        current_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe incorrect !")
        play_audio(ERROR_SOUND_PATH)
        return response_status is not None, current_page_elements, handle_events_on_login_page

    clear_page(current_page_elements)
    lobby_page_elements = create_gui_elements_lobby_page(manager)

    update_sound_button(lobby_page_elements["sound_button"], sound_enabled)

    # Afficher les informations du JSON
    player_stats = response_json.get("player_stats", {})
    score = player_stats.get("score", 0)
    wins = player_stats.get("wins", 0)
    losses = player_stats.get("losses", 0)
    forfeits = player_stats.get("forfeits", 0)
    games_played = player_stats.get("games_played", 0)
    display_player_stats(lobby_page_elements)

    play_audio(LOBBY_ENTRY_SOUND_PATH)

    send_json(user_socket, create_get_lobby_json())

    return True, lobby_page_elements, handle_events_on_lobby_page


def handle_login_event(login_page_elements, user_socket):
    global player_name
    username = login_page_elements["username_entry"].get_text()
    password = login_page_elements["password_entry"].get_text()

    if not username or not password:
        print("Nom d'utilisateur ou mot de passe vide !")
        login_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe vide !")
        play_audio(ERROR_SOUND_PATH)
        return

    print(f"Tentative de connexion : {username}, {password}")
    json_authencation_message = create_auth_json(username, password)

    if not json_authencation_message:
        print("Erreur lors de la création du message.")
        return

    player_name = username

    send_json(user_socket, json_authencation_message)


def handle_create_new_account_event(new_account_page_elements, user_socket):
    global player_name

    username = new_account_page_elements["username_entry"].get_text()
    password = new_account_page_elements["password_entry"].get_text()
    conf_password = new_account_page_elements["conf_password_entry"].get_text()

    if not username or not password:
        new_account_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe vide !")
        play_audio(ERROR_SOUND_PATH)
        return

    if len(password) < 12:
        new_account_page_elements["error_label"].set_text("Le mot de passe doit contenir au moins 12 caractères.")
        play_audio(ERROR_SOUND_PATH)
        return

    if password != conf_password:
        new_account_page_elements["error_label"].set_text("Les mots de passe ne correspondent pas.")
        play_audio(ERROR_SOUND_PATH)
        return

    print(f"Tentative de création de compte : {username}, {password}")
    json_new_account_message = create_new_account_json(username, password, conf_password)

    if not json_new_account_message:
        print("Erreur lors de la création du message.")
        return

    player_name = username

    send_json(user_socket, json_new_account_message)


def handle_create_new_game_event(new_game_page_elements, user_socket):
    local_game_name = new_game_page_elements["game_name_entry"].get_text()

    if not local_game_name:
        new_game_page_elements["error_label"].set_text("Veuillez donner un nom à la partie")
        return

    if len(local_game_name) >= 20:
        new_game_page_elements["error_label"].set_text("Maximum 20 caractères")
        return

    print(f"Tentative de création de la partie : {local_game_name}")
    json_new_game_message = create_new_game_json(local_game_name)
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
                clear_page(new_game_page_elements)
                lobby_page_elements = create_gui_elements_lobby_page(manager)
                display_player_stats(lobby_page_elements)
                send_json(user_socket, create_get_lobby_json())
                return True, lobby_page_elements, handle_events_on_lobby_page

        manager.process_events(event)
    return True, new_game_page_elements, handle_events_on_create_new_game_page


def get_grid_coordinates(x, y):
    # Ajustement avec les décalages
    adjusted_x = x - MARGIN_X
    adjusted_y = y - MARGIN_Y

    # Vérifie si le clic est dans la zone étendue avec tolérance
    if not (
            -TOLERANCE <= adjusted_x <= GRID_DIMENSIONS + TOLERANCE and
            -TOLERANCE <= adjusted_y <= GRID_DIMENSIONS + TOLERANCE
    ):
        return -1, -1

    # Calcul des indices de la grille
    col = round(adjusted_x / CELL_SIZE)
    row = round(adjusted_y / CELL_SIZE)

    # Vérifie si les indices sont dans les limites de la grille
    if not (0 <= col < GRID_COLS and 0 <= row < GRID_ROWS):
        return -1, -1

    return col, row


def handle_events_on_game_page(manager, page_game_elements, user_socket):
    global is_grid_visible, is_board_visible, is_host
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, None, None

        elif event.type == pygame.MOUSEBUTTONDOWN:
            col, row = get_grid_coordinates(*event.pos)

            if (col, row) != (-1, -1):
                print("Placement du pion")
                send_json(user_socket, create_play_move_json(col, row))
            elif page_game_elements["quit_button"].get_relative_rect().collidepoint(event.pos):
                print("Abandon de la partie")
                send_json(user_socket, create_quit_game_json())
            else:
                print("Clic en dehors de la grille.")
                page_game_elements["error_label"].set_text("Clic en dehors de la grille.")

        manager.process_events(event)

    return True, page_game_elements, handle_events_on_game_page


def handle_events_on_lobby_page(manager, lobby_page_elements, user_socket):
    global sound_enabled
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

            elif event.ui_element == lobby_page_elements["refresh_button"]:
                print("Rafraichissement des parties")
                send_json(user_socket, create_get_lobby_json())

            elif event.ui_element == lobby_page_elements["disconnect_button"]:
                print("Déconnexion.")
                send_json(user_socket, create_deconnection_json())

            elif event.ui_element == lobby_page_elements["sound_button"]:
                sound_enabled = toggle_sound(sound_enabled)
                update_sound_button(lobby_page_elements["sound_button"], sound_enabled)

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

            if is_grid_visible:
                draw_grid(SCREEN)

            if is_board_visible:
                draw_board()

            pygame.display.update()
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        print("Fermeture de la connexion.")
        user_socket.close()
        pygame.quit()


if __name__ == "__main__":
    main()
