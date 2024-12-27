import json
import re
from typing import Callable, Dict, Tuple

import pygame
import pygame_gui
from pygame_gui.elements import UIImage

from classes.AudioManager import AudioManager
from classes.GUIElementsManager import GUIElementsManager
from classes.RequestManager import RequestManager

# pdoc: format de la documentation
__docformat__: str = "google"

# Configuration du serveur
SERVER_INFO: dict[str, str | int] = {
    "host": "127.0.0.1",
    "port": 55555
}

# Messages du protocole de communication
SERVER_RESPONSES: dict[str, str] = {
    "auth": "auth_response",
    "new_account": "new_account_response",
    "disconnect": "disconnect_ack",
    "get_lobby": "get_lobby_response",
    "create_game": "create_game_response",
    "join_game": "join_game_response",
    "alert_start_game": "alert_start_game",
    "quit_game": "quit_game_response",
    "move": "move_response",
    "new_board": "new_board_state",
    "game_over": "game_over"
}

# Chemin des fichiers audio
AUDIO_PATHS: dict[str, str] = {
    "background_music": "assets/audio/background-music.mp3",
    "error_sound": "assets/audio/login-error.wav",
    "lobby_entry_sound": "assets/audio/lobby-entry.mp3",
    "start_game_opponent_sound": "assets/audio/starting-game-opponent.mp3",
    "start_game_host_sound": "assets/audio/starting-game-host.mp3",
    "move_failed": "assets/audio/move-fail.wav",
    "victory_sound": "assets/audio/victory.mp3",
    "defeat_sound": "assets/audio/defeat.mp3",
    "capture_sound": "assets/audio/capture.mp3",
    "forfeit_sound": "assets/audio/forfeit.mp3"
}

# Longueur minimale du mot de passes et du nom de la partie
MIN_LENGTHS: dict[str, int] = {
    "game_name": 20,
    "password": 12
}

# Status de la réponse (JSON)
RESPONSE_STATUS: dict[str, int] = {
    "fail": 0,
    "success": 1
}

# Status de fin de partie
GAME_OVER_STATUS: dict[str, int] = {
    "victory": 0,
    "defeat": 1,
    "withdraw": 2
}

# Regex's
REGEX_CAPTURE_GAME_NAME: str = r"Name:\s*(.*?)\s*Status:"

# Facteur de durée pour chaque tic en millisecondes
TICK_DURATION_FACTOR: float = 1000.0

# Statistiques du joueur connecté
score: int = 0
wins: int = 0
losses: int = 0
forfeits: int = 0
games_played: int = 0

# Afficher le plateau de jeu
is_grid_visible: bool = False
is_board_visible: bool = False

# Info de la partie
game_name: str = ""
player_name: str = ""
opponent_name: str = ""
captures: int = 0
is_host: bool = False
is_my_turn: bool = False

# Initialisation de l'interface graphique
gui_elements_manager: GUIElementsManager = GUIElementsManager()

# Gestion des requêtes JSON
request_manager: RequestManager = RequestManager(SERVER_INFO.get("host"), SERVER_INFO.get("port"))

# Gestion du son
audio_manager: AudioManager = AudioManager()


