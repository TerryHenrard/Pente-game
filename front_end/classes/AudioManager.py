import os

import pygame
from pygame_gui.elements import UIButton

# pdoc: format de la documentation
__docformat__ = "google"


class AudioManager:
    """Gestionnaire audio pour la lecture de musique et de sons."""

    def __init__(self, sound_enabled: bool = True) -> None:
        """Initialise le gestionnaire audio avec un état du son activé par défaut."""
        if not isinstance(sound_enabled, bool):
            raise TypeError("Le paramètre 'sound_enabled' doit être un booléen.")

        pygame.mixer.init()
        self.sound_enabled = sound_enabled

    def toggle_sound(self) -> bool:
        """
        Active ou désactive le son. Audio et musique seront coupés si le son est désactivé.

        Returns:
            bool: Le nouvel état du son (True pour activé, False pour désactivé).

        Raises:
            RuntimeError: Si le mixeur de pygame n'est pas initialisé.
        """
        # Vérifie si le mixeur de pygame est initialisé
        if not pygame.mixer.get_init():
            raise RuntimeError(
                "pygame.mixer n'est pas initialisé. Assurez-vous que pygame.mixer.init() est appelé avant de basculer le son."
            )

        # Arrête tout audio en cours de lecture si nécessaire
        if pygame.mixer.get_busy():
            pygame.mixer.stop()

        # Inverse l'état actuel du son
        self.sound_enabled = not self.sound_enabled

        # Ajuste le volume en fonction du nouvel état
        pygame.mixer.music.set_volume(1 if self.sound_enabled else 0)

        return self.sound_enabled

    def update_sound_button(self, sound_button: UIButton) -> None:
        """
        Met à jour le texte du bouton en fonction de l'état du son.

        Args:
            sound_button (UIButton): Objet du bouton à modifier (doit implémenter la méthode `set_text`).

        Raises:
            ValueError: Si le bouton fourni est invalide ou ne contient pas la méthode `set_text`.
        """
        # Vérifie que le bouton est valide
        if not sound_button or not hasattr(sound_button, "set_text"):
            raise ValueError("Le bouton fourni est invalide ou ne possède pas de méthode `set_text`.")

        # Détermine le texte du bouton en fonction de l'état du son
        button_text = "Désactiver le son" if self.sound_enabled else "Activer le son"

        # Met à jour le texte du bouton
        sound_button.set_text(button_text)

    def play_music(self, music_path: str, volume: float = 1.0, fade_ms: int = 0, is_loop: bool = False) -> None:
        """
        Joue un fichier musical.

        Args:
            music_path (str): Chemin du fichier audio.
            volume (float): Niveau du volume (valeurs entre 0.0 et 1.0). Par défaut, 1.0.
            fade_ms (int): Durée de transition (en millisecondes) pour l'apparition progressive de la musique. Par défaut, 0.
            is_loop (bool): Si vrai, boucle la musique indéfiniment. Par défaut, False.

        Raises:
            ValueError: Si le volume est hors de l'intervalle [0.0, 1.0].
            FileNotFoundError: Si le fichier audio spécifié n'existe pas.
            pygame.error: Si une erreur Pygame survient.
        """
        # Vérifie si le chemin est une chaîne non vide
        if not music_path or not isinstance(music_path, str):
            raise ValueError("Le chemin de la musique doit être une chaîne non vide.")

        # Vérifie si le fichier existe
        if not os.path.exists(music_path):
            raise FileNotFoundError(f"Le fichier audio spécifié n'existe pas : {music_path}")

        # Vérifie si le volume est dans les limites acceptables
        if not (0.0 <= volume <= 1.0):
            raise ValueError("Le volume doit être compris entre 0.0 et 1.0.")

        # Si le son est activé, joue la musique
        if self.sound_enabled:
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(loops=-1 if is_loop else 0, fade_ms=fade_ms)
            except pygame.error as pe:
                raise pygame.error(f"Erreur Pygame lors de la lecture de la musique : {pe}") from pe

    def play_audio(self, sound_path: str, volume: float = 0.1) -> None:
        """
        Joue un fichier audio.

        Args:
            sound_path (str): Chemin vers le fichier audio à jouer.
            volume (float): Niveau du volume (valeurs entre 0.0 et 1.0). Par défaut, 0.1.

        Raises:
            ValueError: Si le volume est hors des limites acceptables.
            TypeError: Si les paramètres sont de types incorrects.
            FileNotFoundError: Si le fichier audio spécifié n'existe pas.
            pygame.error: Si une erreur se produit lors de la lecture audio.
        """
        # Validation des paramètres
        if not isinstance(sound_path, str) or not sound_path.strip():
            raise ValueError("Le paramètre 'sound_path' doit être une chaîne non vide.")

        if not os.path.exists(sound_path):
            raise FileNotFoundError(f"Le fichier audio spécifié n'existe pas : {sound_path}")

        if not (0.0 <= volume <= 1.0):
            raise ValueError("Le volume doit être compris entre 0.0 et 1.0.")

        # Si le son est activé et aucun autre son n'est en cours de lecture
        if self.sound_enabled and not pygame.mixer.get_busy():
            try:
                sound = pygame.mixer.Sound(sound_path)
                sound.set_volume(volume)
                sound.play()
            except pygame.error as pe:
                raise pygame.error(f"Erreur Pygame lors de la lecture de l'audio : {pe}") from pe
