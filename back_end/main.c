// FIXME: Client n'est pas retiré de la liste quand il se déconnecte

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <fcntl.h>
#include <time.h>

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
#define READY_TO_PLAY_VERB "ready_to_play"     // Verbe attendu pour signaler que le joueur est prêt à commencer la partie



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

typedef enum {
    not_authenticated,
    authenticated
} authenticated_status;


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
    authenticated_status is_authenticated;
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
    client_node *player1;
    client_node *player2;
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

game_node *find_game_by_name(const char *game_name);

game_node *find_game_by_player(const client_node *client);

void add_client_to_list(int client_socket);

int remove_client_from_list(int client_socket);

game_node *add_game_to_list(const cJSON *json, client_node *client);

int remove_game_from_list(int game_id);

void print_game_list();

void process_cmd(client_node *client, const char *command);

void send_packet(client_node *client);

cJSON *create_auth_response_success(const client_node *client);

cJSON *create_auth_response_failure();

cJSON *create_new_account_response_success(const client_node *client);

cJSON *create_disconnect_response();

cJSON *create_new_account_response_failure();

cJSON *create_get_lobby_response();

cJSON *create_game_response_success(const game_node *game);

cJSON *create_game_response_failure();

cJSON *create_join_game_response_success();

cJSON *create_join_game_response_failure();

cJSON *create_unknow_response();

cJSON *create_game_over_victory_response(const client_node *winner);

cJSON *create_game_over_defeat_response(const client_node *loser);

cJSON *create_player_stat_json(const player_stat *player_stats);

cJSON *create_ready_to_play_response_success();

cJSON *create_ready_to_play_response_failure();

cJSON *create_alert_start_game_success();

cJSON *create_alert_start_game_failure();

void print_game_info(const game_node *game);

void validate_game_list();

void handle_client_response_type(client_node *client, const char *request_type, const cJSON *json);

char *handle_ready_to_play_response(const client_node *client);

char *handle_auth_response(const cJSON *json, client_node *client);

char *handle_new_account_response(const cJSON *json, client_node *client);

char *handle_get_lobby_response();

char *handle_disconnect_response(client_node *client);

char *handle_create_game_response(const cJSON *json, client_node *client);

char *handle_join_game_response(const cJSON *json, client_node *client);

int add_client_to_game(game_node *game, client_node *client);

void finish_game(game_node *game);

void complete_client_node(client_node *client, const cJSON *json);

void empty_client(client_node *client);

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
            "%d .Client name=%s, is_authenticated=%s\n",
            i++,
            current->username,
            current->is_authenticated ? "true" : "false"
        );
        current = current->next;
    }
}

game_node *find_game_by_name(const char *game_name) {
    game_node *current = head_linked_list_game;

    while (
        current &&
        strcmp(current->name, game_name) != 0
    ) {
        current = current->next;
    }

    return current;
}

game_node *find_game_by_player(const client_node *client) {
    game_node *current = head_linked_list_game;

    while (
        current &&
        current->player1 != client &&
        current->player2 != client
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

    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "welcome");
    cJSON_AddStringToObject(response, "message", "Bienvenue sur le serveur de jeu multijoueur !");
    snprintf(new_node->send_buffer, BUFFER_SIZE, "%s", cJSON_Print(response));
    send_packet(new_node); // Envoyer un message de bienvenue au client
}

int remove_client_from_list(const int client_socket) {
    client_node **current = &head_linked_list_client;
    while (*current) {
        client_node *entry = *current;
        if (entry->socket == client_socket) {
            printf("Suppression du client %s\n", entry->username);
            *current = entry->next; // Supprimer le client de la liste
            free(entry); // Libérer la mémoire associée au client

            if (*current == NULL) {
                head_linked_list_client = NULL; // Si la liste est vide, assigner NULL à la tête
            }

            return 1; // Client trouvé et supprimé
        }
        current = &entry->next; // Passer au client suivant
    }
    return 0; // Client non trouvé
}

game_node *add_game_to_list(const cJSON *json, client_node *client) {
    game_node *new_game_node = malloc(sizeof(game_node));
    if (!new_game_node) {
        perror("Memory allocation error\n");
        return NULL;
    }

    const cJSON *game_name = cJSON_GetObjectItemCaseSensitive(json, "game_name");
    if (!cJSON_IsString(game_name) || game_name == NULL) {
        perror("Invalid JSON format\n");
        free(new_game_node);
        return NULL;
    }

    new_game_node->player1 = client;
    new_game_node->id = 1;
    strncpy(new_game_node->player1->username, client->username, sizeof(new_game_node->player1->username) - 1);
    strncpy(new_game_node->name, game_name->valuestring, sizeof(new_game_node->name) - 1);
    new_game_node->status = waiting;
    new_game_node->next = head_linked_list_game;
    head_linked_list_game = new_game_node;

    printf(
        "Game added: ID=%d, Game name: %s, Player1=%s, Status=%s\n",
        new_game_node->id,
        new_game_node->name,
        new_game_node->player1->username,
        "waiting"
    );

    return new_game_node;
}

