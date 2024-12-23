#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <fcntl.h>
#include <sqlite3.h>
#include <openssl/evp.h>

#include "cJSON.h"                             // Bibliothèque pour manipuler des objets JSON

#define PORT 55555                             // Port sur lequel le serveur écoute
#define BUFFER_SIZE 1048                       // Taille du buffer pour les messages
#define MAX_CONNECTIONS 10                     // Nombre maximum de connexions actives

#define BOARD_ROWS 19                          // Nombre de lignes du plateau de jeu
#define BOARD_COLS 19                          // Nombre de colonnes du plateau de jeu
#define BOARD_SIZE (BOARD_COLS * BOARD_ROWS)   // Taille du plateau de jeu
#define EMPTY_CHAR '-'                         // Cellule vide
#define PLAYER1_CHAR 'x'                       // Cellule du joueur 1
#define PLAYER2_CHAR 'o'                       // Cellule du joueur 2

#define PLAY_MOVE_VERB "play_move"             // Verbe attendu pour jouer un coup
#define QUIT_GAME_VERB "quit_game"             // Verbe attendu pour quitter une partie
#define AUTHENTICATION_VERB "auth"             // Verbe attendu pour l'authentification
#define NEW_ACCOUNT_VERB "new_account"         // Verbe attendu pour la création d'un nouveau compte
#define GET_LOBBY_VERB "get_lobby"             // Verbe attendu pour obtenir la liste des parties en attente
#define DISCONNECT_VERB "disconnect"           // Verbe attendu pour la déconnexion
#define CREATE_GAME_VERB "create_game"         // Verbe attendu pour la création d'une nouvelle partie
#define JOIN_GAME_VERB "join_game"             // Verbe attendu pour rejoindre une partie
#define READY_TO_PLAY_VERB "ready_to_play"     // Verbe attendu pour signaler que le joueur est prêt à commencer la partie



typedef struct game_node game_node;
typedef struct player_node player_node;
typedef struct player_stat player_stat;
typedef enum request_status request_status;
typedef enum game_status game_status;
typedef enum authenticated_status authenticated_status;
typedef enum victory_status victory_status;

// enum pour les statuts de la victoire
enum victory_status {
    victory,
    defeat,
    draw
};

// enum pour les statuts de la requête
enum request_status {
    failure,
    success
};

// enum pour les statuts de la partie
enum game_status {
    waiting,
    ongoing
};

// enum pour les statuts d'authentification
enum authenticated_status {
    not_authenticated,
    authenticated
};

// Structure pour représenter les statistiques d'un joueur
struct player_stat {
    int score;
    int wins;
    int losses;
    int forfeits;
    int games_played;
};

// Structure pour représenter un client dans une liste chaînée
struct player_node {
    int socket;
    int id;
    authenticated_status is_authenticated;
    char username[50];
    char password[50];
    player_stat player_stats;
    char recv_buffer[BUFFER_SIZE];
    char send_buffer[BUFFER_SIZE];
    int captures;
    game_node *current_game;
    player_node *next;
};

player_node *head_linked_list_client = NULL; // Tête de la liste des clients

// Structure pour représenter une partie dans une liste chaînée
struct game_node {
    int id;
    char name[50];
    player_node *player1;
    player_node *player2;
    game_status status; // "waiting" or "ongoing"
    char board[BOARD_SIZE]; // '-' = empty, 'x' = player1, 'o' = player2
    player_node *current_player;
    game_node *next;
};

game_node *head_linked_list_game = NULL; // Tête de la liste des parties

int total_connections = 0; // Nombre total de connexions acceptées
int active_connections = 0; // Nombre de connexions actuellement actives

// Base de données SQLite
sqlite3 *db;
int rc;

// Prototypes des fonctions
int setup_server_socket();

void run_server_loop(int server_socket);

void handle_new_connection(int server_socket);

void handle_client(player_node *client);

void print_client_list();

game_node *find_game_by_name(const char *game_name);

game_node *find_game_by_player(const player_node *client);

void add_client_to_list(int client_socket);

int remove_client_from_list(int client_socket);

game_node *add_game_to_list(const cJSON *json, player_node *client);

int remove_game_from_list(const char *game_name);

void print_game_list();