def handle_server_response(
        current_page_elements: dict[str, pygame_gui.elements],
        current_event_handler: callable(dict[str, pygame_gui.elements])
) -> Tuple[
    bool,
    dict[str, pygame_gui.elements],
    Callable[
        [
            Dict[str, str | int | list],
            Dict[str, pygame_gui.elements]
        ],
        Tuple[bool, Dict[str, pygame_gui.elements], Callable]
    ]
]:
    """
    Gère les réponses du serveur et les associe aux gestionnaires de réponses appropriés.

    Args :
        current_page_elements (dict): Éléments de l'état actuel de la page.
        current_event_handler (callable): Gestionnaire d'événements actuel.

    Returns :
        tuple: (bool, current_page_elements, current_event_handler)
    """
    try:
        if not request_manager.is_socket_ready():
            # Si le socket n'est pas prête, on retourne l'état actuel.
            return True, current_page_elements, current_event_handler

        # Tentative de réception de la réponse JSON
        response_json = request_manager.receive_json()

        # Récupérer le type de réponse avec un accès sécurisé
        response_type = response_json.get("type")
        if not response_type:
            # Si le type de réponse est manquant ou invalide
            return True, current_page_elements, current_event_handler

        # Alias de type pour simplifier les annotations
        respons_json_type = Dict[str, str | int | list]
        page_elements_type = Dict[str, pygame_gui.elements]
        handle_return_type = Tuple[bool, page_elements_type, Callable]

        handler_type = Callable[[respons_json_type, page_elements_type], handle_return_type]

        # Association du type de réponse avec les gestionnaires
        handlers_map: Dict[str, handler_type] = {
            SERVER_RESPONSES.get("auth"): handle_auth_response,
            SERVER_RESPONSES.get("new_account"): handle_auth_response,
            SERVER_RESPONSES.get("disconnect"): handle_disconnect_ack_response,
            SERVER_RESPONSES.get("get_lobby"): handle_get_lobby_response,
            SERVER_RESPONSES.get("create_game"): handle_create_game_response,
            SERVER_RESPONSES.get("join_game"): handle_join_game_response,
            SERVER_RESPONSES.get("alert_start_game"): handle_alert_start_game,
            SERVER_RESPONSES.get("quit_game"): handle_quit_game_response,
            SERVER_RESPONSES.get("move"): handle_move_response,
            SERVER_RESPONSES.get("new_board"): handle_move_response,
            SERVER_RESPONSES.get("game_over"): handle_game_over_response,
        }

        # Trouver et invoquer le gestionnaire approprié
        handler = handlers_map.get(response_type)
        if handler:
            return handler(response_json, current_page_elements)

        # Cas par défaut si le type de réponse est non reconnu
        return True, current_page_elements, current_event_handler


    except BlockingIOError as bioe:
        print(f"Le socket est temporairement indisponible. Nouvelle tentative. {bioe}")
        return True, current_page_elements, current_event_handler


    except json.JSONDecodeError as jde:
        print(f"Erreur lors du décodage de la réponse JSON : {jde}")
        raise RuntimeError("Décodage JSON échoué.") from jde


    except ConnectionError as ce:
        print(f"Erreur de connexion, tentative de reconnexion : {ce}")
        raise RuntimeError("Erreur de connexion détectée.") from ce


