#include <cjson/cJSON.h>  // Bibliothèque pour manipuler des objets JSON
#include "types.h"        // Fichier d'en-tête contenant les structures et les énumérations

/**
 * @brief Crée une réponse de succès pour l'authentification.
 *
 * @param client Pointeur vers le client authentifié.
 * @return Un objet JSON contenant les informations de réponse.
 */
cJSON *create_auth_response_success(const player_node *client);

/**
 * @brief Crée une réponse d'échec pour l'authentification.
 *
 * @return Un objet JSON contenant les informations d'échec.
 */
cJSON *create_auth_response_failure();

/**
 * @brief Crée une réponse de succès pour la création de compte.
 *
 * @param client Pointeur vers le client pour lequel le compte a été créé.
 * @return Un objet JSON contenant les informations de réponse.
 */
cJSON *create_new_account_response_success(const player_node *client);

/**
 * @brief Crée une réponse d'échec pour la création de compte.
 *
 * @return Un objet JSON contenant les informations d'échec.
 */
cJSON *create_new_account_response_failure();

/**
 * @brief Crée une réponse de déconnexion réussie.
 *
 * @return Un objet JSON contenant les informations de déconnexion.
 */
cJSON *create_disconnect_response();

/**
 * @brief Crée une réponse de succès pour le statut "prêt à jouer".
 *
 * @return Un objet JSON contenant les informations de succès.
 */
cJSON *create_ready_to_play_response_success();

/**
 * @brief Crée une réponse d'échec pour le statut "prêt à jouer".
 *
 * @return Un objet JSON contenant les informations d'échec.
 */
cJSON *create_ready_to_play_response_failure();

/**
 * @brief Crée une réponse contenant les informations du lobby.
 *
 * @param active_connections Nombre total de joueurs actifs.
 * @param head_linked_list_game Pointeur vers la tête de la liste chaînée des jeux.
 * @return Un objet JSON contenant les informations du lobby.
 */
cJSON *create_get_lobby_response(const int active_connections, const game_node *head_linked_list_game);

/**
 * @brief Crée une réponse de succès pour la création d'un jeu.
 *
 * @param game Pointeur vers le jeu nouvellement créé.
 * @return Un objet JSON contenant les informations du jeu.
 */
cJSON *create_game_response_success(const game_node *game);

/**
 * @brief Crée une réponse d'échec pour la création d'un jeu.
 *
 * @return Un objet JSON contenant les informations d'échec.
 */
cJSON *create_game_response_failure();

/**
 * @brief Crée une réponse de succès pour rejoindre un jeu.
 *
 * @return Un objet JSON contenant les informations de succès.
 */
cJSON *create_join_game_response_success();

/**
 * @brief Crée une réponse d'échec pour rejoindre un jeu.
 *
 * @return Un objet JSON contenant les informations d'échec.
 */
cJSON *create_join_game_response_failure();

/**
 * @brief Crée une réponse pour une commande inconnue.
 *
 * @return Un objet JSON indiquant une commande inconnue.
 */
cJSON *create_unknow_response();

/**
 * @brief Crée une réponse pour la victoire d'un joueur.
 *
 * @param winner Pointeur vers le joueur victorieux.
 * @return Un objet JSON contenant les informations de victoire.
 */
cJSON *create_game_over_victory_response(const player_node *winner);

/**
 * @brief Crée une réponse pour la défaite d'un joueur.
 *
 * @param loser Pointeur vers le joueur perdant.
 * @return Un objet JSON contenant les informations de défaite.
 */
cJSON *create_game_over_defeat_response(const player_node *loser);

/**
 * @brief Génère un objet JSON représentant les statistiques d'un joueur.
 *
 * @param player_stats Pointeur vers les statistiques du joueur.
 * @return Un objet JSON contenant les statistiques du joueur.
 */
cJSON *create_player_stat_json(const player_stat *player_stats);

/**
 * @brief Convertit un tableau de jeu en format JSON.
 *
 * @param board Le tableau représentant l'état du plateau.
 * @return Un objet JSON contenant le plateau sous forme de chaîne.
 */
cJSON *board_to_json(const char board[BOARD_SIZE]);

/**
 * @brief Initialise un plateau de jeu avec des caractères par défaut.
 *
 * @param board Tableau à initialiser.
 * @param player1_char Caractère représentant le joueur 1.
 */