void validate_game_list() {
    const game_node *current = head_linked_list_game;
    while (current) {
        if (!current->name || !current->player1) {
            printf("Invalid game node detected!\n");
            return;
        }
        current = current->next;
    }
    printf("Game list is valid.\n");
}


int remove_game_from_list(const int game_id) {
    game_node **current = &head_linked_list_game;
    while (*current) {
        game_node *entry = *current;
        if (entry->id == game_id) {
            printf("Removing game %d\n", game_id);
            *current = entry->next; // Remove the game from the list
            free(entry); // Free the memory associated with the game

            // Vérification : Si la liste devient vide, mettre head à NULL
            if (*current == NULL) {
                head_linked_list_game = NULL;
            }

            return 1; // Game found and removed
        }
        current = &entry->next; // Move to the next game
    }
    return 0; // Game not found
}


void print_game_list() {
    const game_node *current = head_linked_list_game;
    int i = 0;
    printf("Game list:\n");
    if (!current) {
        // Si la liste est vide
        printf("No games available.\n");
        return;
    }
    while (current) {
        printf(
            "%d. Game ID=%d, Name=%s, Player1=%s, Player2=%s, Status=%s\n",
            i++,
            current->id,
            current->name,
            current->player1->username,
            current->player2 ? current->player2->username : "Unknown",
            current->status == waiting ? "waiting" : "ongoing"
        );
        current = current->next;
    }
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

    cJSON *player_stats = create_player_stat_json(&client->player_stats);
    cJSON_AddItemToObject(response, "player_stats", player_stats);

    return response;
}

cJSON *create_auth_response_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "auth_response");
    cJSON_AddStringToObject(response, "status", "error");
    return response;
}

cJSON *create_new_account_response_success(const client_node *client) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "new_account_response");
    cJSON_AddNumberToObject(response, "status", success);

    cJSON *player_stats = create_player_stat_json(&client->player_stats);
    cJSON_AddItemToObject(response, "player_stats", player_stats);

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
    cJSON_AddNumberToObject(response, "status", success);

    return response;
}

cJSON *create_ready_to_play_response_success() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "ready_to_play_response");
    cJSON_AddNumberToObject(response, "status", success);

    return response;
}

cJSON *create_ready_to_play_response_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "ready_to_play_response");
    cJSON_AddNumberToObject(response, "status", failure);

    return response;
}

cJSON *create_get_lobby_response() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "get_lobby_response");
    cJSON_AddNumberToObject(response, "status", success);

    cJSON *games = cJSON_CreateArray();
    const game_node *current_game = head_linked_list_game;

    print_game_list();
    while (current_game) {
        printf("Game name: %s\n", current_game->name);
        cJSON *game = cJSON_CreateObject();
        cJSON_AddNumberToObject(game, "id", current_game->id);
        cJSON_AddStringToObject(game, "name", current_game->name);
        cJSON_AddNumberToObject(game, "status", current_game->status == waiting ? waiting : ongoing);

        cJSON *players = cJSON_CreateArray();
        cJSON_AddItemToArray(players, cJSON_CreateString(current_game->player1->username));
        if (current_game->player2) {
            cJSON_AddItemToArray(players, cJSON_CreateString(current_game->player2->username));
        }

        cJSON_AddItemToObject(game, "players", players);
        cJSON_AddItemToArray(games, game);

        current_game = current_game->next;
    }

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
    cJSON_AddStringToObject(game_obj, "host", game->player1->username);

    cJSON *players = cJSON_CreateArray();
    cJSON_AddItemToArray(players, cJSON_CreateString(game->player1->username));
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
    cJSON_AddNumberToObject(response, "status", success);

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

cJSON *create_game_over_victory_response(const client_node *winner) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "game_over");
    cJSON_AddStringToObject(response, "status", "victory");

    cJSON *player_stats = create_player_stat_json(&winner->player_stats);
    cJSON_AddItemToObject(response, "player_stats", player_stats);

    return response;
}

cJSON *create_game_over_defeat_response(const client_node *loser) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "game_over");
    cJSON_AddStringToObject(response, "status", "defeat");

    cJSON *player_stats = create_player_stat_json(&loser->player_stats);
    cJSON_AddItemToObject(response, "player_stats", player_stats);

    return response;
}

