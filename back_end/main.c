// TODO: Implémenter les fonctions qui gèrent les requêtes comme celle pour l'authentification

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <fcntl.h>

#include "cJSON.h"                      // Bibliothèque pour manipuler des objets JSON

#define PORT 55555                      // Port sur lequel le serveur écoute
#define BUFFER_SIZE 1024                // Taille du buffer pour les messages
#define MAX_CONNECTIONS 10              // Nombre maximum de connexions actives

#define AUTHENTICATION_VERB "auth"      // Verbe attendu pour l'authentification
#define NEW_ACCOUNT_VERB "new_account"  // Verbe attendu pour la création d'un nouveau compte
#define GET_LOBBY_VERB "get_lobby"      // Verbe attendu pour obtenir la liste des parties en attente
#define DISCONNECT_VERB "disconnect"    // Verbe attendu pour la déconnexion
#define CREATE_GAME_VERB "create_game"  // Verbe attendu pour la création d'une nouvelle partie
#define JOIN_GAME_VERB "join_game"      // Verbe attendu pour rejoindre une partie

// enum pour les statuts de la requête
typedef enum {
    failure,
    success
} request_status;

// enum pour les statuts de la partie
typedef enum {
    waiting,
    ongoing
} game_status;

// Structure pour représenter les statistiques d'un joueur
typedef struct player_stat {
    int score;
    int wins;
    int losses;
    int games_played;
} player_stat;

// Structure pour représenter un client dans une liste chaînée
typedef struct client_node {
    int socket;
    int is_authenticated;
    char username[50];
    char password[50];
    player_stat player_stats;
    char recv_buffer[BUFFER_SIZE];
    char send_buffer[BUFFER_SIZE];
    struct client_node *next;
} client_node;

client_node *head_linked_list_client = NULL; // Tête de la liste des clients

// Structure pour représenter une partie dans une liste chaînée
typedef struct game_node {
    int id;
    char name[50];
    char player1_name[50];
    char player2_name[50];
    game_status status; // "waiting" or "ongoing"
    struct game_node *next;
} game_node;

game_node *head_linked_list_game = NULL; // Tête de la liste des parties

int total_connections = 0; // Nombre total de connexions acceptées
int active_connections = 0; // Nombre de connexions actuellement actives

// Prototypes des fonctions
int setup_server_socket();

void run_server_loop(int server_socket);

void handle_new_connection(int server_socket);

void handle_client(client_node *client);

void print_client_list();

const game_node *find_game_by_name(const char *game_name);

void add_client_to_list(int client_socket);

int remove_client_from_list(int client_socket);

game_node *add_game_to_list(const cJSON *json);

int remove_game_from_list(int game_id);

void process_cmd(client_node *client, const char *command);

void send_packet(client_node *client);

cJSON *create_auth_response_success(const client_node *client);

cJSON *create_auth_response_failure();

cJSON *create_new_account_response_success();

cJSON *create_disconnect_response();

cJSON *create_new_account_response_failure();

cJSON *create_get_lobby_response();

cJSON *create_game_response_success(const game_node *game);

cJSON *create_game_response_failure();

cJSON *create_join_game_response_success();

cJSON *create_join_game_response_failure();

cJSON *create_unknow_response();

void handle_response_type(client_node *client, const char *request_type, const cJSON *json);

char *handle_auth_response(const cJSON *json, client_node *client);

char *handle_new_account_response(const cJSON *json);

char *handle_get_lobby_response();

char *handle_disconnect_response();

char *handle_create_game_response(const cJSON *json);

