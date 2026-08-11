import time
import sys
import math

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher
# On repasse sur les DDS de bas niveau (LowCmd)
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_ as LowCmd_default

TOPIC_LOWCMD = "rt/lowcmd"

def main():
    ChannelFactoryInitialize(1, "lo0")
    
    low_cmd_publisher = ChannelPublisher(TOPIC_LOWCMD, LowCmd_)
    low_cmd_publisher.Init()
    
    print("[INFO] Lanceur du générateur de marche déterministe (Low-Level)...")
    
    cmd = LowCmd_default()
    NUM_MOTORS = 29 
    
    # Paramètres de la marche (générateur de rythme)
    frequence = 1.2       # Vitesse des pas (en Hz)
    amplitude_marche = 0.25 # Amplitude de l'oscillation des hanches
    amplitude_genou = 0.35  # Amplitude de la flexion du genou
    
    start_time = time.time()

    try:
        while True:
            t = time.time() - start_time
            q_target = [0.0] * NUM_MOTORS 
            
            # Calcul du rythme de marche déphasé de 180° entre jambe gauche et droite
            # La jambe gauche est basée sur t, la jambe droite est déphasée de pi
            rythme_gauche = 2 * math.pi * frequence * t
            rythme_droit = 2 * math.pi * frequence * t + math.pi
            
            # Posture de base stable (légèrement accroupi pour de bons appuis)
            offset_hip = -0.1
            offset_knee = 0.4
            offset_ankle = -0.1

            # CINÉMATIQUE DE LA JAMBE GAUCHE (Index 0 à 5)
            # La hanche balance d'avant en arrière
            q_target[0] = offset_hip + amplitude_marche * math.sin(rythme_gauche) 
            # Le genou se plie (on utilise math.sin(t) redressé pour ne plier que vers l'avant)
            q_target[3] = offset_knee + amplitude_genou * max(0, math.cos(rythme_gauche)) 
            # La cheville compense pour garder le pied parallèle au sol
            q_target[4] = offset_ankle - q_target[0] + (q_target[3] * 0.3)

            # CINÉMATIQUE DE LA JAMBE DROITE (Index 6 à 11) -> Inversée par rapport à la gauche
            q_target[6] = offset_hip + amplitude_marche * math.sin(rythme_droit)
            q_target[9] = offset_knee + amplitude_genou * max(0, math.cos(rythme_droit))
            q_target[10] = offset_ankle - q_target[6] + (q_target[9] * 0.3)

            # Remplissage des DDS
            for i in range(NUM_MOTORS):
                cmd.motor_cmd[i].q = q_target[i]
                cmd.motor_cmd[i].dq = 0.0
                cmd.motor_cmd[i].kp = 80.0 if i <= 11 else 0.0 # Force forte sur les jambes, aucune sur le buste
                cmd.motor_cmd[i].kd = 2.0 if i <= 11 else 0.5
                cmd.motor_cmd[i].tau = 0.0
            
            low_cmd_publisher.Write(cmd)
            time.sleep(0.005) # Fréquence de contrôle de 200 Hz
            
    except KeyboardInterrupt:
        print("\n[INFO] Arrêt du contrôleur de marche.")
        
if __name__ == "__main__":
    main()