#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <fcntl.h>
#include <sqlite3.h>
#include <time.h>
#include <crypt.h>
#include <tgmath.h>
#include <cjson/cJSON.h>                       // Bibliothèque pour manipuler des objets JSON
#include "types.h"                             // Fichier d'en-tête contenant les structures et les énumérations

#include "json_helpers.c"                      // Fichier d'en-tête contenant les fonctions pour créer des objets JSON

#define PORT 55555                             // Port sur lequel le serveur écoute
#define MAX_CONNECTIONS 10                     // Nombre maximum de connexions actives

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



#define MAX_TIMEOUT_MS 1000                    // Délai d'attente max pour les appels à select()
#define MIN_TIMEOUT_MS 0                       // Délai d'attente min pour les appels à select()

#define BACKLOG 10                             // Taille de la file d'attente pour listen()
#define DB_PATH "pente-game.db"                // Chemin par défaut de la base de données SQLite

player_node *head_linked_list_client = NULL; // Tête de la liste des clients
game_node *head_linked_list_game = NULL; // Tête de la liste des parties

int total_connections = 0; // Nombre total de connexions acceptées
int active_connections = 0; // Nombre de connexions actuellement actives

// Base de données SQLite
sqlite3 *db;
int rc;

// Prototypes des fonctions
void generate_salt(char *salt, size_t length);

int compare_password(const char *input_password, const char *stored_hashed_password);

char *hash_password(const char *password);

int connect_to_db(sqlite3 **db, const char *db_path);

int insert_player(sqlite3 *db, const char *username, const char *password);

int update_player(sqlite3 *db, const player_node *player);

int delete_player(sqlite3 *db, int id);

player_node *select_player(sqlite3 *db, const char *search_column, const char *search_value);

void handle_error(const char *message, int socket_fd);

int setup_server_socket(int port);

void print_client_list();

game_node *find_game_by_name(const char *game_name);

game_node *find_game_by_player(const player_node *client);

void add_client_to_list(int client_socket);

int remove_client_from_list(int client_socket);

game_node *add_game_to_list(player_node *client, const char *game_name);

int remove_game_from_list(const char *game_name);

void print_game_list();

void run_server_loop(int server_socket);

void handle_new_connection(int server_socket);

void handle_client(player_node *client);

void complete_client_node(player_node *client, const player_node *client_db, const cJSON *json);

void empty_client(player_node *client);

void print_board(const char board[BOARD_SIZE]);

char *handle_auth_response(const cJSON *json, player_node *client);

char *handle_new_account_response(const cJSON *json, player_node *client);

char *handle_get_lobby_response();

char *handle_disconnect_response(player_node *client);

char *handle_create_game_response(const cJSON *json, player_node *client);

void print_game_info(const game_node *game);

int add_client_to_game(game_node *game, player_node *client);

void forfeit_game(const game_node *game, player_node *forfeiter);

char *handle_join_game_response(const cJSON *json, player_node *client);

char *handle_ready_to_play_response(const player_node *client);

char *handle_quit_game_response(player_node *client);

int count_in_direction(const char *board, int start_x, int start_y, int dx, int dy, char player_char);

int check_alignements(const char *board, int last_x, int last_y, char player_char);

int check_captures(char *board, int last_x, int last_y, char player_char, player_node *client);

void send_packet(player_node *client);

int calculate_delta(int sg, int sp);

void handle_win(const game_node *game, player_node *winner, player_node *loser);

cJSON *handle_game_over(player_node *winner, player_node *loser, const game_node *game);

player_node *get_opponent(const game_node *game, const player_node *client);

char *handle_play_move_response(const cJSON *json, player_node *client);

void handle_client_response_type(player_node *client, const char *request_type, const cJSON *json);

void process_cmd(player_node *client, const char *command);

int main() {
    // Initialiser le générateur de nombres aléatoires avec une graine moins prévisible
    srand((unsigned int) time(NULL) ^ (unsigned int) getpid());

    // Connexion à la base de données SQLite
    if (!connect_to_db(&db, DB_PATH)) {
        fprintf(stderr, "Échec de connexion à la base de données. Arrêt du programme.\n");
        return EXIT_FAILURE;
    }

    // Configuration du socket serveur
    const int server_socket = setup_server_socket(PORT);
    if (server_socket < 0) {
        fprintf(stderr, "Erreur lors de la configuration du socket serveur. Arrêt du programme.\n");
        sqlite3_close(db);
        return EXIT_FAILURE;
    }

    // Lancer la boucle principale du serveur
    run_server_loop(server_socket);

    // Nettoyage des ressources
    printf("Arrêt du serveur...\n");
    close(server_socket); // Fermer le socket principal
    sqlite3_close(db); // Fermer la connexion à la base de données
    printf("Serveur arrêté proprement.\n");

    return EXIT_SUCCESS;
}

/**
 * @brief Génère un sel aléatoire pour le hachage de mot de passe.
 *
 * Cette fonction crée un sel aléatoire basé sur l'algorithme SHA256 (indiqué par le préfixe "$5$").
 * Le sel est composé de caractères alphanumériques et de symboles spécifiques.
 *
 * @param salt Un pointeur vers le buffer où le sel généré sera stocké.
 *             Ce buffer doit avoir une taille d'au moins `length` octets.
 * @param length La longueur totale du sel, y compris le préfixe et le caractère nul de fin de chaîne.
 *
 * @note La fonction utilise `random()` pour générer des valeurs aléatoires. Assurez-vous d'appeler
 *       `srand()` avec une graine appropriée avant de l'utiliser pour garantir l'unicité du sel.
 * @note Si `length` est inférieur à la taille du préfixe plus 1, la fonction peut entraîner un
 *       comportement indéfini.
 */
void generate_salt(char *salt, const size_t length) {
    const char *charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./";
    const size_t charset_size = strlen(charset);

    // Ajoute un préfixe pour choisir l'algorithme (SHA256 ici, représenté par "$5$")
    strcpy(salt, "$5$");
    const size_t prefix_length = strlen(salt);

    // Remplit le reste du sel avec des caractères aléatoires
    for (size_t i = prefix_length; i < length - 1; i++) {
        salt[i] = charset[random() % charset_size];
    }

    salt[length - 1] = '\0'; // Fin de chaîne
}

/**
 * @brief Compare un mot de passe en clair avec son hachage stocké.
 *
 * Cette fonction extrait le sel du mot de passe haché, recompose le hachage à partir
 * du mot de passe en clair fourni, et compare les deux pour vérifier leur correspondance.
 *
 * @param input_password Le mot de passe en clair saisi par l'utilisateur.
 * @param stored_hashed_password Le mot de passe haché stocké (incluant le sel).
 *                               Le format attendu inclut un préfixe contenant trois
 *                               caractères `$` pour spécifier l'algorithme et le sel.
 *
 * @return `1` si le mot de passe correspond au hachage stocké, `0` sinon.
 *
 * @note La fonction utilise `crypt()` pour générer le hachage du mot de passe saisi.
 *       Assurez-vous que la bibliothèque cryptographique est correctement configurée
 *       dans votre environnement.
 *
 * @note Si le format du hachage stocké est invalide (moins de trois `$`), la fonction
 *       retourne directement `0` après affichage d'un message d'erreur.
 */
int compare_password(const char *input_password, const char *stored_hashed_password) {
    if (!input_password || !stored_hashed_password) {
        fprintf(stderr, "Erreur : entrée invalide dans compare_password.\n");
        return 0;
    }

    char salt[64] = {0};
    size_t dollar_count = 0;

    // Extraction sécurisée du sel
    for (size_t i = 0; i < strlen(stored_hashed_password) && i < sizeof(salt) - 1; i++) {
        salt[i] = stored_hashed_password[i];
        if (stored_hashed_password[i] == '$') {
            dollar_count++;
            if (dollar_count == 3) {
                salt[i + 1] = '\0';
                break;
            }
        }
    }

    if (dollar_count != 3) {
        fprintf(stderr, "Erreur : format du hachage invalide.\n");
        return 0;
    }

    // Comparaison des hachages
    char *rehashed_password = crypt(input_password, salt);
    if (!rehashed_password) {
        perror("Erreur lors du hachage");
        return 0;
    }

    return strcmp(rehashed_password, stored_hashed_password) == 0;
}


/**
 * @brief Hache un mot de passe en utilisant un sel aléatoire.
 *
 * Cette fonction génère un sel aléatoire, puis utilise la fonction `crypt` pour hacher
 * le mot de passe fourni. Elle retourne une copie allouée dynamiquement du mot de passe
 * haché, incluant le sel.
 *
 * @param password Le mot de passe en clair à hacher.
 *
 * @return Un pointeur vers une chaîne contenant le mot de passe haché en cas de succès,
 *         ou `NULL` en cas d'erreur. La chaîne retournée doit être libérée par l'appelant.
 *
 * @note La fonction utilise `generate_salt` pour créer le sel. Assurez-vous que cette
 *       fonction est correctement implémentée.
 *
 * @note En cas d'échec de la fonction `crypt`, un message d'erreur est affiché via `perror`.
 */
char *hash_password(const char *password) {
    // Génère un sel aléatoire
    char salt[20];
    generate_salt(salt, sizeof(salt));

    // Hache le mot de passe
    char *hashed_password = crypt(password, salt);
    if (!hashed_password) {
        perror("Erreur de hachage");
        return NULL;
    }

    return strdup(hashed_password); // Retourne une copie pour éviter les problèmes de mémoire
}


/**
 * @brief Connecte à une base de données SQLite.
 *
 * Cette fonction ouvre une connexion à une base de données SQLite spécifiée
 * et retourne un handle à travers le paramètre `db`. En cas d'erreur, un message
 * est affiché, et la fonction retourne une valeur d'échec.
 *
 * @param db Un pointeur vers un pointeur de type `sqlite3` où sera stocké
 *           le handle de la base de données si la connexion réussit.
 * @param db_path Chemin vers le fichier de la base de données. Si NULL, utilise un chemin par défaut.
 *
 * @return `1` si la connexion à la base de données est réussie, `0` en cas d'échec.
 */
int connect_to_db(sqlite3 **db, const char *db_path) {
    if (!db) {
        fprintf(stderr, "Erreur : le paramètre `db` est NULL.\n");
        return 0;
    }

    if (!db_path) {
        db_path = DB_PATH; // Utiliser le chemin par défaut si aucun n'est fourni
    }

    const int rc = sqlite3_open(db_path, db);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Erreur ouverture DB (%s) : %s\n", db_path, sqlite3_errmsg(*db));
        sqlite3_close(*db); // Libération des ressources en cas d'échec
        *db = NULL; // Assurez-vous que le pointeur est NULL pour éviter les utilisations accidentelles
        return 0;
    }

    printf("Connexion à la base de données réussie : %s\n", db_path);
    return 1;
}


