import matplotlib.pyplot as plt
import numpy as np

# pdoc: format de la documentation
__docformat__ = "google"


# Création d'une image représentant l'Anneau Unique stylisé
def generate_one_ring():
    # Configuration de l'image
    fig, ax = plt.subplots(
        figsize=(2, 2),
        dpi=300
    )
    ax.set_facecolor("black")

    # Cercle doré extérieur
    circle_outer = plt.Circle(
        (0.5, 0.5),
        0.4,
        color="#D4AF37",
        fill=True,
        linewidth=2
    )
    ax.add_artist(circle_outer)

    # Cercle intérieur (pour créer un effet d'anneau)
    circle_inner = plt.Circle(
        (0.5, 0.5),
        0.3,
        color="black",
        fill=True
    )
    ax.add_artist(circle_inner)

    # Ajout de "runes elfiques" stylisées (texte symbolique)
    text = "Ash nazg durbatulûk"  # Une partie des inscriptions
    for i, char in enumerate(text):
        angle = i * (360 / len(text))
        x = 0.5 + 0.35 * np.cos(np.radians(angle))
        y = 0.5 + 0.35 * np.sin(np.radians(angle))
        ax.text(
            x,
            y,
            char,
            color="#FF8C00",
            fontsize=6,
            ha='center',
            va='center',
            rotation=angle
        )

    # Suppression des axes
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Sauvegarde de l'image
    plt.savefig("/Downloads/anneau_unique_pion.png", transparent=True)
    plt.close()


generate_one_ring()
"/Downloads/anneau_unique_pion.png"