void process_cmd(player_node *client, const char *command);

void send_packet(player_node *client);

cJSON *create_auth_response_success(const player_node *client);

cJSON *create_auth_response_failure();

cJSON *create_new_account_response_success(const player_node *client);

cJSON *create_disconnect_response();

cJSON *create_new_account_response_failure();

cJSON *create_get_lobby_response();

cJSON *create_game_response_success(const game_node *game);

cJSON *create_game_response_failure();

cJSON *create_join_game_response_success();

cJSON *create_join_game_response_failure();

cJSON *create_unknow_response();

cJSON *create_game_over_victory_response(const player_node *winner);

cJSON *create_game_over_defeat_response(const player_node *loser);

cJSON *create_player_stat_json(const player_stat *player_stats);

cJSON *create_ready_to_play_response_success();

cJSON *create_ready_to_play_response_failure();

cJSON *create_alert_start_game_success_for_host(const game_node *game);

cJSON *create_alert_start_game_success_for_joiner(const game_node *game);

cJSON *board_to_json(const char board[BOARD_SIZE]);

cJSON *create_alert_start_game_failure();

cJSON *create_quit_game_response_succes();

cJSON *create_quit_game_response_failure();

cJSON *create_move_response_success(const game_node *game);

cJSON *create_move_response_failure();

cJSON *create_new_board_stat(const game_node *game);

void print_game_info(const game_node *game);

void validate_game_list();

void handle_client_response_type(player_node *client, const char *request_type, const cJSON *json);

char *handle_ready_to_play_response(const player_node *client);

char *handle_auth_response(const cJSON *json, player_node *client);

char *handle_new_account_response(const cJSON *json, player_node *client);

char *handle_get_lobby_response();

char *handle_disconnect_response(player_node *client);

char *handle_create_game_response(const cJSON *json, player_node *client);

char *handle_join_game_response(const cJSON *json, player_node *client);

int add_client_to_game(game_node *game, player_node *client);

void forfeit_game(const game_node *game, player_node *forfeiter);

void complete_client_node(player_node *client, const player_node *client_db, const cJSON *json);

void empty_client(player_node *client);

void print_board(const char board[BOARD_SIZE]);

void initialize_board(char board[BOARD_SIZE]);

int insert_player(sqlite3 *db, const char *username, const char *password);

int update_player(sqlite3 *db, const player_node *player);

int delete_player(sqlite3 *db, int id);

player_node *select_player(sqlite3 *db, const char *search_colum, const char *search_value);

int connect_to_db(sqlite3 **db);

void hash_password(const char *password, char *hashed_password);

// Fonction principale
int main() {
    connect_to_db(&db); // Se connecter à la base de données SQLite
    const int server_socket = setup_server_socket(); // Configurer le socket serveur
    printf("Serveur en écoute sur le port %d\n", PORT);

    run_server_loop(server_socket); // Lancer la boucle principale
    close(server_socket); // Fermer le socket principal*/
    return 0;
}

// Fonction pour hacher le mot de passe avec SHA-256
void hash_password(const char *password, char *hashed_password) {
    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int length;

    EVP_MD_CTX *context = EVP_MD_CTX_new();
    if (!context) {
        fprintf(stderr, "Erreur création contexte SHA-256.\n");
        return;
    }

    if (EVP_DigestInit_ex(context, EVP_sha3_256(), NULL) != 1 ||
        EVP_DigestUpdate(context, password, strlen(password)) != 1 ||
        EVP_DigestFinal_ex(context, hash, &length) != 1) {
        fprintf(stderr, "Erreur hachage SHA-256.\n");
        EVP_MD_CTX_free(context);
        return;
    }

    EVP_MD_CTX_free(context);

    // Convertir le hash en une chaîne hexadécimale
    for (unsigned int i = 0; i < length; ++i) {
        sprintf(&hashed_password[i * 2], "%02x", hash[i]);
    }
    hashed_password[length * 2] = '\0'; // Ajouter un terminateur de chaîne
}

int connect_to_db(sqlite3 **db) {
    if (sqlite3_open("pente-game.db", db) != SQLITE_OK) {
        fprintf(stderr, "Erreur ouverture DB: %s\n", sqlite3_errmsg(*db));
        return 0;
    }
    printf("Connexion à la base de données réussie.\n");
    return 1;
}