/**
 * @brief Insère un nouveau joueur dans la table Players de la base de données.
 *
 * @param db Pointeur vers l'objet SQLite.
 * @param username Nom d'utilisateur à insérer.
 * @param password Mot de passe à hacher et à insérer.
 * @return 1 si l'insertion réussit, 0 en cas d'erreur.
 */
int insert_player(sqlite3 *db, const char *username, const char *password) {
    if (!db || !username || !password || strlen(username) == 0 || strlen(password) == 0) {
        fprintf(stderr, "Paramètres invalides : db, username ou password est NULL ou vide.\n");
        return 0;
    }

    const char *sql = "INSERT INTO Players (username, password) VALUES (?, ?);";
    sqlite3_stmt *stmt = NULL;
    char *hashed = NULL;
    int result = 0; // Indique succès ou échec

    // Préparation de la requête SQL
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) != SQLITE_OK) {
        fprintf(stderr, "Erreur lors de la préparation de la requête : %s\n", sqlite3_errmsg(db));
        return 0;
    }

    // Hachage du mot de passe
    hashed = hash_password(password);
    if (!hashed) {
        fprintf(stderr, "Erreur lors du hachage du mot de passe.\n");
        sqlite3_finalize(stmt);
        return 0;
    }

    // Liaison des paramètres à la requête
    if (sqlite3_bind_text(stmt, 1, username, -1, SQLITE_TRANSIENT) != SQLITE_OK ||
        sqlite3_bind_text(stmt, 2, hashed, -1, SQLITE_TRANSIENT) != SQLITE_OK) {
        fprintf(stderr, "Erreur lors de la liaison des paramètres : %s\n", sqlite3_errmsg(db));
        sqlite3_finalize(stmt);
        free(hashed);
        return 0;
    }

    // Exécution de la requête
    const int rc = sqlite3_step(stmt);
    if (rc == SQLITE_DONE) {
        result = 1; // Succès
    } else {
        fprintf(stderr, "Erreur lors de l'insertion : %s\n", sqlite3_errmsg(db));
    }

    // Libération des ressources
    sqlite3_finalize(stmt);
    free(hashed);

    return result;
}

/**
 * @brief Met à jour les statistiques d'un joueur dans la base de données.
 *
 * Cette fonction met à jour les colonnes "wins", "losses", "forfeits", "played_games",
 * et "score" pour un joueur spécifique identifié par son `player_id`.
 *
 * @param db Un pointeur vers le handle de la base de données SQLite.
 * @param player Un pointeur vers une structure `player_node` contenant les informations
 *               du joueur à mettre à jour.
 *
 * @return `0` si la mise à jour réussit, `-1` en cas d'échec.
 *
 * @note La fonction utilise une requête SQL paramétrée pour éviter les injections SQL.
 *
 * @note En cas d'erreur (préparation, liaison des paramètres ou exécution de la requête),
 *       un message d'erreur est affiché via `sqlite3_errmsg`.
 */
int update_player(sqlite3 *db, const player_node *player) {
    if (!db) {
        fprintf(stderr, "Erreur : base de données invalide.\n");
        return -1;
    }
    if (!player) {
        fprintf(stderr, "Erreur : joueur invalide.\n");
        return -1;
    }

    const char *sql =
            "UPDATE Players SET "
            "wins = ?, "
            "losses = ?, "
            "forfeits = ?, "
            "played_games = ?, "
            "score = ? "
            "WHERE player_id = ?;";
    sqlite3_stmt *stmt = NULL;

    // Préparer la requête SQL
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) != SQLITE_OK) {
        fprintf(stderr, "Erreur préparation de la requête : %s\n", sqlite3_errmsg(db));
        return -1;
    }

    // Lier les paramètres
    if (
        sqlite3_bind_int(stmt, 1, player->player_stats.wins) != SQLITE_OK ||
        sqlite3_bind_int(stmt, 2, player->player_stats.losses) != SQLITE_OK ||
        sqlite3_bind_int(stmt, 3, player->player_stats.forfeits) != SQLITE_OK ||
        sqlite3_bind_int(stmt, 4, player->player_stats.games_played) != SQLITE_OK ||
        sqlite3_bind_int(stmt, 5, player->player_stats.score) != SQLITE_OK ||
        sqlite3_bind_int(stmt, 6, player->id) != SQLITE_OK
    ) {
        fprintf(stderr, "Erreur lors de la liaison des paramètres : %s\n", sqlite3_errmsg(db));
        sqlite3_finalize(stmt);
        return -1;
    }

    // Exécuter la requête
    const int rc = sqlite3_step(stmt);
    if (rc != SQLITE_DONE) {
        fprintf(stderr, "Erreur lors de la mise à jour du joueur : %s\n", sqlite3_errmsg(db));
        sqlite3_finalize(stmt);
        return -1;
    }

    // Libérer les ressources
    sqlite3_finalize(stmt);
    printf("Statistiques du joueur avec l'id %d mises à jour avec succès.\n", player->id);
    return 0;
}

/**
 * @brief Supprime un joueur de la base de données en fonction de son identifiant.
 *
 * Cette fonction supprime un enregistrement dans la table "Players" basé sur
 * l'identifiant unique du joueur (`id`).
 *
 * @param db Un pointeur vers le handle de la base de données SQLite.
 * @param id L'identifiant unique du joueur à supprimer.
 *
 * @return `0` si la suppression réussit, `-1` en cas d'erreur.
 *
 * @note En cas d'erreur, un message est affiché sur la sortie standard d'erreur via `fprintf`.
 */
int delete_player(sqlite3 *db, const int id) {
    if (!db) {
        fprintf(stderr, "Erreur : handle de base de données invalide.\n");
        return -1;
    }

    const char *sql = "DELETE FROM Players WHERE id = ?;";
    sqlite3_stmt *stmt = NULL;

    // Préparer la requête SQL
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) != SQLITE_OK) {
        fprintf(stderr, "Erreur préparation de la requête DELETE : %s\n", sqlite3_errmsg(db));
        return -1;
    }

    // Lier l'identifiant du joueur
    if (sqlite3_bind_int(stmt, 1, id) != SQLITE_OK) {
        fprintf(stderr, "Erreur lors de la liaison de l'identifiant : %s\n", sqlite3_errmsg(db));
        sqlite3_finalize(stmt);
        return -1;
    }

    // Exécuter la requête
    const int rc = sqlite3_step(stmt);
    if (rc != SQLITE_DONE) {
        fprintf(stderr, "Erreur lors de la suppression du joueur : %s\n", sqlite3_errmsg(db));
        sqlite3_finalize(stmt);
        return -1;
    }

    // Libérer les ressources
    sqlite3_finalize(stmt);
    printf("Joueur avec l'id %d supprimé avec succès.\n", id);
    return 0;
}


/**
 * @brief Recherche un joueur dans la base de données selon une colonne et une valeur spécifiques.
 *
 * Cette fonction exécute une requête SQL pour rechercher un joueur dans la table "players"
 * en fonction d'une colonne et d'une valeur fournies. Si un joueur est trouvé, ses données
 * sont stockées dans une structure `player_node` allouée dynamiquement.
 *
 * @param db Un pointeur vers le handle de la base de données SQLite.
 * @param search_column La colonne de la table à utiliser pour la recherche.
 * @param search_value La valeur à rechercher dans la colonne spécifiée.
 *
 * @return Un pointeur vers une structure `player_node` si un joueur est trouvé,
 *         ou `NULL` en cas d'erreur ou si aucun joueur ne correspond.
 *
 * @note L'appelant doit libérer la mémoire de la structure retournée avec `free()`.
 */
player_node *select_player(sqlite3 *db, const char *search_column, const char *search_value) {
    if (!db || !search_column || !search_value) {
        fprintf(stderr, "Erreur : paramètres invalides pour select_player.\n");
        return NULL;
    }

    // Vérification de la colonne pour éviter les injections SQL
    const char *valid_columns[] = {"id", "username", "password", "forfeits", "wins", "losses", "games_played", "score"};
    const size_t num_columns = sizeof(valid_columns) / sizeof(valid_columns[0]);
    int is_valid_column = 0; // Utilisation d'un entier pour valider la colonne

    for (size_t i = 0; i < num_columns; i++) {
        if (strcmp(search_column, valid_columns[i]) == 0) {
            is_valid_column = 1;
            break;
        }
    }

    if (!is_valid_column) {
        fprintf(stderr, "Erreur : colonne de recherche non valide : %s\n", search_column);
        return NULL;
    }

    // Préparation de la requête SQL
    char sql[256];
    snprintf(sql, sizeof(sql), "SELECT * FROM players WHERE %s = ?;", search_column);

    sqlite3_stmt *stmt = NULL;
    player_node *player = NULL;

    if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) != SQLITE_OK) {
        fprintf(stderr, "Erreur préparation de la requête : %s\n", sqlite3_errmsg(db));
        return NULL;
    }

    sqlite3_bind_text(stmt, 1, search_value, -1, SQLITE_STATIC);

    // Exécution de la requête
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        player = (player_node *) malloc(sizeof(player_node));
        if (!player) {
            fprintf(stderr, "Erreur : échec de l'allocation mémoire pour le joueur.\n");
            sqlite3_finalize(stmt);
            return NULL;
        }

        // Récupération des données du joueur
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
        fprintf(stderr, "Joueur introuvable pour %s = %s.\n", search_column, search_value);
    }

    sqlite3_finalize(stmt);
    return player;
}

/**
 * @brief Gère les erreurs critiques et ferme les ressources si nécessaire.
 *
 * @param message Message d'erreur à afficher.
 * @param socket_fd Le descripteur de socket à fermer, ou -1 s'il n'y en a pas.
 */
void handle_error(const char *message, const int socket_fd) {
    perror(message);
    if (socket_fd != -1) {
        close(socket_fd);
    }
    exit(EXIT_FAILURE);
}

/**
 * @brief Configure un socket serveur TCP en mode non-bloquant.
 *
 * @param port Le port sur lequel le serveur écoute.
 * @return Le descripteur du socket configuré.
 */
