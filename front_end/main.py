import json
import socket

import select

# Configuration du serveur
HOST = '127.0.0.1'  # Adresse IP du serveur (localhost)
PORT = 55555  # Port du serveur
BUFFER_SIZE = 1024


def send_json(s, json_message):
    try:
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
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print("Connecté au serveur.")
    return s


def handle_server_response(s):
    """
    Vérifie et traite la réponse du serveur de manière non bloquante.

    Args:
        s socket: Socket connecté au serveur.
    Returns:
        bool: True si la connexion reste active, False en cas d'erreur.
    """
    try:
        # Utiliser select pour vérifier si des données sont disponibles sans bloquer
        ready_to_read, _, _ = select.select([s], [], [], 0.1)

        # Vérifier s'il y a des données à lire
        if s in ready_to_read:
            # Recevoir et décoder les données
            response_json = receive_json(s)

            # Afficher la réponse de manière lisible
            print("Réponse du serveur :")
            print(json.dumps(response_json, indent=4))

            # Gérer les différents cas de réception
            if not response_json or response_json.get("type") == "disconnect_ack":
                print("Connexion fermée par le serveur.")
                return False

            return True

        # Aucune donnée disponible actuellement
        print("En attente de données du serveur...")
        return True

    except BlockingIOError:
        # Gérer spécifiquement les erreurs de socket non bloquant
        print("Socket temporairement indisponible. Nouvelle tentative...")
        return True

    except Exception as e:
        # Capture des erreurs inattendues
        print(f"Erreur de communication : {e}")
        return False


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


def create_new_account(username, password, conf_password):
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


def handle_authentication_choice():
    username = input("Entrez votre nom d'utilisateur : ")
    password = input("Entrez votre mot de passe : ")

    return create_auth_json(username, password)


def handle_create_new_account():
    username = input("Entrez votre nom d'utilisateur :")
    password = input("Entrez votre mot de passe :")
    conf_password = input("Confirmez votre mot de passe :")

    return create_new_account(username, password, conf_password)


def handle_create_new_game():
    game_name = input("Entrez le nom de la partie à créer : ")

    return create_new_game_json(game_name)


def handle_join_game():
    game_name = input("Entrez le nom de la partie à rejoidre : ")

    return create_join_game_json(game_name)


def handle_message_choice(choice):
    if choice == "1":
        return handle_authentication_choice()
    elif choice == "2":
        return handle_create_new_account()
    elif choice == "3":
        return create_get_lobby_json()
    elif choice == "4":
        return handle_create_new_game()
    elif choice == "5":
        return handle_join_game()
    elif choice == "6":
        return create_deconnection_json()
    else:
        print("Choix invalide.")
        return json.dumps({"type": "invalid_choice"})


def display_choices():
    print("1. Se connecter")
    print("2. Créer un nouveau compte")
    print("3. Afficher le lobby")
    print("4. Créer une nouvelle partie")
    print("5. Rejoinde une partie")
    print("6. Quitter")


def get_choice():
    choice = input("Entrez votre choix : ")
    return handle_message_choice(choice)


def main():
    try:
        with connect_to_server(HOST, PORT) as s:
            while True:
                if not handle_server_response(s):
                    break

                display_choices()
                json_message = get_choice()
                if not json_message:
                    continue

                send_json(s, json_message)

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        print("Connexion fermée.")


if __name__ == "__main__":
    main()
