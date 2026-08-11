import time
from stable_baselines3 import PPO
from g1_ppo_env import G1StandEnv

def main():
    print("[TRAINING] Création de l'environnement G1...")
    env = G1StandEnv()

    # Initialisation de l'IA PPO
    # MlpPolicy signifie qu'on utilise un réseau de neurones classique (Multi-Layer Perceptron)
    print("[TRAINING] Configuration de l'algorithme PPO...")
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1, 
        learning_rate=3e-4, 
        tensorboard_log="./ppo_g1_tensorboard/"
    )

    # Lancer l'apprentissage sur 100 000 pas de temps
    # Au début, le robot va s'effondrer en boucle. C'est normal, il teste des choses au hasard.
    # Au fur et à mesure que les points de récompense s'accumulent, il va ajuster ses muscles.
    print("[TRAINING] Début de l'entraînement de l'IA (100k steps)...")
    
    # Si tu veux voir le robot pendant qu'il apprend (attention cela ralentit un peu l'entraînement) :
    # Décommente la ligne dans une boucle personnalisée, ou laisse SB3 s'entraîner en tâche de fond.
    model.learn(total_timesteps=500000)

    # Sauvegarder le cerveau de l'IA une fois entraîné
    model.save("ppo_g1_stand_model")
    print("[SUCCESS] L'IA a fini son entraînement ! Modèle sauvegardé sous 'ppo_g1_stand_model.zip'")

if __name__ == "__main__":
    main()