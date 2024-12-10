import socket

import select

# Configuration du serveur
HOST = '127.0.0.1'  # Adresse IP du serveur (localhost)
PORT = 55555  # Port du serveur


def connect_to_server(host, port):
    ws = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ws.connect((host, port))
    print("Connecté au serveur.")
    return ws


def handle_server_response(ws):
    ready_to_read, _, _ = select.select([ws], [], [], 0.1)
    if ws in ready_to_read:
        data = ws.recv(1024)

        if not data:
            print("Connexion fermée par le serveur.")
            return False

        response = data.decode()
        print(f"Réponse du serveur : {response}")

        if response.startswith("SERVER_CLOSE"):
            print("Le serveur a fermé la connexion : Limite atteinte.")
            return False

    return True


def main():
    try:
        with connect_to_server(HOST, PORT) as ws:
            while True:
                if not handle_server_response(ws):
                    break

                message = input("Entrez un message ('quit' pour quitter) : ")
                ws.sendall(message.encode())

                if message.lower() == "quit":
                    print("Déconnexion.")
                    break
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        print("Connexion fermée.")


if __name__ == "__main__":
    main()