void initialize_board(char board[BOARD_SIZE], char player1_char);

/**
 * @brief Crée une alerte de démarrage réussie pour l'hôte d'un jeu.
 *
 * @param game Pointeur vers le jeu démarré.
 * @return Un objet JSON contenant les informations de l'alerte.
 */
cJSON *create_alert_start_game_success_for_host(const game_node *game);

/**
 * @brief Crée une alerte de démarrage réussie pour le joueur rejoignant un jeu.
 *
 * @param game Pointeur vers le jeu démarré.
 * @return Un objet JSON contenant les informations de l'alerte.
 */
cJSON *create_alert_start_game_success_for_joiner(const game_node *game);

/**
 * @brief Crée une alerte pour l'échec du démarrage d'un jeu.
 *
 * @return Un objet JSON contenant les informations d'échec.
 */
cJSON *create_alert_start_game_failure();

/**
 * @brief Crée une réponse de succès pour quitter un jeu.
 *
 * @param player_stats Pointeur vers les statistiques du joueur.
 * @return Un objet JSON contenant les informations de succès.
 */
cJSON *create_quit_game_response_success(const player_stat *player_stats);

/**
 * @brief Crée une réponse d'échec pour quitter un jeu.
 *
 * @return Un objet JSON contenant les informations d'échec.
 */
cJSON *create_quit_game_response_failure();

/**
 * @brief Crée une réponse de succès pour un mouvement dans le jeu.
 *
 * @param game Pointeur vers le jeu concerné.
 * @param player Pointeur vers le joueur ayant effectué le mouvement.
 * @return Un objet JSON contenant les informations de succès.
 */
cJSON *create_move_response_success(const game_node *game, const player_node *player);

/**
 * @brief Crée une réponse d'échec pour un mouvement dans le jeu.
 *
 * @return Un objet JSON contenant les informations d'échec.
 */
cJSON *create_move_response_failure();

/**
 * @brief Crée un objet JSON représentant le nouvel état d'un plateau.
 *
 * @param game Pointeur vers le jeu concerné.
 * @return Un objet JSON contenant l'état mis à jour du plateau.
 */
cJSON *create_new_board_stat(const game_node *game);


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
    cJSON_AddNumberToObject(response, "status", failure);
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

cJSON *create_get_lobby_response(const int active_connections, const game_node *head_linked_list_game) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "get_lobby_response");
    cJSON_AddNumberToObject(response, "status", success);
    cJSON_AddNumberToObject(response, "total_active_players", active_connections);

    cJSON *games = cJSON_CreateArray();
    const game_node *current_game = head_linked_list_game;

    while (current_game) {
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
    cJSON_AddNumberToObject(game_obj, "id", 1); // TODO: retirer car l'id est le nom de la partie
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

    cJSON *player_stats = create_player_stat_json(&winner->player_stats);
    cJSON_AddItemToObject(response, "player_stats", player_stats);

    return response;
}

cJSON *create_game_over_defeat_response(const player_node *loser) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "game_over");
    cJSON_AddNumberToObject(response, "status", defeat);

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

void initialize_board(char board[BOARD_SIZE], const char player1_char) {
    memset(board, '-', BOARD_SIZE); // Remplir le tableau avec des tirets
    board[(BOARD_SIZE / 2)] = player1_char; // Joueur 1
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
    return response;
}

cJSON *create_alert_start_game_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "alert_start_game");
    cJSON_AddNumberToObject(response, "status", failure);

    return response;
}

cJSON *create_quit_game_response_success(const player_stat *player_stats) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "quit_game_response");
    cJSON_AddNumberToObject(response, "status", success);
    cJSON_AddItemToObject(response, "player_stats", create_player_stat_json(player_stats));

    return response;
}

cJSON *create_quit_game_response_failure() {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "quit_game_response");
    cJSON_AddNumberToObject(response, "status", failure);

    return response;
}

cJSON *create_move_response_success(const game_node *game, const player_node *player) {
    cJSON *response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "type", "move_response");
    cJSON_AddNumberToObject(response, "status", success);
    cJSON_AddItemToObject(response, "board_state", board_to_json(game->board));
    cJSON_AddNumberToObject(response, "captures", player->captures);

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