char *handle_join_game_response();

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
    const int opt = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("Erreur avec setsockopt");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    // Mettre le socket en mode non bloquant
    const int flags = fcntl(server_socket, F_GETFL, 0);
    if (flags == -1) {
        perror("Erreur fcntl F_GETFL");
        exit(EXIT_FAILURE);
    }

    if (fcntl(server_socket, F_SETFL, flags | O_NONBLOCK) == -1) {
        perror("Erreur fcntl F_SETFL");
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

void print_client_list() {
    const client_node *current = head_linked_list_client;
    int i = 0;
    printf("Client list:\n");
    while (current) {
        printf(
            "%d .Client name=%s, is_authenticated%s\n",
            i++,
            current->username,
            current->is_authenticated ? "true" : "false"
        );
        current = current->next;
    }
}

const game_node *find_game_by_name(const char *game_name) {
    const game_node *current = head_linked_list_game;

    while (
        current &&
        strcmp(current->name, game_name) != 0
    ) {
        current = current->next;
    }

    return current;
}

// Ajouter un client à la liste chaînée
void add_client_to_list(const int client_socket) {
    client_node *new_node = malloc(sizeof(client_node));
    if (!new_node) {
        perror("Erreur d'allocation mémoire pour un nouveau client");
        return;
    }

    new_node->is_authenticated = 0; // Initialiser l'authentification à faux
    new_node->socket = client_socket; // Initialiser le socket du client
    new_node->next = head_linked_list_client; // Ajouter le nouveau client au début de la liste
    head_linked_list_client = new_node; // Mettre à jour la tête de la liste
}

int remove_client_from_list(const int client_socket) {
    client_node **current = &head_linked_list_client;
    while (*current) {
        client_node *entry = *current;
        if (entry->socket == client_socket) {
            *current = entry->next; // Supprimer le client de la liste
            free(entry); // Libérer la mémoire associée au client
            return 1; // Client trouvé et supprimé
        }
        current = &entry->next; // Passer au client suivant
    }
    return 0; // Client non trouvé
}

game_node *add_game_to_list(const cJSON *json) {
    game_node *new_node = malloc(sizeof(game_node));
    if (!new_node) {
        perror("Memory allocation error\n");
        return NULL;
    }

    const cJSON *id = cJSON_GetObjectItemCaseSensitive(json, "id");
    const cJSON *player1 = cJSON_GetObjectItemCaseSensitive(json, "player1");
    const cJSON *player2 = cJSON_GetObjectItemCaseSensitive(json, "player2");
    const cJSON *status = cJSON_GetObjectItemCaseSensitive(json, "status");

    if (
        !cJSON_IsNumber(id) || id == NULL ||
        !cJSON_IsString(player1) || player1 == NULL ||
        !cJSON_IsString(player2) || player2 == NULL ||
        !cJSON_IsString(status) || status == NULL
    ) {
        perror("Invalid JSON format\n");
        free(new_node);
        return NULL;
    }

    new_node->id = id->valueint;
    strncpy(new_node->player1_name, player1->valuestring, sizeof(new_node->player1_name) - 1);
    strncpy(new_node->player2_name, player2->valuestring, sizeof(new_node->player2_name) - 1);
    new_node->status = strcmp(status->valuestring, "waiting") == 0 ? waiting : ongoing;
    new_node->next = head_linked_list_game;
    head_linked_list_game = new_node;

    printf(
        "Game added: ID=%d, Player1=%s, Player2=%s, Status=%s\n",
        new_node->id,
        new_node->player1_name,
        new_node->player2_name,
        status->valuestring
    );

    return new_node;
}

int remove_game_from_list(const int game_id) {
    game_node **current = &head_linked_list_game;
    while (*current) {
        game_node *entry = *current;
        if (entry->id == game_id) {
            *current = entry->next; // Remove the game from the list
            free(entry); // Free the memory associated with the game
            return 1; // Game found and removed
        }
        current = &entry->next; // Move to the next game
    }
    return 0; // Game not found
}

// Lancer la boucle principale du serveur
void run_server_loop(const int server_socket) {
    fd_set read_fds;
    int max_fd = server_socket; // Initialiser le max_fd

    while (1) {
        FD_ZERO(&read_fds); // Réinitialiser l'ensemble des descripteurs
        FD_SET(server_socket, &read_fds); // Ajouter le socket principal

        // Ajouter tous les sockets des clients à l'ensemble
        client_node *current = head_linked_list_client;
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
        current = head_linked_list_client;
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
void handle_new_connection(const int server_socket) {
    struct sockaddr_in client_addr;
    socklen_t addrlen = sizeof(client_addr);

    const int client_socket = accept(server_socket, (struct sockaddr *) &client_addr, &addrlen);
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

    add_client_to_list(client_socket); // Ajouter le client à la liste chaînée
}

// Gérer la communication avec un client
void handle_client(client_node *client) {
    char command[BUFFER_SIZE];
    const ssize_t bytes_read = recv(client->socket, command, sizeof(command) - 1, 0);

    if (bytes_read > 0) {
        command[bytes_read] = '\0'; // Terminer correctement la chaîne
        printf("Message reçu de %d : %s\n", client->socket, command);
        process_cmd(client, command); // Traiter la commande
    } else if (bytes_read == 0) {
        printf("Client %d déconnecté.\n", client->socket);
        remove_client_from_list(client->socket);
    } else {
        perror("Erreur lors de la réception");
        remove_client_from_list(client->socket);
    }
}

cJSON *create_auth_response_success(const client_node *client) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "auth_response");
    cJSON_AddNumberToObject(response, "status", success);

    cJSON *player_stats = cJSON_CreateObject();
    cJSON_AddItemToObject(response, "player_stats", player_stats);
    cJSON_AddNumberToObject(player_stats, "score", client->player_stats.score);
    cJSON_AddNumberToObject(player_stats, "wins", client->player_stats.wins);
    cJSON_AddNumberToObject(player_stats, "losses", client->player_stats.losses);
    cJSON_AddNumberToObject(player_stats, "games_played", client->player_stats.games_played);

    return response;
}

cJSON *create_auth_response_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "auth_response");
    cJSON_AddStringToObject(response, "status", "error");
    return response;
}

