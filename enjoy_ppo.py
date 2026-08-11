import time
import sys
from stable_baselines3 import PPO
from g1_ppo_env import G1StandEnv

def main():
    print("[TEST] Chargement de l'environnement G1 Stand personnalisé...")
    env = G1StandEnv()
    
    print("[TEST] Chargement du fichier de neurones ppo_g1_stand_model.zip...")
    try:
        # On force le chargement du modèle sur l'environnement actuel
        model = PPO.load("ppo_g1_stand_model", env=env)
    except Exception as e:
        print(f"[ERREUR] Impossible de charger le modèle : {e}")
        sys.exit(1)
        
    print("[SUCCESS] Le modèle est bien lié à l'environnement.")
    print("[TEST] Lancement du test visuel autonome...")

    obs, info = env.reset()
    
    while True:
        # L'IA prédit l'action en mode déterministe strict
        action, _states = model.predict(obs, deterministic=True)
        
        # On applique l'action dans notre environnement personnalisé
        obs, reward, terminated, truncated, info = env.step(action)
        
        # On appelle le rafraîchissement visuel de MuJoCo
        env.render()
        
        # Si le robot tombe (Z < 0.52m ou trop incliné), l'environnement fait un reset automatique
        if terminated or truncated:
            print("[INFO] Le robot a perdu l'équilibre ou est sorti des limites. Reset de la posture...")
            obs, info = env.reset()
            
        # Petit délai calé sur le pas de simulation pour une observation fluide
        time.sleep(0.005)

if __name__ == "__main__":
    main()