#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/select.h>

#define PORT 55555         // Port sur lequel le serveur écoute
#define BUFFER_SIZE 1024   // Taille du buffer pour les messages
#define MAX_CONNECTIONS 10 // Nombre maximum de connexions actives

// Structure pour représenter un client dans une liste chaînée
typedef struct client_node {
    int socket; // Socket du client
    char recv_buffer[BUFFER_SIZE]; // Buffer de réception
    char send_buffer[BUFFER_SIZE]; // Buffer d'envoi
    struct client_node *next; // Pointeur vers le prochain client
} client_node;

client_node *head = NULL; // Tête de la liste des clients

// Variables globales pour le suivi des connexions
int total_connections = 0; // Nombre total de connexions acceptées
int active_connections = 0; // Nombre de connexions actuellement actives

// Prototypes des fonctions
int setup_server_socket();

void run_server_loop(int server_socket);

void handle_new_connection(int server_socket);

void handle_client(client_node *client);

void add_client(int client_socket);

void close_connection(int client_socket);

client_node *find_client(int client_socket);

void process_cmd(client_node *client, const char *command);

void send_packet(client_node *client);

// Fonction principale
int main() {
    const int server_socket = setup_server_socket(); // Configurer le socket serveur
    printf("Serveur en écoute sur le port %d\n", PORT);

    run_server_loop(server_socket); // Lancer la boucle principale
    close(server_socket); // Fermer le socket principal
    return 0;
}