int setup_server_socket(const int port) {
    struct sockaddr_in server_addr;

    // Créer un socket TCP
    const int server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket == -1) {
        handle_error("Erreur lors de la création du socket", -1);
    }

    // Réutiliser l'adresse et le port immédiatement après fermeture
    const int opt = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) == -1) {
        handle_error("Erreur avec setsockopt", server_socket);
    }

    // Mettre le socket en mode non-bloquant
    const int flags = fcntl(server_socket, F_GETFL, 0);
    if (flags == -1) {
        handle_error("Erreur fcntl F_GETFL", server_socket);
    }

    if (fcntl(server_socket, F_SETFL, flags | O_NONBLOCK) == -1) {
        handle_error("Erreur fcntl F_SETFL", server_socket);
    }

    // Configurer l'adresse du serveur
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET; // IPv4
    server_addr.sin_addr.s_addr = INADDR_ANY; // Accepter des connexions depuis n'importe quelle IP
    server_addr.sin_port = htons(port); // Convertir le port en format réseau

    // Associer le socket à l'adresse et au port
    if (bind(server_socket, (struct sockaddr *) &server_addr, sizeof(server_addr)) == -1) {
        handle_error("Erreur avec bind", server_socket);
    }

    // Mettre le socket en mode écoute
    if (listen(server_socket, BACKLOG) == -1) {
        handle_error("Erreur avec listen", server_socket);
    }

    printf("Serveur en écoute sur le port %d...\n", port);
    return server_socket;
}

/**
 * @brief Affiche la liste des clients connectés et leur état d'authentification.
 *
 * Parcourt une liste chaînée de clients et affiche pour chacun le nom et l'état
 * d'authentification. Si la liste est vide, affiche un message approprié.
 */
void print_client_list() {
    const player_node *current_node = head_linked_list_client;

    if (!current_node) {
        printf("The client list is empty.\n");
        return;
    }

    int index = 0;
    printf("Client list:\n");
    while (current_node) {
        printf(
            "%d. Client name = %s, is_authenticated = %s\n",
            index++,
            current_node->username,
            current_node->is_authenticated ? "true" : "false"
        );
        current_node = current_node->next;
    }
}

/**
 * @brief Recherche une partie dans une liste chaînée par son nom.
 *
 * Parcourt une liste chaînée de jeux pour trouver un nœud correspondant
 * au nom spécifié. Si aucune partie correspondant n'est trouvé, retourne `NULL`.
 *
 * @param game_name Nom de la partie à rechercher (non NULL).
 * @return Pointeur vers le nœud correspondant si trouvé, sinon NULL.
 */
game_node *find_game_by_name(const char *game_name) {
    game_node *current = head_linked_list_game;

    while (current && strcmp(current->name, game_name) != 0) {
        current = current->next; // Passe au nœud suivant.
    }

    return current; // Retourne le nœud trouvé ou NULL si introuvable.
}

/**
 * @brief Recherche une partie dans une liste chaînée en fonction d'un joueur.
 *
 * Parcourt une liste chaînée de jeux pour trouver une partie où le joueur
 * spécifié est impliqué en tant que `player1` ou `player2`. Si aucune
 * correspondance n'est trouvée, retourne `NULL`.
 *
 * @param client Pointeur vers le nœud du joueur à rechercher (non NULL).
 * @return Pointeur vers le nœud de la partie trouvée, ou NULL si introuvable.
 */
game_node *find_game_by_player(const player_node *client) {
    game_node *current = head_linked_list_game;

    // Parcourt la liste des parties pour trouver une correspondance avec le joueur.
    while (current && current->player1 != client && current->player2 != client) {
        current = current->next;
    }

    return current; // Retourne le nœud correspondant ou NULL si introuvable.
}

/**
 * @brief Ajoute un client à la liste chaînée des joueurs connectés.
 *
 * Cette fonction crée un nouveau nœud pour représenter un client,
 * l'ajoute au début de la liste chaînée des clients et envoie un message
 * de bienvenue au client via son socket.
 *
 * @param client_socket Le descripteur de socket associé au client à ajouter.
 */
void add_client_to_list(const int client_socket) {
    // Allouer de la mémoire pour le nouveau noeud.
    player_node *new_node = malloc(sizeof(player_node));
    if (!new_node) {
        perror("Erreur d'allocation mémoire pour un nouveau client");
        return;
    }

    // Initialisation des champs du nœud.
    new_node->is_authenticated = 0; // Le client n'est pas authentifié par défaut.
    new_node->socket = client_socket; // Associer le socket du client.
    new_node->next = head_linked_list_client; // Ajouter le noeud en tête de liste.
    head_linked_list_client = new_node; // Mettre à jour la tête de la liste.

    // Créer un message de bienvenue.
    cJSON *response = cJSON_CreateObject();
    if (!response) {
        perror("Erreur de création de l'objet JSON pour le message de bienvenue");
        free(new_node); // Libérer la mémoire si la création JSON échoue.
        return;
    }

    cJSON_AddStringToObject(response, "type", "welcome");
    cJSON_AddStringToObject(response, "message", "Bienvenue sur le serveur de jeu multijoueur !");

    // Formater le message et l'envoyer.
    if (snprintf(new_node->send_buffer, BUFFER_SIZE, "%s", cJSON_PrintUnformatted(response)) >= BUFFER_SIZE) {
        fprintf(stderr, "Erreur : le message JSON dépasse la taille du tampon\n");
    } else {
        send_packet(new_node); // Envoyer le message de bienvenue au client.
    }

    // Libérer la mémoire JSON.
    cJSON_Delete(response);
}

/**
 * @brief Supprime un client de la liste chaînée des joueurs connectés.
 *
 * Cette fonction recherche un client par son descripteur de socket, le supprime de la liste chaînée
 * et libère la mémoire associée. Si le client était impliqué dans une partie en attente,
 * cette partie est également supprimée.
 *
 * @param client_socket Descripteur de socket du client à supprimer.
 * @return 1 si le client a été trouvé et supprimé, 0 sinon.
 */
int remove_client_from_list(const int client_socket) {
    player_node **current = &head_linked_list_client;

    while (*current) {
        player_node *entry = *current;

        // Vérifie si le socket correspond au client à supprimer.
        if (entry->socket == client_socket) {
            printf("Suppression du client %s\n", entry->username);

            // Supprimer le client de la liste et libérer la mémoire.
            *current = entry->next;
            free(entry);
            active_connections--;

            // Supprimer une partie en attente si le client y était impliqué.
            const game_node *game = find_game_by_player(entry);
            if (game && game->status == waiting) {
                remove_game_from_list(game->name);
            }

            print_client_list(); // Affiche la liste mise à jour.
            return 1; // Succès : client supprimé.
        }

        current = &entry->next; // Passe au client suivant.
    }

    return 0; // Échec : client non trouvé.
}

/**
 * @brief Ajoute une nouvelle partie à la liste chaînée des jeux.
 *
 * Cette fonction crée une nouvelle partie, l'initialise avec le joueur donné
 * et le nom spécifié, puis l'ajoute en tête de la liste chaînée des jeux.
 *
 * @param client Pointeur vers le joueur qui crée la partie (non NULL).
 * @param game_name Nom de la partie à créer (non NULL).
 * @return Pointeur vers le nœud de la partie créée, ou NULL en cas d'erreur.
 */
game_node *add_game_to_list(player_node *client, const char *game_name) {
    if (!client || !game_name) {
        fprintf(stderr, "Erreur : client ou nom de partie invalide\n");
        return NULL;
    }

    game_node *new_game_node = malloc(sizeof(game_node));
    if (!new_game_node) {
        perror("Erreur d'allocation mémoire pour la partie");
        return NULL;
    }

    // Initialisation de la nouvelle partie.
    new_game_node->player1 = client;
    new_game_node->player2 = NULL;
    new_game_node->status = waiting;
    new_game_node->next = head_linked_list_game;

    // Copie sécurisée du nom de la partie.
    strncpy(new_game_node->name, game_name, sizeof(new_game_node->name) - 1);
    new_game_node->name[sizeof(new_game_node->name) - 1] = '\0'; // Assurer la terminaison.

    // Ajout de la partie à la liste.
    head_linked_list_game = new_game_node;

    printf(
        "Nouvelle partie ajoutée : Nom=%s, Créateur=%s, État=%s\n",
        new_game_node->name,
        client->username,
        "waiting"
    );

    return new_game_node;
}


/**
 * @brief Supprime une partie de la liste chaînée de parties.
 *
 * Cette fonction recherche une partie dans une liste chaînée par son nom et, s'il
 * est trouvé, le supprime de la liste tout en libérant la mémoire associée.
 *
 * @param game_name Nom de la partoe à supprimer (doit être une chaîne non nulle).
 * @return int Retourne 1 si la partie a été trouvé et supprimé avec succès,
 *         0 sinon.
 *
 * @note La liste chaînée est supposée être gérée via une variable globale
 *       `head_linked_list_game`. Assurez-vous que cette variable est correctement
 *       initialisée avant d'appeler cette fonction.
 */
int remove_game_from_list(const char *game_name) {
    if (!game_name) {
        fprintf(stderr, "Erreur : le nom de la partie ne peut pas être NULL.\n");
        return 0; // Indique une erreur d'entrée
    }

    game_node **current = &head_linked_list_game;

    while (*current) {
        game_node *entry = *current;

        if (strcmp(entry->name, game_name) == 0) {
            printf("Suppression de la partie : %s\n", game_name);

            *current = entry->next; // Réorganisation des pointeurs
            free(entry); // Libération de la mémoire

            printf("Partie supprimé avec succès.\n");

            // Affichage de la liste si nécessaire
            if (head_linked_list_game) {
                print_game_list();
            }
            return 1; // Succès
        }

        current = &entry->next; // Passage au nœud suivant
    }

    fprintf(stderr, "Partie non trouvé dans la liste : %s\n", game_name);
    return 0; // Échec
}

/**
 * @brief Affiche la liste des jeux disponibles.
 *
 * Cette fonction parcourt la liste chaînée des jeux et affiche les informations
 * détaillées sur chaque partie, y compris l'ID, le nom, les joueurs et l'état.
 *
 * @note Si la liste est vide, un message approprié est affiché.
 */
void print_game_list() {
    const game_node *current = head_linked_list_game;
    int i = 0;

    if (!current) {
        // La liste est vide
        printf("Aucune partie disponible.\n");
        return;
    }

    printf("Liste des parties disponibles :\n");

    while (current) {
        printf("%d. ", i++); // Affichage de l'index de la partie
        printf("ID du partie=%d, ", current->id);
        printf("Nom=%s, ", current->name);

        // Informations sur le joueur 1
        if (current->player1) {
            printf("Joueur 1=%s, ", current->player1->username);
        } else {
            printf("Joueur 1=Inconnu, ");
        }

        // Informations sur le joueur 2
        if (current->player2) {
            printf("Joueur 2=%s, ", current->player2->username);
        } else {
            printf("Joueur 2=Inconnu, ");
        }

        // État de la partie
        printf("État=%s\n", current->status == waiting ? "En attente" : "En cours");

        current = current->next; // Passage à la partie suivante
    }
}


