#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <errno.h>

#define PORT 55555
#define MAX_CLIENTS 10
#define BUFFER_SIZE 1024

// Structure représentant un client dans la liste liée
typedef struct ClientNode {
    int socket;
    struct ClientNode *next;
} ClientNode;

// Fonction pour ajouter un client à la liste
void add_client(ClientNode **head, int new_socket, int *client_count) {
    if (*client_count >= MAX_CLIENTS) {
        printf("Nombre maximum de clients atteint, rejet de la connexion : %d\n", new_socket);
        close(new_socket);
        return;
    }

    ClientNode *new_node = (ClientNode *)malloc(sizeof(ClientNode));
    if (!new_node) {
        perror("Échec d'allocation de mémoire pour un nouveau client");
        exit(EXIT_FAILURE);
    }
    new_node->socket = new_socket;
    new_node->next = *head;
    *head = new_node;
    (*client_count)++;
    printf("Client ajouté, nombre total de clients : %d\n", *client_count);
}

// Fonction pour supprimer un client de la liste
void remove_client(ClientNode **head, int socket, int *client_count) {
    ClientNode *temp = *head, *prev = NULL;

    while (temp != NULL && temp->socket != socket) {
        prev = temp;
        temp = temp->next;
    }

    if (temp == NULL) return;

    if (prev == NULL) {
        *head = temp->next;
    } else {
        prev->next = temp->next;
    }

    close(temp->socket);
    free(temp);
    (*client_count)--;
    printf("Client supprimé, nombre total de clients : %d\n", *client_count);
}

// Fonction pour libérer toute la liste
void free_list(ClientNode *head) {
    ClientNode *temp;
    while (head != NULL) {
        temp = head;
        head = head->next;
        close(temp->socket);
        free(temp);
    }
}

int main() {
    int server_socket, new_socket, max_sd, sd, activity, valread;
    struct sockaddr_in address;
    socklen_t addrlen = sizeof(address);
    char buffer[BUFFER_SIZE];
    ClientNode *clients = NULL; // Liste des clients
    int client_count = 0;       // Compteur pour suivre le nombre de clients connectés

    // Créer un socket serveur
    if ((server_socket = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("Erreur lors de la création de la socket");
        exit(EXIT_FAILURE);
    }

    // Configurer l'adresse du serveur
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    // Lier le socket à l'adresse et au port spécifiés
    if (bind(server_socket, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("Échec du bind");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    // Le serveur écoute pour les connexions entrantes
    if (listen(server_socket, 3) < 0) {
        perror("Échec de listen");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    printf("Serveur en écoute sur le port %d\n", PORT);

    fd_set readfds;

    while (1) {
        // Réinitialiser le set de descripteurs de fichiers
        FD_ZERO(&readfds);

        // Ajouter le descripteur du serveur au set
        FD_SET(server_socket, &readfds);
        max_sd = server_socket;

        // Ajouter les sockets clients au set
        ClientNode *current = clients;
        while (current != NULL) {
            sd = current->socket;
            if (sd > 0)
                FD_SET(sd, &readfds);
            if (sd > max_sd)
                max_sd = sd;
            current = current->next;
        }

        // Attendre une activité sur un des sockets
        activity = select(max_sd + 1, &readfds, NULL, NULL, NULL);

        if ((activity < 0) && (errno != EINTR)) {
            perror("Erreur de select");
        }

        // Si le descripteur serveur est prêt, une nouvelle connexion arrive
        if (FD_ISSET(server_socket, &readfds)) {
            if ((new_socket = accept(server_socket, (struct sockaddr *)&address, &addrlen)) < 0) {
                perror("Erreur d'acceptation");
                exit(EXIT_FAILURE);
            }

            printf("Nouvelle connexion, socket fd: %d, IP: %s, Port: %d\n",
                   new_socket, inet_ntoa(address.sin_addr), ntohs(address.sin_port));

            add_client(&clients, new_socket, &client_count);
        }

        // Sinon, c'est un message d'un client existant
        current = clients;
        while (current != NULL) {
            sd = current->socket;

            if (FD_ISSET(sd, &readfds)) {
                if ((valread = read(sd, buffer, BUFFER_SIZE)) == 0) {
                    // Le client a fermé la connexion
                    getpeername(sd, (struct sockaddr *)&address, &addrlen);
                    printf("Client déconnecté, IP: %s, Port: %d\n",
                           inet_ntoa(address.sin_addr), ntohs(address.sin_port));

                    remove_client(&clients, sd, &client_count);
                } else {
                    // Envoyer le message reçu
                    buffer[valread] = '\0';
                    printf("Message reçu: %s\n", buffer);
                    send(sd, buffer, strlen(buffer), 0);
                }
            }

            current = current->next;
        }
    }

    free_list(clients);
    close(server_socket);
    return 0;
}
