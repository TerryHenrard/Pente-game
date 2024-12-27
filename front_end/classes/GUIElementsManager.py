import pygame
import pygame_gui

# pdoc: format de la documentation
__docformat__ = "google"

from pygame_gui.elements import UIButton


class GUIElementsManager:
    """Classe pour créer le gestionnaire GUI et les éléments"""

    # Configuration de l'écran
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 900

    # Dimensions du plateau
    GRID_ROWS = 19
    GRID_COLS = 19
    GRID_SIZE = GRID_ROWS * GRID_COLS
    CELL_SIZE = 45
    PIECE_SIZE = 40
    LINE_WIDTH_DEFAULT = 1
    LINE_WIDTH_CENTER = 2
    TOLERANCE = 5

    # Configuration des titres
    TITLE_WIDTH = 600
    TITLE_HEIGHT = 60

    # Configuration des labels
    LABEL_WIDTH = 300
    LABEL_HEIGHT = 25
    LABEL_MARGIN_BOTTOM = 10
    LABEL_LEFT_MARGIN = 5

    # Buttons dimensions
    BUTTON_WIDTH = 200
    BUTTON_HEIGHT = 50
    BUTTON_LEFT_RIGHT_MARGIN = 10
    BUTTON_BETWEEN_MARGIN = 10
    BUTTON_BOTTOM_MARGIN = 60
    BUTTON_GAME_WIDTH = SCREEN_WIDTH // 2 + 50
    BUTTON_GAME_HEIGHT = 45
    BUTTON_GAME_MARGIN = 10

    # Logo de l'hôte
    HOST_PION_LOGO_X = 10
    HOST_PION_LOGO_Y = 270
    HOST_PION_LOGO_WIDTH = 200
    HOST_PION_LOGO_HEIGHT = 200

    # Logo de l'adversaire
    OPPONENT_PION_LOGO_WIDTH = 200
    OPPONENT_PION_LOGO_HEIGHT = 200
    OPPONENT_PION_LOGO_X = SCREEN_WIDTH - OPPONENT_PION_LOGO_WIDTH - BUTTON_LEFT_RIGHT_MARGIN
    OPPONENT_PION_LOGO_Y = 270

    # Coordonées & dimensions des images
    GANDALF_IMAGE_X = 10
    GANDALF_IMAGE_Y = 200
    GANDALF_IMAGE_WIDTH = 600
    GANDALF_IMAGE_HEIGHT = 900

    SAURON_IMAGE_X = 640
    SAURON_IMAGE_Y = 200
    SAURON_IMAGE_WIDTH = 592
    SAURON_IMAGE_HEIGHT = 900

    GOLLUM_IMAGE_WIDTH = 415
    GOLLUM_IMAGE_HEIGHT = 640
    GOLLUM_IMAGE_X = -35
    GOLLUM_IMAGE_Y = SCREEN_HEIGHT - GOLLUM_IMAGE_HEIGHT

    NAZGUL_IMAGE_WIDTH = 311
    NAZGUL_IMAGE_HEIGHT = 761
    NAZGUL_IMAGE_X = SCREEN_WIDTH // 2 - 470
    NAZGUL_IMAGE_Y = 350

    KING_WITCH_OF_ANGMAR_IMAGE_WIDTH = 400
    KING_WITCH_OF_ANGMAR_IMAGE_HEIGHT = 812
    KING_WITCH_OF_ANGMAR_IMAGE_X = SCREEN_WIDTH // 2 + 130
    KING_WITCH_OF_ANGMAR_IMAGE_Y = 300

    YOUNG_BILBO_IMAGE_WIDTH = 246
    YOUNG_BILBO_IMAGE_HEIGHT = 640
    YOUNG_BILBO_IMAGE_X = 0
    YOUNG_BILBO_IMAGE_Y = 430

    OLD_BILBO_IMAGE_WIDTH = 237
    OLD_BILBO_IMAGE_HEIGHT = 640
    OLD_BILBO_IMAGE_X = SCREEN_WIDTH - OLD_BILBO_IMAGE_WIDTH
    OLD_BILBO_IMAGE_Y = 430

    # Dimensions de la grille
    GRID_DIMENSIONS = (GRID_COLS - 1) * CELL_SIZE

    # Calculer les marges pour centrer la grille
    MARGIN_X = (SCREEN_WIDTH - GRID_DIMENSIONS) // 2
    MARGIN_Y = (SCREEN_HEIGHT - GRID_DIMENSIONS) // 2 + 20

    # Chemin du fichier style
    THEME_PATH = "assets/styles/theme.json"

    # Charger les images
    GANDALF_IMAGE = pygame.image.load("assets/images/gandalf.png")
    SAURON_IMAGE = pygame.image.load("assets/images/sauron.png")
    GOLLUM_IMAGE = pygame.image.load("assets/images/gollum.png")
    NAZGUL_IMAGE = pygame.image.load("assets/images/nazgul.png")
    KING_WITCH_OF_ANGMAR_IMAGE = pygame.image.load("assets/images/king_witch_of_angmar.png")
    YOUNG_BILBO_IMAGE = pygame.image.load("assets/images/young_bilbo.png")
    OLD_BILBO_IMAGE = pygame.image.load("assets/images/old_bilbo.png")
    HOST_PION_IMAGE = pygame.image.load("assets/images/one_ring_pion.png")
    OPPONENT_PION_IMAGE = pygame.image.load("assets/images/eye_of_sauron_pion.png")
    PENTE_LOGO = pygame.image.load("assets/images/pente-game-LOTR-LOGO.webp")

    # Redimensionner les images
    OPPONENT_PION_IMAGE_SCALED = pygame.transform.scale(OPPONENT_PION_IMAGE, (PIECE_SIZE, PIECE_SIZE))
    HOST_PION_IMAGE_SCALED = pygame.transform.scale(HOST_PION_IMAGE, (PIECE_SIZE, PIECE_SIZE))

    # Couleurs
    BACKGROUND_COLOR = (193, 176, 150)
    LINE_COLOR = (0, 0, 0)

    # Points "hoshi" (points spéciaux sur le plateau)
    HOSHI_POINTS = [
        (3, 3), (3, 9), (3, 15),
        (9, 3), (9, 9), (9, 15),
        (15, 3), (15, 9), (15, 15)
    ]
    HOSHI_POINTS_SIZE = 8

    # Caractères des pions
    HOST_CHAR = 'x'
    OPPONENT_CHAR = 'o'
    EMPTY_CHAR = '-'

    def __init__(self) -> None:
        """
        Initialise le gestionnaire d'éléments GUI.

        Raises:
            ValueError: Si le chemin du thème n'est pas une chaîne non vide.
        """

        self.surface = self.__init_pygame()
        self.manager = pygame_gui.UIManager(
            (GUIElementsManager.SCREEN_WIDTH, GUIElementsManager.SCREEN_HEIGHT),
            GUIElementsManager.THEME_PATH
        )
        self.background = self.__create_background()
        self.screen = pygame.display.set_mode((GUIElementsManager.SCREEN_WIDTH, GUIElementsManager.SCREEN_HEIGHT))
        self._board = ""

    @property
    def board(self) -> str:
        """
        Récupère le plateau de jeu.

        Returns:
            str: Le plateau de jeu.
        """
        return self._board

    @board.setter
    def board(self, board: str) -> None:
        """
        Définit le plateau de jeu.

        Args:
            board (str): Le plateau de jeu.
        """
        if not isinstance(board, str) or not board:
            raise ValueError("Le plateau de jeu doit être une chaîne non vide.")

        self._board = board
        self.print_board()

    def print_board(self) -> None:
        """
        Affiche le plateau de jeu de manière lisible avec les numéros de colonnes et de lignes.

        Returns:
            None
        """
        # Affiche les numéros des colonnes en haut du plateau.
        print("   " + " ".join(f"{x + 1:2}" for x in range(19)))

        # Parcourt chaque ligne du plateau pour l'afficher avec son numéro.
        for y in range(19):
            # Affiche le numéro de la ligne suivi des cases correspondantes.
            print(f"{y + 1:2} " + "  ".join(self.board[y * 19:(y + 1) * 19]))

    def process_events_manager(self, event: pygame.event.Event) -> None:
        """
        Traite les événements du gestionnaire d'interface utilisateur.

        Args:
            event (pygame.event.Event): L'événement à traiter.
        """
        self.manager.process_events(event)

    def draw_ui(self) -> None:
        """
        Dessine les éléments de l'interface utilisateur.
        """
        self.manager.draw_ui(self.screen)

    def update_manager(self, time_delta: float) -> None:
        """
        Met à jour le gestionnaire d'interface utilisateur.

        Args:
            time_delta (float): Le temps écoulé depuis la dernière mise à jour.
        """
        self.manager.update(time_delta)

    def blit_background(self) -> None:
        """
        Affiche l'arrière-plan sur l'écran.
        """
        self.screen.blit(self.background, (0, 0))

    def __init_pygame(self) -> pygame.Surface:
        """
        Initialise Pygame et crée une fenêtre de jeu.

        Returns:
            pygame.Surface: La surface d'affichage créée.

        Raises:
            RuntimeError: Si Pygame ne peut pas être initialisé correctement.
        """
        try:
            # Initialise Pygame
            pygame.init()

            # Vérifie si le module de vidéo est correctement initialisé
            if not pygame.get_init():
                raise RuntimeError("Échec de l'initialisation de Pygame.")

            # Crée une fenêtre de jeu
            screen = pygame.display.set_mode((GUIElementsManager.SCREEN_WIDTH, GUIElementsManager.SCREEN_HEIGHT))
            pygame.display.set_caption("Pente Game / LOTR Edition")
            pygame.display.set_icon(GUIElementsManager.PENTE_LOGO)

            return screen
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'initialisation de Pygame : {e}") from e

    @staticmethod
    def update_display() -> None:
        """
        Met à jour l'affichage de la fenêtre de jeu.
        """
        pygame.display.update()

    @staticmethod
    def __create_background() -> pygame.Surface:
        """
        Crée une surface d'arrière-plan pour la fenêtre de jeu.

        Returns:
            pygame.Surface: La surface d'arrière-plan remplie avec la couleur de fond.
        """
        background = pygame.Surface((GUIElementsManager.SCREEN_WIDTH, GUIElementsManager.SCREEN_HEIGHT))
        background.fill(GUIElementsManager.BACKGROUND_COLOR)
        return background

    def draw_host_pion_logo(self) -> pygame_gui.elements.UIImage:
        """
        Dessine le logo du pion de l'hôte sur l'interface utilisateur.

        Returns:
            pygame_gui.elements.UIImage: L'élément graphique représentant le logo du pion de l'hôte.
        """
        # Crée et retourne un élément UIImage pour afficher le logo du pion de l'hôte.
        return pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(
                (GUIElementsManager.HOST_PION_LOGO_X, GUIElementsManager.HOST_PION_LOGO_Y),  # Position du logo.
                (GUIElementsManager.HOST_PION_LOGO_WIDTH, GUIElementsManager.HOST_PION_LOGO_HEIGHT)  # Taille du logo.
            ),
            image_surface=GUIElementsManager.HOST_PION_IMAGE,  # Image utilisée pour le logo.
            manager=self.manager  # Gestionnaire d'interface utilisateur.
        )

    def draw_opponent_pion_logo(self) -> pygame_gui.elements.UIImage:
        """
        Dessine le logo du pion de l'adversaire sur l'interface utilisateur.

        Returns:
            pygame_gui.elements.UIImage: L'élément graphique représentant le logo du pion de l'adversaire.
        """
        # Crée et retourne un élément UIImage pour afficher le logo du pion de l'adversaire.
        return pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(
                (GUIElementsManager.OPPONENT_PION_LOGO_X, GUIElementsManager.OPPONENT_PION_LOGO_Y),  # Position du logo.
                (GUIElementsManager.OPPONENT_PION_LOGO_WIDTH, GUIElementsManager.OPPONENT_PION_LOGO_HEIGHT)
                # Taille du logo.
            ),
            image_surface=GUIElementsManager.OPPONENT_PION_IMAGE,  # Image utilisée pour le logo.
            manager=self.manager  # Gestionnaire d'interface utilisateur.
        )

    def draw_pion(
            self,
            x: int,
            y: int,
            width: int,
            height: int,
            pion_image: pygame.Surface
    ) -> pygame_gui.elements.UIImage:
        """
        Dessine un pion sur l'écran.

        Args:
            x (int): La coordonnée x du coin supérieur gauche du pion.
            y (int): La coordonnée y du coin supérieur gauche du pion.
            width (int): La largeur du pion.
            height (int): La hauteur du pion.
            pion_image (pygame.Surface): La surface contenant l'image du pion.

        Returns:
            pygame_gui.elements.UIImage: L'élément UIImage représentant le pion.
        """
        return pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect((x, y), (width, height)),  # Position et taille
            image_surface=pion_image,
            manager=self.manager
        )

    @staticmethod
    def __add_padding(
            text: str,
            total_length: int = 20,
            align: str = "left",
            padding_char: str = " "
    ) -> str:
        """
        Ajuste une chaîne de caractères pour qu'elle atteigne une longueur spécifique
        en ajoutant du padding, avec alignement défini.

        Args:
            text (str): La chaîne de caractères à ajuster.
            total_length (int): La longueur totale souhaitée pour la chaîne. Par défaut, 20.
            align (str): L'alignement du texte. Valeurs possibles : "left", "right", "center".
            padding_char (str): Le caractère utilisé pour remplir les espaces vides. Par défaut, un espace.

        Returns:
            str: La chaîne ajustée ou tronquée selon la longueur spécifiée.

        Raises:
            ValueError: Si l'argument `align` n'est pas "left", "right" ou "center".
        """
        # Supprime les espaces inutiles au début et à la fin du texte.
        text = str(text).strip()

        # Tronque la chaîne si elle dépasse la longueur totale.
        if len(text) > total_length:
            return text[:total_length]

        # Ajuste la chaîne en fonction de l'alignement demandé.
        if align == "left":
            return text.ljust(total_length, padding_char)
        elif align == "right":
            return text.rjust(total_length, padding_char)
        elif align == "center":
            return text.center(total_length, padding_char)
        else:
            # Erreur si l'alignement spécifié est invalide.
            raise ValueError("L'argument 'align' doit être 'left', 'right' ou 'center'.")

    def create_gui_join_game_button_element(self, game_json: dict, index: int) -> UIButton | None:
        """
        Crée un bouton graphique pour rejoindre une partie, basé sur les informations fournies.

        Args:
            game_json (dict): Un dictionnaire contenant les informations sur la partie.
                - id (int): L'identifiant de la partie.
                - name (str): Le nom de la partie.
                - players (list[str]): La liste des joueurs dans la partie.
                - status (int): Le statut de la partie (0 pour "waiting", 1 pour "ongoing").
            index (int): L'index du bouton (utilisé pour positionner verticalement les boutons).

        Returns:
            pygame_gui.elements.UIButton | None: Le bouton créé, ou None si les données du bouton sont incomplètes.
        """
        # Récupère les données nécessaires depuis game_json.
        game_button_id = game_json.get("id")
        game_button_name = game_json.get("name")
        game_button_players = game_json.get("players")
        game_button_status = game_json.get("status")  # 0: waiting, 1: ongoing

        # Vérifie si toutes les données nécessaires sont présentes.
        if None in [game_button_id, game_button_name, game_button_players, game_button_status]:
            return None

        # Crée le texte affiché sur le bouton avec un alignement personnalisé.
        button_text = (
                self.__add_padding(f"N°{index + 1}", total_length=7) +
                self.__add_padding(f"Name: {game_button_name}", total_length=20) +
                self.__add_padding(f"Status: {'waiting' if game_button_status == 0 else 'ongoing'}") +
                self.__add_padding(f"Players: {', '.join(game_button_players)}", total_length=30)
        )

        # Retourne un bouton pygame_gui avec les dimensions et le texte spécifiés.
        return pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (
                    GUIElementsManager.SCREEN_WIDTH // 2 - (GUIElementsManager.BUTTON_GAME_WIDTH // 2),
                    # Position horizontale.
                    (100 + (GUIElementsManager.BUTTON_GAME_HEIGHT * index) + 10)  # Position verticale.
                ),
                (GUIElementsManager.BUTTON_GAME_WIDTH, GUIElementsManager.BUTTON_GAME_HEIGHT)  # Dimensions du bouton.
            ),
            text=button_text,  # Texte affiché sur le bouton.
            manager=self.manager,  # Gestionnaire d'interface.
            object_id=f"#button_game_{game_button_id}"  # Identifiant unique du bouton.
        )

    @staticmethod
    def get_grid_coordinates(x: int, y: int) -> tuple[int, int]:
        """
        Convertit les coordonnées d'un clic en indices de la grille.

        Args:
            x (int): La position horizontale du clic en pixels.
            y (int): La position verticale du clic en pixels.

        Returns:
            tuple[int, int]: Un tuple contenant les indices (colonne, ligne) de la grille.
                Retourne (-1, -1) si le clic est en dehors des limites de la grille.
        """
        # Ajustement des coordonnées en prenant en compte les marges.
        adjusted_x = x - GUIElementsManager.MARGIN_X
        adjusted_y = y - GUIElementsManager.MARGIN_Y

        # Vérifie si le clic est dans la zone étendue avec une tolérance.
        if not (
                -GUIElementsManager.TOLERANCE <= adjusted_x <= GUIElementsManager.GRID_DIMENSIONS + GUIElementsManager.TOLERANCE and
                -GUIElementsManager.TOLERANCE <= adjusted_y <= GUIElementsManager.GRID_DIMENSIONS + GUIElementsManager.TOLERANCE
        ):
            return -1, -1  # Clic en dehors de la zone.

        # Calcul des indices de la grille en fonction de la taille des cellules.
        col = round(adjusted_x / GUIElementsManager.CELL_SIZE)
        row = round(adjusted_y / GUIElementsManager.CELL_SIZE)

        # Vérifie si les indices calculés sont dans les limites de la grille.
        if not (0 <= col < GUIElementsManager.GRID_COLS and 0 <= row < GUIElementsManager.GRID_ROWS):
            return -1, -1  # Indices hors limites.

        # Retourne les indices valides (colonne, ligne).
        return col, row

    @staticmethod
    def clear_page(elements: dict[str, pygame_gui.elements]) -> None:
        """
        Supprime tous les éléments graphiques d'une page et vide le dictionnaire d'éléments.

        Args:
            elements (dict[str, pygame_gui.elements]):
                Un dictionnaire contenant les éléments graphiques de la page à supprimer.

        Returns:
            None
        """
        # Parcourt tous les éléments du dictionnaire.
        for key, element in elements.items():
            # Si l'élément est une liste, tente de supprimer chaque sous-élément.
            if isinstance(element, list):
                for sub_element in element:
                    if hasattr(sub_element, "kill"):
                        sub_element.kill()  # Supprime l'élément graphique.
            # Si l'élément individuel possède une méthode kill(), la déclenche.
            elif hasattr(element, "kill"):
                element.kill()
            # Avertit si l'élément n'a pas de méthode kill().
            else:
                print(f"Warning: Element {element} n'a pas de méthode kill().")

        # Vide le dictionnaire après avoir supprimé les éléments graphiques.
        elements.clear()

    def create_gui_elements_lobby_page(self) -> dict[str, pygame_gui.elements]:
        """
        Crée et retourne les éléments graphiques nécessaires pour la page du lobby.

        Returns:
            dict[str, pygame_gui.elements]: Un dictionnaire contenant tous les éléments de l'interface utilisateur pour la page du lobby.
        """
        return {
            # Titre principal de la page.
            "title_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - 300,
                        GUIElementsManager.SCREEN_HEIGHT // 2 - 400
                    ),
                    (GUIElementsManager.TITLE_WIDTH, GUIElementsManager.TITLE_HEIGHT)
                ),
                text="Menu principal",
                manager=self.manager,
                object_id='#lobby_title_label'
            ),

            # Étiquettes pour les statistiques des joueurs.
            "score_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.LABEL_LEFT_MARGIN, GUIElementsManager.BUTTON_BETWEEN_MARGIN),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="score_label",
                manager=self.manager,
                object_id="#score_label"
            ),
            "wins_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.LABEL_LEFT_MARGIN,
                        GUIElementsManager.LABEL_HEIGHT + ((3 / 2) * GUIElementsManager.BUTTON_BETWEEN_MARGIN)
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="wins_label",
                manager=self.manager,
                object_id="#wins_label"
            ),
            "losses_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.LABEL_LEFT_MARGIN,
                        2 * (GUIElementsManager.LABEL_HEIGHT + GUIElementsManager.BUTTON_BETWEEN_MARGIN)
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="losses_label",
                manager=self.manager,
                object_id="#losses_label"
            ),
            "forfeits_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.LABEL_LEFT_MARGIN,
                        3 * (GUIElementsManager.LABEL_HEIGHT + GUIElementsManager.BUTTON_BETWEEN_MARGIN) -
                        (GUIElementsManager.BUTTON_BETWEEN_MARGIN // 2)
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="",
                manager=self.manager,
                object_id="#forfeits_label"
            ),
            "games_played_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.LABEL_LEFT_MARGIN,
                        4 * (
                                GUIElementsManager.LABEL_HEIGHT + GUIElementsManager.BUTTON_BETWEEN_MARGIN
                        ) - GUIElementsManager.BUTTON_BETWEEN_MARGIN
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="games_played_label",
                manager=self.manager,
                object_id="#games_played_label"
            ),

            # Images décoratives.
            "young_bilbo_image": pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.YOUNG_BILBO_IMAGE_X, GUIElementsManager.YOUNG_BILBO_IMAGE_Y),
                    (GUIElementsManager.YOUNG_BILBO_IMAGE_WIDTH, GUIElementsManager.YOUNG_BILBO_IMAGE_HEIGHT)
                ),
                image_surface=GUIElementsManager.YOUNG_BILBO_IMAGE,
                manager=self.manager
            ),
            "old_bilbo_image": pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.OLD_BILBO_IMAGE_X, GUIElementsManager.OLD_BILBO_IMAGE_Y),
                    (GUIElementsManager.OLD_BILBO_IMAGE_WIDTH, GUIElementsManager.OLD_BILBO_IMAGE_HEIGHT)
                ),
                image_surface=GUIElementsManager.OLD_BILBO_IMAGE,
                manager=self.manager
            ),

            # Boutons d'action.
            "create_game_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - (
                                3 * GUIElementsManager.BUTTON_WIDTH // 2
                        ) - GUIElementsManager.BUTTON_LEFT_RIGHT_MARGIN,
                        GUIElementsManager.SCREEN_HEIGHT - GUIElementsManager.BUTTON_BOTTOM_MARGIN
                    ),
                    (GUIElementsManager.BUTTON_WIDTH, GUIElementsManager.BUTTON_HEIGHT)
                ),
                text="Créer une partie",
                manager=self.manager
            ),
            "refresh_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - (GUIElementsManager.BUTTON_WIDTH // 2),
                        GUIElementsManager.SCREEN_HEIGHT - GUIElementsManager.BUTTON_BOTTOM_MARGIN
                    ),
                    (GUIElementsManager.BUTTON_WIDTH, GUIElementsManager.BUTTON_HEIGHT)
                ),
                text="Rafraîchir",
                manager=self.manager
            ),
            "disconnect_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 + (
                                GUIElementsManager.BUTTON_WIDTH // 2
                        ) + GUIElementsManager.BUTTON_LEFT_RIGHT_MARGIN,
                        GUIElementsManager.SCREEN_HEIGHT - GUIElementsManager.BUTTON_BOTTOM_MARGIN
                    ),
                    (GUIElementsManager.BUTTON_WIDTH, GUIElementsManager.BUTTON_HEIGHT)
                ),
                text="Se déconnecter",
                manager=self.manager
            ),

            # Étiquettes supplémentaires.
            "error_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 200, GUIElementsManager.SCREEN_HEIGHT // 2 + 120),
                    (400, 30)
                ),
                text="",
                manager=self.manager,
                object_id="#error_label"
            ),
            "sound_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH - 160,
                        10
                    ),
                    (150, 40)
                ),
                text="Désactiver le son",
                manager=self.manager
            ),
            "total_active_players_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.LABEL_LEFT_MARGIN,
                        5 * (
                                GUIElementsManager.LABEL_HEIGHT + GUIElementsManager.BUTTON_BETWEEN_MARGIN
                        ) - GUIElementsManager.BUTTON_BETWEEN_MARGIN
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="",
                manager=self.manager,
                object_id="#total_active_players_label"
            )
        }

    def create_gui_elements_create_game_page(self) -> dict[str, pygame_gui.elements]:
        """
        Crée et retourne les éléments graphiques nécessaires pour la page de création d'une nouvelle partie.

        Returns:
            dict[str, pygame_gui.elements]: Un dictionnaire contenant tous les éléments de l'interface utilisateur pour la page de création d'une partie.
        """
        return {
            # Titre principal de la page.
            "title_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - 300,
                        GUIElementsManager.SCREEN_HEIGHT // 2 - 400
                    ),
                    (GUIElementsManager.TITLE_WIDTH, GUIElementsManager.TITLE_HEIGHT)
                ),
                text="Créer une partie",
                manager=self.manager,
                object_id='#new_game_title_label'
            ),

            # Images décoratives.
            "nazgul_image": pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.NAZGUL_IMAGE_X, GUIElementsManager.NAZGUL_IMAGE_Y),
                    (GUIElementsManager.NAZGUL_IMAGE_WIDTH, GUIElementsManager.NAZGUL_IMAGE_HEIGHT)
                ),
                image_surface=GUIElementsManager.NAZGUL_IMAGE,
                manager=self.manager
            ),
            "king_witch_of_angmar_image": pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.KING_WITCH_OF_ANGMAR_IMAGE_X, GUIElementsManager.KING_WITCH_OF_ANGMAR_IMAGE_Y),
                    (GUIElementsManager.KING_WITCH_OF_ANGMAR_IMAGE_WIDTH,
                     GUIElementsManager.KING_WITCH_OF_ANGMAR_IMAGE_HEIGHT)
                ),
                image_surface=GUIElementsManager.KING_WITCH_OF_ANGMAR_IMAGE,
                manager=self.manager
            ),

            # Label et champ de texte pour le nom de la partie.
            "game_name_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - (GUIElementsManager.BUTTON_WIDTH // 2),
                        GUIElementsManager.SCREEN_HEIGHT // 2 - 115
                    ),
                    (200, 30)
                ),
                text="Nom de la partie",
                manager=self.manager,
                object_id="#game_name_label"
            ),
            "game_name_entry": pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - (GUIElementsManager.BUTTON_WIDTH // 2),
                        GUIElementsManager.SCREEN_HEIGHT // 2 - 85
                    ),
                    (200, 30)
                ),
                manager=self.manager,
                object_id="#game_name_entry"
            ),

            # Boutons pour créer une partie ou retourner au menu précédent.
            "create_new_game_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - (GUIElementsManager.BUTTON_WIDTH // 2),
                        GUIElementsManager.SCREEN_HEIGHT // 2 + 25
                    ),
                    (GUIElementsManager.BUTTON_WIDTH, GUIElementsManager.BUTTON_HEIGHT)
                ),
                text="Créer",
                manager=self.manager
            ),
            "back_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - (GUIElementsManager.BUTTON_WIDTH // 2),
                        GUIElementsManager.SCREEN_HEIGHT // 2 + 85
                    ),
                    (GUIElementsManager.BUTTON_WIDTH, GUIElementsManager.BUTTON_HEIGHT)
                ),
                text="Retour",
                manager=self.manager
            ),

            # Label pour afficher les erreurs éventuelles.
            "error_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 150, GUIElementsManager.SCREEN_HEIGHT // 2 + 155),
                    (300, 30)
                ),
                text="",
                manager=self.manager,
                object_id="#error_label"
            )
        }

    def create_gui_elements_login_page(self) -> dict[str, pygame_gui.elements]:
        """
        Crée et retourne les éléments graphiques nécessaires pour la page de connexion.

        Returns:
            dict[str, pygame_gui.elements]: Un dictionnaire contenant tous les éléments de l'interface utilisateur pour la page de connexion.
        """
        return {
            # Titre principal de la page.
            "title_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - 300,
                        GUIElementsManager.SCREEN_HEIGHT // 2 - 200
                    ),
                    (GUIElementsManager.TITLE_WIDTH, GUIElementsManager.TITLE_HEIGHT)
                ),
                text="Se connecter",
                manager=self.manager,
                object_id='#login_title_label'
            ),

            # Images décoratives.
            "gandalf_image": pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.GANDALF_IMAGE_X, GUIElementsManager.GANDALF_IMAGE_Y),
                    (GUIElementsManager.GANDALF_IMAGE_WIDTH, GUIElementsManager.GANDALF_IMAGE_HEIGHT)
                ),
                image_surface=GUIElementsManager.GANDALF_IMAGE,
                manager=self.manager
            ),
            "sauron_image": pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SAURON_IMAGE_X, GUIElementsManager.SAURON_IMAGE_Y),
                    (GUIElementsManager.SAURON_IMAGE_WIDTH, GUIElementsManager.SAURON_IMAGE_HEIGHT)
                ),
                image_surface=GUIElementsManager.SAURON_IMAGE,
                manager=self.manager
            ),

            # Labels et champs de texte pour le nom d'utilisateur et le mot de passe.
            "username_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 - 115),
                    (200, 30)
                ),
                text="Nom d'utilisateur",
                manager=self.manager,
                object_id="#username_label"
            ),
            "username_entry": pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 - 85),
                    (200, 30)
                ),
                manager=self.manager,
                object_id="#username_login_entry"
            ),
            "password_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 - 55),
                    (200, 30)
                ),
                text="Mot de passe",
                manager=self.manager,
                object_id="#password_label"
            ),
            "password_entry": pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 - 25),
                    (200, 30)
                ),
                manager=self.manager,
                object_id="#password_login_entry"
            ),

            # Boutons pour se connecter ou créer un compte.
            "login_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 + 25),
                    (GUIElementsManager.BUTTON_WIDTH, GUIElementsManager.BUTTON_HEIGHT)
                ),
                text="Se connecter",
                manager=self.manager
            ),
            "create_account_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 + 85),
                    (GUIElementsManager.BUTTON_WIDTH, GUIElementsManager.BUTTON_HEIGHT)
                ),
                text="Créer un compte",
                manager=self.manager
            ),

            # Label pour afficher les erreurs éventuelles.
            "error_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 300, GUIElementsManager.SCREEN_HEIGHT // 2 + 155),
                    (GUIElementsManager.TITLE_WIDTH, 30)
                ),
                text="",
                manager=self.manager,
                object_id="#error_label"
            )
        }

    def create_gui_elements_new_account_page(self) -> dict[str, pygame_gui.elements]:
        """
        Crée et retourne les éléments graphiques nécessaires pour la page de création d'un nouveau compte.

        Returns:
            dict[str, pygame_gui.elements]: Un dictionnaire contenant tous les éléments de l'interface utilisateur pour la page de création d'un compte.
        """
        return {
            # Titre principal de la page.
            "title_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - 300,
                        GUIElementsManager.SCREEN_HEIGHT // 2 - 200
                    ),
                    (GUIElementsManager.TITLE_WIDTH, GUIElementsManager.TITLE_HEIGHT)
                ),
                text="S'inscrire",
                manager=self.manager,
                object_id='#new_account_title_label'
            ),

            # Labels et champs de texte pour le nom d'utilisateur, le mot de passe et la confirmation.
            "username_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 - 115),
                    (200, 30)
                ),
                text="Nom d'utilisateur",
                manager=self.manager,
                object_id="#username_label"
            ),
            "username_entry": pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 - 85),
                    (200, 30)
                ),
                manager=self.manager,
                object_id="#username_create_account_entry"
            ),
            "password_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 - 55),
                    (200, 30)
                ),
                text="Mot de passe",
                manager=self.manager,
                object_id="#password_label"
            ),
            "password_entry": pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 - 25),
                    (200, 30)
                ),
                manager=self.manager,
                object_id="#password_create_account_entry"
            ),
            "conf_password_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 + 5),
                    (200, 30)
                ),
                text="Confirmez le mot de passe",
                manager=self.manager,
                object_id="#conf_password_label"
            ),
            "conf_password_entry": pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 + 35),
                    (200, 30)
                ),
                manager=self.manager,
                object_id="#conf_password_create_account_entry"
            ),

            # Image décorative de Gollum.
            "gollum_image": pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.GOLLUM_IMAGE_X, GUIElementsManager.GOLLUM_IMAGE_Y),
                    (GUIElementsManager.GOLLUM_IMAGE_WIDTH, GUIElementsManager.GOLLUM_IMAGE_HEIGHT)
                ),
                image_surface=GUIElementsManager.GOLLUM_IMAGE,
                manager=self.manager
            ),

            # Boutons pour créer un compte ou retourner au menu précédent.
            "create_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 + 75),
                    (GUIElementsManager.BUTTON_WIDTH, GUIElementsManager.BUTTON_HEIGHT)
                ),
                text="Créer",
                manager=self.manager
            ),
            "back_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 100, GUIElementsManager.SCREEN_HEIGHT // 2 + 135),
                    (GUIElementsManager.BUTTON_WIDTH, GUIElementsManager.BUTTON_HEIGHT)
                ),
                text="Retour",
                manager=self.manager
            ),

            # Label pour afficher les erreurs éventuelles.
            "error_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (GUIElementsManager.SCREEN_WIDTH // 2 - 300, GUIElementsManager.SCREEN_HEIGHT // 2 + 195),
                    (GUIElementsManager.TITLE_WIDTH, 30)
                ),
                text="",
                manager=self.manager,
                object_id="#error_label"
            )
        }

    def create_gui_elements_game_page(self) -> dict[str, pygame_gui.elements]:
        """
        Crée et retourne les éléments graphiques nécessaires pour la page de jeu.

        Returns:
            dict[str, pygame_gui.elements]:
                Un dictionnaire contenant tous les éléments de l'interface utilisateur pour la page de jeu.
        """
        return {
            # Titre principal de la page.
            "title_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH // 2 - 300,
                        0
                    ),
                    (GUIElementsManager.TITLE_WIDTH, GUIElementsManager.TITLE_HEIGHT)
                ),
                text="",
                manager=self.manager,
                object_id='#new_join_game_title_label'
            ),

            # Label pour afficher les erreurs.
            "error_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (10, 10),
                    (400, 30)
                ),
                text="",
                manager=self.manager,
                object_id="#error_label_on_game_page"
            ),

            # Informations sur les joueurs.
            "player1_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.MARGIN_X // 11,
                        GUIElementsManager.MARGIN_Y
                    ),
                    (200, 30)
                ),
                text="Player 1: ",
                manager=self.manager,
                object_id="#player1_label"
            ),
            "player2_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.MARGIN_X +
                        GUIElementsManager.GRID_DIMENSIONS +
                        GUIElementsManager.MARGIN_X // 10,
                        GUIElementsManager.MARGIN_Y
                    ),
                    (200, 30)
                ),
                text="",
                manager=self.manager,
                object_id="#player2_label"
            ),

            # Bouton pour quitter la partie.
            "quit_button": pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH - GUIElementsManager.BUTTON_WIDTH - GUIElementsManager.BUTTON_LEFT_RIGHT_MARGIN,
                        GUIElementsManager.SCREEN_HEIGHT - GUIElementsManager.BUTTON_BOTTOM_MARGIN
                    ),
                    (GUIElementsManager.BUTTON_WIDTH, GUIElementsManager.BUTTON_HEIGHT)
                ),
                text="Quitter la partie",
                manager=self.manager,
                object_id="#quit_button"
            ),

            # Statistiques du joueur local.
            "score_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.LABEL_LEFT_MARGIN,
                        GUIElementsManager.BUTTON_BETWEEN_MARGIN + 100
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="score_label",
                manager=self.manager,
                object_id="#score_label"
            ),
            "wins_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.LABEL_LEFT_MARGIN,
                        GUIElementsManager.LABEL_HEIGHT + ((3 / 2) * GUIElementsManager.BUTTON_BETWEEN_MARGIN) + 100
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="wins_label",
                manager=self.manager,
                object_id="#wins_label"
            ),
            "losses_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.LABEL_LEFT_MARGIN,
                        2 * (GUIElementsManager.LABEL_HEIGHT + GUIElementsManager.BUTTON_BETWEEN_MARGIN) + 100
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="losses_label",
                manager=self.manager,
                object_id="#losses_label"
            ),
            "forfeits_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.LABEL_LEFT_MARGIN,
                        3 * (GUIElementsManager.LABEL_HEIGHT + GUIElementsManager.BUTTON_BETWEEN_MARGIN) -
                        (GUIElementsManager.BUTTON_BETWEEN_MARGIN // 2) + 100
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="forfeits_label",
                manager=self.manager,
                object_id="#forfeits_label"
            ),
            "games_played_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.LABEL_LEFT_MARGIN,
                        4 * (GUIElementsManager.LABEL_HEIGHT + GUIElementsManager.BUTTON_BETWEEN_MARGIN) -
                        (GUIElementsManager.BUTTON_BETWEEN_MARGIN // 2) + 90
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="games_played_label",
                manager=self.manager,
                object_id="#games_played_label"
            ),

            # Statistiques de l'adversaire.
            "opponent_score_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH - GUIElementsManager.LABEL_LEFT_MARGIN - GUIElementsManager.LABEL_WIDTH,
                        GUIElementsManager.BUTTON_BETWEEN_MARGIN + 100
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="",
                manager=self.manager,
                object_id="#opponent_score_label"
            ),
            "opponent_wins_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH - GUIElementsManager.LABEL_LEFT_MARGIN - GUIElementsManager.LABEL_WIDTH,
                        GUIElementsManager.LABEL_HEIGHT + ((3 / 2) * GUIElementsManager.BUTTON_BETWEEN_MARGIN) + 100
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="",
                manager=self.manager,
                object_id="#opponent_wins_label"
            ),
            "opponent_losses_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH - GUIElementsManager.LABEL_LEFT_MARGIN - GUIElementsManager.LABEL_WIDTH,
                        2 * (GUIElementsManager.LABEL_HEIGHT + GUIElementsManager.BUTTON_BETWEEN_MARGIN) + 100
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="",
                manager=self.manager,
                object_id="#opponent_losses_label"
            ),
            "opponent_forfeits_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH - GUIElementsManager.LABEL_LEFT_MARGIN - GUIElementsManager.LABEL_WIDTH,
                        3 * (GUIElementsManager.LABEL_HEIGHT + GUIElementsManager.BUTTON_BETWEEN_MARGIN) -
                        (GUIElementsManager.BUTTON_BETWEEN_MARGIN // 2) + 100
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="",
                manager=self.manager,
                object_id="#opponent_forfeits_label"
            ),
            "opponent_games_played_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH - GUIElementsManager.LABEL_LEFT_MARGIN - GUIElementsManager.LABEL_WIDTH,
                        4 * (GUIElementsManager.LABEL_HEIGHT + GUIElementsManager.BUTTON_BETWEEN_MARGIN) -
                        (GUIElementsManager.BUTTON_BETWEEN_MARGIN // 2) + 90
                    ),
                    (GUIElementsManager.LABEL_WIDTH, GUIElementsManager.LABEL_HEIGHT)
                ),
                text="",
                manager=self.manager,
                object_id="#opponent_games_played_label"
            ),

            # Instructions pour le joueur.
            "instruction_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (
                        GUIElementsManager.SCREEN_WIDTH - GUIElementsManager.LABEL_LEFT_MARGIN - GUIElementsManager.LABEL_WIDTH,
                        10
                    ),
                    (GUIElementsManager.LABEL_WIDTH, 30)
                ),
                text="",
                manager=self.manager,
                object_id="#instruction_label_on_game_page"
            ),

            # Affichage des captures.
            "captures_label": pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (10, GUIElementsManager.SCREEN_HEIGHT // 2 + 30),
                    (GUIElementsManager.LABEL_WIDTH, 30)
                ),
                text="Captures: 0",
                manager=self.manager,
                object_id="#captures_label_on_game_page"
            ),
        }

    def draw_board(self) -> None:
        """
        Dessine le plateau de jeu en affichant les pièces à leurs positions respectives.

        Raises:
            NameError: Si des constantes ou variables utilisées ne sont pas définies.
            TypeError: Si le tableau `board` ou ses éléments sont mal définis.
        """
        # Parcourt chaque rangée de la grille
        for y in range(GUIElementsManager.GRID_ROWS):
            # Parcourt chaque colonne de la grille
            for x in range(GUIElementsManager.GRID_COLS):
                # Récupère l'état de la case actuelle
                cell = self.board[y * GUIElementsManager.GRID_COLS + x]

                # Calcul de la position en pixels de l'image
                img_x = GUIElementsManager.MARGIN_X + (x * GUIElementsManager.CELL_SIZE) - (
                        GUIElementsManager.PIECE_SIZE // 2)
                img_y = GUIElementsManager.MARGIN_Y + (y * GUIElementsManager.CELL_SIZE) - (
                        GUIElementsManager.PIECE_SIZE // 2)

                # Détermine l'image à utiliser en fonction du caractère dans la case
                pion_image = {
                    GUIElementsManager.HOST_CHAR: GUIElementsManager.HOST_PION_IMAGE_SCALED,
                    GUIElementsManager.OPPONENT_CHAR: GUIElementsManager.OPPONENT_PION_IMAGE_SCALED
                }.get(cell)

                # Dessine l'image si elle est définie
                if pion_image:
                    self.screen.blit(pion_image, (img_x, img_y))

    def draw_grid(self) -> None:
        """
        Dessine la grille du plateau et les points "hoshi" sur la surface donnée.

        Raises:
            ValueError: Si la surface n'est pas valide.
        """
        # Vérifie que la surface est valide
        if not isinstance(self.surface, pygame.Surface):
            raise ValueError("La surface fournie n'est pas valide.")

        # Dessiner les lignes verticales
        for x in range(GUIElementsManager.GRID_COLS):
            pygame.draw.line(
                self.surface,
                GUIElementsManager.LINE_COLOR,
                (GUIElementsManager.MARGIN_X + x * GUIElementsManager.CELL_SIZE, GUIElementsManager.MARGIN_Y),
                (GUIElementsManager.MARGIN_X + x * GUIElementsManager.CELL_SIZE,
                 GUIElementsManager.MARGIN_Y + GUIElementsManager.GRID_DIMENSIONS),
                GUIElementsManager.LINE_WIDTH_CENTER if x == GUIElementsManager.GRID_COLS // 2 else GUIElementsManager.LINE_WIDTH_DEFAULT
            )

        # Dessiner les lignes horizontales
        for y in range(GUIElementsManager.GRID_ROWS):
            pygame.draw.line(
                self.surface,
                GUIElementsManager.LINE_COLOR,
                (GUIElementsManager.MARGIN_X, GUIElementsManager.MARGIN_Y + y * GUIElementsManager.CELL_SIZE),
                (GUIElementsManager.MARGIN_X + GUIElementsManager.GRID_DIMENSIONS,
                 GUIElementsManager.MARGIN_Y + y * GUIElementsManager.CELL_SIZE),
                GUIElementsManager.LINE_WIDTH_CENTER if y == GUIElementsManager.GRID_ROWS // 2 else GUIElementsManager.LINE_WIDTH_DEFAULT
            )

        # Ajouter les points "hoshi" sur le plateau
        for px, py in GUIElementsManager.HOSHI_POINTS:
            pygame.draw.rect(
                self.surface,
                GUIElementsManager.LINE_COLOR,
                pygame.Rect(
                    GUIElementsManager.MARGIN_X + px * GUIElementsManager.CELL_SIZE - GUIElementsManager.HOSHI_POINTS_SIZE // 2,
                    GUIElementsManager.MARGIN_Y + py * GUIElementsManager.CELL_SIZE - GUIElementsManager.HOSHI_POINTS_SIZE // 2,
                    GUIElementsManager.HOSHI_POINTS_SIZE,
                    GUIElementsManager.HOSHI_POINTS_SIZE
                )
            )