/**
 * @brief Lance la boucle principale du serveur pour gérer les connexions et l'activité des clients.
 *
 * Cette fonction écoute les descripteurs de fichiers en attente d'activité, notamment :
 * - Les nouvelles connexions sur le socket du serveur.
 * - Les messages ou événements des clients connectés.
 *
 * @param server_socket Socket principal du serveur, utilisé pour accepter de nouvelles connexions.
 *
 * @details
 * - Utilise `select` pour surveiller les descripteurs de fichiers.
 * - Gère les nouvelles connexions via `handle_new_connection`.
 * - Traite les clients actifs via `handle_client`.
 *
 * @note
 * - La liste des clients est supposée être gérée via une structure de type `player_node`
 *   reliée par `head_linked_list_client`.
 * - La fonction ne retourne jamais et se termine uniquement si le processus est interrompu ou en cas d'erreur critique.
 */
void run_server_loop(const int server_socket) {
    fd_set read_fds;
    int max_fd = server_socket; // Initialise le descripteur maximal

    while (1) {
        // Prépare l'ensemble des descripteurs pour `select`
        FD_ZERO(&read_fds); // Réinitialise l'ensemble
        FD_SET(server_socket, &read_fds); // Ajoute le socket principal

        // Ajoute tous les sockets clients à l'ensemble
        player_node *current = head_linked_list_client;
        while (current) {
            FD_SET(current->socket, &read_fds);
            if (current->socket > max_fd) {
                max_fd = current->socket; // Met à jour le descripteur maximal
            }
            current = current->next;
        }

        // Définit un timeout court pour éviter le blocage prolongé
        struct timeval timeout;
        timeout.tv_sec = MIN_TIMEOUT_MS;
        timeout.tv_usec = MAX_TIMEOUT_MS; // Timeout de 1 milliseconde

        // Attend l'activité sur un descripteur
        const int activity = select(max_fd + 1, &read_fds, NULL, NULL, &timeout);
        if (activity < 0) {
            perror("Erreur avec select");
            exit(EXIT_FAILURE); // Termine en cas d'erreur critique
        }

        // Vérifie si une nouvelle connexion est en attente
        if (FD_ISSET(server_socket, &read_fds)) {
            handle_new_connection(server_socket);
        }

        // Parcourt les clients pour vérifier leur activité
        current = head_linked_list_client;
        while (current) {
            player_node *next = current->next; // Sauvegarde le pointeur suivant
            if (FD_ISSET(current->socket, &read_fds)) {
                handle_client(current); // Traite le client actif
            }
            current = next;
        }
    }
}


/**
 * @brief Gère une nouvelle connexion entrante sur le serveur.
 *
 * Cette fonction accepte une nouvelle connexion, vérifie si la limite de connexions
 * actives est atteinte, et met à jour les statistiques de connexions. Si la limite
 * est atteinte, elle refuse la connexion en envoyant un message explicite au client.
 *
 * @param server_socket Socket principal du serveur, utilisé pour accepter les connexions.
 *
 * @details
 * - En cas de succès, le socket client est ajouté à une liste chaînée via `add_client_to_list`.
 * - Les statistiques des connexions (`active_connections` et `total_connections`) sont mises à jour.
 * - Si la limite des connexions actives est atteinte, la connexion est refusée proprement.
 *
 * @note
 * - La fonction utilise les variables globales `active_connections`, `total_connections`,
 *   et `MAX_CONNECTIONS` pour gérer les limites et statistiques.
 * - La liste chaînée des clients est supposée être gérée par `add_client_to_list`.
 */
void handle_new_connection(const int server_socket) {
    struct sockaddr_in client_addr;
    socklen_t addrlen = sizeof(client_addr);

    // Accepter une nouvelle connexion
    const int client_socket = accept(server_socket, (struct sockaddr *) &client_addr, &addrlen);
    if (client_socket < 0) {
        perror("Erreur lors de l'acceptation de la connexion");
        return;
    }

    // Vérifier si le nombre maximum de connexions est atteint
    if (active_connections >= MAX_CONNECTIONS) {
        const char *refus_message = "SERVER_CLOSE: Connexion refusée : Limite atteinte.";
        send(client_socket, refus_message, strlen(refus_message), 0); // Envoyer un message d'erreur
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

    // Log des informations sur la nouvelle connexion
    printf(
        "Nouvelle connexion acceptée : socket %d (IP: %s, PORT: %hu). Connexions actives : %d/%d, Total connexions : %d\n",
        client_socket,
        inet_ntoa(client_addr.sin_addr),
        ntohs(client_addr.sin_port),
        active_connections,
        MAX_CONNECTIONS,
        total_connections
    );

    // Ajouter le client à la liste chaînée des clients
    add_client_to_list(client_socket);
}


/**
 * @brief Gère la communication avec un client connecté.
 *
 * Cette fonction lit les données envoyées par un client via son socket,
 * traite les commandes reçues et gère les déconnexions ou erreurs éventuelles.
 *
 * @param client Pointeur vers la structure `player_node` représentant le client.
 *
 * @details
 * - Les données sont lues dans un tampon de taille définie par `BUFFER_SIZE`.
 * - Si des données valides sont reçues, elles sont terminées correctement par `\0`
 *   pour éviter tout dépassement de tampon.
 * - En cas de déconnexion ou d'erreur de réception, le client est retiré de la liste des connexions.
 *
 * @note
 * - Cette fonction repose sur la fonction `process_cmd` pour analyser et traiter les commandes.
 * - La suppression des clients est effectuée via `remove_client_from_list`.
 */
void handle_client(player_node *client) {
    char command[BUFFER_SIZE];

    // Recevoir des données du client
    const ssize_t bytes_read = recv(client->socket, command, sizeof(command) - 1, 0);

    if (bytes_read > 0) {
        // Traiter les données reçues
        command[bytes_read] = '\0'; // Terminer correctement la chaîne
        printf("Reçu de %d : %s\n", client->socket, command); // Log de débogage
        process_cmd(client, command); // Traiter la commande
    } else if (bytes_read == 0) {
        // Le client s'est déconnecté proprement
        printf("Client %d déconnecté.\n", client->socket);

        // termine la partie si un client est déconnecté
        if (client->current_game) {
            printf("Le client %s a été déconnecté de la partie %s.\n", client->username, client->current_game->name);
            forfeit_game(client->current_game, client);
        }
        remove_client_from_list(client->socket); // Retirer le client
    } else {
        // Une erreur s'est produite lors de la réception
        perror("Erreur lors de la réception");
        remove_client_from_list(client->socket); // Retirer le client
    }
}

/**
 * @brief Complète un nœud de type `player_node` avec les informations d'un JSON et d'une base de données.
 *
 * Cette fonction utilise un objet JSON pour remplir certains champs du nœud `client`, tels que
 * `username` et `password`, puis copie les autres informations directement depuis un nœud de base de données
 * `client_db`. Elle marque également le client comme authentifié et initialise certains champs.
 *
 * @param client Pointeur vers le nœud `player_node` à compléter.
 * @param client_db Pointeur constant vers le nœud `player_node` servant de base de données.
 * @param json Pointeur constant vers l'objet JSON contenant les informations du client.
 */
void complete_client_node(player_node *client, const player_node *client_db, const cJSON *json) {
    // Récupère le champ "username" du JSON
    const cJSON *username = cJSON_GetObjectItemCaseSensitive(json, "username");
    const cJSON *password = cJSON_GetObjectItemCaseSensitive(json, "password");

    // Copie le nom d'utilisateur si présent et valide
    if (username && cJSON_IsString(username)) {
        strncpy(client->username, username->valuestring, sizeof(client->username) - 1);
        client->username[sizeof(client->username) - 1] = '\0'; // Assure une terminaison nulle
    }

    // Copie le mot de passe si présent et valide
    if (password && cJSON_IsString(password)) {
        strncpy(client->password, password->valuestring, sizeof(client->password) - 1);
        client->password[sizeof(client->password) - 1] = '\0'; // Assure une terminaison nulle
    }

    // Copie les informations de base depuis `client_db`
    client->id = client_db->id;

    // Copie les statistiques du joueur
    client->player_stats = client_db->player_stats;

    // Marque le client comme authentifié et initialise d'autres champs
    client->is_authenticated = 1;
    client->captures = 0;
}

/**
 * @brief Réinitialise un nœud de type `player_node` pour le remettre à l'état non authentifié.
 *
 * Cette fonction efface toutes les données sensibles et statistiques du client,
 * le marquant comme non authentifié et réinitialisant ses champs à des valeurs par défaut.
 *
 * @param client Pointeur vers le nœud `player_node` à réinitialiser.
 */
void empty_client(player_node *client) {
    if (!client) {
        fprintf(stderr, "Erreur : Le pointeur client est NULL.\n");
        return;
    }

    // Affichage du client en cours de réinitialisation (utile pour le débogage)
    printf("Réinitialisation du client %s\n", client->username);

    // Réinitialisation de l'état d'authentification
    client->is_authenticated = not_authenticated;

    // Effacement des données sensibles et buffers
    memset(client->username, 0, sizeof(client->username));
    memset(client->password, 0, sizeof(client->password));
    memset(client->recv_buffer, 0, sizeof(client->recv_buffer));
    memset(client->send_buffer, 0, sizeof(client->send_buffer));

    // Réinitialisation des statistiques du joueur
    client->player_stats.score = 0;
    client->player_stats.wins = 0;
    client->player_stats.losses = 0;
    client->player_stats.games_played = 0;

    // Réinitialisation des champs de la partie en cours
    client->current_game = NULL;
    client->captures = 0;
}

/**
 * @brief Affiche le contenu du plateau de la partie sous une forme lisible.
 *
 * Cette fonction affiche un plateau de la partie 2D, avec des indices de colonnes et de lignes pour une meilleure compréhension.
 * Chaque cellule du plateau est affichée avec son contenu.
 *
 * @param board Tableau 1D représentant le plateau de la partie
 *        La taille du tableau est supposée être BOARD_ROWS * BOARD_COLS.
 */
void print_board(const char board[BOARD_SIZE]) {
    // Vérification basique
    if (!board) {
        fprintf(stderr, "Erreur : Le plateau de la partie est NULL.\n");
        return;
    }

    // Affichage de l'en-tête des colonnes
    printf("   "); // Espace initial pour aligner les colonnes avec les lignes
    for (int x = 0; x < BOARD_COLS; x++) {
        printf("%2d ", x + 1); // Numéro de la colonne (décalage de 1 pour démarrer à 1)
    }
    printf("\n");

    // Affichage des lignes du plateau
    for (int y = 0; y < BOARD_ROWS; y++) {
        printf("%2d ", y + 1); // Numéro de la ligne (décalage de 1 pour démarrer à 1)
        for (int x = 0; x < BOARD_COLS; x++) {
            // Affichage de chaque cellule du plateau
            printf(" %c ", board[y * BOARD_COLS + x]);
        }
        printf("\n");
    }
    printf("\n"); // Ligne vide après l'affichage pour aérer
}

/**
 * @brief Gère la réponse d'authentification pour un client.
 *
 * Cette fonction vérifie les informations d'identification fournies par le client
 * (nom d'utilisateur et mot de passe) et tente de les valider contre une base de données.
 * Si l'authentification réussit, les données du client sont mises à jour et une réponse de succès est générée.
 * Sinon, une réponse d'échec est retournée.
 *
 * @param json Objet JSON contenant les informations d'identification du client.
 * @param client Pointeur vers le nœud `player_node` représentant le client à authentifier.
 * @return Chaîne JSON représentant la réponse d'authentification (succès ou échec).
 */
char *handle_auth_response(const cJSON *json, player_node *client) {
    if (!json || !client) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à handle_auth_response.\n");
        return cJSON_Print(create_auth_response_failure());
    }

    printf("Authentification du client en cours...\n");

    // Récupération et vérification du champ "password"
    const cJSON *password = cJSON_GetObjectItemCaseSensitive(json, "password");
    if (!password || !cJSON_IsString(password)) {
        fprintf(stderr, "Erreur : Champ 'password' manquant ou invalide.\n");
        return cJSON_Print(create_auth_response_failure());
    }

    // Récupération et vérification du champ "username"
    const cJSON *username = cJSON_GetObjectItemCaseSensitive(json, "username");
    if (!username || !cJSON_IsString(username)) {
        fprintf(stderr, "Erreur : Champ 'username' manquant ou invalide.\n");
        return cJSON_Print(create_auth_response_failure());
    }

    // Recherche du joueur dans la base de données
    player_node *player_db = select_player(db, "username", username->valuestring);
    if (!player_db) {
        fprintf(stderr, "Erreur : Utilisateur '%s' introuvable dans la base de données.\n", username->valuestring);
        return cJSON_Print(create_auth_response_failure());
    }

    // Vérification du mot de passe
    const char *client_password = password->valuestring;
    if (compare_password(client_password, player_db->password) != 1) {
        fprintf(stderr, "Erreur : Mot de passe incorrect pour l'utilisateur '%s'.\n", username->valuestring);
        free(player_db);
        return cJSON_Print(create_auth_response_failure());
    }

    // Authentification réussie : Mise à jour des informations du client
    complete_client_node(client, player_db, json);
    free(player_db);

    // Afficher la liste des clients pour le suivi (optionnel, utile en débogage)
    print_client_list();

    // Générer une réponse de succès
    return cJSON_Print(create_auth_response_success(client));
}