cJSON *create_player_stat_json(const player_stat *player_stats) {
    cJSON *player_stats_json = cJSON_CreateObject();
    cJSON_AddNumberToObject(player_stats_json, "score", player_stats->score);
    cJSON_AddNumberToObject(player_stats_json, "wins", player_stats->wins);
    cJSON_AddNumberToObject(player_stats_json, "losses", player_stats->losses);
    cJSON_AddNumberToObject(player_stats_json, "games_played", player_stats->games_played);

    return player_stats_json;
}

cJSON *create_alert_start_game_success() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "alert_start_game");
    cJSON_AddNumberToObject(response, "status", success);

    return response;
}

cJSON *create_alert_start_game_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "alert_start_game");
    cJSON_AddNumberToObject(response, "status", failure);

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

void empty_client(client_node *client) {
    printf("Emptying client %s\n", client->username);
    client->is_authenticated = not_authenticated;
    memset(client->username, 0, sizeof(client->username));
    memset(client->password, 0, sizeof(client->password));
    memset(client->recv_buffer, 0, sizeof(client->recv_buffer));
    memset(client->send_buffer, 0, sizeof(client->send_buffer));
    client->player_stats.score = 0;
    client->player_stats.wins = 0;
    client->player_stats.losses = 0;
    client->player_stats.games_played = 0;
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

// TODO: Vérifier si le nom d'utilisateur est déjà pris dans la db
char *handle_new_account_response(const cJSON *json, client_node *client) {
    const cJSON *password = cJSON_GetObjectItemCaseSensitive(json, "password");
    const cJSON *conf_password = cJSON_GetObjectItemCaseSensitive(json, "conf_password");

    if (
        !password ||
        !conf_password ||
        strcmp(password->valuestring, conf_password->valuestring) != 0
    ) {
        return cJSON_Print(create_new_account_response_failure());
    }

    return cJSON_Print(create_new_account_response_success(client));
}


char *handle_get_lobby_response() {
    char *response_string = NULL;
    response_string = cJSON_Print(create_get_lobby_response());
    return response_string;
}

char *handle_disconnect_response(client_node *client) {
    empty_client(client);

    char *response_string = cJSON_Print(create_disconnect_response());
    return response_string;
}

char *handle_create_game_response(const cJSON *json, client_node *client) {
    const char *game_name = cJSON_GetObjectItemCaseSensitive(json, "game_name")->valuestring;
    if (find_game_by_name(game_name)) {
        printf("Game already exists\n");
        return cJSON_Print(create_game_response_failure());
    }

    const game_node *game = add_game_to_list(json, client);
    if (!game) {
        printf("Error creating game\n");
        return cJSON_Print(create_game_response_failure());
    }

    print_game_list();

    return cJSON_Print(create_game_response_success(game));
}

void print_game_info(const game_node *game) {
    if (!game) {
        printf("Erreur : le pointeur de la partie est nul.\n");
        return;
    }

    printf("Informations de la partie:\n");
    printf("ID: %d\n", game->id);
    printf("Nom: %s\n", game->name ? game->name : "Inconnu");

    if (game->player1) {
        printf("Joueur 1: %s\n", game->player1->username);
    } else {
        printf("Joueur 1: Inconnu\n");
    }

    if (game->player2) {
        printf("Joueur 2: %s\n", game->player2->username);
    } else {
        printf("Joueur 2: Inconnu\n");
    }

    printf("Statut: %s\n", game->status == waiting ? "En attente" : "En cours");
}

int add_client_to_game(game_node *game, client_node *client) {
    if (
        !game ||
        !client ||
        game->status == ongoing
    ) {
        return 0; // Retourner une erreur si game ou client est nul ou si la partie est déjà en cours
    }

    if (!game->player1) {
        printf("Adding player %s to the game\n", client->username);
        game->player1 = client;
    } else if (!game->player2) {
        printf("Adding player %s to the game\n", client->username);
        game->player2 = client;
    } else {
        return 0; // La partie est déjà pleine
    }

    return 1; // Client ajouté avec succès
}

void finish_game(game_node *game) {
    // Choisir au hasard le gagnant et le perdant
    srandom(time(NULL));
    client_node *winner = random() % 2 == 0 ? game->player1 : game->player2;
    client_node *loser = winner == game->player1 ? game->player2 : game->player1;
    printf("Winner: %s, Loser: %s\n", winner->username, loser->username);

    // Mettre à jour les scores
    winner->player_stats.wins++;
    winner->player_stats.score += 100;
    winner->player_stats.games_played++;
    loser->player_stats.losses++;
    loser->player_stats.score -= 100;
    loser->player_stats.games_played++;

    // Écrire dans les buffers d'envoi
    char *victory_response = cJSON_Print(create_game_over_victory_response(winner));
    char *defeat_response = cJSON_Print(create_game_over_defeat_response(loser));
    snprintf(winner->send_buffer, BUFFER_SIZE, "%s", victory_response);
    snprintf(loser->send_buffer, BUFFER_SIZE, "%s", defeat_response);
    free(victory_response);
    free(defeat_response);

    // Envoyer les paquets
    send_packet(winner);
    send_packet(loser);

    // Retirer la partie de la liste chaînée
    remove_game_from_list(game->id);
}

char *handle_join_game_response(const cJSON *json, client_node *client) {
    const char *game_name = cJSON_GetObjectItemCaseSensitive(json, "game_name")->valuestring;
    game_node *game = find_game_by_name(game_name);
    if (!game) {
        printf("Game not found\n");
        return cJSON_Print(create_join_game_response_failure());
    }

    if (add_client_to_game(game, client) != 1) {
        printf("Game is full or already started\n");
        return cJSON_Print(create_join_game_response_failure());
    }

    print_game_list();

    return cJSON_Print(create_join_game_response_success());
}

char *handle_ready_to_play_response(const client_node *client) {
    game_node *game = find_game_by_player(client);
    if (!game) {
        return cJSON_Print(create_ready_to_play_response_failure());
    }

    if (!game->player1 || !game->player2) {
        return cJSON_Print(create_ready_to_play_response_failure());
    }

    game->status = ongoing;

    snprintf(
        game->player1->send_buffer,
        BUFFER_SIZE,
        "%s",
        cJSON_Print(create_alert_start_game_success())
    );
    send_packet(game->player1);

    return cJSON_Print(create_alert_start_game_success());
}

void handle_client_response_type(client_node *client, const char *request_type, const cJSON *json) {
    char *response_string = NULL;

    if (strcmp(request_type, AUTHENTICATION_VERB) == 0) {
        response_string = handle_auth_response(json, client);
    } else if (strcmp(request_type, NEW_ACCOUNT_VERB) == 0) {
        response_string = handle_new_account_response(json, client);
    } else if (strcmp(request_type, GET_LOBBY_VERB) == 0) {
        response_string = handle_get_lobby_response();
    } else if (strcmp(request_type, DISCONNECT_VERB) == 0) {
        response_string = handle_disconnect_response(client);
    } else if (strcmp(request_type, CREATE_GAME_VERB) == 0) {
        response_string = handle_create_game_response(json, client);
    } else if (strcmp(request_type, JOIN_GAME_VERB) == 0) {
        response_string = handle_join_game_response(json, client);
    } else if (strcmp(request_type, READY_TO_PLAY_VERB) == 0) {
        response_string = handle_ready_to_play_response(client);
    } else {
        response_string = cJSON_Print(create_unknow_response());
    }

    if (response_string != NULL) {
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", response_string);
        free(response_string);
    }
}

void process_cmd(client_node *client, const char *command) {
    // Parser la chaîne JSON
    cJSON *json = cJSON_Parse(command);
    if (json == NULL) {
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", cJSON_Print(create_unknow_response()));
        send_packet(client);
        return;
    }

    // Afficher le JSON reçu
    char *json_string = cJSON_Print(json);
    printf("JSON reçu de %s:\n%s\n", client->username, json_string);
    free(json_string);

    // Récupérer la valeur de la clé "type"
    const cJSON *type = cJSON_GetObjectItemCaseSensitive(json, "type");
    if (
        !cJSON_IsString(type) ||
        type->valuestring == NULL
    ) {
        printf("Type de requête inconnu\n");
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", cJSON_Print(create_unknow_response()));
        send_packet(client);
        cJSON_Delete(json);
        return;
    }

    // Déléguer le traitement à handle_client_response_type
    handle_client_response_type(client, type->valuestring, json);

    // Envoyer la réponse au client
    printf("Réponse SERVEUR:\n%s\n", client->send_buffer);
    send_packet(client);

    // Libérer la mémoire du JSON
    cJSON_Delete(json);
}

void send_packet(client_node *client) {
    if (strlen(client->send_buffer) > 0) {
        printf("Envoie du paquet à %s\n", client->username);
        send(client->socket, client->send_buffer, strlen(client->send_buffer), 0);
        memset(client->send_buffer, 0, BUFFER_SIZE); // Nettoyer le buffer après envoi
    }
}
