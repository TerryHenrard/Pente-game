import json
import socket

# pdoc: format de la documentation
__docformat__ = "google"

import select


class RequestManager:
    """Classe utilitaire pour la création de chaînes JSON et les communications via un socket."""

    MIN_PORT = 1
    MAX_PORT = 65535

    def __init__(self, host: str, port: int, buffer_size: int = 1024) -> None:
        """
        Initialise la classe avec un socket connecté et une taille de tampon.

        Args:
            host (str): L'adresse du serveur (nom d'hôte ou IP).
            port (int): Le numéro de port du serveur.
            buffer_size (int): La taille du tampon pour les réceptions. Par défaut, 1024.

        Raises:
            ValueError: Si le port ou le host est invalide.
            TypeError: Si `buffer_size` n'est pas un entier.
            ConnectionError: Si la connexion au serveur échoue.
        """
        if not isinstance(host, str) or not host:
            raise ValueError("L'adresse du serveur 'host' doit être une chaîne non vide.")
        if not isinstance(port, int) or not (RequestManager.MIN_PORT < port < RequestManager.MAX_PORT):
            raise ValueError("Le numéro de port doit être un entier entre 1 et 65535.")
        if not isinstance(buffer_size, int):
            raise TypeError("La taille du tampon doit être un entier.")

        # Taille du tampon
        self.buffer_size = buffer_size

        # Connexion au serveur
        self._user_socket = self.__connect_to_server(host, port)

    def get_user_socket(self) -> socket.socket:
        """
        Getter pour l'attribut `user_socket`.

        Returns:
            socket.socket: Le socket connecté.
        """
        return self._user_socket

    def is_socket_ready(self, timeout: float = 0.001) -> bool:
        return self._user_socket in select.select([self._user_socket], [], [], timeout)[0]

    @staticmethod
    def __connect_to_server(host: str, port: int) -> socket.socket:
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

    def __send_json(self, json_message: str) -> None:
        """
        Envoie un message JSON via le socket utilisateur.

        Args:
            json_message (str): Le message JSON à envoyer sous forme de chaîne.

        Raises:
            ValueError: Si le message JSON est invalide.
            ConnectionError: Si une erreur de connexion survient lors de l'envoi.
        """
        try:
            # Valide et formate le message JSON avant l'envoi
            parsed_json = json.loads(json_message)
            print("Envoi du message JSON formaté :")
            print(json.dumps(parsed_json, indent=4))

            # Envoie le message via le socket
            self.get_user_socket().sendall(json_message.encode('utf-8'))

        except json.JSONDecodeError as je:
            raise ValueError(f"Le message fourni n'est pas un JSON valide : {je}") from je
        except socket.error as se:
            raise ConnectionError(f"Erreur de connexion lors de l'envoi du message : {se}") from se

    def receive_json(self) -> json:
        """
        Reçoit un message JSON via le socket et le décode.

        Returns:
            dict: Le message JSON décodé sous forme de dictionnaire.

        Raises:
            ConnectionError: Si aucune donnée n'est reçue ou si une erreur de connexion survient.
            json.JSONDecodeError: Si le message reçu n'est pas un JSON valide.
        """
        try:
            # Réception des données depuis le socket
            data = self.get_user_socket().recv(self.buffer_size).decode("utf-8")

            # Vérifie si des données ont été reçues
            if not data:
                raise ConnectionError("Aucune donnée reçue ou le socket est fermé.")

            # Tente de charger les données en tant que JSON
            return json.loads(data)

        except json.JSONDecodeError as jde:
            raise json.JSONDecodeError(f"Erreur de décodage JSON : {jde.msg}", jde.doc, jde.pos) from jde
        except socket.error as se:
            raise ConnectionError(f"Erreur de connexion au socket : {se}") from se

    def send_play_move_json(self, x: int, y: int) -> None:
        """
        Envoie une chaîne JSON représentant un coup de jeu avec les coordonnées fournies.

        Args:
            x (int): Coordonnée x du coup.
            y (int): Coordonnée y du coup.

        Returns:
            str: Le message JSON représentant le coup de jeu.

        Raises:
            TypeError: Si les coordonnées x et y ne sont pas des entiers.
        """
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("Les coordonnées x et y doivent être des entiers.")

        self.__send_json(json.dumps({
            "type": "play_move",
            "x": x,
            "y": y
        }))

    def send_quit_game_json(self) -> None:
        """
        Envoie une chaîne JSON représentant une action de quitter la partie.

        Returns:
            str: Le message JSON représentant l'action de quitter la partie.
        """
        self.__send_json(json.dumps({"type": "quit_game"}))

    def send_ready_to_play_message(self) -> None:
        """
        Envoie une chaîne JSON représentant un message indiquant que le joueur est prêt à jouer.

        Returns:
            str: Le message JSON indiquant que le joueur est prêt à jouer.
        """
        self.__send_json(json.dumps({"type": "ready_to_play"}))

    def send_auth_json(self, username: str, password: str) -> None:
        """
        Envoie une chaîne JSON représentant un message d'authentification.

        Args:
            username (str): Nom d'utilisateur.
            password (str): Mot de passe.

        Returns:
            str: Le message JSON représentant l'authentification.

        Raises:
            TypeError: Si les paramètres `username` et `password` ne sont pas des chaînes.
            ValueError: Si les paramètres `username` et `password` sont vides.
        """
        if not isinstance(username, str) or not isinstance(password, str):
            raise TypeError("Les paramètres 'username' et 'password' doivent être des chaînes.")
        if not username or not password:
            raise ValueError("Les paramètres 'username' et 'password' ne peuvent pas être vides.")

        self.__send_json(json.dumps({
            "type": "auth",
            "username": username,
            "password": password
        }))

    def send_new_account_json(self, username: str, password: str, conf_password: str) -> None:
        """
        Envoie une chaîne JSON représentant une demande de création de nouveau compte.

        Args:
            username (str): Nom d'utilisateur.
            password (str): Mot de passe.
            conf_password (str): Confirmation du mot de passe.

        Returns:
            str: Le message JSON représentant la création de compte.

        Raises:
            TypeError: Si les paramètres `username`, `password` et `conf_password` ne sont pas des chaînes.
            ValueError: Si les paramètres `username`, `password` et `conf_password` sont vides.
        """
        if not all(isinstance(param, str) for param in [username, password, conf_password]):
            raise TypeError("Les paramètres 'username', 'password' et 'conf_password' doivent être des chaînes.")
        if not username or not password or not conf_password:
            raise ValueError("Les paramètres 'username', 'password' et 'conf_password' ne peuvent pas être vides.")

        self.__send_json(json.dumps({
            "type": "new_account",
            "username": username,
            "password": password,
            "conf_password": conf_password
        }))

    def send_deconnection_json(self) -> None:
        """
        Envoie une chaîne JSON représentant une demande de déconnexion.

        Returns:
            str: Le message JSON représentant la déconnexion.
        """
        self.__send_json(json.dumps({"type": "disconnect"}))

    def send_get_lobby_json(self) -> None:
        """
        Envoie une chaîne JSON représentant une demande pour obtenir les informations du lobby.

        Returns:
            str: Le message JSON représentant la demande pour obtenir les informations du lobby.
        """
        self.__send_json(json.dumps({"type": "get_lobby"}))

    def send_join_game_json(self, game_name_param: str) -> None:
        """
        Envoie une chaîne JSON représentant une demande de rejoindre une partie.

        Args:
            game_name_param (str): Nom de la partie à rejoindre.

        Returns:
            str: Le message JSON représentant la demande de rejoindre une partie.

        Raises:
            TypeError: Si `game_name_param` n'est pas une chaîne.
            ValueError: Si `game_name_param` est vide
        """
        if not isinstance(game_name_param, str):
            raise TypeError("Le paramètre 'game_name_param' doit être une chaîne.")
        if not game_name_param:
            raise ValueError("Le paramètre 'game_name_param' ne peut pas être vide.")

        self.__send_json(json.dumps({
            "type": "join_game",
            "game_name": game_name_param
        }))

    def send_new_game_json(self, game_name_param: str) -> None:
        """
        Envoie une chaîne JSON représentant une demande de création de nouvelle partie.

        Args:
            game_name_param (str): Nom de la nouvelle partie.

        Returns:
            str: Le message JSON représentant la demande de création de nouvelle partie.

        Raises:
            TypeError: Si `game_name_param` n'est pas une chaîne.
            ValueError: Si `game_name_param` est vide.
        """
        if not isinstance(game_name_param, str):
            raise TypeError("Le paramètre 'game_name_param' doit être une chaîne.")
        if not game_name_param:
            raise ValueError("Le paramètre 'game_name_param' ne peut pas être vide.")

        self.__send_json(json.dumps({
            "type": "create_game",
            "game_name": game_name_param
        }))

    def close_socket(self) -> None:
        """
        Ferme le socket connecté.

        Raises:
            RuntimeError: Si le socket est déjà fermé.
        """
        try:
            if self._user_socket:
                print("Fermeture du socket.")
                self._user_socket.close()
                self._user_socket = None
            else:
                raise RuntimeError("Le socket est déjà fermé.")
        except socket.error as se:
            raise RuntimeError(f"Erreur lors de la fermeture du socket : {se}") from se

    def __del__(self) -> None:
        """
        Méthode spéciale appelée à la destruction de l'objet.

        Ferme le socket si ce n'est pas déjà fait.

        Returns:
            None

        Raises:
            Exception: Si une erreur survient lors de la fermeture du socket
        """
        try:
            print("Destruction de l'objet RequestManager : fermeture du socket.")
            self.close_socket()
        except Exception as ex:
            raise Exception(f"Erreur lors de la destruction de l'objet : {ex}") from ex