cJSON *create_new_account_response_success() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "new_account_response");
    cJSON_AddStringToObject(response, "status", "success");
    cJSON_AddStringToObject(response, "username", "Djimmi");
    cJSON_AddStringToObject(response, "password", "GrosZgeg");

    return response;
}

cJSON *create_new_account_response_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "new_account_response");
    cJSON_AddStringToObject(response, "status", "failure");

    return response;
}

cJSON *create_disconnect_response() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "disconnect_ack");

    return response;
}

cJSON *create_get_lobby_response() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "get_lobby_response");
    cJSON_AddStringToObject(response, "status", "success");

    cJSON *games = cJSON_CreateArray();

    cJSON *game1 = cJSON_CreateObject();
    cJSON_AddNumberToObject(game1, "id", 1);
    cJSON_AddStringToObject(game1, "name", "Game 1");
    cJSON_AddStringToObject(game1, "status", "waiting");

    cJSON *players = cJSON_CreateArray();
    cJSON_AddItemToArray(players, cJSON_CreateString("Player 1"));

    cJSON_AddItemToObject(game1, "players", players);

    cJSON *game2 = cJSON_CreateObject();
    cJSON_AddNumberToObject(game2, "id", 2);
    cJSON_AddStringToObject(game2, "name", "Game 2");
    cJSON_AddStringToObject(game2, "status", "in_progress");

    cJSON *players2 = cJSON_CreateArray();
    cJSON_AddItemToArray(players2, cJSON_CreateString("Player 2"));
    cJSON_AddItemToArray(players2, cJSON_CreateString("Player 3"));

    cJSON_AddItemToObject(game2, "players", players2);

    cJSON_AddItemToArray(games, game1);
    cJSON_AddItemToArray(games, game2);

    cJSON_AddItemToObject(response, "games", games);

    return response;
}

cJSON *create_game_response_success(const game_node *game) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "create_game_response");
    cJSON_AddNumberToObject(response, "status", success);

    cJSON *game_obj = cJSON_CreateObject();
    cJSON_AddNumberToObject(game_obj, "id", 1);
    cJSON_AddStringToObject(game_obj, "name", game->name);
    cJSON_AddNumberToObject(game_obj, "status", game->status);
    cJSON_AddStringToObject(game_obj, "host", game->player1_name);

    cJSON *players = cJSON_CreateArray();
    cJSON_AddItemToArray(players, cJSON_CreateString(game->player1_name));
    cJSON_AddItemToObject(game_obj, "players", players);

    cJSON_AddItemToObject(response, "game", game_obj);

    return response;
}

cJSON *create_game_response_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "create_game_response");
    cJSON_AddStringToObject(response, "status", "error");

    return response;
}

cJSON *create_join_game_response_success() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "join_game_response");
    cJSON_AddStringToObject(response, "status", "success");

    return response;
}

cJSON *create_join_game_response_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "join_game_response");
    cJSON_AddStringToObject(response, "status", "error");

    return response;
}


cJSON *create_unknow_response() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "unknown_command");
    return response;
}

void complete_client_node(client_node *client, const cJSON *json) {
    const cJSON *username = cJSON_GetObjectItemCaseSensitive(json, "username");
    const cJSON *password = cJSON_GetObjectItemCaseSensitive(json, "password");

    const cJSON *player_stats = cJSON_GetObjectItemCaseSensitive(json, "player_stats");
    const cJSON *score = cJSON_CreateNumber(1);
    const cJSON *wins = cJSON_CreateNumber(2);
    const cJSON *losses = cJSON_CreateNumber(3);
    const cJSON *games_played = cJSON_CreateNumber(1000);

    if (username && cJSON_IsString(username)) {
        strncpy(client->username, username->valuestring, sizeof(client->username) - 1);
    }

    if (password && cJSON_IsString(password)) {
        strncpy(client->password, password->valuestring, sizeof(client->password) - 1);
    }

    if (score && cJSON_IsNumber(score)) {
        client->player_stats.score = score->valueint;
    }

    if (wins && cJSON_IsNumber(wins)) {
        client->player_stats.wins = wins->valueint;
    }

    if (losses && cJSON_IsNumber(losses)) {
        client->player_stats.losses = losses->valueint;
    }

    if (games_played && cJSON_IsNumber(games_played)) {
        client->player_stats.games_played = games_played->valueint;
    }

    client->is_authenticated = 1;
}