int insert_player(sqlite3 *db, const char *username, const char *password) {
    const char *sql = "INSERT INTO Players (username, password) VALUES (?, ?);";
    sqlite3_stmt *stmt;
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) != SQLITE_OK) {
        fprintf(stderr, "Erreur préparation: %s\n", sqlite3_errmsg(db));
        return 0;
    }

    // hash le mot de passes avant de l'envoyer en db
    char hashed_password[EVP_MAX_MD_SIZE * 2 + 1];
    hash_password(password, hashed_password);
    printf("Hashed password: %s\n", hashed_password);

    sqlite3_bind_text(stmt, 1, username, -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 2, hashed_password, -1, SQLITE_STATIC);

    const int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    if (rc != SQLITE_DONE) {
        fprintf(stderr, "Erreur insertion: %s\n", sqlite3_errmsg(db));
        return 0;
    }
    return 1;
}

int update_player(
    sqlite3 *db,
    const player_node *player
) {
    const char *sql =
            "UPDATE Players SET victories = ?, defeats = ?, forfeits = ?, games_played = ?, score = ? WHERE id = ?;";
    sqlite3_stmt *stmt;
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) != SQLITE_OK) {
        fprintf(stderr, "Erreur préparation: %s\n", sqlite3_errmsg(db));
        return -1;
    }
    sqlite3_bind_int(stmt, 1, player->player_stats.wins);
    sqlite3_bind_int(stmt, 2, player->player_stats.losses);
    sqlite3_bind_int(stmt, 3, player->player_stats.forfeits);
    sqlite3_bind_int(stmt, 4, player->player_stats.games_played);
    sqlite3_bind_int(stmt, 5, player->player_stats.score);
    sqlite3_bind_int(stmt, 6, player->id);

    const int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        fprintf(stderr, "Erreur mise à jour: %s\n", sqlite3_errmsg(db));
        return -1;
    }
    return 0;
}

int delete_player(sqlite3 *db, const int id) {
    const char *sql = "DELETE FROM Players WHERE id = ?;";
    sqlite3_stmt *stmt;
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) != SQLITE_OK) {
        fprintf(stderr, "Erreur préparation: %s\n", sqlite3_errmsg(db));
        return -1;
    }
    sqlite3_bind_int(stmt, 1, id);

    const int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        fprintf(stderr, "Erreur suppression: %s\n", sqlite3_errmsg(db));
        return -1;
    }
    return 0;
}

player_node *select_player(sqlite3 *db, const char *search_colum, const char *search_value) {
    const char *sql = strcat(strcat("SELECT * FROM players WHERE ", search_colum), " = ?;");
    sqlite3_stmt *stmt;
    player_node *player = NULL;

    if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) != SQLITE_OK) {
        fprintf(stderr, "Erreur préparation: %s\n", sqlite3_errmsg(db));
        return NULL;
    }

    sqlite3_bind_text(stmt, 1, search_value, -1, SQLITE_STATIC);

    if (sqlite3_step(stmt) == SQLITE_ROW) {
        player = (player_node *) malloc(sizeof(player_node));
        if (player == NULL) {
            fprintf(stderr, "Erreur allocation mémoire.\n");
            sqlite3_finalize(stmt);
            return NULL;
        }

        player->id = sqlite3_column_int(stmt, 0);
        const char *username = (const char *) sqlite3_column_text(stmt, 1);
        const char *password = (const char *) sqlite3_column_text(stmt, 2);
        snprintf(player->username, sizeof(player->username), "%s", username ? username : "");
        snprintf(player->password, sizeof(player->password), "%s", password ? password : "");
        player->player_stats.forfeits = sqlite3_column_int(stmt, 3);
        player->player_stats.wins = sqlite3_column_int(stmt, 4);
        player->player_stats.losses = sqlite3_column_int(stmt, 5);
        player->player_stats.games_played = sqlite3_column_int(stmt, 6);
        player->player_stats.score = sqlite3_column_int(stmt, 7);
    } else {
        fprintf(stderr, "Joueur introuvable.\n");
    }

    sqlite3_finalize(stmt);
    return player;
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
    const player_node *current = head_linked_list_client;
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

