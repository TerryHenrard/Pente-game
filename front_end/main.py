import json
import re
from typing import Callable, Dict, Tuple

import pygame
import pygame_gui

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

# Images par secondes (FPS)
FPS: int = 60

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
        current_page_elements: Dict[str, "pygame_gui.elements"]
) -> Tuple[bool, Dict[str, "pygame_gui.elements"], Callable]:
    """
    Réinitialise les éléments de l'interface utilisateur (GUI) de la page actuelle
    et configure ceux de la page du lobby.

    Args:
        current_page_elements (Dict[str, pygame_gui.elements]):
            Un dictionnaire contenant les éléments GUI de la page actuelle.

    Returns:
        Tuple[bool, Dict[str, pygame_gui.elements], Callable]:
            - Un booléen indiquant si l'opération a réussi.
            - Un dictionnaire contenant les éléments GUI de la page du lobby.
            - Une fonction à appeler pour gérer les événements sur la page du lobby.
    """
    # Supprime les éléments GUI de la page actuelle.
    gui_elements_manager.clear_page(current_page_elements)

    # Crée les nouveaux éléments GUI pour la page du lobby.
    lobby_page_elements = gui_elements_manager.create_gui_elements_lobby_page()

    # Affiche les statistiques des joueurs dans les éléments du lobby.
    display_player_stats(lobby_page_elements)

    # Retourne les résultats avec succès.
    return True, lobby_page_elements, handle_events_on_lobby_page


def reset_game_info() -> None:
    """
    Réinitialise toutes les informations de jeu globales à leurs valeurs par défaut.
    """
    global is_grid_visible, is_board_visible, is_host, is_my_turn
    global game_name, player_name, opponent_name, captures

    # Rend la grille et le plateau invisibles.
    is_grid_visible = False
    is_board_visible = False

    # Indique que le joueur n'est pas l'hôte et que ce n'est pas son tour.
    is_host = False
    is_my_turn = False

    # Réinitialise les noms des parties et des joueurs à des chaînes vides.
    game_name = ""
    player_name = ""
    opponent_name = ""

    # Réinitialise le compteur de captures à zéro.
    captures = 0


def handle_quit_game_response(
        response_json: json,
        current_page_elements: dict[str, "pygame_gui.elements"]
) -> tuple[bool, dict[str, "pygame_gui.elements"], callable]:
    """
    Gère la réponse lorsqu'un joueur quitte la partie.

    Args:
        response_json (json): La réponse JSON contenant les informations sur l'état de la demande.
        current_page_elements (dict[str, pygame_gui.elements]):
            Un dictionnaire des éléments GUI de la page actuelle.

    Returns:
        tuple[bool, dict[str, pygame_gui.elements], callable]:
            - Un booléen indiquant si le retour au lobby a réussi.
            - Un dictionnaire des éléments GUI pour la page du lobby.
            - Une fonction à appeler pour gérer les événements sur la page du lobby.
    """
    global is_grid_visible, is_board_visible, is_host, is_my_turn

    # Vérifie le statut de la réponse pour déterminer si l'opération a réussi.
    response_status = response_json.get("status", None)
    if (
            response_status is None or
            response_status != RESPONSE_STATUS.get("success")
    ):
        # En cas d'échec, retourne au lobby sans modifier les données du jeu.
        return return_to_lobby(current_page_elements)

    # Réinitialise les informations de jeu globales.
    reset_game_info()

    # Joue un son spécifique pour indiquer l'abandon.
    audio_manager.play_audio(AUDIO_PATHS.get("forfeit_sound"))

    # Met à jour les statistiques du joueur avec les données fournies.
    update_player_stats(response_json.get("player_stats", {}))

    # Retourne au lobby après avoir appliqué les mises à jour nécessaires.
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


def update_player_stats(player_stats: dict) -> None:
    """
    Met à jour les statistiques du joueur à partir des données fournies.

    Args:
        player_stats (dict): Un dictionnaire contenant les statistiques du joueur.
    """
    global score, wins, losses, games_played, forfeits

    # Mise à jour des statistiques avec des valeurs par défaut en cas de données manquantes.
    score = player_stats.get("score", 0)
    wins = player_stats.get("wins", 0)
    losses = player_stats.get("losses", 0)
    games_played = player_stats.get("games_played", 0)
    forfeits = player_stats.get("forfeits", 0)