char *handle_auth_response(const cJSON *json, client_node *client) {
    const cJSON *password = cJSON_GetObjectItemCaseSensitive(json, "password");

    // Vérifie si le champ "password" existe et est une chaîne valide
    if (!password || !cJSON_IsString(password)) {
        return cJSON_Print(create_auth_response_failure());
    }

    // Si le mot de passe est incorrect, retourne une réponse d'échec
    if (strcmp(password->valuestring, "ok") != 0) {
        return cJSON_Print(create_auth_response_failure());
    }

    // Authentification réussie
    complete_client_node(client, json);
    print_client_list();
    return cJSON_Print(create_auth_response_success(client));
}

// TODO: Vérifier si le nom d'utilisateur est déjà pris
char *handle_new_account_response(const cJSON *json) {
    const cJSON *password = cJSON_GetObjectItemCaseSensitive(json, "password");
    const cJSON *conf_password = cJSON_GetObjectItemCaseSensitive(json, "conf_password");

    if (!password || !conf_password) {
        return cJSON_Print(create_new_account_response_failure());
    }

    if (strcasecmp(password->valuestring, conf_password->valuestring) != 0) {
        return cJSON_Print(create_new_account_response_failure());
    }

    return cJSON_Print(create_new_account_response_success());
}


char *handle_get_lobby_response() {
    char *response_string = NULL;
    response_string = cJSON_Print(create_get_lobby_response());
    return response_string;
}

char *handle_disconnect_response() {
    char *response_string = cJSON_Print(create_disconnect_response());
    return response_string;
}

char *handle_create_game_response(const cJSON *json) {
    const char *game_name = cJSON_GetObjectItemCaseSensitive(json, "game_name")->valuestring;
    if (find_game_by_name(game_name)) {
        return cJSON_Print(create_game_response_failure());
    }

    const game_node *game = add_game_to_list(json);
    if (!game) {
        return cJSON_Print(create_game_response_failure());
    }

    return cJSON_Print(create_game_response_success(game));
}

char *handle_join_game_response(const cJSON *json) {
    const char *game_name = cJSON_GetObjectItemCaseSensitive(json, "game_name")->valuestring;
    if (find_game_by_name(game_name)) {
        return cJSON_Print(create_join_game_response_failure());
    }

    return cJSON_Print(create_join_game_response_success());
}

void handle_response_type(client_node *client, const char *request_type, const cJSON *json) {
    char *response_string = NULL;

    if (strcmp(request_type, AUTHENTICATION_VERB) == 0) {
        response_string = handle_auth_response(json, client);
    } else if (strcmp(request_type, NEW_ACCOUNT_VERB) == 0) {
        response_string = handle_new_account_response(json);
    } else if (strcmp(request_type, GET_LOBBY_VERB) == 0) {
        response_string = handle_get_lobby_response();
    } else if (strcmp(request_type, DISCONNECT_VERB) == 0) {
        response_string = handle_disconnect_response();
    } else if (strcasecmp(request_type, CREATE_GAME_VERB) == 0) {
        response_string = handle_create_game_response(json);
    } else if (strcasecmp(request_type, JOIN_GAME_VERB) == 0) {
        response_string = handle_join_game_response(json);
    } else {
        response_string = cJSON_Print(create_unknow_response());
    }

    if (response_string != NULL) {
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", response_string);
        free(response_string);
    }
}

void process_cmd(client_node *client, const char *command) {
    printf("Traitement de la commande : %s\n", command);

    // Parser la chaîne JSON
    cJSON *json = cJSON_Parse(command);
    if (json == NULL) {
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", cJSON_Print(create_unknow_response()));
        send(client->socket, client->send_buffer, strlen(client->send_buffer), 0);
        return;
    }

    // Afficher le JSON reçu
    char *json_string = cJSON_Print(json);
    printf("JSON reçu:\n%s\n", json_string);
    free(json_string);

    // Récupérer la valeur de la clé "type"
    const cJSON *type = cJSON_GetObjectItemCaseSensitive(json, "type");
    if (
        !cJSON_IsString(type) ||
        type->valuestring == NULL
    ) {
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", cJSON_Print(create_unknow_response()));
        send(client->socket, client->send_buffer, strlen(client->send_buffer), 0);
        cJSON_Delete(json);
        return;
    }

    // Déléguer le traitement à handle_response_type
    handle_response_type(client, type->valuestring, json);

    // Envoyer la réponse au client
    printf("Réponse SERVEUR:\n%s\n", client->send_buffer);
    send(client->socket, client->send_buffer, strlen(client->send_buffer), 0);

    // Ferme la connexion si le type est "disconnect"
    if (strcmp(type->valuestring, "disconnect") == 0) {
        remove_client_from_list(client->socket);
    }

    // Libérer la mémoire du JSON
    cJSON_Delete(json);
}

void send_packet(client_node *client) {
    if (strlen(client->send_buffer) > 0) {
        send(client->socket, client->send_buffer, strlen(client->send_buffer), 0);
        memset(client->send_buffer, 0, BUFFER_SIZE); // Nettoyer le buffer après envoi
    }
}