game_node *find_game_by_player(const player_node *client) {
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
    player_node *new_node = malloc(sizeof(player_node));
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
    player_node **current = &head_linked_list_client;
    while (*current) {
        player_node *entry = *current;
        if (entry->socket == client_socket) {
            printf("Suppression du client %s\n", entry->username);
            *current = entry->next; // Supprimer le client de la liste
            free(entry); // Libérer la mémoire associée au client
            active_connections--;
            const game_node *game = find_game_by_player(entry);
            if (game && game->status == waiting) {
                remove_game_from_list(game->name);
            }

            if (*current == NULL) {
                head_linked_list_client = NULL; // Si la liste est vide, assigner NULL à la tête
            }

            return 1; // Client trouvé et supprimé
        }
        current = &entry->next; // Passer au client suivant
    }
    return 0; // Client non trouvé
}

game_node *add_game_to_list(const cJSON *json, player_node *client) {
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


int remove_game_from_list(const char *game_name) {
    game_node **current = &head_linked_list_game;
    while (*current) {
        game_node *entry = *current;
        if (strcmp(entry->name, game_name) == 0) {
            printf("Removing game %s\n", game_name);
            *current = entry->next; // Remove the game from the list
            free(entry); // Free the memory associated with the game

            // Vérification : Si la liste devient vide, mettre head à NULL
            if (*current == NULL) {
                head_linked_list_game = NULL;
            }

            printf("Game removed\n");
            print_game_list();
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
        player_node *current = head_linked_list_client;
        while (current) {
            FD_SET(current->socket, &read_fds);
            if (current->socket > max_fd) {
                max_fd = current->socket;
            }
            current = current->next;
        }

        // Attendre l'activité sur un descripteur
        struct timeval timeout;
        timeout.tv_sec = 0;
        timeout.tv_usec = 1000;
        const int activity = select(max_fd + 1, &read_fds, NULL, NULL, &timeout);
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
            player_node *next = current->next; // Sauvegarder le pointeur suivant
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
void handle_client(player_node *client) {
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

cJSON *create_auth_response_success(const player_node *client) {
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

cJSON *create_new_account_response_success(const player_node *client) {
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
    cJSON_AddNumberToObject(response, "status", failure);

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

cJSON *create_game_over_victory_response(const player_node *winner) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "game_over");
    cJSON_AddNumberToObject(response, "status", victory);

    const char *board = winner->current_game ? winner->current_game->board : "";
    cJSON_AddStringToObject(response, "board", board);

    cJSON *player_stats = create_player_stat_json(&winner->player_stats);
    cJSON_AddItemToObject(response, "player_stats", player_stats);

    return response;
}

cJSON *create_game_over_defeat_response(const player_node *loser) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "game_over");
    cJSON_AddNumberToObject(response, "status", defeat);

    const char *board = loser->current_game ? loser->current_game->board : "";
    cJSON_AddStringToObject(response, "board", board);

    cJSON *player_stats = create_player_stat_json(&loser->player_stats);
    cJSON_AddItemToObject(response, "player_stats", player_stats);

    return response;
}

cJSON *create_player_stat_json(const player_stat *player_stats) {
    cJSON *player_stats_json = cJSON_CreateObject();
    cJSON_AddNumberToObject(player_stats_json, "score", player_stats->score);
    cJSON_AddNumberToObject(player_stats_json, "wins", player_stats->wins);
    cJSON_AddNumberToObject(player_stats_json, "losses", player_stats->losses);
    cJSON_AddNumberToObject(player_stats_json, "forfeits", player_stats->forfeits);
    cJSON_AddNumberToObject(player_stats_json, "games_played", player_stats->games_played);

    return player_stats_json;
}

cJSON *board_to_json(const char board[BOARD_SIZE]) {
    cJSON *json_board = cJSON_CreateString(board);
    if (!json_board) {
        fprintf(stderr, "Erreur : Impossible de créer une chaîne JSON.\n");
        return NULL;
    }
    return json_board;
}

void initialize_board(char board[BOARD_SIZE]) {
    memset(board, '-', BOARD_SIZE); // Remplir le tableau avec des tirets
    board[(BOARD_ROWS / 2) * BOARD_COLS + (BOARD_COLS / 2)] = PLAYER1_CHAR; // Joueur 1
    printf("Board initialized\n");
}

cJSON *create_alert_start_game_success_for_host(const game_node *game) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "alert_start_game");
    cJSON_AddNumberToObject(response, "status", success);

    // FIXME : changer en chaine de caractères
    cJSON *board = board_to_json(game->board);
    cJSON_AddItemToObject(response, "board", board);

    cJSON *opponent_info = create_player_stat_json(&game->player2->player_stats);
    cJSON_AddStringToObject(opponent_info, "name", game->player2->username);
    cJSON_AddItemToObject(response, "opponent_info", opponent_info);

    cJSON_AddStringToObject(response, "game_name", game->name);

    print_board(game->board);

    return response;
}

cJSON *create_alert_start_game_success_for_joiner(const game_node *game) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "alert_start_game");
    cJSON_AddNumberToObject(response, "status", success);

    // FIXME : changer en chaine de caractères
    cJSON *board = board_to_json(game->board);
    cJSON_AddItemToObject(response, "board", board);

    cJSON *opponent_info = create_player_stat_json(&game->player1->player_stats);
    cJSON_AddStringToObject(opponent_info, "name", game->player1->username);
    cJSON_AddItemToObject(response, "opponent_info", opponent_info);

    cJSON_AddStringToObject(response, "game_name", game->name);

    print_board(game->board);

    return response;
}