def return_to_lobby(
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    gui_elements_manager.clear_page(current_page_elements)
    lobby_page_elements = gui_elements_manager.create_gui_elements_lobby_page()
    display_player_stats(lobby_page_elements)

    return True, lobby_page_elements, handle_events_on_lobby_page


def reset_game_info() -> None:
    global is_grid_visible, is_board_visible, is_host, is_my_turn, game_name, player_name, opponent_name, captures

    is_grid_visible = False
    is_board_visible = False
    is_host = False
    is_my_turn = False
    game_name = ""
    player_name = ""
    opponent_name = ""
    captures = 0


def handle_quit_game_response(
        response_json: json,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    global is_grid_visible, is_board_visible, is_host, is_my_turn

    response_status = response_json.get("status", None)
    if (
            response_status is None or
            not response_status == RESPONSE_STATUS.get("success")
    ):
        return return_to_lobby(current_page_elements)

    reset_game_info()

    audio_manager.play_audio(AUDIO_PATHS.get("forfeit_sound"))
    update_player_stats(response_json.get("player_stats", {}))

    return return_to_lobby(current_page_elements)


def handle_move_response(
        response_json: dict,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère la réponse après un mouvement dans le jeu.

    Args:
        response_json (dict): La réponse JSON contenant l'état de la partie.
        current_page_elements (dict): Les éléments GUI de la page actuelle.

    Returns:
        tuple: (bool, éléments GUI mis à jour, gestionnaire d'événements suivant).
    """
    # Variables globales (à réviser si possible)
    global is_my_turn, captures

    # Récupération des données de la réponse
    response_status = response_json.get("status")
    response_board = response_json.get("board_state")

    # Vérification de l'état de la réponse
    if response_status != RESPONSE_STATUS.get("success") or response_board is None:
        current_page_elements.get("error_label").set_text(
            "Placement invalide ou pas votre tour."
        )
        audio_manager.play_audio(AUDIO_PATHS.get("move_failed"))
        return True, current_page_elements, handle_events_on_game_page

    # Réinitialisation du message d'erreur si succès
    current_page_elements.get("error_label").set_text("")

    # Gestion des captures
    response_captures = response_json.get("captures", 0)
    if response_captures > captures:
        current_page_elements.get("captures_label").set_text(
            f"Captures: {response_captures}"
        )
        audio_manager.play_audio(AUDIO_PATHS.get("capture_sound"))
        captures = response_captures

    # Mise à jour de l'instruction
    instruction_text = (
        f"Attendez que {opponent_name} joue."
        if response_json.get("status", "") == SERVER_RESPONSES.get("move_response")
        else f"À vous de jouer, {player_name} !"
    )
    current_page_elements.get("instruction_label").set_text(instruction_text)

    # Mise à jour du tour et de l'état du plateau
    is_my_turn = not is_my_turn
    gui_elements_manager.board = response_board

    # Retour des valeurs mises à jour
    return True, current_page_elements, handle_events_on_game_page


def update_player_stats(player_stats: json) -> None:
    global score, wins, losses, games_played, forfeits

    score = player_stats.get("score", 0)
    wins = player_stats.get("wins", 0)
    losses = player_stats.get("losses", 0)
    games_played = player_stats.get("games_played", 0)
    forfeits = player_stats.get("forfeits", 0)


def handle_game_over_response(
        response_json: json,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    global is_board_visible, is_grid_visible, is_host, is_my_turn
    response_status = response_json.get("status", None)

    if response_status is None:
        is_running, next_page_element, next_page_handler = return_to_lobby(current_page_elements)
        next_page_element["error_label"].set_text("Une erreur est survenue, partie finie.")
        return is_running, next_page_element, next_page_handler

    if response_status == GAME_OVER_STATUS.get("victory"):
        current_page_elements["instruction_label"].set_text("Vous avez gagné la partie!")
        audio_manager.play_audio(AUDIO_PATHS.get("victory_sound"))
    elif response_status == GAME_OVER_STATUS.get("defeat"):
        current_page_elements["instruction_label"].set_text("Vous avez perdu la partie !")
        audio_manager.play_audio(AUDIO_PATHS.get("defeat_sound"))
    elif response_status == GAME_OVER_STATUS.get("withdraw"):
        current_page_elements["instruction_label"].set_text("Vous avez abandoné la partie!")

    reset_game_info()

    player_stat = response_json.get("player_stats", None)
    if player_stat is None:
        display_player_stats(current_page_elements)
        return return_to_lobby(current_page_elements)

    update_player_stats(player_stat)

    print("Fin de la partie")
    return return_to_lobby(current_page_elements)


def handle_alert_start_game(
        response_json: json,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    global is_board_visible, is_grid_visible, opponent_name, is_my_turn

    response_status = response_json.get("status", None)
    if (
            response_status is None or
            not response_status == RESPONSE_STATUS.get("success")
    ):
        return return_to_lobby(current_page_elements)

    response_board: str = response_json.get("board", None)
    if response_board is None:
        return return_to_lobby(current_page_elements)

    gui_elements_manager.board = response_board
    is_board_visible = True
    is_grid_visible = True

    opponent_info = response_json.get("opponent_info", None)
    if opponent_info is None:
        return return_to_lobby(current_page_elements)

    opponent_name = opponent_info.get("name", "Nom inconnu")

    current_page_elements["title_label"].set_text(response_json.get("game_name", "Nom inconnu"))
    current_page_elements["player1_label"].set_text(player_name)
    current_page_elements["player2_label"].set_text(opponent_info.get("name", "Nom inconnu"))

    if not is_host:
        current_page_elements["host_pion_logo"]: UIImage = gui_elements_manager.draw_host_pion_logo()
        current_page_elements["oppenent_pion_logo"]: UIImage = gui_elements_manager.draw_opponent_pion_logo()
        current_page_elements["instruction_label"].set_text(f"À vous de jouer, {player_name} !")
        is_my_turn = not is_my_turn
        audio_manager.play_audio(AUDIO_PATHS.get("start_game_opponent_sound"))
    else:
        current_page_elements["oppenent_pion_logo"] = gui_elements_manager.draw_opponent_pion_logo()
        current_page_elements["instruction_label"].set_text(f"Attendez que {opponent_name} joue.")
        audio_manager.play_audio(AUDIO_PATHS.get("start_game_host_sound"))

    display_player_stats(current_page_elements)
    display_opponent_stats(current_page_elements, opponent_info)

    return True, current_page_elements, handle_events_on_game_page


def handle_join_game_response(
        response_json: json,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    response_status = response_json.get("status", None)

    if (
            response_status is None or
            not response_status == RESPONSE_STATUS.get("success")
    ):
        current_page_elements["error_label"].set_text("Partie complète ou impossible à rejoindre.")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    gui_elements_manager.clear_page(current_page_elements)
    game_page_elements = gui_elements_manager.create_gui_elements_game_page()
    request_manager.send_ready_to_play_message()

    return True, game_page_elements, handle_events_on_game_page


def handle_create_game_response(
        response_json: json,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    global is_grid_visible, is_host, game_name, player_name

    response_status = response_json.get("status", None)
    if (
            response_status is None or
            not response_status == RESPONSE_STATUS.get("success")
    ):
        current_page_elements["error_label"].set_text("Une partie contenant ce nom existe déjà.")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    gui_elements_manager.clear_page(current_page_elements)
    game_page_elements = gui_elements_manager.create_gui_elements_game_page()
    game_page_elements["title_label"].set_text("En attente d'un autre joueur...")
    game_page_elements["player1_label"].set_text(f"{player_name}")
    display_player_stats(game_page_elements)

    game_name = response_json.get("game", {}).get("name", "")

    is_grid_visible = True
    is_host = True

    host_pion_logo = gui_elements_manager.draw_host_pion_logo()
    game_page_elements["host_pion_logo"] = host_pion_logo

    return True, game_page_elements, handle_events_on_game_page


def handle_get_lobby_response(
        response_json: json,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    response_status = response_json.get("status", None)

    if response_status is None or not response_status == RESPONSE_STATUS.get("success"):
        current_page_elements["error_label"].set_text("Erreur lors de la récupération des parties.")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    display_player_stats(current_page_elements)
    display_total_activer_players(response_json.get("total_active_players", 0), current_page_elements)

    game_list = response_json.get("games", [])
    if not game_list:
        if "game_buttons" in current_page_elements:
            for button in current_page_elements["game_buttons"]:
                button.kill()

        current_page_elements["error_label"].set_text("Aucune partie disponible.")
        return True, current_page_elements, handle_events_on_lobby_page

    # Supprimer l'ancienne liste de boutons si elle existe quand on vient d'une autre page
    gui_elements_manager.clear_page(current_page_elements)
    current_page_elements = gui_elements_manager.create_gui_elements_lobby_page()

    # Ajouter les nouveaux boutons dans un tableau
    buttons = []
    for index, game_json in enumerate(game_list):
        button = gui_elements_manager.create_gui_join_game_button_element(game_json, index)
        if button:
            buttons.append(button)

    # Stocker le tableau des boutons dans current_page_elements
    buttons.reverse()

    current_page_elements["game_buttons"] = buttons

    return True, current_page_elements, handle_events_on_lobby_page


def handle_disconnect_ack_response(
        response_json: json,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    response_status: str = response_json.get("status", None)

    if response_status is None or not response_status == RESPONSE_STATUS.get("success"):
        current_page_elements["error_label"].set_text("Déconnexion échouée !")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    print(current_page_elements)
    gui_elements_manager.clear_page(current_page_elements)
    login_page_elements = gui_elements_manager.create_gui_elements_login_page()

    return True, login_page_elements, handle_events_on_login_page


def set_stat_label(
        page_elements: dict[str, pygame_gui.elements],
        label_prefix: str,
        stats: json
) -> None:
    """
    Met à jour les labels de statistiques pour un joueur ou un adversaire.

    Args:
        page_elements (dict[str, pygame_gui.elements]) : Dictionnaire des éléments de la page.
        label_prefix (str) : Préfixe pour différencier les labels (ex : "opponent_" ou "").
        stats (json) : Dictionnaire contenant les statistiques à afficher.
    """
    page_elements[f"{label_prefix}score_label"].set_text(f"Score: {stats.get('score', 'Unknown')}")
    page_elements[f"{label_prefix}wins_label"].set_text(f"Victoires: {stats.get('wins', 'Unknown')}")
    page_elements[f"{label_prefix}losses_label"].set_text(f"Défaites: {stats.get('losses', 'Unknown')}")
    page_elements[f"{label_prefix}forfeits_label"].set_text(f"Forfaits: {stats.get('forfeits', 'Unknown')}")
    page_elements[f"{label_prefix}games_played_label"].set_text(
        f"Parties jouées: {stats.get('games_played', 'Unknown')}")


def display_total_activer_players(
        total_active_players: int,
        page_elements: dict[str, pygame_gui.elements]
) -> None:
    page_elements["total_active_players_label"].set_text(f"Joueurs actifs: {total_active_players}")


def display_player_stats(page_elements: dict[str, pygame_gui.elements]) -> None:
    set_stat_label(
        page_elements,
        "",
        {
            "score": score,
            "wins": wins,
            "losses": losses,
            "forfeits": forfeits,
            "games_played": games_played,
        }
    )


def display_opponent_stats(
        page_elements: dict[str, pygame_gui.elements],
        opponent_stats: json
) -> None:
    set_stat_label(
        page_elements,
        "opponent_",
        {
            "score": opponent_stats.get("score", 0),
            "wins": opponent_stats.get("wins", 0),
            "losses": opponent_stats.get("losses", 0),
            "forfeits": opponent_stats.get("forfeits", 0),
            "games_played": opponent_stats.get("games_played", 0)
        }
    )


def handle_auth_response(
        response_json: json,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    global score, wins, losses, forfeits, games_played, player_name

    response_status = response_json.get("status", None)

    if response_status is None or not response_status == RESPONSE_STATUS.get("success"):
        player_name = ""
        current_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe incorrect !")
        audio_manager.play_audio(AUDIO_PATHS.get("error_sound"))
        return response_status is not None, current_page_elements, handle_events_on_login_page

    gui_elements_manager.clear_page(current_page_elements)
    lobby_page_elements = gui_elements_manager.create_gui_elements_lobby_page()

    audio_manager.update_sound_button(lobby_page_elements["sound_button"])

    # Afficher les informations du JSON
    player_stats = response_json.get("player_stats", {})
    score = player_stats.get("score", 0)
    wins = player_stats.get("wins", 0)
    losses = player_stats.get("losses", 0)
    forfeits = player_stats.get("forfeits", 0)
    games_played = player_stats.get("games_played", 0)
    display_player_stats(lobby_page_elements)

    audio_manager.play_audio(AUDIO_PATHS.get("lobby_entry_sound"))

    request_manager.send_get_lobby_json()

    return True, lobby_page_elements, handle_events_on_lobby_page


def handle_login_event(login_page_elements: dict[str, pygame_gui.elements]) -> None:
    global player_name
    username: str = login_page_elements["username_entry"].get_text()
    password: str = login_page_elements["password_entry"].get_text()

    if not username or not password:
        print("Nom d'utilisateur ou mot de passe vide !")
        login_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe vide !")
        audio_manager.play_audio(AUDIO_PATHS.get("error_sound"))
        return

    print(f"Tentative de connexion : {username}, {password}")

    player_name = username

    request_manager.send_auth_json(username, password)


def handle_create_new_account_event(new_account_page_elements: dict[str, pygame_gui.elements]) -> None:
    global player_name

    username: str = new_account_page_elements["username_entry"].get_text()
    password: str = new_account_page_elements["password_entry"].get_text()
    conf_password: str = new_account_page_elements["conf_password_entry"].get_text()

    if not username or not password:
        new_account_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe vide !")
        audio_manager.play_audio(AUDIO_PATHS.get("error_sound"))
        return

    if len(password) < MIN_LENGTHS.get("password"):
        new_account_page_elements["error_label"].set_text("Le mot de passe doit contenir au moins 12 caractères.")
        audio_manager.play_audio(AUDIO_PATHS.get("error_sound"))
        return

    if password != conf_password:
        new_account_page_elements["error_label"].set_text("Les mots de passe ne correspondent pas.")
        audio_manager.play_audio(AUDIO_PATHS.get("error_sound"))
        return

    print(f"Tentative de création de compte : {username}, {password}")

    player_name = username

    request_manager.send_new_account_json(username, password, conf_password)


def handle_create_new_game_event(new_game_page_elements: dict[str, pygame_gui.elements]) -> None:
    local_game_name: str = new_game_page_elements["game_name_entry"].get_text()

    if not local_game_name:
        new_game_page_elements["error_label"].set_text("Veuillez donner un nom à la partie")
        return

    if len(local_game_name) >= MIN_LENGTHS.get("game_name"):
        new_game_page_elements["error_label"].set_text("Maximum 20 caractères")
        return

    print(f"Tentative de création de la partie : {local_game_name}")

    request_manager.send_new_game_json(local_game_name)


def handle_events_on_create_new_game_page(
        new_game_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, new_game_page_elements, handle_events_on_create_new_game_page

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == new_game_page_elements["create_new_game_button"]:
                print("Création de la partie")
                handle_create_new_game_event(new_game_page_elements)

            elif event.ui_element == new_game_page_elements["back_button"]:
                print("Retour au lobby")
                gui_elements_manager.clear_page(new_game_page_elements)
                lobby_page_elements = gui_elements_manager.create_gui_elements_lobby_page()
                display_player_stats(lobby_page_elements)
                request_manager.send_get_lobby_json()
                return True, lobby_page_elements, handle_events_on_lobby_page

        gui_elements_manager.process_events_manager(event)
    return True, new_game_page_elements, handle_events_on_create_new_game_page


def handle_events_on_game_page(
        page_game_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    global is_grid_visible, is_board_visible, is_host
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, page_game_elements, handle_events_on_game_page

        elif event.type == pygame.MOUSEBUTTONDOWN:
            col, row = gui_elements_manager.get_grid_coordinates(*event.pos)

            if is_my_turn and (col, row) != (-1, -1):
                print("Placement du pion")
                request_manager.send_play_move_json(col, row)
            elif page_game_elements["quit_button"].get_relative_rect().collidepoint(event.pos):
                print("Abandon de la partie")
                request_manager.send_quit_game_json()
            else:
                print("Clic en dehors de la grille.")
                page_game_elements["error_label"].set_text("Clic en dehors de la grille.")

        gui_elements_manager.process_events_manager(event)

    return True, page_game_elements, handle_events_on_game_page


def handle_events_on_lobby_page(
        lobby_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, lobby_page_elements, handle_events_on_lobby_page

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == lobby_page_elements["create_game_button"]:
                print("Création d'une partie.")
                gui_elements_manager.clear_page(lobby_page_elements)
                create_new_game_elements = gui_elements_manager.create_gui_elements_create_game_page()
                return True, create_new_game_elements, handle_events_on_create_new_game_page

            elif (
                    "game_buttons" in lobby_page_elements and
                    event.ui_element in lobby_page_elements["game_buttons"]
            ):
                clicked_button_index = lobby_page_elements["game_buttons"].index(event.ui_element)
                button_text = lobby_page_elements["game_buttons"][clicked_button_index].text
                match = re.search(REGEX_CAPTURE_GAME_NAME, button_text)
                request_manager.send_join_game_json(match.group(1))

            elif event.ui_element == lobby_page_elements["refresh_button"]:
                print("Rafraichissement des parties")
                request_manager.send_get_lobby_json()

            elif event.ui_element == lobby_page_elements["disconnect_button"]:
                print("Déconnexion.")
                request_manager.send_deconnection_json()

            elif event.ui_element == lobby_page_elements["sound_button"]:
                audio_manager.toggle_sound()
                audio_manager.update_sound_button(lobby_page_elements["sound_button"])

        gui_elements_manager.process_events_manager(event)

    return True, lobby_page_elements, handle_events_on_lobby_page


def handle_events_on_new_account_page(
        create_account_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, create_account_elements, handle_events_on_new_account_page

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                handle_create_new_account_event(create_account_elements)
            else:
                create_account_elements["error_label"].set_text("")

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == create_account_elements["create_button"]:
                handle_create_new_account_event(create_account_elements)

            elif event.ui_element == create_account_elements["back_button"]:
                gui_elements_manager.clear_page(create_account_elements)
                login_page_elements = gui_elements_manager.create_gui_elements_login_page()
                return True, login_page_elements, handle_events_on_login_page

        gui_elements_manager.process_events_manager(event)

    return True, create_account_elements, handle_events_on_new_account_page


# Fonction pour gérer les événements
def handle_events_on_login_page(
        login_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, login_page_elements, handle_events_on_login_page

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                handle_login_event(login_page_elements)
            else:
                login_page_elements["error_label"].set_text("")

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == login_page_elements["login_button"]:
                handle_login_event(login_page_elements)

            elif event.ui_element == login_page_elements["create_account_button"]:
                gui_elements_manager.clear_page(login_page_elements)
                create_account_elements = gui_elements_manager.create_gui_elements_new_account_page()
                return True, create_account_elements, handle_events_on_new_account_page

        elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            login_page_elements["error_label"].set_text("")

        gui_elements_manager.process_events_manager(event)

    return True, login_page_elements, handle_events_on_login_page


def main():
    global request_manager

    # Initialisation de la musique de fond
    audio_manager.play_music(AUDIO_PATHS.get("background_music"), 1, 5000, True)

    # Initialtion de l'horloge
    clock = pygame.time.Clock()

    # Initialisation de la condition de boucle
    is_running = True

    try:
        current_page_elements = gui_elements_manager.create_gui_elements_login_page()
        current_event_handler = handle_events_on_login_page

        while is_running:
            frame_per_second = clock.tick(60) / TICK_DURATION_FACTOR

            # Handle events and update the current page elements and event handler
            # based on the current event handler's return values
            (
                is_current_handler_running,
                current_page_elements,
                current_event_handler
            ) = current_event_handler(current_page_elements)

            (
                is_server_running,
                current_page_elements,
                current_event_handler
            ) = handle_server_response(
                current_page_elements,
                current_event_handler
            )

            is_running = is_current_handler_running and is_server_running

            gui_elements_manager.update_manager(frame_per_second)
            gui_elements_manager.blit_background()
            gui_elements_manager.draw_ui()

            if is_grid_visible:
                gui_elements_manager.draw_grid()

            if is_board_visible:
                gui_elements_manager.draw_board()

            gui_elements_manager.update_display()
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        print("Fermeture de la connexion.")
        del request_manager
        pygame.quit()


if __name__ == "__main__":
    main()
