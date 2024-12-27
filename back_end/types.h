#pragma once

#define BUFFER_SIZE 1024                       // Taille du buffer
#define BOARD_ROWS 19                          // Nombre de lignes du plateau de jeu
#define BOARD_COLS 19                          // Nombre de colonnes du plateau de jeu
#define BOARD_SIZE (BOARD_COLS * BOARD_ROWS)   // Taille du plateau de jeu

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
    char password[64];
    player_stat player_stats;
    char recv_buffer[BUFFER_SIZE];
    char send_buffer[BUFFER_SIZE];
    int captures;
    game_node *current_game;
    player_node *next;
};

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