/**
 * @brief Gère la création d'un nouveau compte utilisateur.
 *
 * Cette fonction valide les informations fournies pour un nouveau compte, notamment la correspondance
 * des mots de passe et la disponibilité du nom d'utilisateur. Elle insère le nouvel utilisateur dans la
 * base de données et met à jour les informations du client en cas de succès.
 *
 * @param json Objet JSON contenant les informations du nouvel utilisateur.
 * @param client Pointeur vers le nœud `player_node` représentant le client créant un compte.
 * @return Chaîne JSON représentant la réponse (succès ou échec).
 */
char *handle_new_account_response(const cJSON *json, player_node *client) {
    if (!json || !client) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à handle_new_account_response.\n");
        return cJSON_Print(create_new_account_response_failure());
    }

    // Récupération des mots de passe
    const cJSON *password = cJSON_GetObjectItemCaseSensitive(json, "password");
    const cJSON *conf_password = cJSON_GetObjectItemCaseSensitive(json, "conf_password");

    // Validation des mots de passe
    if (!password || !conf_password || strcmp(password->valuestring, conf_password->valuestring) != 0) {
        fprintf(stderr, "Erreur : Les mots de passe ne correspondent pas ou sont invalides.\n");
        return cJSON_Print(create_new_account_response_failure());
    }

    // Récupération et validation du nom d'utilisateur
    const cJSON *username = cJSON_GetObjectItemCaseSensitive(json, "username");
    if (!username || !cJSON_IsString(username)) {
        fprintf(stderr, "Erreur : Nom d'utilisateur manquant ou invalide.\n");
        return cJSON_Print(create_new_account_response_failure());
    }

    // Insertion du joueur dans la base de données
    if (!insert_player(db, username->valuestring, password->valuestring)) {
        fprintf(stderr, "Erreur : Échec de l'insertion du joueur dans la base de données.\n");
        return cJSON_Print(create_new_account_response_failure());
    }

    // Récupération des informations utilisateur nouvellement insérées
    player_node *player_db = select_player(db, "username", username->valuestring);
    if (!player_db) {
        fprintf(stderr, "Erreur : Impossible de récupérer le joueur après insertion.\n");
        return cJSON_Print(create_new_account_response_failure());
    }

    // Mise à jour des informations du client
    complete_client_node(client, player_db, json);
    free(player_db);

    // Afficher la liste des clients pour le suivi (optionnel)
    print_client_list();

    // Réponse de succès
    return cJSON_Print(create_new_account_response_success(client));
}

/**
 * @brief Génère une réponse JSON contenant les informations du lobby.
 *
 * Cette fonction crée une réponse JSON détaillant les connexions actives et l'état actuel
 * des parties dans le système. La réponse est prête à être envoyée au client.
 *
 * @return Chaîne JSON représentant la réponse du lobby (à libérer après utilisation).
 */
char *handle_get_lobby_response() {
    // Génère la réponse JSON en utilisant les données disponibles
    cJSON *response_json = create_get_lobby_response(active_connections, head_linked_list_game);
    if (!response_json) {
        fprintf(stderr, "Erreur : Échec de la création de la réponse du lobby.\n");
        return NULL;
    }

    // Convertit l'objet JSON en chaîne
    char *response_string = cJSON_Print(response_json);
    if (!response_string) {
        fprintf(stderr, "Erreur : Échec de la conversion de l'objet JSON en chaîne.\n");
    }

    // Libère l'objet JSON une fois la chaîne créée
    cJSON_Delete(response_json);

    return response_string;
}

/**
 * @brief Gère la déconnexion d'un client et génère une réponse JSON.
 *
 * Cette fonction réinitialise l'état du client déconnecté en appelant `empty_client`
 * et génère une réponse JSON indiquant la réussite de la déconnexion.
 *
 * @param client Pointeur vers le nœud `player_node` représentant le client à déconnecter.
 * @return Chaîne JSON représentant la réponse de déconnexion (à libérer après utilisation).
 */
char *handle_disconnect_response(player_node *client) {
    if (!client) {
        fprintf(stderr, "Erreur : Pointeur client NULL passé à handle_disconnect_response.\n");
        return NULL;
    }

    // Réinitialisation des informations du client
    empty_client(client);

    // Création de la réponse JSON pour la déconnexion
    cJSON *response_json = create_disconnect_response();
    if (!response_json) {
        fprintf(stderr, "Erreur : Échec de la création de la réponse JSON pour la déconnexion.\n");
        return NULL;
    }

    // Conversion de la réponse JSON en chaîne
    char *response_string = cJSON_Print(response_json);
    if (!response_string) {
        fprintf(stderr, "Erreur : Échec de la conversion de la réponse JSON en chaîne.\n");
    }

    // Libération de la mémoire associée à l'objet JSON
    cJSON_Delete(response_json);

    return response_string;
}

/**
 * @brief Gère la création d'une nouvelle partie et génère une réponse JSON.
 *
 * Cette fonction vérifie si une partie portant le même nom existe déjà, puis tente de
 * créer une nouvelle partie. En cas de succès, elle associe le client à cette partie
 * et génère une réponse JSON positive. En cas d'échec, une réponse JSON d'échec est retournée.
 *
 * @param json Objet JSON contenant les informations nécessaires pour créer une partie.
 * @param client Pointeur vers le nœud `player_node` représentant le client initiateur.
 * @return Chaîne JSON représentant la réponse de création de partie (succès ou échec).
 */
char *handle_create_game_response(const cJSON *json, player_node *client) {
    if (!json || !client) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à handle_create_game_response.\n");
        return cJSON_Print(create_game_response_failure());
    }

    // Récupération du nom de la partie à partir du JSON
    const cJSON *game_name_item = cJSON_GetObjectItemCaseSensitive(json, "game_name");
    if (!game_name_item || !cJSON_IsString(game_name_item)) {
        fprintf(stderr, "Erreur : Nom de partie manquant ou invalide dans le JSON.\n");
        return cJSON_Print(create_game_response_failure());
    }
    const char *game_name = game_name_item->valuestring;

    // Vérification si une partie avec ce nom existe déjà
    if (find_game_by_name(game_name)) {
        fprintf(stderr, "Erreur : Une partie nommée '%s' existe déjà.\n", game_name);
        return cJSON_Print(create_game_response_failure());
    }

    // Création de la nouvelle partie
    game_node *game = add_game_to_list(client, game_name);
    if (!game) {
        fprintf(stderr, "Erreur : Échec de la création de la partie.\n");
        return cJSON_Print(create_game_response_failure());
    }

    // Associer le client à la partie nouvellement créée
    client->current_game = game;

    // Affichage des parties pour le débogage
    print_game_list();

    // Génération de la réponse JSON de succès
    return cJSON_Print(create_game_response_success(game));
}


/**
 * @brief Affiche les informations détaillées d'une partie.
 *
 * Cette fonction affiche les informations principales d'une partie, telles que son ID,
 * son nom, les joueurs participants, et son statut actuel. Si un pointeur invalide est fourni,
 * un message d'erreur est affiché.
 *
 * @param game Pointeur constant vers le nœud `game_node` représentant la partie à afficher.
 */
