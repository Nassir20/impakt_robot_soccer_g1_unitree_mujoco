import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np
import time

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

class G1StandEnv(gym.Env):
    """Environnement Gymnasium personnalisé pour apprendre au G1 à tenir debout"""
    metadata = {"render_modes": ["human"], "render_fps": 200}

    def __init__(self):
        super(G1StandEnv, self).__init__()
        
        # 1. Chargement du modèle XML du G1 (29 DDL)
        # Ajuste le chemin vers ton fichier scene.xml
        self.model = mujoco.MjModel.from_xml_path("../unitree_robots/g1/scene.xml")
        self.data = mujoco.MjData(self.model)
        
        # On se concentre uniquement sur le contrôle des 12 moteurs des jambes
        self.num_leg_motors = 12
        
        # 2. Définition des espaces d'action et d'observation
        # Actions : Consignes de position delta pour les 12 moteurs des jambes [-1, 1]
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(self.num_leg_motors,), dtype=np.float32)
        
        # Observations : IMU (3 angles + 3 vitesses) + Positions/Vitesses des 12 moteurs = 30 valeurs
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(30,), dtype=np.float32)
        
        # Paramètres du contrôleur PD local du simulateur
        self.kp = 60.0
        self.kd = 2.0
        
        # Posture "debout" de référence (offset)
        self.nominal_pose = np.array([-0.15, 0.0, 0.0, 0.35, -0.2, 0.0,   # Jambe Gauche
                                      -0.15, 0.0, 0.0, 0.35, -0.2, 0.0])  # Jambe Droite

    def _get_obs(self):
        # Extraction de l'IMU (orientation de la base et vitesse angulaire)
        torso_quat = self.data.qpos[3:7]  # Quaternion
        torso_angvel = self.data.qvel[3:6] # Vitesse angulaire
        
        # Positions et vitesses des articulations des jambes (index 7 à 18 dans qpos)
        leg_positions = self.data.qpos[7:19]
        leg_velocities = self.data.qvel[6:18]
        
        return np.concatenate([torso_quat[1:], torso_angvel, leg_positions, leg_velocities]).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Réinitialisation de la simulation MuJoCo
        mujoco.mj_resetData(self.model, self.data)
        
        # Placer le robot un peu au-dessus du sol pour le spawn
        self.data.qpos[2] = 0.82 
        
        # Appliquer la posture nominale dès le départ
        self.data.qpos[7:19] = self.nominal_pose
        mujoco.mj_forward(self.model, self.data)
        
        return self._get_obs(), {}

    def step(self, action):
        # 1. Convertir les actions [-1, 1] du réseau en angles réels (max +- 0.2 radian autour de la pose nominale)
        target_angles = self.nominal_pose + action * 0.2
        
        # 2. Appliquer le contrôle PD sur les moteurs des jambes dans MuJoCo
        for i in range(self.num_leg_motors):
            current_pos = self.data.qpos[7 + i]
            current_vel = self.data.qvel[6 + i]
            # Calcul du couple
            self.data.ctrl[i] = self.kp * (target_angles[i] - current_pos) - self.kd * current_vel
            
        # Relâcher le reste du corps (index 12 à 28)
        for i in range(self.num_leg_motors, self.model.nu):
            self.data.ctrl[i] = 0.0

        # 3. Avancer d'un pas de simulation physique
        mujoco.mj_step(self.model, self.data)
        
        # 4. Calcul de la fonction de récompense (Reward Shaping)
        torso_height = self.data.qpos[2]
        upward_orientation = self.data.xmat[self.model.body("torso_link").id][8] # Orientation Z du torse
        
        # Bonus de verticalité
        reward = 1.0 * upward_orientation
        # Pénalité d'efforts moteurs excessive (régularisation)
        reward -= 0.001 * np.sum(np.square(self.data.ctrl))
        
        # 5. Conditions d'arrêt (Si le robot s'effondre)
        terminated = False
        if torso_height < 0.5 or upward_orientation < 0.7:
            terminated = True
            reward -= 10.0  # Grosse pénalité de chute
            
        truncated = False # Limite de temps gérée par SB3 (max_episode_steps)
        
        return self._get_obs(), reward, terminated, truncated, {}

# --- SCRIPT PRINCIPAL D'ENTRAÎNEMENT ---
if __name__ == "__main__":
    # Création de l'environnement
    env = G1StandEnv()
    
    # Vérification de la conformité de l'environnement avec les standards Gym
    print("[INFO] Vérification de l'environnement...")
    check_env(env)
    
    # Configuration des hyperparamètres PPO de départ (alignés sur ton document de cadrage)
    model = PPO(
        "MlpPolicy", 
        env, 
        learning_rate=3e-4,     # lr standard robuste pour la locomotion [cite: 254, 257]
        gamma=0.99,             # Facteur d'atténuation [cite: 254, 257]
        gae_lambda=0.95,        # Paramètre GAE pour réduire la variance [cite: 254, 257]
        clip_range=0.2,         # Évite les mises à jour trop brutales de la politique [cite: 254, 257]
        verbose=1,
        tensorboard_log="./ppo_g1_tensorboard/"
    )
    
    # Lancement de l'apprentissage sur 500 000 pas de simulation
    print("[INFO] Début de l'entraînement PPO. Laisse tourner...")
    model.learn(total_timesteps=500000)
    
    # Sauvegarde du modèle entraîné
    model.save("ppo_g1_stand_model")
    print("[INFO] Entraînement terminé et modèle sauvegardé !")