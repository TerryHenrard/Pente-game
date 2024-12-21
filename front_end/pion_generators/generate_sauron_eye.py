from matplotlib import pyplot as plt
from matplotlib.patches import Ellipse


def generate_eye_of_sauron_ellipses():
    # Configuration de l'image
    fig, ax = plt.subplots(
        figsize=(2, 2),
        dpi=300
    )
    ax.set_facecolor("none")  # Transparence pour le fond

    # Ellipse extérieure horizontale (mélange de rouge et noir)
    ellipse_outer = plt.matplotlib.patches.Ellipse(
        (0, 0),
        width=1.2,
        height=0.6,
        color="#8B0000",
        alpha=0.8,
        fill=True
    )
    ax.add_artist(ellipse_outer)

    ellipse_glow_outer = plt.matplotlib.patches.Ellipse(
        (0, 0),
        width=1.3,
        height=0.7,
        color="#FF4500",
        alpha=0.5,
        fill=True
    )
    ax.add_artist(ellipse_glow_outer)

    # Ellipse centrale noire et verticale
    ellipse_inner_black = plt.matplotlib.patches.Ellipse(
        (0, 0),
        width=0.2,
        height=0.8,
        color="black",
        fill=True
    )
    ax.add_artist(ellipse_inner_black)

    # Mélange des effets de lumière autour de l'ellipse centrale
    ellipse_inner_glow = plt.matplotlib.patches.Ellipse(
        (0, 0),
        width=0.25,
        height=0.85,
        color="#FF0000",
        alpha=0.6,
        fill=True
    )
    ax.add_artist(ellipse_inner_glow)

    # Suppression des axes pour un effet propre
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.axis('off')

    # Sauvegarde de l'image
    plt.savefig(
        "/Downloads/eye_of_sauron_final.png",
        transparent=True
    )
    plt.close()


generate_eye_of_sauron_ellipses()
"/Downloads/eye_of_sauron_final.png"
