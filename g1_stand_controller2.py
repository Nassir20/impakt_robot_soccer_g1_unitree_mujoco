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

    print("[INFO] Posture dynamique : jambes verrouillées et bras relâchés...")

    cmd = LowCmd_default()
    NUM_MOTORS = 29

    try:
        while True:
            # 1. On prépare le tableau de positions cibles pour les jambes
            q_target = [0.0] * NUM_MOTORS

            # Posture des jambes (légèrement fléchies et reculées)
            q_target[0] = -0.15  # left_hip_pitch (On recule un peu plus la hanche)
            q_target[3] = 0.6  # left_knee (Genou bien fléchi)
            q_target[4] = -0.15  # left_ankle_pitch

            q_target[6] = -0.15  # right_hip_pitch
            q_target[9] = 0.6  # right_knee
            q_target[10] = -0.15  # right_ankle_pitch

            # 2. On applique les commandes moteur par moteur
            for i in range(NUM_MOTORS):
                if i <= 11:
                    # --- GROUPE JAMBES : Actif et Rigide ---
                    cmd.motor_cmd[i].q = q_target[i]
                    cmd.motor_cmd[i].dq = 0.0
                    cmd.motor_cmd[i].kp = 80.0  # On augmente la force sur les jambes
                    cmd.motor_cmd[i].kd = 2.0
                    cmd.motor_cmd[i].tau = 0.0
                else:
                    # --- GROUPE BUSTE & BRAS : Totalement relâchés (Passifs) ---
                    cmd.motor_cmd[i].q = 0.0
                    cmd.motor_cmd[i].dq = 0.0
                    cmd.motor_cmd[i].kp = 0.0  # Plus aucune raideur ! Le moteur est "mou"
                    cmd.motor_cmd[i].kd = 0.5  # Juste un poil de friction pour amortir la chute des bras
                    cmd.motor_cmd[i].tau = 0.0

            low_cmd_publisher.Write(cmd)
            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\n[INFO] Contrôleur arrêté.")


if __name__ == "__main__":
    main()