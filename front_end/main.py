import socket
import json
import select

# Configuration du serveur
HOST = '127.0.0.1'  # Adresse IP du serveur (localhost)
PORT = 55555  # Port du serveur
BUFFER_SIZE = 1024

def send_json(s, message):
    try:
        json_message = json.dumps(message)
        s.sendall(json_message.encode())
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")


def receive_json(s):
    try:
        data = s.recv(BUFFER_SIZE).decode()
        print()
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


def handle_server_response(socket):
    """
    Vérifie et traite la réponse du serveur de manière non bloquante.

    Args:
        socket (socket): Le socket à surveiller pour des données.

    Returns:
        bool: True si la connexion reste active, False en cas d'erreur.
    """
    try:
        # Utiliser select pour vérifier si des données sont disponibles sans bloquer
        ready_to_read, _, _ = select.select([socket], [], [], 0.1)

        # Vérifier s'il y a des données à lire
        if socket in ready_to_read:
            # Recevoir et décoder les données
            response = socket.recv(BUFFER_SIZE).decode()

            # Gérer les différents cas de réception
            if not response:
                print("Connexion fermée par le serveur.")
                return False

            # Afficher la réponse de manière lisible
            print("Réponse du serveur :")
            print(json.dumps(response, indent=2))

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


def main():
    try:
        with connect_to_server(HOST, PORT) as s:
            while True:
                if not handle_server_response(s):
                    break

                message = input("Entrez un message ('quit' pour quitter) : ")
                s.sendall(message.encode())

                if message.lower() == "quit":
                    print("Déconnexion.")
                    break
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        print("Connexion fermée.")


if __name__ == "__main__":
    main()
