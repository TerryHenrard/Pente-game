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
            print("Connexion fermée par le serveur")
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
        s socket: Socket connectée au serveur.
    Returns:
        bool: True si la connexion reste active, False en cas d'erreur.
    """
    try:
        # Utiliser select pour vérifier si des données sont disponibles sans bloquer
        ready_to_read, _, _ = select.select([s], [], [], 0.1)

        # Vérifier s'il y a des données à lire
        if s in ready_to_read:
            # Recevoir et décoder les données
            response = receive_json(s)

            # Gérer les différents cas de réception
            if not response:
                print("Connexion fermée par le serveur.")
                return False

            # Afficher la réponse de manière lisible
            print("Réponse du serveur :")
            print(json.dumps(response, indent=4))
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
        return json.dumps({"type": "auth", "username": username, "password": password})
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def create_deconnection_json():
    try:
        return json.dumps({"type": "disconnect"})
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
        return None


def handle_authentication_choice():
    username = input("Entrez votre nom d'utilisateur : ")
    password = input("Entrez votre mot de passe : ")

    return create_auth_json(username, password)


def handle_deconnection_choice():
    return create_deconnection_json()


def handle_message_choice(choice):
    if choice == "1":
        return handle_authentication_choice()
    elif choice == "2":
        return handle_deconnection_choice()
    else:
        print("Choix invalide.")
        return None


def display_choices():
    print("1. Se connecter")
    print("2. Quitter")


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