// Configurer le socket serveur
int setup_server_socket() {
    int server_socket;
    struct sockaddr_in server_addr;

    // Créer un socket TCP
    if ((server_socket = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("Erreur lors de la création du socket");
        exit(EXIT_FAILURE);
    }

    // Réutiliser l'adresse et le port immédiatement après fermeture
    // Cette option permet de réutiliser l'adresse et le port immédiatement après la fermeture du socket,
    // ce qui est utile pour éviter les erreurs "Address already in use" lors du redémarrage rapide du serveur.
    int opt = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("Erreur avec setsockopt");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    // Configurer l'adresse du serveur
    server_addr.sin_family = AF_INET; // IPv4
    server_addr.sin_addr.s_addr = INADDR_ANY; // Accepter des connexions depuis n'importe quelle IP
    server_addr.sin_port = htons(PORT); // Convertir le port en format réseau

    // Associer le socket à l'adresse et au port
    if (bind(server_socket, (struct sockaddr *) &server_addr, sizeof(server_addr)) < 0) {
        perror("Erreur avec bind");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    // Mettre le socket en mode écoute
    if (listen(server_socket, 10) < 0) {
        perror("Erreur avec listen");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    return server_socket;
}

// Ajouter un client à la liste chaînée
void add_client(int client_socket) {
    client_node *new_node = (client_node *) malloc(sizeof(client_node));
    if (!new_node) {
        perror("Erreur d'allocation mémoire pour un nouveau client");
        return;
    }
    new_node->socket = client_socket; // Initialiser le socket du client
    new_node->next = head; // Ajouter le nouveau client au début de la liste
    head = new_node; // Mettre à jour la tête de la liste
}

// Retirer un client de la liste chaînée
void close_connection(int client_socket) {
    client_node **current = &head;
    while (*current) {
        client_node *entry = *current;
        if (entry->socket == client_socket) {
            *current = entry->next; // Supprimer le client de la liste
            close(entry->socket); // Fermer le socket du client
            free(entry); // Libérer la mémoire associée au client
            active_connections--; // Mettre à jour les statistiques des connexions
            printf(
                "Client %d déconnecté et retiré de la liste. Connexions actives : %d\n",
                client_socket,
                active_connections
            );
            return;
        }
        current = &entry->next; // Passer au client suivant
    }
}

// Lancer la boucle principale du serveur
void run_server_loop(int server_socket) {
    fd_set read_fds;
    int max_fd = server_socket; // Initialiser le max_fd

    while (1) {
        FD_ZERO(&read_fds); // Réinitialiser l'ensemble des descripteurs
        FD_SET(server_socket, &read_fds); // Ajouter le socket principal

        // Ajouter tous les sockets des clients à l'ensemble
        client_node *current = head;
        while (current) {
            FD_SET(current->socket, &read_fds);
            if (current->socket > max_fd) {
                max_fd = current->socket;
            }
            current = current->next;
        }

        // Attendre l'activité sur un descripteur
        const int activity = select(max_fd + 1, &read_fds, NULL, NULL, NULL);
        if (activity < 0) {
            perror("Erreur avec select");
            exit(EXIT_FAILURE);
        }

        // Vérifier si une nouvelle connexion est en attente
        if (FD_ISSET(server_socket, &read_fds)) {
            handle_new_connection(server_socket);
        }

        // Vérifier l'activité sur les sockets des clients
        current = head;
        while (current) {
            client_node *next = current->next; // Sauvegarder le pointeur suivant
            if (FD_ISSET(current->socket, &read_fds)) {
                handle_client(current);
            }
            current = next;
        }
    }
}

// Gérer une nouvelle connexion
void handle_new_connection(int server_socket) {
    struct sockaddr_in client_addr;
    socklen_t addrlen = sizeof(client_addr);

    int client_socket = accept(server_socket, (struct sockaddr *) &client_addr, &addrlen);
    if (client_socket < 0) {
        perror("Erreur avec accept");
        return;
    }

    // Vérifier si le nombre maximum de connexions actives est atteint
    if (active_connections >= MAX_CONNECTIONS) {
        const char *refus_message = "SERVER_CLOSE: Connexion refusée : Limite atteinte.";
        send(client_socket, refus_message, strlen(refus_message), 0); // Envoyer le message d'erreur explicite
        printf(
            "Connexion refusée : socket %d (IP: %s, PORT: %hu). Limite atteinte.\n",
            client_socket,
            inet_ntoa(client_addr.sin_addr),
            ntohs(client_addr.sin_port)
        );
        close(client_socket); // Fermer la connexion proprement
        return;
    }

    // Mettre à jour les statistiques des connexions
    total_connections++;
    active_connections++;

    // Le spécificateur de format %hu est utilisé pour afficher une valeur de type unsigned short en C.
    printf(
        "Nouvelle connexion acceptée : socket %d (IP: %s, PORT: %hu). Connexions actives : %d/%d, Total connexions : %d\n",
        client_socket,
        inet_ntoa(client_addr.sin_addr),
        ntohs(client_addr.sin_port),
        active_connections,
        MAX_CONNECTIONS,
        total_connections
    );

    add_client(client_socket); // Ajouter le client à la liste chaînée
}

// Gérer la communication avec un client
void handle_client(client_node *client) {
    char buffer[BUFFER_SIZE];
    const ssize_t bytes_read = recv(client->socket, buffer, sizeof(buffer) - 1, 0);

    if (bytes_read > 0) {
        buffer[bytes_read] = '\0'; // Terminer correctement la chaîne
        printf("Message reçu de %d : %s\n", client->socket, buffer);
        process_cmd(client, buffer); // Traiter la commande
    } else if (bytes_read == 0) {
        printf("Client %d déconnecté.\n", client->socket);
        close_connection(client->socket);
    } else {
        perror("Erreur lors de la réception");
        close_connection(client->socket);
    }
}

void process_cmd(client_node *client, const char *command) {
    printf("Traitement de la commande : %s\n", command);

    // Exemple de commandes
    if (strcasecmp(command, "HELLO") == 0) {
        snprintf(client->send_buffer, BUFFER_SIZE, "SERVER: Hello, client %d!\n", client->socket);
    } else if (strcasecmp(command, "QUIT") == 0) {
        snprintf(client->send_buffer, BUFFER_SIZE, "SERVER: Bye, client %d!\n", client->socket);
        close_connection(client->socket);
        return;
    } else {
        snprintf(client->send_buffer, BUFFER_SIZE, "SERVER: Commande inconnue : %s\n", command);
    }

    send(client->socket, client->send_buffer, strlen(client->send_buffer), 0);
}

void send_packet(client_node *client) {
    if (strlen(client->send_buffer) > 0) {
        send(client->socket, client->send_buffer, strlen(client->send_buffer), 0);
        memset(client->send_buffer, 0, BUFFER_SIZE); // Nettoyer le buffer après envoi
    }
}
