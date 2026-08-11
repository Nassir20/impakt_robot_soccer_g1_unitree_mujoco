import time
import sys

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_ as LowCmd_default

TOPIC_LOWCMD = "rt/lowcmd"

def main():
    # Connexion calée sur ta config.py
    ChannelFactoryInitialize(1, "lo0")
    low_cmd_publisher = ChannelPublisher(TOPIC_LOWCMD, LowCmd_)
    low_cmd_publisher.Init()
    
    print("[INFO] Contrôleur déterministe de KICK initialisé...")
    cmd = LowCmd_default()
    NUM_MOTORS = 29 
    
    start_time = time.time()

    try:
        while True:
            t = time.time() - start_time
            q_target = [0.0] * NUM_MOTORS 
            
            # Posture nominale par défaut (Jambe gauche d'appui et hanche droite stables)
            q_target[0] = -0.15  # left_hip_pitch
            q_target[3] = 0.4    # left_knee (Genou gauche plié pour l'appui)
            q_target[4] = -0.15  # left_ankle_pitch
            
            q_target[6] = -0.15  # right_hip_pitch
            q_target[10] = -0.15 # right_ankle_pitch

            # --- SÉQUENCE CHRONOMÉTRÉE DU COUP DE PIED DROIT ---
            if t < 2.0:
                # Étape A : Position d'attente stable au sol
                q_target[9] = 0.4   # Genou droit légèrement plié
            elif t >= 2.0 and t < 3.0:
                # Étape B : On arme la jambe droite vers l'arrière
                q_target[6] = -0.4  # La hanche droite recule
                q_target[9] = 0.8   # Le genou droit se fléchit fort
            elif t >= 3.0 and t < 3.6:
                # Étape C : LE SHOT ! Extension vers l'avant
                q_target[6] = 0.4   # La hanche droite est projetée en avant
                q_target[9] = 0.0   # Le genou droit se détend d'un coup sec
            else:
                # Étape D : Retour à la posture de repos et boucle finie
                q_target[6] = -0.15
                q_target[9] = 0.4

            # Remplissage du message DDS pour MuJoCo
            for i in range(NUM_MOTORS):
                cmd.motor_cmd[i].q = q_target[i]
                cmd.motor_cmd[i].dq = 0.0
                # On met de la force uniquement sur les jambes (index 0 à 11)
                cmd.motor_cmd[i].kp = 80.0 if i <= 11 else 0.0
                cmd.motor_cmd[i].kd = 2.0 if i <= 11 else 0.5
                cmd.motor_cmd[i].tau = 0.0
            
            low_cmd_publisher.Write(cmd)
            time.sleep(0.005) # Fréquence de contrôle de 200 Hz
            
    except KeyboardInterrupt:
        print("\n[INFO] Arrêt du contrôleur.")

if __name__ == "__main__":
    main()