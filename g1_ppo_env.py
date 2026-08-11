import gymnasium as gym
from gymnasium import spaces
import numpy as np
import mujoco

class G1StandEnv(gym.Env):
    """
    Environnement Gymnasium complet et calibré pour le Unitree G1.
    Objectif : Apprendre au robot à rester debout de manière stable avec PPO.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self):
        super(G1StandEnv, self).__init__()

        # 1. Chargement du modèle XML officiel du G1
        # (Vérifie bien que le chemin vers ton dossier scene.xml est correct)
        self.mj_model = mujoco.MjModel.from_xml_path("../unitree_robots/g1/scene.xml")
        self.mj_data = mujoco.MjData(self.mj_model)

        # 2. Espace d'Action : Couples cibles pour les 12 moteurs des jambes
        # Bornés entre -15 et +15 N.m pour laisser assez de force au robot pour porter ses 35 kg
        self.action_space = spaces.Box(low=-15.0, high=15.0, shape=(12,), dtype=np.float32)

        # 3. Espace d'Observation : 29 positions (qpos) + 28 vitesses (qvel) = 57 éléments
        # Cela donne à l'IA une vue mathématique complète de l'état du robot
       # Remplace la ligne de ton constructeur par celle-ci :
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(71,), dtype=np.float32)
        
        self.viewer = None

    def _get_obs(self):
        """Récupère les données physiques de MuJoCo pour les envoyer au réseau de neurones"""
        positions = np.array(self.mj_data.qpos, dtype=np.float32) # Taille 29 (Base + Articulations)
        vitesses = np.array(self.mj_data.qvel, dtype=np.float32)  # Taille 28 (Vitesses linéaires, angulaires et moteurs)
        
        return np.concatenate([positions, vitesses])

    def step(self, action):
        # 1. Application des couples de l'IA sur les actionneurs des jambes (index 0 à 11 dans MuJoCo)
        for i in range(12):
            self.mj_data.ctrl[i] = action[i]

        # 2. Avancement de la simulation physique d'un pas de calcul
        mujoco.mj_step(self.mj_model, self.mj_data)

        # 3. Capture du nouvel état
        obs = self._get_obs()

        # ====================================================================
        # RECOMPENSE OPTIMISÉE (Reward Shaping) POUR ÉVITER LES CHUTES
        # ====================================================================
        torso_z = self.mj_data.qpos[2]  # Hauteur réelle du torse
        v_z = self.mj_data.qvel[2]      # Vitesse verticale du torse
        
        # R1 : Plus le robot est proche de sa hauteur debout parfaite (0.74m), plus il gagne de points
        reward_height = 10.0 * (1.0 - abs(0.74 - torso_z) / 0.74)
        
        # R2 : Énorme pénalité si le robot est en train de s'affaisser (v_z négatif)
        penalty_falling = -8.0 * max(0.0, -v_z)
        
        # R3 : Pénalité d'inclinaison. Si les quaternions X (qpos[4]) ou Y (qpos[5]) bougent, 
        # c'est que le robot bascule en avant ou sur le côté. On le pénalise lourdement.
        penalty_tilt = -10.0 * (self.mj_data.qpos[4]**2 + self.mj_data.qpos[5]**2)
        
        # R4 : Pénalité d'effort (ctrl_cost) pour éviter les tremblements et économiser les moteurs
        penalty_ctrl = -0.01 * np.sum(np.square(action))

        # Somme totale des objectifs
        reward = reward_height + penalty_falling + penalty_tilt + penalty_ctrl

        # ====================================================================
        # CONDITIONS D'ARRÊT DE L'ÉPISODE (Échec)
        # ====================================================================
        # Si le torse descend sous 0.52m (robot complètement écrasé ou à genoux)
        # ou s'il bascule trop (quaternions > 0.4), on coupe l'épisode immédiatement.
        is_too_low = bool(torso_z < 0.52)
        is_tilted_too_much = bool(abs(self.mj_data.qpos[4]) > 0.4 or abs(self.mj_data.qpos[5]) > 0.4)
        
        terminated = bool(is_too_low or is_tilted_too_much)
        truncated = False

        info = {}
        
        # Optionnel : Décommente la ligne ci-dessous si tu veux forcer le rendu visuel automatique
        # self.render()

        return obs, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Réinitialisation propre de la mémoire physique de MuJoCo
        mujoco.mj_resetData(self.mj_model, self.mj_data)
        
        # Initialisation de la position spatiale (Debout au centre)
        self.mj_data.qpos[0] = 0.0  # X
        self.mj_data.qpos[1] = 0.0  # Y
        self.mj_data.qpos[2] = 0.74 # Z (Hauteur nominale d'origine)
        
        # Orientation d'origine parfaitement verticale (Quaternion neutre)
        self.mj_data.qpos[3] = 1.0  # W
        self.mj_data.qpos[4] = 0.0  # X
        self.mj_data.qpos[5] = 0.0  # Y
        self.mj_data.qpos[6] = 0.0  # Z
        
        # Génération d'un tout petit bruit aléatoire initial sur les moteurs des jambes
        # pour obliger l'IA à apprendre à se rattraper en cas de micro-déséquilibre
        bruit_moteurs = np.random.uniform(-0.02, 0.02, size=(12,))
        for i in range(12):
            self.mj_data.qpos[7 + i] = bruit_moteurs[i]

        obs = self._get_obs()
        info = {}
        return obs, info

    def render(self):
        """Ouvre et synchronise la fenêtre graphique MuJoCo"""
        if self.viewer is None:
            import mujoco.viewer
            self.viewer = mujoco.viewer.launch_passive(self.mj_model, self.mj_data)
        self.viewer.sync()

    def close(self):
        if self.viewer is not None:
            self.viewer.close()