def handle_game_over_response(
        response_json: dict,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère la réponse de fin de partie et met à jour l'interface utilisateur en fonction du statut de la partie.

    Args:
        response_json (dict): Un dictionnaire contenant les informations sur la fin de la partie.
        current_page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page actuelle.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page suivante.
            - callable : La fonction de gestion pour la page suivante.
    """
    response_status = response_json.get("status")

    # Si le statut est absent, retour au lobby avec un message d'erreur.
    if response_status is None:
        is_running, next_page_element, next_page_handler = return_to_lobby(current_page_elements)
        next_page_element["error_label"].set_text("Une erreur est survenue, partie finie.")
        return is_running, next_page_element, next_page_handler

    # Mise à jour des éléments de l'interface utilisateur en fonction du statut de la partie.
    if response_status == GAME_OVER_STATUS.get("victory"):
        current_page_elements["instruction_label"].set_text("Vous avez gagné la partie!")
        audio_manager.play_audio(AUDIO_PATHS.get("victory_sound"))
    elif response_status == GAME_OVER_STATUS.get("defeat"):
        current_page_elements["instruction_label"].set_text("Vous avez perdu la partie!")
        audio_manager.play_audio(AUDIO_PATHS.get("defeat_sound"))
    elif response_status == GAME_OVER_STATUS.get("withdraw"):
        current_page_elements["instruction_label"].set_text("Vous avez abandonné la partie!")

    # Réinitialisation des informations liées à la partie.
    reset_game_info()

    # Récupération et mise à jour des statistiques du joueur.
    player_stat = response_json.get("player_stats")
    if player_stat is None:
        # Si les statistiques du joueur sont absentes, affiche les statistiques par défaut.
        display_player_stats(current_page_elements)
        return return_to_lobby(current_page_elements)

    # Mise à jour des statistiques du joueur si elles sont disponibles.
    update_player_stats(player_stat)

    # Retour au lobby avec les éléments mis à jour.
    return return_to_lobby(current_page_elements)


def handle_alert_start_game(
        response_json: dict,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère la réponse d'alerte pour le début de la partie et met à jour l'interface utilisateur.

    Args:
        response_json (dict): Un dictionnaire contenant les informations sur la partie (statut, plateau, adversaire, etc.).
        current_page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page actuelle.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page actuelle.
            - callable : La fonction de gestion des événements pour la page de jeu.
    """
    global is_board_visible, is_grid_visible, opponent_name, is_my_turn

    # Vérification du statut de la réponse.
    response_status = response_json.get("status")
    if response_status is None or response_status != RESPONSE_STATUS.get("success"):
        return return_to_lobby(current_page_elements)

    # Vérification et récupération du plateau de jeu.
    response_board = response_json.get("board")
    if response_board is None:
        return return_to_lobby(current_page_elements)

    # Mise à jour du plateau et visibilité.
    gui_elements_manager.board = response_board
    is_board_visible = True
    is_grid_visible = True

    # Vérification et récupération des informations sur l'adversaire.
    opponent_info = response_json.get("opponent_info")
    if opponent_info is None:
        return return_to_lobby(current_page_elements)

    opponent_name = opponent_info.get("name", "Nom inconnu")

    # Mise à jour des labels de la page avec les informations du jeu et des joueurs.
    current_page_elements["title_label"].set_text(response_json.get("game_name", "Nom inconnu"))
    current_page_elements["player1_label"].set_text(player_name)
    current_page_elements["player2_label"].set_text(opponent_info.get("name", "Nom inconnu"))

    # Mise à jour des éléments spécifiques en fonction de l'hôte ou du joueur invité.
    if not is_host:
        current_page_elements["host_pion_logo"] = gui_elements_manager.draw_host_pion_logo()
        current_page_elements["oppenent_pion_logo"] = gui_elements_manager.draw_opponent_pion_logo()
        current_page_elements["instruction_label"].set_text(f"À vous de jouer, {player_name} !")
        is_my_turn = not is_my_turn
        audio_manager.play_audio(AUDIO_PATHS.get("start_game_opponent_sound"))
    else:
        current_page_elements["oppenent_pion_logo"] = gui_elements_manager.draw_opponent_pion_logo()
        current_page_elements["instruction_label"].set_text(f"Attendez que {opponent_name} joue.")
        audio_manager.play_audio(AUDIO_PATHS.get("start_game_host_sound"))

    # Affichage des statistiques du joueur et de l'adversaire.
    display_player_stats(current_page_elements)
    display_opponent_stats(current_page_elements, opponent_info)

    # Retourne les éléments mis à jour et la fonction de gestion des événements pour la page de jeu.
    return True, current_page_elements, handle_events_on_game_page


def handle_join_game_response(
        response_json: dict,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère la réponse de tentative de rejoindre une partie et met à jour l'interface utilisateur en conséquence.

    Args:
        response_json (dict): Un dictionnaire contenant les informations sur la tentative de rejoindre une partie.
        current_page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page actuelle.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page suivante.
            - callable : La fonction de gestion des événements pour la page suivante.
    """
    # Récupération du statut de la réponse.
    response_status = response_json.get("status")

    # Vérifie si le statut est invalide ou indique un échec.
    if response_status is None or response_status != RESPONSE_STATUS.get("success"):
        current_page_elements["error_label"].set_text("Partie complète ou impossible à rejoindre.")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    # Effacement des éléments actuels de la page et création des éléments pour la page de jeu.
    gui_elements_manager.clear_page(current_page_elements)
    game_page_elements = gui_elements_manager.create_gui_elements_game_page()

    # Envoi d'un message indiquant que le joueur est prêt à jouer.
    request_manager.send_ready_to_play_message()

    # Retourne les nouveaux éléments de la page de jeu et la fonction de gestion correspondante.
    return True, game_page_elements, handle_events_on_game_page


def handle_create_game_response(
        response_json: dict,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère la réponse pour la création d'une partie et met à jour l'interface utilisateur.

    Args:
        response_json (dict): Un dictionnaire contenant les informations sur la tentative de création de partie.
        current_page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page actuelle.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page suivante.
            - callable : La fonction de gestion des événements pour la page suivante.
    """
    global is_grid_visible, is_host, game_name, player_name

    # Récupération et vérification du statut de la réponse.
    response_status = response_json.get("status")
    if response_status is None or response_status != RESPONSE_STATUS.get("success"):
        # Affiche un message d'erreur si la création de la partie échoue.
        current_page_elements["error_label"].set_text("Une partie contenant ce nom existe déjà.")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    # Efface les éléments actuels de la page et configure les nouveaux éléments pour la page de jeu.
    gui_elements_manager.clear_page(current_page_elements)
    game_page_elements = gui_elements_manager.create_gui_elements_game_page()

    # Mise à jour des labels et affichage des statistiques du joueur.
    game_page_elements["title_label"].set_text("En attente d'un autre joueur...")
    game_page_elements["player1_label"].set_text(f"{player_name}")
    display_player_stats(game_page_elements)

    # Récupération du nom de la partie depuis la réponse.
    game_name = response_json.get("game", {}).get("name", "")

    # Configuration du joueur en tant qu'hôte et affichage de la grille.
    is_grid_visible = True
    is_host = True

    # Dessine le logo de pion pour l'hôte et l'ajoute aux éléments de la page de jeu.
    host_pion_logo = gui_elements_manager.draw_host_pion_logo()
    game_page_elements["host_pion_logo"] = host_pion_logo

    # Retourne les nouveaux éléments de la page de jeu et la fonction de gestion correspondante.
    return True, game_page_elements, handle_events_on_game_page


def handle_get_lobby_response(
        response_json: dict,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère la réponse pour la récupération de la liste des parties dans le lobby.

    Args:
        response_json (dict): Un dictionnaire contenant les informations sur les parties disponibles et les joueurs actifs.
        current_page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page actuelle.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour le lobby.
            - callable : La fonction de gestion des événements pour la page du lobby.
    """
    # Vérification du statut de la réponse.
    response_status = response_json.get("status")
    if response_status is None or response_status != RESPONSE_STATUS.get("success"):
        # Affiche un message d'erreur si la récupération des parties échoue.
        current_page_elements["error_label"].set_text("Erreur lors de la récupération des parties.")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    # Affichage des statistiques du joueur et du nombre total de joueurs actifs.
    total_active_players = response_json.get("total_active_players", 0)
    display_total_activer_players(total_active_players, current_page_elements)

    # Récupération de la liste des parties disponibles.
    game_list = response_json.get("games", [])
    if not game_list:
        # Supprime les boutons existants, s'ils sont présents.
        if "game_buttons" in current_page_elements:
            for button in current_page_elements["game_buttons"]:
                button.kill()

        # Affiche un message indiquant qu'aucune partie n'est disponible.
        current_page_elements["error_label"].set_text("Aucune partie disponible.")
        return True, current_page_elements, handle_events_on_lobby_page

    # Efface les anciens éléments de la page et configure les nouveaux pour le lobby.
    gui_elements_manager.clear_page(current_page_elements)
    current_page_elements = gui_elements_manager.create_gui_elements_lobby_page()
    display_player_stats(current_page_elements)

    # Création des boutons pour chaque partie disponible.
    buttons = []
    for index, game_json in enumerate(game_list):
        button = gui_elements_manager.create_gui_join_game_button_element(game_json, index)
        if button:
            buttons.append(button)

    # Stocke les boutons dans l'élément de la page et les affiche dans l'ordre inverse.
    buttons.reverse()
    current_page_elements["game_buttons"] = buttons

    # Retourne les éléments mis à jour et la fonction de gestion correspondante.
    return True, current_page_elements, handle_events_on_lobby_page


def handle_disconnect_ack_response(
        response_json: dict,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère la réponse pour l'accusé de réception de la déconnexion et met à jour l'interface utilisateur.

    Args:
        response_json (dict): Un dictionnaire contenant le statut de la déconnexion.
        current_page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page actuelle.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page de connexion.
            - callable : La fonction de gestion des événements pour la page de connexion.
    """
    # Récupération et vérification du statut de la réponse.
    response_status = response_json.get("status")
    if response_status is None or response_status != RESPONSE_STATUS.get("success"):
        # Affiche un message d'erreur si la déconnexion échoue.
        current_page_elements["error_label"].set_text("Déconnexion échouée !")
        return response_status is not None, current_page_elements, handle_events_on_lobby_page

    # Efface les éléments actuels de la page.
    gui_elements_manager.clear_page(current_page_elements)

    # Création des éléments pour la page de connexion.
    login_page_elements = gui_elements_manager.create_gui_elements_login_page()

    # Retourne les nouveaux éléments de la page de connexion et la fonction de gestion correspondante.
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
    """
    Affiche le nombre total de joueurs actifs dans l'interface utilisateur.

    Args:
        total_active_players (int): Le nombre total de joueurs actifs.
        page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page actuelle.

    Returns:
        None
    """
    # Met à jour le texte de l'étiquette pour afficher le nombre de joueurs actifs.
    page_elements["total_active_players_label"].set_text(f"Joueurs actifs : {total_active_players}")


def display_player_stats(page_elements: dict[str, pygame_gui.elements]) -> None:
    """
    Affiche les statistiques du joueur dans l'interface utilisateur.

    Args:
        page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page actuelle.

    Returns:
        None
    """
    # Met à jour les étiquettes des statistiques du joueur avec les données actuelles.
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
        opponent_stats: dict
) -> None:
    """
    Affiche les statistiques de l'adversaire dans l'interface utilisateur.

    Args:
        page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page actuelle.
        opponent_stats (dict): Un dictionnaire contenant les statistiques de l'adversaire.

    Returns:
        None
    """
    # Met à jour les étiquettes des statistiques de l'adversaire avec les données fournies.
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
        response_json: dict,
        current_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère la réponse d'authentification et met à jour l'interface utilisateur en fonction du résultat.

    Args:
        response_json (dict): Un dictionnaire contenant le statut d'authentification et les statistiques du joueur.
        current_page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page actuelle.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page suivante (lobby ou connexion).
            - callable : La fonction de gestion des événements pour la page suivante.
    """
    global score, wins, losses, forfeits, games_played, player_name

    # Vérification du statut de la réponse.
    response_status = response_json.get("status")
    if response_status is None or response_status != RESPONSE_STATUS.get("success"):
        # Réinitialise le nom du joueur et affiche un message d'erreur en cas d'échec.
        player_name = ""
        current_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe incorrect !")
        audio_manager.play_audio(AUDIO_PATHS.get("error_sound"))
        return response_status is not None, current_page_elements, handle_events_on_login_page

    # Efface les éléments actuels de la page et configure les nouveaux éléments pour le lobby.
    gui_elements_manager.clear_page(current_page_elements)
    lobby_page_elements = gui_elements_manager.create_gui_elements_lobby_page()

    # Met à jour le bouton de gestion des sons dans la nouvelle page.
    audio_manager.update_sound_button(lobby_page_elements["sound_button"])

    # Récupère les statistiques du joueur depuis le JSON et les affiche.
    player_stats = response_json.get("player_stats", {})
    score = player_stats.get("score", 0)
    wins = player_stats.get("wins", 0)
    losses = player_stats.get("losses", 0)
    forfeits = player_stats.get("forfeits", 0)
    games_played = player_stats.get("games_played", 0)
    display_player_stats(lobby_page_elements)

    # Joue un son d'entrée dans le lobby.
    audio_manager.play_audio(AUDIO_PATHS.get("lobby_entry_sound"))

    # Envoie une requête pour récupérer les données du lobby.
    request_manager.send_get_lobby_json()

    # Retourne les éléments du lobby et la fonction de gestion des événements correspondante.
    return True, lobby_page_elements, handle_events_on_lobby_page


def handle_login_event(login_page_elements: dict[str, pygame_gui.elements]) -> None:
    """
    Gère l'événement de tentative de connexion en récupérant les informations saisies par l'utilisateur.

    Args:
        login_page_elements (dict[str, pygame_gui.elements]): Les éléments de l'interface utilisateur de la page de connexion.

    Returns:
        None
    """
    global player_name

    # Récupère les informations d'identification saisies par l'utilisateur.
    username: str = login_page_elements["username_entry"].get_text()
    password: str = login_page_elements["password_entry"].get_text()

    # Vérifie si le nom d'utilisateur ou le mot de passe est vide.
    if not username or not password:
        login_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe vide !")
        audio_manager.play_audio(AUDIO_PATHS.get("error_sound"))
        return

    # Mise à jour du nom du joueur et affichage d'une tentative de connexion.
    player_name = username
    print(f"Tentative de connexion : {username}, {password}")

    # Envoie les informations d'authentification au serveur.
    request_manager.send_auth_json(username, password)


def handle_create_new_account_event(new_account_page_elements: dict[str, pygame_gui.elements]) -> None:
    """
    Gère l'événement de création d'un nouveau compte en vérifiant les entrées utilisateur
    et en envoyant une requête pour créer le compte.

    Args:
        new_account_page_elements (dict[str, pygame_gui.elements]):
            Les éléments de l'interface utilisateur pour la page de création de compte.

    Returns:
        None
    """
    global player_name

    # Récupération des valeurs des champs de texte.
    username: str = new_account_page_elements["username_entry"].get_text()
    password: str = new_account_page_elements["password_entry"].get_text()
    conf_password: str = new_account_page_elements["conf_password_entry"].get_text()

    # Vérification des champs vides.
    if not username or not password:
        new_account_page_elements["error_label"].set_text("Nom d'utilisateur ou mot de passe vide !")
        audio_manager.play_audio(AUDIO_PATHS.get("error_sound"))
        return

    # Vérification de la longueur minimale du mot de passe.
    if len(password) < MIN_LENGTHS.get("password", 12):  # Valeur par défaut pour éviter une erreur.
        new_account_page_elements["error_label"].set_text("Le mot de passe doit contenir au moins 12 caractères.")
        audio_manager.play_audio(AUDIO_PATHS.get("error_sound"))
        return

    # Vérification de la correspondance des mots de passe.
    if password != conf_password:
        new_account_page_elements["error_label"].set_text("Les mots de passe ne correspondent pas.")
        audio_manager.play_audio(AUDIO_PATHS.get("error_sound"))
        return

    # Affichage de la tentative dans la console (pour le débogage).
    print(f"Tentative de création de compte : {username}")

    # Mise à jour du nom du joueur global.
    player_name = username

    # Envoi des informations pour créer un nouveau compte.
    request_manager.send_new_account_json(username, password, conf_password)


def handle_create_new_game_event(new_game_page_elements: dict[str, pygame_gui.elements]) -> None:
    """
    Gère l'événement de création d'une nouvelle partie en vérifiant le nom de la partie
    et en envoyant une requête pour la créer.

    Args:
        new_game_page_elements (dict[str, pygame_gui.elements]):
            Les éléments de l'interface utilisateur pour la page de création de partie.

    Returns:
        None
    """
    # Récupération du nom de la partie depuis le champ de texte.
    local_game_name: str = new_game_page_elements["game_name_entry"].get_text()

    # Vérification si le champ est vide.
    if not local_game_name:
        new_game_page_elements["error_label"].set_text("Veuillez donner un nom à la partie.")
        return

    # Vérification de la longueur maximale du nom de la partie.
    max_length = MIN_LENGTHS.get("game_name", 20)  # Valeur par défaut pour éviter une erreur.
    if len(local_game_name) > max_length:
        new_game_page_elements["error_label"].set_text(
            f"Le nom de la partie ne peut pas dépasser {max_length} caractères.")
        return

    # Affichage de la tentative dans la console (pour le débogage).
    print(f"Tentative de création de la partie : {local_game_name}")

    # Envoi des informations pour créer une nouvelle partie.
    request_manager.send_new_game_json(local_game_name)


def handle_events_on_create_new_game_page(
        new_game_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère les événements de la page de création de nouvelle partie et met à jour l'interface utilisateur en conséquence.

    Args:
        new_game_page_elements (dict[str, pygame_gui.elements]):
            Les éléments de l'interface utilisateur pour la page de création de partie.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page en cours ou la page suivante.
            - callable : La fonction de gestion des événements pour la page en cours ou la page suivante.
    """
    # Parcourt les événements pygame en cours.
    for event in pygame.event.get():
        # Vérifie si l'utilisateur ferme l'application.
        if event.type == pygame.QUIT:
            return False, new_game_page_elements, handle_events_on_create_new_game_page

        # Gère les clics sur les boutons de l'interface utilisateur.
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            # Bouton "Créer une nouvelle partie".
            if event.ui_element == new_game_page_elements["create_new_game_button"]:
                print("Création de la partie en cours")
                handle_create_new_game_event(new_game_page_elements)

            # Bouton "Retour" vers le lobby.
            elif event.ui_element == new_game_page_elements["back_button"]:
                print("Retour au lobby")
                gui_elements_manager.clear_page(new_game_page_elements)
                lobby_page_elements = gui_elements_manager.create_gui_elements_lobby_page()
                display_player_stats(lobby_page_elements)
                request_manager.send_get_lobby_json()
                return True, lobby_page_elements, handle_events_on_lobby_page

        # Passe l'événement au gestionnaire d'événements GUI.
        gui_elements_manager.process_events_manager(event)

    # Retourne les éléments de la page actuelle si aucun changement de page n'est requis.
    return True, new_game_page_elements, handle_events_on_create_new_game_page


def handle_events_on_game_page(
        page_game_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère les événements de la page de jeu et met à jour l'état ou l'interface utilisateur en conséquence.

    Args:
        page_game_elements (dict[str, pygame_gui.elements]):
            Les éléments de l'interface utilisateur pour la page de jeu.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page de jeu.
            - callable : La fonction de gestion des événements pour la page de jeu.
    """
    global is_grid_visible, is_board_visible, is_host

    # Parcourt les événements pygame.
    for event in pygame.event.get():
        # Vérifie si l'utilisateur ferme l'application.
        if event.type == pygame.QUIT:
            return False, page_game_elements, handle_events_on_game_page

        # Gère les clics de la souris.
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Obtient les coordonnées de la grille à partir de la position du clic.
            col, row = gui_elements_manager.get_grid_coordinates(*event.pos)

            # Si c'est au tour du joueur et que le clic est dans la grille.
            if is_my_turn and (col, row) != (-1, -1):
                print("Placement du pion")
                request_manager.send_play_move_json(col, row)

            # Si le bouton "Quitter" est cliqué.
            elif page_game_elements["quit_button"].get_relative_rect().collidepoint(event.pos):
                print("Abandon de la partie")
                request_manager.send_quit_game_json()

            # Si le clic est en dehors de la grille.
            else:
                print("Clic en dehors de la grille.")
                page_game_elements["error_label"].set_text("Clic en dehors de la grille.")

        # Passe l'événement au gestionnaire d'événements GUI.
        gui_elements_manager.process_events_manager(event)

    # Retourne les éléments actuels de la page de jeu et la fonction de gestion des événements.
    return True, page_game_elements, handle_events_on_game_page


def handle_events_on_lobby_page(
        lobby_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère les événements sur la page du lobby et met à jour l'état ou l'interface utilisateur en conséquence.

    Args:
        lobby_page_elements (dict[str, pygame_gui.elements]):
            Les éléments de l'interface utilisateur pour la page du lobby.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page en cours ou une nouvelle page.
            - callable : La fonction de gestion des événements pour la page active ou une nouvelle page.
    """
    # Parcourt les événements pygame.
    for event in pygame.event.get():
        # Vérifie si l'utilisateur ferme l'application.
        if event.type == pygame.QUIT:
            return False, lobby_page_elements, handle_events_on_lobby_page

        # Gère les clics sur les boutons de l'interface utilisateur.
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            # Bouton pour créer une nouvelle partie.
            if event.ui_element == lobby_page_elements["create_game_button"]:
                print("Création d'une partie.")
                gui_elements_manager.clear_page(lobby_page_elements)
                create_new_game_elements = gui_elements_manager.create_gui_elements_create_game_page()
                return True, create_new_game_elements, handle_events_on_create_new_game_page

            # Boutons des parties disponibles.
            elif (
                    "game_buttons" in lobby_page_elements and
                    event.ui_element in lobby_page_elements["game_buttons"]
            ):
                clicked_button_index = lobby_page_elements["game_buttons"].index(event.ui_element)
                button_text = lobby_page_elements["game_buttons"][clicked_button_index].text
                match = re.search(REGEX_CAPTURE_GAME_NAME, button_text)
                if match:
                    local_game_name = match.group(1)
                    print(f"Rejoindre la partie : {local_game_name}")
                    request_manager.send_join_game_json(local_game_name)

            # Bouton pour rafraîchir la liste des parties.
            elif event.ui_element == lobby_page_elements["refresh_button"]:
                print("Rafraîchissement des parties.")
                request_manager.send_get_lobby_json()

            # Bouton pour se déconnecter.
            elif event.ui_element == lobby_page_elements["disconnect_button"]:
                print("Déconnexion.")
                request_manager.send_deconnection_json()

            # Bouton pour activer/désactiver le son.
            elif event.ui_element == lobby_page_elements["sound_button"]:
                audio_manager.toggle_sound()
                audio_manager.update_sound_button(lobby_page_elements["sound_button"])

        # Passe l'événement au gestionnaire d'événements GUI.
        gui_elements_manager.process_events_manager(event)

    # Retourne les éléments actuels de la page du lobby et la fonction de gestion des événements.
    return True, lobby_page_elements, handle_events_on_lobby_page


def handle_events_on_new_account_page(
        create_account_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère les événements sur la page de création d'un nouveau compte et met à jour l'interface utilisateur en conséquence.

    Args:
        create_account_elements (dict[str, pygame_gui.elements]):
            Les éléments de l'interface utilisateur pour la page de création de compte.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page en cours ou une nouvelle page.
            - callable : La fonction de gestion des événements pour la page active ou une nouvelle page.
    """
    # Parcourt les événements pygame.
    for event in pygame.event.get():
        # Vérifie si l'utilisateur ferme l'application.
        if event.type == pygame.QUIT:
            return False, create_account_elements, handle_events_on_new_account_page

        # Gère les événements clavier.
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Soumission du formulaire avec la touche "Entrée".
                handle_create_new_account_event(create_account_elements)
            else:
                # Efface les messages d'erreur au moindre changement.
                create_account_elements["error_label"].set_text("")

        # Gère les clics sur les boutons de l'interface utilisateur.
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            # Bouton pour créer un nouveau compte.
            if event.ui_element == create_account_elements["create_button"]:
                handle_create_new_account_event(create_account_elements)

            # Bouton pour revenir à la page de connexion.
            elif event.ui_element == create_account_elements["back_button"]:
                gui_elements_manager.clear_page(create_account_elements)
                login_page_elements = gui_elements_manager.create_gui_elements_login_page()
                return True, login_page_elements, handle_events_on_login_page

        # Passe l'événement au gestionnaire d'événements GUI.
        gui_elements_manager.process_events_manager(event)

    # Retourne les éléments actuels de la page de création de compte et la fonction de gestion des événements.
    return True, create_account_elements, handle_events_on_new_account_page


def handle_events_on_login_page(
        login_page_elements: dict[str, pygame_gui.elements]
) -> tuple[bool, dict[str, pygame_gui.elements], callable]:
    """
    Gère les événements sur la page de connexion et met à jour l'interface utilisateur en conséquence.

    Args:
        login_page_elements (dict[str, pygame_gui.elements]):
            Les éléments de l'interface utilisateur pour la page de connexion.

    Returns:
        tuple:
            - bool : Indique si l'application doit continuer à fonctionner.
            - dict[str, pygame_gui.elements] : Les éléments mis à jour pour la page en cours ou une nouvelle page.
            - callable : La fonction de gestion des événements pour la page active ou une nouvelle page.
    """
    # Parcourt les événements pygame.
    for event in pygame.event.get():
        # Vérifie si l'utilisateur ferme l'application.
        if event.type == pygame.QUIT:
            return False, login_page_elements, handle_events_on_login_page

        # Gère les événements clavier.
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Soumission du formulaire avec la touche "Entrée".
                handle_login_event(login_page_elements)
            else:
                # Efface les messages d'erreur au moindre changement.
                login_page_elements["error_label"].set_text("")

        # Gère les clics sur les boutons de l'interface utilisateur.
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            # Bouton pour se connecter.
            if event.ui_element == login_page_elements["login_button"]:
                handle_login_event(login_page_elements)

            # Bouton pour accéder à la création d'un nouveau compte.
            elif event.ui_element == login_page_elements["create_account_button"]:
                gui_elements_manager.clear_page(login_page_elements)
                create_account_elements = gui_elements_manager.create_gui_elements_new_account_page()
                return True, create_account_elements, handle_events_on_new_account_page

        # Gère les modifications dans les champs de texte.
        elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            # Efface les messages d'erreur si un champ de texte est modifié.
            login_page_elements["error_label"].set_text("")

        # Passe l'événement au gestionnaire d'événements GUI.
        gui_elements_manager.process_events_manager(event)

    # Retourne les éléments actuels de la page de connexion et la fonction de gestion des événements.
    return True, login_page_elements, handle_events_on_login_page


def main() -> None:
    """
    Point d'entrée principal de l'application.
    Gère l'initialisation, la boucle principale,
    et la fermeture de l'application.

    Returns:
        None
    """
    global request_manager

    # Initialisation de la musique de fond.
    audio_manager.play_music(AUDIO_PATHS.get("background_music"), 1, 5000, True)

    # Initialisation de l'horloge.
    clock = pygame.time.Clock()

    # Initialisation de la condition de boucle.
    is_running = True

    try:
        # Création des éléments pour la page de connexion.
        current_page_elements = gui_elements_manager.create_gui_elements_login_page()
        current_event_handler = handle_events_on_login_page

        # Boucle principale.
        while is_running:
            # Limite la boucle à X FPS et calcule la durée du tick.
            frame_per_second = clock.tick(FPS) / TICK_DURATION_FACTOR

            # Gestion des événements et mise à jour des éléments et gestionnaires.
            (
                is_current_handler_running,
                current_page_elements,
                current_event_handler
            ) = current_event_handler(current_page_elements)

            # Gestion des réponses du serveur.
            (
                is_server_running,
                current_page_elements,
                current_event_handler
            ) = handle_server_response(
                current_page_elements,
                current_event_handler
            )

            # Mise à jour de la condition de fonctionnement.
            is_running = is_current_handler_running and is_server_running

            # Mise à jour de l'interface graphique.
            gui_elements_manager.update_manager(frame_per_second)
            gui_elements_manager.blit_background()
            gui_elements_manager.draw_ui()

            # Dessin de la grille si elle est visible.
            if is_grid_visible:
                gui_elements_manager.draw_grid()

            # Dessin du plateau si visible.
            if is_board_visible:
                gui_elements_manager.draw_board()

            # Mise à jour de l'affichage.
            gui_elements_manager.update_display()

    except Exception as e:
        # Gestion des erreurs non interceptées.
        print(f"Une erreur est survenue : {e}")

    finally:
        # Fermeture de l'application et nettoyage des ressources.
        print("Fermeture de la connexion.")
        del request_manager
        pygame.quit()


if __name__ == "__main__":
    main()
