import math


def estimatePosition(
    x_center_box,
    y_center_box,
    frame_width,
    frame_height,
    fov_x_deg,
    fov_y_deg,
    alt,
    lat=None,
    lon=None,
    heading_deg=0
):
    """
    Estime la position au sol d'un objet détecté.

    Le principe est le suivant :

        1. YOLO donne le centre de l'objet dans l'image.
        2. On compare ce centre au centre de l'image.
        3. Avec l'altitude et le champ de vision de la caméra,
           on convertit l'écart en pixels vers un écart en mètres.
        4. Avec le heading du drone, on transforme cet écart en axes :
           Nord / Est.
        5. Si le GPS du drone est disponible, on estime le GPS de l'objet.

    Args:
        x_center_box (int | float):
            Position X du centre de la box en pixels.

        y_center_box (int | float):
            Position Y du centre de la box en pixels.

        frame_width (int):
            Largeur de l'image en pixels.

        frame_height (int):
            Hauteur de l'image en pixels.

        fov_x_deg (float):
            Champ de vision horizontal de la caméra en degrés.

        fov_y_deg (float):
            Champ de vision vertical de la caméra en degrés.

        alt (float):
            Altitude relative du drone par rapport au sol en mètres.

        lat (float | None):
            Latitude GPS du drone.

        lon (float | None):
            Longitude GPS du drone.

        heading_deg (float):
            Orientation du drone en degrés.
            0° = Nord
            90° = Est
            180° = Sud
            270° = Ouest

    Returns:
        dict:
            Position estimée de l'objet.
    """

    # Conversion des angles de degrés vers radians.
    fov_x = math.radians(fov_x_deg)
    fov_y = math.radians(fov_y_deg)

    # Largeur et hauteur de la zone observée au sol.
    # Plus le drone est haut, plus la zone visible au sol est grande.
    ground_width = 2 * alt * math.tan(fov_x / 2)
    ground_height = 2 * alt * math.tan(fov_y / 2)

    # Décalage du centre de l'objet par rapport au centre de l'image.
    #
    # dx_pixel > 0 : objet à droite de l'image.
    # dx_pixel < 0 : objet à gauche de l'image.
    #
    # dy_pixel > 0 : objet en bas de l'image.
    # dy_pixel < 0 : objet en haut de l'image.
    dx_pixel = x_center_box - frame_width / 2
    dy_pixel = y_center_box - frame_height / 2

    # Conversion du décalage pixel en mètres.
    #
    # right_m :
    #   distance à droite/gauche du drone.
    #
    # forward_m :
    #   distance devant/derrière le drone.
    #
    # Le signe moins sur dy_pixel est important :
    # dans une image, Y augmente vers le bas,
    # alors qu'en repère drone, l'avant est considéré positif.
    right_m = (dx_pixel / frame_width) * ground_width
    forward_m = -(dy_pixel / frame_height) * ground_height

    # Conversion du heading en radians pour utiliser sin/cos.
    heading_rad = math.radians(heading_deg)

    # Rotation du repère drone vers le repère géographique.
    #
    # forward/right sont liés au drone.
    # north/east sont liés à la Terre.
    north_m = forward_m * math.cos(heading_rad) - right_m * math.sin(heading_rad)
    east_m = forward_m * math.sin(heading_rad) + right_m * math.cos(heading_rad)

    result = {
        "pixel_center": {
            "x": x_center_box,
            "y": y_center_box
        },
        "relative_position_m": {
            "forward_m": forward_m,
            "right_m": right_m,
            "north_m": north_m,
            "east_m": east_m
        },
        "gps": None
    }

    # Si le GPS du drone est disponible,
    # on estime la latitude et la longitude de l'objet.
    if lat is not None and lon is not None:
        # Approximation :
        # 1 degré de latitude ≈ 111 km.
        delta_lat = north_m / 111000

        # La longitude dépend de la latitude.
        delta_lon = east_m / (111000 * math.cos(math.radians(lat)))

        result["gps"] = {
            "latitude": lat + delta_lat,
            "longitude": lon + delta_lon
        }

    return result