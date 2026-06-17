from pymavlink import mavutil
from datetime import datetime
import math


# Port série utilisé pour communiquer avec le contrôleur de vol.
# Sur Raspberry Pi, /dev/serial0 correspond souvent à l'UART principal.
PORT = "/dev/serial0"

# Vitesse de communication série.
# Elle doit être identique à celle configurée sur le contrôleur de vol.
BAUDRATE = 57600


def now_iso():
    """
    Retourne la date et l'heure actuelles au format ISO.

    Cette fonction permet d'ajouter un timestamp aux données reçues.
    Cela permet de savoir quand la position ou l'orientation du drone
    a été mise à jour.

    Returns:
        str: Date et heure actuelles.
    """
    return datetime.now().isoformat()


def safe_degrees(rad):
    """
    Convertit un angle en radians vers un angle en degrés.

    MAVLink envoie souvent les angles en radians.
    Les degrés sont plus simples à lire et à utiliser pour l'affichage.

    Args:
        rad (float | None): Angle en radians.

    Returns:
        float | None: Angle en degrés, ou None si la valeur est absente.
    """
    if rad is None:
        return None

    return math.degrees(rad)


def create_initial_state():
    """
    Crée la structure de base contenant l'état du drone.

    Au début, les valeurs sont à None parce qu'aucun message MAVLink
    n'a encore été reçu.

    Returns:
        dict: État initial du drone.
    """
    return {
        "port": PORT,
        "baudrate": BAUDRATE,
        "start_time": now_iso(),
        "position": None,
        "orientation": None,
        "gps_raw": None,
        "hud": None,
        "system": None,
        "heartbeat": None,
        "last_update": None
    }


def update_state(state, msg):
    """
    Met à jour l'état du drone à partir d'un message MAVLink.

    Le contrôleur de vol envoie plusieurs types de messages.
    Cette fonction regarde le type du message reçu et extrait seulement
    les informations utiles.

    Args:
        state (dict): État actuel du drone.
        msg: Message MAVLink reçu.

    Returns:
        dict: État du drone mis à jour.
    """

    msg_type = msg.get_type()

    if msg_type == "HEARTBEAT":
        # HEARTBEAT indique que l'autopilote est vivant et répond.
        state["heartbeat"] = msg.to_dict()

    elif msg_type == "GLOBAL_POSITION_INT":
        # GLOBAL_POSITION_INT contient la position GPS du drone.
        #
        # MAVLink envoie :
        # - latitude et longitude multipliées par 10^7
        # - altitude en millimètres
        # - vitesses en cm/s
        #
        # Ici, on convertit tout dans des unités plus lisibles.
        state["position"] = {
            "timestamp": now_iso(),
            "latitude": msg.lat / 1e7,
            "longitude": msg.lon / 1e7,
            "altitude_m": msg.alt / 1000.0,
            "relative_altitude_m": msg.relative_alt / 1000.0,
            "vx_m_s": msg.vx / 100.0,
            "vy_m_s": msg.vy / 100.0,
            "vz_m_s": msg.vz / 100.0,
            "heading_deg": msg.hdg / 100.0 if msg.hdg != 65535 else None
        }

    elif msg_type == "ATTITUDE":
        # ATTITUDE contient l'orientation du drone :
        # - roll  : inclinaison gauche/droite
        # - pitch : inclinaison avant/arrière
        # - yaw   : direction du nez du drone
        #
        # Les angles sont en radians, donc on les convertit en degrés.
        yaw = safe_degrees(msg.yaw)

        # Si yaw est négatif, on le remet entre 0° et 360°.
        # Exemple : -10° devient 350°.
        if yaw is not None and yaw < 0:
            yaw += 360

        state["orientation"] = {
            "timestamp": now_iso(),
            "roll_deg": safe_degrees(msg.roll),
            "pitch_deg": safe_degrees(msg.pitch),
            "yaw_deg": yaw,
            "rollspeed_rad_s": msg.rollspeed,
            "pitchspeed_rad_s": msg.pitchspeed,
            "yawspeed_rad_s": msg.yawspeed
        }

    elif msg_type == "GPS_RAW_INT":
        # Données GPS brutes.
        # Utile pour vérifier la qualité du GPS :
        # nombre de satellites, type de fix, précision, etc.
        state["gps_raw"] = msg.to_dict()

    elif msg_type == "VFR_HUD":
        # Données simplifiées de vol :
        # vitesse air, vitesse sol, altitude, gaz, montée/descente.
        state["hud"] = msg.to_dict()

    elif msg_type == "SYS_STATUS":
        # État général du système :
        # batterie, capteurs présents, capteurs actifs, erreurs.
        state["system"] = msg.to_dict()

    # Date de dernière mise à jour.
    state["last_update"] = now_iso()

    return state


def connect_mavlink():
    """
    Se connecte au contrôleur de vol via MAVLink.

    Cette fonction ouvre le port série, puis attend un message HEARTBEAT.
    Le HEARTBEAT confirme que le contrôleur de vol communique bien.

    Returns:
        mavutil.mavfile: Connexion MAVLink active.
    """

    print(f"Connexion MAVLink sur {PORT} à {BAUDRATE} bauds...")

    master = mavutil.mavlink_connection(PORT, baud=BAUDRATE)

    print("Attente heartbeat...")
    master.wait_heartbeat()

    print("Autopilote détecté")

    return master