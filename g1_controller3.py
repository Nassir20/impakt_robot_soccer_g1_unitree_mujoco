import time
import sys

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_ as LowCmd_default

TOPIC_LOWCMD = "rt/lowcmd"

def main():
    ChannelFactoryInitialize(1, "lo0")
    low_cmd_publisher = ChannelPublisher(TOPIC_LOWCMD, LowCmd_)
    low_cmd_publisher.Init()
    
    print("[INFO] Lancement du contrôleur d'équilibre géométrique...")
    cmd = LowCmd_default()
    NUM_MOTORS = 29 

    # Pour stabiliser le choc initial, on utilise des gains très fermes sur les jambes
    KP_LEGS = 95.0  
    KD_LEGS = 3.5

    try:
        while True:
            q_target = [0.0] * NUM_MOTORS 
            
            # --- POSTURE SCIENTIFIQUE D'ÉQUILIBRE DU G1 ---
            # On penche légèrement le bassin vers l'avant pour contrer le poids du dos
            q_target[0] = 0.15   # left_hip_pitch 
            q_target[6] = 0.15   # right_hip_pitch
            
            # On fléchit modérément les genoux pour baisser le centre de masse
            q_target[3] = 0.35   # left_knee 
            q_target[9] = 0.35   # right_knee
            
            # On incline les chevilles pour ramener les pieds bien à plat sous le nouveau centre de gravité
            q_target[4] = -0.2   # left_ankle_pitch
            q_target[10] = -0.2  # right_ankle_pitch

            for i in range(NUM_MOTORS):
                if i <= 11:
                    # Configuration jambes (Rigide)
                    cmd.motor_cmd[i].q = q_target[i]
                    cmd.motor_cmd[i].dq = 0.0
                    cmd.motor_cmd[i].kp = KP_LEGS
                    cmd.motor_cmd[i].kd = KD_LEGS
                    cmd.motor_cmd[i].tau = 0.0
                else:
                    # Configuration buste et bras (Léger amortissement passif)
                    cmd.motor_cmd[i].q = 0.0
                    cmd.motor_cmd[i].dq = 0.0
                    cmd.motor_cmd[i].kp = 0.0
                    cmd.motor_cmd[i].kd = 0.8
                    cmd.motor_cmd[i].tau = 0.0
            
            low_cmd_publisher.Write(cmd)
            time.sleep(0.005)
            
    except KeyboardInterrupt:
        print("\n[INFO] Contrôleur arrêté.")

if __name__ == "__main__":
    main()