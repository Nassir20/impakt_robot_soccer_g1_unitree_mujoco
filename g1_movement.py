import time
import sys
import math  # On importe math pour utiliser le sinus au cours du temps

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_ as LowCmd_default

TOPIC_LOWCMD = "rt/lowcmd"

def main():
    ChannelFactoryInitialize(1, "lo0")
    
    low_cmd_publisher = ChannelPublisher(TOPIC_LOWCMD, LowCmd_)
    low_cmd_publisher.Init()
    
    print("[INFO] Mode animation : Le G1 balance la jambe droite...")
    
    cmd = LowCmd_default()
    NUM_MOTORS = 29 

    # Gains de raideur
    KP_STIFF = 80.0  
    KD_DAMP = 2.0
    
    start_time = time.time()

    try:
        while True:
            # Calcul du temps écoulé depuis le début du script
            t = time.time() - start_time
            
            # Initialisation des positions cibles
            q_target = [0.0] * NUM_MOTORS 
            
            # --- POSTURE DE BASE FIXE (Jambe Gauche et hanche droite) ---
            q_target[0] = -0.15  # left_hip_pitch
            q_target[3] = 0.6    # left_knee
            q_target[4] = -0.15  # left_ankle_pitch
            
            q_target[6] = -0.15  # right_hip_pitch
            q_target[10] = -0.15 # right_ankle_pitch

            # --- CORPS DU MOUVEMENT : Jambe Droite Mobile (Index 9) ---
            # Le genou droit (index 9) va osciller entre 0.2 et 0.8 radian
            # math.sin(2 * t) crée un mouvement fluide de va-et-vient toutes les quelques secondes
            q_target[9] = 0.5 + 0.3 * math.sin(2 * t) 

            # Envoi des commandes
            for i in range(NUM_MOTORS):
                if i <= 11:
                    cmd.motor_cmd[i].q = q_target[i]
                    cmd.motor_cmd[i].dq = 0.0
                    cmd.motor_cmd[i].kp = KP_STIFF
                    cmd.motor_cmd[i].kd = KD_DAMP
                    cmd.motor_cmd[i].tau = 0.0
                else:
                    # On laisse le haut du corps détendu
                    cmd.motor_cmd[i].q = 0.0
                    cmd.motor_cmd[i].dq = 0.0
                    cmd.motor_cmd[i].kp = 0.0
                    cmd.motor_cmd[i].kd = 0.5
                    cmd.motor_cmd[i].tau = 0.0
            
            low_cmd_publisher.Write(cmd)
            time.sleep(0.005)
            
    except KeyboardInterrupt:
        print("\n[INFO] Contrôleur arrêté.")

if __name__ == "__main__":
    main()