cJSON *create_alert_start_game_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "alert_start_game");
    cJSON_AddNumberToObject(response, "status", failure);

    return response;
}

cJSON *create_quit_game_response_succes() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "quit_game_response");
    cJSON_AddNumberToObject(response, "status", success);

    return response;
}

cJSON *create_quit_game_response_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "quit_game_response");
    cJSON_AddNumberToObject(response, "status", failure);

    return response;
}

cJSON *create_move_response_success(const game_node *game) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "move_response");
    cJSON_AddNumberToObject(response, "status", success);
    cJSON_AddItemToObject(response, "board_state", board_to_json(game->board));

    return response;
}

cJSON *create_move_response_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "move_response");
    cJSON_AddNumberToObject(response, "status", failure);

    return response;
}

cJSON *create_new_board_stat(const game_node *game) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "new_board_state");
    cJSON_AddNumberToObject(response, "status", success);
    cJSON_AddItemToObject(response, "board_state", board_to_json(game->board));

    return response;
}

void complete_client_node(player_node *client, const player_node *client_db, const cJSON *json) {
    const cJSON *username = cJSON_GetObjectItemCaseSensitive(json, "username");
    const cJSON *password = cJSON_GetObjectItemCaseSensitive(json, "password");

    const cJSON *player_stats = cJSON_GetObjectItemCaseSensitive(json, "player_stats");
    const cJSON *score = cJSON_CreateNumber(client_db->player_stats.score);
    const cJSON *wins = cJSON_CreateNumber(client_db->player_stats.wins);
    const cJSON *losses = cJSON_CreateNumber(client_db->player_stats.losses);
    const cJSON *forfeits = cJSON_CreateNumber(client_db->player_stats.forfeits);
    const cJSON *games_played = cJSON_CreateNumber(client_db->player_stats.games_played);

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

    if (forfeits && cJSON_IsNumber(forfeits)) {
        client->player_stats.forfeits = forfeits->valueint;
    }

    if (games_played && cJSON_IsNumber(games_played)) {
        client->player_stats.games_played = games_played->valueint;
    }

    client->is_authenticated = 1;
}

