import time
import sys

# Initialisation des outils de communication du SDK2 d'Unitree
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_ as LowCmd_default

# Nom du canal (topic) sur lequel le simulateur écoute les ordres
TOPIC_LOWCMD = "rt/lowcmd"


def main():
    # 1. Initialisation de la fabrique réseau CycloneDDS d'Unitree [cite: 30, 54]
    # "lo" signifie Localhost (boucle locale). Le Domain ID par défaut est 0.
    ChannelFactoryInitialize(1, "lo0")

    # 2. On crée le diffuseur (Publisher) réseau pour injecter nos commandes
    low_cmd_publisher = ChannelPublisher(TOPIC_LOWCMD, LowCmd_)
    low_cmd_publisher.Init()

    print("[INFO] Contrôleur démarré. Envoi de la consigne de position 'Debout'...")

    # 3. Génération de l'objet de commande à partir du schéma IDL officiel d'Unitree
    cmd = LowCmd_default()

    # Le robot G1 en version IDL HG possède 35 moteurs configurables par défaut
    NUM_MOTORS = 35

    # Définition des gains PD pour "verrouiller" le squelette mécanique
    # Kp élevé = muscles rigides (lutte contre la gravité)
    # Kd = amortissement pour supprimer les tremblements
    KP_STIFF = 80.0
    KD_DAMP = 2.0

    # 4. Boucle temps-réel d'envoi à haute fréquence
    try:
        while True:
            # On parcourt chaque articulation du robot pour lui attribuer son comportement
            for i in range(NUM_MOTORS):
                cmd.motor_cmd[i].q = 0.0  # Position articulaire cible (alignement neutre droit)
                cmd.motor_cmd[i].dq = 0.0  # Vitesse cible nulle (immobile)
                cmd.motor_cmd[i].kp = KP_STIFF  # Injection de la raideur
                cmd.motor_cmd[i].kd = KD_DAMP  # Injection de l'amortisseur
                cmd.motor_cmd[i].tau = 0.0  # Aucun couple additionnel (Feedforward)

            # Publication du paquet LowCmd sur le bus DDS local
            low_cmd_publisher.Write(cmd)

            # Envoi toutes les 5 millisecondes (Fréquence de contrôle de 200 Hz) [cite: 259]
            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\n[INFO] Fermeture propre du contrôleur.")


if __name__ == "__main__":
    main()