import socket

# Configuration
SERVER_HOST = "127.0.0.1"  # Adresse IP du serveur
SERVER_PORT = 55555        # Port du serveur

def main():
    try:
        # Création de la socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Socket créée.")

        # Connexion au serveur
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print(f"Connecté au serveur {SERVER_HOST}:{SERVER_PORT}")

        while True:
            # Lecture de la chaîne de l'utilisateur
            message = input("Entrez un message (ou 'quit' pour quitter) : ")

            if message.lower() == "quit":
                print("Fermeture de la connexion...")
                client_socket.close()
                break

            # Envoi de la chaîne au serveur
            client_socket.sendall(message.encode())

            # Lecture de la réponse du serveur
            response = client_socket.recv(1024).decode()
            print(f"Réponse du serveur : {response}")

    except ConnectionError as e:
        print(f"Erreur de connexion : {e}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass
        print("Connexion fermée.")

if __name__ == "__main__":
    main()