void empty_client(player_node *client) {
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

void print_board(const char board[BOARD_SIZE]) {
    printf("   ");
    for (int x = 0; x < BOARD_COLS; x++) {
        printf("%2d ", x + 1); // Affiche les numéros de colonnes
    }
    printf("\n");

    for (int y = 0; y < BOARD_ROWS; y++) {
        printf("%2d ", y + 1); // Affiche les numéros de lignes
        for (int x = 0; x < BOARD_COLS; x++) {
            printf(" %c ", board[y * BOARD_COLS + x]); // Affiche directement le contenu de la case
        }
        printf("\n");
    }
    printf("\n");
}

char *handle_auth_response(const cJSON *json, player_node *client) {
    const cJSON *password = cJSON_GetObjectItemCaseSensitive(json, "password");

    // Vérifie si le champ "password" existe et est une chaîne valide
    if (!password || !cJSON_IsString(password)) {
        return cJSON_Print(create_auth_response_failure());
    }

    const player_node *player_db = select_player(db, "username", client->username);
    // unsigned char hashed_password[SHA256_DIGSET_LENGTH];
    // const char *client_password = password->valuestring;
    // Calcul du hachage SHA256
    // SHA256((unsigned char *) client_password, strlen(client_password), hashed_password);
    //printf("Hashed password: %s\n", hashed_password);

    // Si player existe en DB, le mot de passe est incorrect, retourne une réponse d'échec
    // TODO : Hacher le password recu du client
    if (
        !player_db // &&
        //strcmp(hashed_password, player_db->password) != 0
    ) {
        return cJSON_Print(create_auth_response_failure());
    }

    // Authentification réussie
    complete_client_node(client, player_db, json);
    print_client_list();
    return cJSON_Print(create_auth_response_success(client));
}


char *handle_new_account_response(const cJSON *json, player_node *client) {
    const cJSON *password = cJSON_GetObjectItemCaseSensitive(json, "password");
    const cJSON *conf_password = cJSON_GetObjectItemCaseSensitive(json, "conf_password");

    if (
        !password ||
        !conf_password ||
        strcmp(password->valuestring, conf_password->valuestring) != 0
    ) {
        return cJSON_Print(create_new_account_response_failure());
    }

    if (!insert_player(db, client->username, client->password)) {
        return cJSON_Print(create_new_account_response_failure());
    }

    return cJSON_Print(create_new_account_response_success(client));
}


char *handle_get_lobby_response() {
    char *response_string = NULL;
    response_string = cJSON_Print(create_get_lobby_response());
    return response_string;
}

char *handle_disconnect_response(player_node *client) {
    empty_client(client);

    char *response_string = cJSON_Print(create_disconnect_response());
    return response_string;
}

char *handle_create_game_response(const cJSON *json, player_node *client) {
    const char *game_name = cJSON_GetObjectItemCaseSensitive(json, "game_name")->valuestring;
    if (find_game_by_name(game_name)) {
        printf("Game already exists\n");
        return cJSON_Print(create_game_response_failure());
    }

    game_node *game = add_game_to_list(json, client);
    if (!game) {
        printf("Error creating game\n");
        return cJSON_Print(create_game_response_failure());
    }

    client->current_game = game;

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
    printf("Nom: %s\n", game->name);

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

int add_client_to_game(game_node *game, player_node *client) {
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

void forfeit_game(const game_node *game, player_node *forfeiter) {
    // Déterminer le gagnant
    player_node *winner = game->player1 == forfeiter ? game->player2 : game->player1;

    // Mettre à jour les scores
    winner->player_stats.wins++;
    winner->player_stats.score += 100;
    winner->player_stats.games_played++;
    winner->current_game = NULL;
    forfeiter->player_stats.losses++;
    forfeiter->player_stats.score -= 100;
    forfeiter->player_stats.games_played++;
    forfeiter->player_stats.forfeits++;
    forfeiter->current_game = NULL;

    // Écrire dans les buffers d'envoi
    char *victory_response = cJSON_Print(create_game_over_victory_response(winner));
    snprintf(winner->send_buffer, BUFFER_SIZE, "%s", victory_response);
    free(victory_response);

    // Envoyer les paquets
    send_packet(winner);

    // Update en DB
    update_player(db, forfeiter);
    update_player(db, winner);

    // Retirer la partie de la liste chaînée
    remove_game_from_list(game->name);
}

char *handle_join_game_response(const cJSON *json, player_node *client) {
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

    client->current_game = game;
    print_game_list();

    return cJSON_Print(create_join_game_response_success());
}

char *handle_ready_to_play_response(const player_node *client) {
    game_node *game = find_game_by_player(client);
    if (!game) {
        return cJSON_Print(create_ready_to_play_response_failure());
    }

    if (!game->player1 || !game->player2) {
        return cJSON_Print(create_ready_to_play_response_failure());
    }

    game->status = ongoing;
    game->current_player = game->player2;
    initialize_board(game->board);

    snprintf(
        game->player1->send_buffer,
        BUFFER_SIZE,
        "%s",
        cJSON_Print(create_alert_start_game_success_for_host(game))
    );
    send_packet(game->player1);

    return cJSON_Print(create_alert_start_game_success_for_joiner(game));
}

char *handle_quit_game_response(player_node *client) {
    game_node *game = client->current_game;
    if (!game) {
        return cJSON_Print(create_quit_game_response_failure());
    }

    if (game->status == ongoing) {
        forfeit_game(game, client);
    }

    // Cas ou la partie est en attente "waiting"
    remove_game_from_list(game->name);
    return cJSON_Print(create_quit_game_response_succes());
}

int count_in_direction(
    const char *board,
    const int start_x,
    const int start_y,
    const int dx,
    const int dy,
    const char player_char
) {
    int count = 0;
    for (int i = 1; i < 5; i++) {
        const int x = start_x + i * dx;
        const int y = start_y + i * dy;

        if (
            x >= 0 && x < BOARD_COLS &&
            y >= 0 && y < BOARD_ROWS &&
            board[y * BOARD_COLS + x] == player_char
        ) {
            count++;
        } else {
            break;
        }
    }
    return count;
}

int check_alignements(
    const char *board,
    const int last_x,
    const int last_y,
    const char player_char
) {
    // Vérifier les 4 directions : horizontal, vertical, diagonale principale, diagonale secondaire
    const int directions[4][2] = {
        {1, 0}, // Horizontal
        {0, 1}, // Vertical
        {1, 1}, // Diagonale principale
        {1, -1} // Diagonale secondaire
    };

    for (int i = 0; i < 4; i++) {
        const int dx = directions[i][0];
        const int dy = directions[i][1];

        // Compte les pions dans les deux directions
        int total = 1; // Inclut le dernier coup
        total += count_in_direction(board, last_x, last_y, dx, dy, player_char);
        total += count_in_direction(board, last_x, last_y, -dx, -dy, player_char);

        if (total >= 5) {
            return 1; // Alignement trouvé
        }
    }

    return 0; // Aucun alignement
}


int check_captures(
    char *board,
    const int last_x,
    const int last_y,
    const char player_char,
    player_node *client
) {
    printf("Checking captures\n");
    const int directions[8][2] = {
        {1, 0}, // Vers la droite (horizontale)
        {0, 1}, // Vers le bas (verticale)
        {1, 1}, // vers la droite bas (diag
        {1, -1}, // vers la droite haut
        {-1, 0}, // vers la gauche (horizontale)
        {0, -1}, // vers le haut (verticale)
        {-1, -1}, // vers la gauche haut
        {-1, 1} // vers la gauche bas
    };
    const char opponent_char = player_char == PLAYER1_CHAR ? PLAYER2_CHAR : PLAYER1_CHAR;
    int captures = 0;

    for (int i = 0; i < 8; i++) {
        const int dx = directions[i][0];
        const int dy = directions[i][1];

        const int x1 = last_x + dx; // Coup initial + 1
        const int y1 = last_y + dy;
        const int x2 = last_x + 2 * dx; // Coup initial + 2
        const int y2 = last_y + 2 * dy;
        const int x3 = last_x + 3 * dx; // Coup initial + 3
        const int y3 = last_y + 3 * dy;

        if (
            x1 >= 0 && x1 < BOARD_COLS && y1 >= 0 && y1 < BOARD_ROWS &&
            x2 >= 0 && x2 < BOARD_COLS && y2 >= 0 && y2 < BOARD_ROWS &&
            x3 >= 0 && x3 < BOARD_COLS && y3 >= 0 && y3 < BOARD_ROWS &&
            board[y1 * BOARD_COLS + x1] == opponent_char &&
            board[y2 * BOARD_COLS + x2] == opponent_char &&
            board[y3 * BOARD_COLS + x3] == player_char
        ) {
            printf("Capture!\n");
            board[y1 * BOARD_COLS + x1] = EMPTY_CHAR;
            board[y2 * BOARD_COLS + x2] = EMPTY_CHAR;
            captures++;
        }
    }

    client->captures += captures;
    return captures;
}


void handle_win(const game_node *game, player_node *winner, player_node *loser) {
    // Mettre à jour les scores
    winner->player_stats.wins++;
    winner->player_stats.score += 100;
    winner->player_stats.games_played++;

    loser->player_stats.losses++;
    loser->player_stats.score -= 100;
    loser->player_stats.games_played++;

    char *defeat_response = cJSON_Print(create_game_over_defeat_response(loser));
    snprintf(loser->send_buffer, BUFFER_SIZE, "%s", defeat_response);
    free(defeat_response);

    // Envoyer les paquets
    send_packet(loser);

    // Retirer la partie de la liste chaînée
    remove_game_from_list(game->name);
}

cJSON *handle_game_over(player_node *winner, player_node *loser, const game_node *game) {
    handle_win(game, winner, loser); // Met à jour les données du jeu pour la victoire.
    cJSON *response = create_game_over_victory_response(winner); // Crée la réponse JSON pour le gagnant.
    winner->current_game = NULL; // Réinitialise les données de jeu des joueurs.
    loser->current_game = NULL;
    return response;
}

player_node *get_opponent(const game_node *game, const player_node *client) {
    return client == game->player1 ? game->player2 : game->player1;
}


cJSON *handle_play_move_response(const cJSON *json, player_node *client) {
    const cJSON *x = cJSON_GetObjectItemCaseSensitive(json, "x");
    const cJSON *y = cJSON_GetObjectItemCaseSensitive(json, "y");
    game_node *game = client->current_game;

    if (
        !x || !y ||
        !cJSON_IsNumber(x) || !cJSON_IsNumber(y)
    ) {
        return create_move_response_failure();
    }

    if (!game) {
        return create_move_response_failure();
    }

    if (game->status != ongoing) {
        return create_move_response_failure();
    }

    if (game->current_player != client) {
        return create_move_response_failure();
    }

    const int x_val = x->valueint;
    const int y_val = y->valueint;

    if (
        x_val < 0 ||
        x_val >= BOARD_COLS ||
        y_val < 0 ||
        y_val >= BOARD_ROWS
    ) {
        return create_move_response_failure();
    }

    const int index = y_val * BOARD_COLS + x_val;
    if (game->board[index] != EMPTY_CHAR) {
        return create_move_response_failure();
    }

    game->board[index] =
            game->current_player == game->player1 ? PLAYER1_CHAR : PLAYER2_CHAR;
    print_board(game->board);

    player_node *opponent = get_opponent(game, client);
    const char current_char =
            game->current_player == game->player1 ? PLAYER1_CHAR : PLAYER2_CHAR;

    if (
        check_alignements(
            game->board,
            x_val,
            y_val,
            current_char
        )
    ) {
        return handle_game_over(
            client,
            opponent,
            game
        );
    }

    if (
        check_captures(
            game->board,
            x_val,
            y_val,
            current_char,
            client
        )
    ) {
        if (client->captures >= 5) {
            return handle_game_over(
                client,
                opponent,
                game
            );
        }
    }

    game->current_player = opponent;

    snprintf(
        game->current_player->send_buffer,
        BUFFER_SIZE,
        "%s",
        cJSON_Print(create_new_board_stat(game))
    );
    send_packet(game->current_player);

    return create_move_response_success(game);
}

void handle_client_response_type(player_node *client, const char *request_type, const cJSON *json) {
    char *response_string = NULL;

    // TODO: renvoyer des *cJSON au lieu de *char comme handle_play_move_response
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
    } else if (strcmp(request_type, QUIT_GAME_VERB) == 0) {
        response_string = handle_quit_game_response(client);
    } else if (strcmp(request_type, PLAY_MOVE_VERB) == 0) {
        response_string = cJSON_Print(handle_play_move_response(json, client));
    } else {
        response_string = cJSON_Print(create_unknow_response());
    }

    if (response_string != NULL) {
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", response_string);
        free(response_string);
    }
}

void process_cmd(player_node *client, const char *command) {
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

void send_packet(player_node *client) {
    if (strlen(client->send_buffer) > 0) {
        printf("Envoie du paquet à %s\n", client->username);
        send(client->socket, client->send_buffer, strlen(client->send_buffer), 0);
        memset(client->send_buffer, 0, BUFFER_SIZE); // Nettoyer le buffer après envoi
    }
}