void print_game_info(const game_node *game) {
    if (!game) {
        fprintf(stderr, "Erreur : Le pointeur de la partie est nul.\n");
        return;
    }

    printf("=== Informations de la Partie ===\n");
    printf("ID de la partie       : %d\n", game->id);
    printf("Nom de la partie      : %s\n", game->name);

    // Informations sur le joueur 1
    if (game->player1) {
        printf("Joueur 1              : %s\n", game->player1->username);
    } else {
        printf("Joueur 1              : Aucun joueur connecté\n");
    }

    // Informations sur le joueur 2
    if (game->player2) {
        printf("Joueur 2              : %s\n", game->player2->username);
    } else {
        printf("Joueur 2              : Aucun joueur connecté\n");
    }

    // Affichage du statut de la partie
    printf("Statut de la partie   : %s\n", game->status == waiting ? "En attente" : "En cours");
    printf("================================\n");
}


/**
 * @brief Ajoute un client à une partie si les conditions le permettent.
 *
 * Cette fonction tente d'ajouter un joueur à une partie. Si la partie est déjà en cours ou complète,
 * ou si les paramètres sont invalides, l'ajout échoue.
 *
 * @param game Pointeur vers le nœud `game_node` représentant la partie.
 * @param client Pointeur vers le nœud `player_node` représentant le client à ajouter.
 * @return 1 si le client a été ajouté avec succès, 0 en cas d'échec.
 */
int add_client_to_game(game_node *game, player_node *client) {
    // Vérifications des paramètres et de l'état de la partie
    if (!game) {
        fprintf(stderr, "Erreur : Le pointeur de la partie est nul.\n");
        return 0;
    }

    if (!client) {
        fprintf(stderr, "Erreur : Le pointeur du client est nul.\n");
        return 0;
    }

    if (game->status == ongoing) {
        fprintf(stderr, "Erreur : Impossible d'ajouter un joueur, la partie est déjà en cours.\n");
        return 0;
    }

    // Ajout du joueur à un emplacement libre
    if (!game->player1) {
        printf("Ajout du joueur %s en tant que Joueur 1.\n", client->username);
        game->player1 = client;
    } else if (!game->player2) {
        printf("Ajout du joueur %s en tant que Joueur 2.\n", client->username);
        game->player2 = client;
    } else {
        fprintf(stderr, "Erreur : La partie est déjà pleine.\n");
        return 0;
    }

    return 1; // Ajout réussi
}


/**
 * @brief Gère l'abandon d'une partie par un joueur.
 *
 * Cette fonction met à jour les statistiques des deux joueurs (le perdant et le gagnant),
 * notifie le gagnant de sa victoire via un message, et supprime la partie de la liste des parties actives.
 *
 * @param game Pointeur constant vers le nœud `game_node` représentant la partie en cours.
 * @param forfeiter Pointeur vers le nœud `player_node` représentant le joueur qui abandonne.
 */
void forfeit_game(const game_node *game, player_node *forfeiter) {
    // Validation des paramètres
    if (!game || !forfeiter) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à forfeit_game.\n");
        return;
    }

    // Déterminer le gagnant
    player_node *winner = (game->player1 == forfeiter) ? game->player2 : game->player1;
    if (!winner) {
        fprintf(
            stderr, "Erreur : Impossible de déterminer le gagnant. Les joueurs ne sont pas définis correctement.\n");
        return;
    }

    // Calculer le delta de score
    const int delta = calculate_delta(winner->player_stats.score, forfeiter->player_stats.score);

    // Mettre à jour les statistiques du gagnant
    winner->player_stats.wins++;
    winner->player_stats.score += delta;
    winner->player_stats.games_played++;
    winner->current_game = NULL;

    // Mettre à jour les statistiques du perdant
    forfeiter->player_stats.losses++;
    forfeiter->player_stats.score -= delta;
    forfeiter->player_stats.games_played++;
    forfeiter->player_stats.forfeits++;
    forfeiter->current_game = NULL;

    // Préparer et écrire la réponse de victoire dans le buffer du gagnant
    char *victory_response = cJSON_Print(create_game_over_victory_response(winner));
    if (victory_response) {
        snprintf(winner->send_buffer, BUFFER_SIZE, "%s", victory_response);
        free(victory_response);
    } else {
        fprintf(stderr, "Erreur : Échec de la création de la réponse de victoire.\n");
    }

    // Envoyer les paquets au gagnant
    send_packet(winner);

    // Mettre à jour les informations en base de données
    update_player(db, forfeiter);
    update_player(db, winner);

    // Retirer la partie de la liste des parties actives
    remove_game_from_list(game->name);

    printf("La partie '%s' a été supprimée suite à l'abandon de '%s'.\n", game->name, forfeiter->username);
}

/**
 * @brief Gère la réponse pour qu'un joueur rejoigne une partie.
 *
 * Cette fonction vérifie si une partie avec le nom donné existe, tente d'ajouter le joueur
 * à la partie, et renvoie une réponse JSON en fonction du succès ou de l'échec de l'opération.
 *
 * @param json Objet JSON contenant les informations nécessaires pour rejoindre une partie.
 * @param client Pointeur vers le nœud `player_node` représentant le joueur tentant de rejoindre la partie.
 * @return Chaîne JSON représentant la réponse (succès ou échec). À libérer après utilisation.
 */
char *handle_join_game_response(const cJSON *json, player_node *client) {
    if (!json || !client) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à handle_join_game_response.\n");
        return cJSON_Print(create_join_game_response_failure());
    }

    // Récupération du nom de la partie depuis le JSON
    const cJSON *game_name_item = cJSON_GetObjectItemCaseSensitive(json, "game_name");
    if (!game_name_item || !cJSON_IsString(game_name_item)) {
        fprintf(stderr, "Erreur : Nom de partie manquant ou invalide dans le JSON.\n");
        return cJSON_Print(create_join_game_response_failure());
    }
    const char *game_name = game_name_item->valuestring;

    // Recherche de la partie par nom
    game_node *game = find_game_by_name(game_name);
    if (!game) {
        fprintf(stderr, "Erreur : Partie '%s' introuvable.\n", game_name);
        return cJSON_Print(create_join_game_response_failure());
    }

    // Tentative d'ajouter le joueur à la partie
    if (add_client_to_game(game, client) != 1) {
        fprintf(stderr, "Erreur : Impossible de rejoindre la partie '%s' (pleine ou déjà commencée).\n", game_name);
        return cJSON_Print(create_join_game_response_failure());
    }

    // Mise à jour de la partie actuelle pour le client
    client->current_game = game;

    // Affichage de la liste des parties pour le suivi
    print_game_list();

    // Retourner une réponse de succès
    return cJSON_Print(create_join_game_response_success());
}


/**
 * @brief Gère la réponse d'un joueur signalant qu'il est prêt à jouer.
 *
 * Cette fonction vérifie que la partie est prête à commencer (deux joueurs présents),
 * initialise le plateau de la partie, met à jour l'état de la partie, et envoie une notification
 * aux joueurs pour indiquer le début de la partie.
 *
 * @param client Pointeur constant vers le nœud `player_node` représentant le joueur signalant sa disponibilité.
 * @return Chaîne JSON représentant la réponse (succès ou échec) pour l'autre joueur. À libérer après utilisation.
 */
char *handle_ready_to_play_response(const player_node *client) {
    if (!client) {
        fprintf(stderr, "Erreur : Le pointeur du client est NULL.\n");
        return cJSON_Print(create_ready_to_play_response_failure());
    }

    // Trouver la partie associée au joueur
    game_node *game = find_game_by_player(client);
    if (!game) {
        fprintf(stderr, "Erreur : Aucune partie associée au joueur '%s'.\n", client->username);
        return cJSON_Print(create_ready_to_play_response_failure());
    }

    // Vérifier que les deux joueurs sont présents
    if (!game->player1 || !game->player2) {
        fprintf(stderr, "Erreur : La partie '%s' n'est pas prête. Deux joueurs sont requis.\n", game->name);
        return cJSON_Print(create_ready_to_play_response_failure());
    }

    // Initialiser le plateau et mettre à jour l'état de la partie
    initialize_board(game->board, EMPTY_CHAR);
    game->status = ongoing;
    game->current_player = game->player2;

    // Notifier le joueur hôte que la partie commence
    char *host_message = cJSON_Print(create_alert_start_game_success_for_host(game));
    if (host_message) {
        snprintf(game->player1->send_buffer, BUFFER_SIZE, "%s", host_message);
        free(host_message);
        send_packet(game->player1);
    } else {
        fprintf(stderr, "Erreur : Échec de la création du message pour l'hôte.\n");
    }

    // Retourner la réponse pour l'autre joueur
    return cJSON_Print(create_alert_start_game_success_for_joiner(game));
}


/**
 * @brief Gère la déconnexion d'un joueur d'une partie.
 *
 * Cette fonction vérifie si le joueur fait partie d'une partie en cours ou en attente. Si la partie est en cours,
 * elle gère l'abandon du joueur (forfeit) et met à jour l'état de la partie et des joueurs. Ensuite, elle supprime
 * la partie de la liste des parties actives et renvoie une réponse JSON appropriée.
 *
 * @param client Pointeur vers le nœud `player_node` représentant le joueur quittant la partie.
 * @return Chaîne JSON représentant la réponse (succès ou échec). À libérer après utilisation.
 */
char *handle_quit_game_response(player_node *client) {
    // Vérification du pointeur client
    if (!client) {
        fprintf(stderr, "Erreur : Le pointeur du client est NULL.\n");
        return cJSON_Print(create_quit_game_response_failure());
    }

    // Vérifier si le joueur est actuellement dans une partie
    game_node *game = client->current_game;
    if (!game) {
        fprintf(stderr, "Erreur : Le joueur '%s' n'est pas dans une partie.\n", client->username);
        return cJSON_Print(create_quit_game_response_failure());
    }

    // Si la partie est en cours, gérer l'abandon
    if (game->status == ongoing) {
        fprintf(stdout, "Le joueur '%s' abandonne la partie '%s'.\n", client->username, game->name);
        forfeit_game(game, client);
    }

    // Si la partie est en attente, la supprimer directement
    if (game->status == waiting) {
        fprintf(stdout, "La partie '%s' est en attente. Suppression de la partie.\n", game->name);
        remove_game_from_list(game->name);
    }

    // Mettre à jour les informations du client
    client->current_game = NULL;

    // Générer une réponse JSON de succès
    return cJSON_Print(create_quit_game_response_success(&client->player_stats));
}


/**
 * @brief Compte le nombre de jetons alignés dans une direction donnée sur le plateau.
 *
 * Cette fonction parcourt le plateau de la partie dans une direction spécifique (définie par `dx` et `dy`)
 * à partir d'une position de départ `(start_x, start_y)` pour compter le nombre de jetons appartenant
 * au joueur spécifié par `player_char`.
 *
 * @param board Tableau représentant le plateau de la partie (de taille BOARD_ROWS * BOARD_COLS).
 * @param start_x Coordonnée x de départ.
 * @param start_y Coordonnée y de départ.
 * @param dx Direction sur l'axe x (peut être -1, 0 ou 1).
 * @param dy Direction sur l'axe y (peut être -1, 0 ou 1).
 * @param player_char Caractère représentant le joueur dont les jetons doivent être comptés.
 * @return Le nombre de jetons alignés dans la direction spécifiée pour le joueur donné.
 */
int count_in_direction(
    const char *board,
    const int start_x,
    const int start_y,
    const int dx,
    const int dy,
    const char player_char
) {
    // Vérification des paramètres
    if (!board) {
        fprintf(stderr, "Erreur : Le pointeur du plateau est NULL.\n");
        return 0;
    }

    int count = 0;

    // Parcourt jusqu'à 4 cases dans la direction spécifiée
    for (int i = 1; i < 5; i++) {
        // Calcul des nouvelles coordonnées
        const int x = start_x + i * dx;
        const int y = start_y + i * dy;

        // Vérifie si les coordonnées sont valides et si le jeton correspond
        if (x >= 0 && x < BOARD_COLS && y >= 0 && y < BOARD_ROWS) {
            if (board[y * BOARD_COLS + x] == player_char) {
                count++;
            } else {
                break; // Arrête si la case ne correspond pas
            }
        } else {
            break; // Arrête si on sort des limites du plateau
        }
    }

    return count;
}

/**
 * @brief Vérifie si un joueur a formé un alignement gagnant à partir de son dernier coup.
 *
 * Cette fonction vérifie les alignements possibles (horizontal, vertical, diagonale principale et diagonale secondaire)
 * à partir des coordonnées du dernier coup joué. Si un alignement de 5 pions ou plus est trouvé, elle retourne 1,
 * sinon elle retourne 0.
 *
 * @param board Tableau représentant le plateau de la partie (de taille BOARD_ROWS * BOARD_COLS).
 * @param last_x Coordonnée x du dernier coup joué.
 * @param last_y Coordonnée y du dernier coup joué.
 * @param player_char Caractère représentant le joueur à vérifier.
 * @return 1 si un alignement gagnant est trouvé, 0 sinon.
 */
int check_alignements(
    const char *board,
    const int last_x,
    const int last_y,
    const char player_char
) {
    // Vérification des paramètres
    if (!board) {
        fprintf(stderr, "Erreur : Le pointeur du plateau est NULL.\n");
        return 0;
    }

    // Définition des directions pour les alignements : horizontal, vertical, diagonales
    const int directions[4][2] = {
        {1, 0}, // Horizontal
        {0, 1}, // Vertical
        {1, 1}, // Diagonale principale
        {1, -1} // Diagonale secondaire
    };

    // Parcourir chaque direction pour vérifier les alignements
    for (int i = 0; i < 4; i++) {
        const int dx = directions[i][0];
        const int dy = directions[i][1];

        // Compte les jetons alignés dans les deux sens de la direction
        int total = 1; // Inclut le dernier coup
        total += count_in_direction(board, last_x, last_y, dx, dy, player_char);
        total += count_in_direction(board, last_x, last_y, -dx, -dy, player_char);

        // Si un alignement de 5 jetons ou plus est trouvé, retourner 1
        if (total >= 5) {
            return 1;
        }
    }

    // Aucun alignement trouvé
    return 0;
}

/**
 * @brief Vérifie si un joueur a capturé des jetons adverses suite à son dernier coup.
 *
 * Cette fonction examine toutes les directions autour du dernier coup joué pour détecter
 * des captures valides. Une capture est définie comme deux jetons adverses consécutifs suivis
 * d'un jeton du joueur. Si une capture est détectée, les jetons adverses sont retirés du plateau.
 *
 * @param board Tableau représentant le plateau de la partie (de taille BOARD_ROWS * BOARD_COLS).
 * @param last_x Coordonnée x du dernier coup joué.
 * @param last_y Coordonnée y du dernier coup joué.
 * @param player_char Caractère représentant le joueur ayant joué le dernier coup.
 * @param client Pointeur vers le joueur ayant joué le dernier coup (pour mettre à jour les captures).
 * @return Nombre total de captures effectuées.
 */
int check_captures(
    char *board,
    const int last_x,
    const int last_y,
    const char player_char,
    player_node *client
) {
    // Vérification des paramètres
    if (!board || !client) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à check_captures.\n");
        return 0;
    }

    printf("Checking captures for player '%c' at position (%d, %d)\n", player_char, last_x, last_y);

    // Directions à vérifier (8 directions autour du dernier coup)
    const int directions[8][2] = {
        {1, 0}, // Droite (horizontale)
        {0, 1}, // Bas (verticale)
        {1, 1}, // Diagonale droite-bas
        {1, -1}, // Diagonale droite-haut
        {-1, 0}, // Gauche (horizontale)
        {0, -1}, // Haut (verticale)
        {-1, -1}, // Diagonale gauche-haut
        {-1, 1} // Diagonale gauche-bas
    };

    // Déterminer le caractère de l'adversaire
    const char opponent_char = player_char == PLAYER1_CHAR ? PLAYER2_CHAR : PLAYER1_CHAR;
    int captures = 0;

    // Parcourir chaque direction pour détecter des captures
    for (int i = 0; i < 8; i++) {
        const int dx = directions[i][0];
        const int dy = directions[i][1];

        // Calcul des positions successives
        const int x1 = last_x + dx;
        const int y1 = last_y + dy;
        const int x2 = last_x + 2 * dx;
        const int y2 = last_y + 2 * dy;
        const int x3 = last_x + 3 * dx;
        const int y3 = last_y + 3 * dy;

        // Vérification des limites et conditions de capture
        if (
            x1 >= 0 && x1 < BOARD_COLS && y1 >= 0 && y1 < BOARD_ROWS &&
            x2 >= 0 && x2 < BOARD_COLS && y2 >= 0 && y2 < BOARD_ROWS &&
            x3 >= 0 && x3 < BOARD_COLS && y3 >= 0 && y3 < BOARD_ROWS &&
            board[y1 * BOARD_COLS + x1] == opponent_char &&
            board[y2 * BOARD_COLS + x2] == opponent_char &&
            board[y3 * BOARD_COLS + x3] == player_char
        ) {
            printf("Capture detected at (%d, %d) and (%d, %d)\n", x1, y1, x2, y2);

            // Retirer les jetons adverses capturés
            board[y1 * BOARD_COLS + x1] = EMPTY_CHAR;
            board[y2 * BOARD_COLS + x2] = EMPTY_CHAR;
            captures++;
        }
    }

    // Mettre à jour le nombre de captures du joueur
    client->captures += captures;

    // Retourner le nombre total de captures
    return captures;
}

/**
 * @brief Calcule la variation de score à appliquer après une partie.
 *
 * Cette fonction utilise une formule pour calculer la variation de score (`delta`)
 * basée sur les scores actuels des deux joueurs.
 *
 * @param sg Score actuel du gagnant (doit être positif).
 * @param sp Score actuel du perdant (doit être positif).
 * @return La variation de score calculée, ou -1 en cas d'erreur de validation.
 */
int calculate_delta(const int sg, const int sp) {
    // Validation des paramètres
    if (sg < 0 || sp < 0) {
        fprintf(stderr, "Erreur : Les scores doivent être positifs.\n");
        return -1;
    }

    return round(30.0 / (1.0 + pow(10.0, (sg - sp) / 400.0)));
}

/**
 * @brief Gère la fin d'une partie où un joueur est déclaré gagnant.
 *
 * Cette fonction met à jour les scores et les statistiques des joueurs (gagnant et perdant),
 * notifie le perdant de sa défaite et supprime la partie de la liste active.
 *
 * @param game Pointeur constant vers le nœud `game_node` représentant la partie.
 * @param winner Pointeur vers le joueur gagnant.
 * @param loser Pointeur vers le joueur perdant.
 */
void handle_win(const game_node *game, player_node *winner, player_node *loser) {
    // Validation des paramètres
    if (!game || !winner || !loser) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à handle_win.\n");
        return;
    }

    // Calculer la variation de score
    const int delta = calculate_delta(loser->player_stats.score, winner->player_stats.score);
    if (delta < 0) {
        fprintf(stderr, "Erreur : Échec du calcul du delta.\n");
        return;
    }

    printf("Delta: %d\n", delta);

    // Mettre à jour les scores et statistiques du gagnant
    winner->player_stats.wins++;
    winner->player_stats.score += delta;
    winner->player_stats.games_played++;

    // Mettre à jour les scores et statistiques du perdant
    loser->player_stats.losses++;
    loser->player_stats.score -= delta;
    loser->player_stats.games_played++;

    // Préparer et envoyer la réponse de défaite au perdant
    char *defeat_response = cJSON_Print(create_game_over_defeat_response(loser));
    if (defeat_response) {
        snprintf(loser->send_buffer, BUFFER_SIZE, "%s", defeat_response);
        free(defeat_response);
        send_packet(loser);
    } else {
        fprintf(stderr, "Erreur : Échec de la création de la réponse de défaite.\n");
    }

    // Mettre à jour les informations des joueurs dans la base de données
    update_player(db, winner);
    update_player(db, loser);

    // Retirer la partie de la liste active
    remove_game_from_list(game->name);

    printf("Partie '%s' terminée. Gagnant : %s, Perdant : %s\n",
           game->name, winner->username, loser->username);
}

/**
 * @brief Gère la fin d'une partie en mettant à jour les données des joueurs et en générant une réponse JSON.
 *
 * Cette fonction met à jour les statistiques des joueurs, réinitialise leur état de la partie, et retourne
 * une réponse JSON indiquant la victoire du gagnant.
 *
 * @param winner Pointeur vers le joueur gagnant.
 * @param loser Pointeur vers le joueur perdant.
 * @param game Pointeur constant vers le nœud `game_node` représentant la partie terminée.
 * @return Pointeur vers un objet JSON représentant la réponse de victoire pour le gagnant.
 *         Retourne `NULL` en cas d'erreur.
 */
cJSON *handle_game_over(player_node *winner, player_node *loser, const game_node *game) {
    // Validation des paramètres
    if (!winner || !loser || !game) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à handle_game_over.\n");
        return NULL;
    }

    // Gérer la victoire
    handle_win(game, winner, loser);

    // Créer une réponse JSON pour le gagnant
    cJSON *response = create_game_over_victory_response(winner);
    if (!response) {
        fprintf(stderr, "Erreur : Échec de la création de la réponse de victoire pour le gagnant '%s'.\n",
                winner->username);
        return NULL;
    }

    // Réinitialiser l'état de la partie des joueurs
    winner->current_game = NULL;
    loser->current_game = NULL;

    return response;
}

/**
 * @brief Renvoie le joueur adverse dans une partie.
 *
 * Cette fonction détermine l'adversaire d'un joueur donné dans une partie.
 *
 * @param game Pointeur constant vers le nœud `game_node` représentant la partie.
 * @param client Pointeur constant vers le joueur pour lequel l'adversaire est recherché.
 * @return Pointeur vers le joueur adverse, ou `NULL` si le joueur n'est pas trouvé ou si les paramètres sont invalides.
 */
player_node *get_opponent(const game_node *game, const player_node *client) {
    // Validation des paramètres
    if (!game || !client) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à get_opponent.\n");
        return NULL;
    }

    // Retourner l'adversaire si le client est l'un des deux joueurs de la partie
    if (client == game->player1) {
        return game->player2;
    } else if (client == game->player2) {
        return game->player1;
    }

    // Le client n'est pas dans cette partie
    fprintf(stderr, "Erreur : Le joueur spécifié n'est pas associé à la partie.\n");
    return NULL;
}

/**
 * @brief Gère une tentative de placement de jeton sur le plateau par un joueur.
 *
 * Cette fonction vérifie la validité du coup, met à jour le plateau, vérifie les alignements gagnants et les captures,
 * puis met à jour le statut de la partie ou bascule au tour de l'adversaire si nécessaire.
 *
 * @param json Objet JSON contenant les coordonnées du coup joué.
 * @param client Pointeur vers le joueur effectuant le coup.
 * @return Objet JSON représentant la réponse (succès, échec ou fin de partie).
 */
char *handle_play_move_response(const cJSON *json, player_node *client) {
    // Vérification des paramètres de base
    if (!json || !client) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à handle_play_move_response.\n");
        return cJSON_Print(create_move_response_failure());
    }

    // Extraction des coordonnées
    const cJSON *x = cJSON_GetObjectItemCaseSensitive(json, "x");
    const cJSON *y = cJSON_GetObjectItemCaseSensitive(json, "y");
    if (!x || !y || !cJSON_IsNumber(x) || !cJSON_IsNumber(y)) {
        fprintf(stderr, "Erreur : Coordonnées invalides dans la requête.\n");
        return cJSON_Print(create_move_response_failure());
    }

    game_node *game = client->current_game;
    if (!game) {
        fprintf(stderr, "Erreur : Le joueur n'est associé à aucune partie.\n");
        return cJSON_Print(create_move_response_failure());
    }

    if (game->status != ongoing) {
        fprintf(stderr, "Erreur : La partie n'est pas en cours.\n");
        return cJSON_Print(create_move_response_failure());
    }

    if (game->current_player != client) {
        fprintf(stderr, "Erreur : Ce n'est pas le tour du joueur '%s'.\n", client->username);
        return cJSON_Print(create_move_response_failure());
    }

    // Validation des coordonnées
    const int x_val = x->valueint;
    const int y_val = y->valueint;
    if (x_val < 0 || x_val >= BOARD_COLS || y_val < 0 || y_val >= BOARD_ROWS) {
        fprintf(stderr, "Erreur : Coordonnées hors limites.\n");
        return cJSON_Print(create_move_response_failure());
    }

    const int index = y_val * BOARD_COLS + x_val;
    if (game->board[index] != EMPTY_CHAR) {
        fprintf(stderr, "Erreur : La case (%d, %d) est déjà occupée.\n", x_val, y_val);
        return cJSON_Print(create_move_response_failure());
    }

    // Placement du jeton
    const char player_char = game->current_player == game->player1 ? PLAYER1_CHAR : PLAYER2_CHAR;
    game->board[index] = player_char;
    print_board(game->board);

    // Vérification des alignements gagnants
    player_node *opponent = get_opponent(game, client);
    const char current_char = player_char;

    if (check_alignements(game->board, x_val, y_val, current_char)) {
        return cJSON_Print(handle_game_over(client, opponent, game));
    }

    // Vérification des captures
    if (check_captures(game->board, x_val, y_val, current_char, client)) {
        if (client->captures >= 5) {
            return cJSON_Print(handle_game_over(client, opponent, game));
        }
    }

    // Passer au tour de l'adversaire
    game->current_player = opponent;

    // Envoyer la mise à jour de l'état du plateau à l'adversaire
    char *board_update = cJSON_Print(create_new_board_stat(game));
    if (board_update) {
        snprintf(game->current_player->send_buffer, BUFFER_SIZE, "%s", board_update);
        free(board_update);
        send_packet(game->current_player);
    } else {
        fprintf(stderr, "Erreur : Échec de la création de la mise à jour du plateau.\n");
    }

    // Retourner une réponse de succès pour le joueur actuel
    return cJSON_Print(create_move_response_success(game, client));
}

/**
 * @brief Gère les types de requêtes reçues d'un client et génère une réponse appropriée.
 *
 * Cette fonction détermine le type de requête reçu et appelle la fonction correspondante pour traiter la requête.
 * Les réponses sont générées sous forme d'objets JSON.
 *
 * @param client Pointeur vers le joueur (client) ayant envoyé la requête.
 * @param request_type Chaîne représentant le type de requête.
 * @param json Objet JSON contenant les détails de la requête.
 */
void handle_client_response_type(player_node *client, const char *request_type, const cJSON *json) {
    // Validation des paramètres
    if (!client || !request_type || !json) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à handle_client_response_type.\n");
        return;
    }

    char *response = NULL;

    // Traitement des différents types de requêtes
    if (strcmp(request_type, AUTHENTICATION_VERB) == 0) {
        response = handle_auth_response(json, client);
    } else if (strcmp(request_type, NEW_ACCOUNT_VERB) == 0) {
        response = handle_new_account_response(json, client);
    } else if (strcmp(request_type, GET_LOBBY_VERB) == 0) {
        response = handle_get_lobby_response(); // Conversion de chaîne en JSON
    } else if (strcmp(request_type, DISCONNECT_VERB) == 0) {
        response = handle_disconnect_response(client);
    } else if (strcmp(request_type, CREATE_GAME_VERB) == 0) {
        response = handle_create_game_response(json, client);
    } else if (strcmp(request_type, JOIN_GAME_VERB) == 0) {
        response = handle_join_game_response(json, client);
    } else if (strcmp(request_type, READY_TO_PLAY_VERB) == 0) {
        response = handle_ready_to_play_response(client);
    } else if (strcmp(request_type, QUIT_GAME_VERB) == 0) {
        response = handle_quit_game_response(client);
    } else if (strcmp(request_type, PLAY_MOVE_VERB) == 0) {
        response = handle_play_move_response(json, client);
    } else {
        response = cJSON_Print(create_unknow_response());
    }

    // Gestion de la réponse
    if (response != NULL) {
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", response);
        free(response);
    } else {
        fprintf(stderr, "Erreur : Aucune réponse générée pour le type de requête '%s'.\n", request_type);
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", cJSON_Print(create_unknow_response()));
    }
}

/**
 * @brief Traite une commande JSON reçue d'un client.
 *
 * Cette fonction parse la commande reçue, vérifie sa validité, et délègue son traitement
 * à la fonction appropriée en fonction du type de requête.
 *
 * @param client Pointeur vers le joueur (client) ayant envoyé la commande.
 * @param command Chaîne de caractères représentant la commande JSON reçue.
 */
void process_cmd(player_node *client, const char *command) {
    // Validation des paramètres
    if (!client || !command) {
        fprintf(stderr, "Erreur : Paramètres invalides passés à process_cmd.\n");
        return;
    }

    // Parser la chaîne JSON
    cJSON *json = cJSON_Parse(command);
    if (json == NULL) {
        fprintf(stderr, "Erreur : Échec du parsing de la commande JSON.\n");
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", cJSON_Print(create_unknow_response()));
        send_packet(client);
        return;
    }

    // Afficher le JSON reçu pour débogage
    char *json_string = cJSON_Print(json);
    if (json_string) {
        printf("JSON reçu de %s :\n%s\n", client->username, json_string);
        free(json_string);
    } else {
        fprintf(stderr, "Erreur : Impossible de convertir l'objet JSON en chaîne.\n");
    }

    // Récupérer la clé "type" du JSON
    const cJSON *type = cJSON_GetObjectItemCaseSensitive(json, "type");
    if (!cJSON_IsString(type) || type->valuestring == NULL) {
        fprintf(stderr, "Erreur : Clé 'type' manquante ou invalide dans la commande JSON.\n");
        snprintf(client->send_buffer, BUFFER_SIZE, "%s", cJSON_Print(create_unknow_response()));
        send_packet(client);
        cJSON_Delete(json);
        return;
    }

    // Déléguer le traitement à handle_client_response_type
    handle_client_response_type(client, type->valuestring, json);

    // Afficher la réponse pour débogage
    printf("Réponse serveur pour %s :\n%s\n", client->username, client->send_buffer);

    // Envoyer la réponse au client
    send_packet(client);

    // Libérer la mémoire du JSON
    cJSON_Delete(json);
}

/**
 * @brief Envoie un paquet au client via son socket.
 *
 * Cette fonction vérifie si le buffer d'envoi du client contient des données,
 * envoie ces données via le socket associé, et nettoie le buffer après l'envoi.
 *
 * @param client Pointeur vers le joueur (client) à qui le paquet doit être envoyé.
 */
void send_packet(player_node *client) {
    // Validation des paramètres
    if (!client) {
        fprintf(stderr, "Erreur : Le pointeur client est NULL.\n");
        return;
    }

    // Vérifier si le buffer d'envoi contient des données
    const size_t buffer_length = strlen(client->send_buffer);
    if (buffer_length > 0) {
        printf("Envoi du paquet au client '%s' (taille : %zu octets).\n", client->username, buffer_length);

        // Envoyer les données via le socket
        const ssize_t bytes_sent = send(client->socket, client->send_buffer, buffer_length, 0);
        if (bytes_sent < 0) {
            perror("Erreur lors de l'envoi du paquet");
        } else {
            printf("Paquet envoyé avec succès (%zd octets).\n", bytes_sent);
        }

        // Nettoyer le buffer après l'envoi
        memset(client->send_buffer, 0, BUFFER_SIZE);
    } else {
        printf("Aucun paquet à envoyer pour le client '%s'.\n", client->username);
    }
}

