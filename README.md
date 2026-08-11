Compte-Rendu de Projet : Contrôleur RL & Déterministe pour l'Humanoïde Unitree G1 dans MuJoCo

Avant-propos
Ce projet s'inscrit dans le cadre du développement de contrôleurs intelligents pour la robotique humanoïde de nouvelle génération. Axé sur le robot Unitree G1, un humanoïde compact à 29 degrés de liberté, ce travail explore la convergence entre la simulation physique haute fidélité sous MuJoCo et les algorithmes d'apprentissage par renforcement (Reinforcement Learning).

Contexte et Motivation
Le contrôle des robots humanoïdes présente des défis scientifiques majeurs en raison de la dynamique non linéaire, du maintien de l'équilibre dynamique et de la gestion de la sous-actionnalisation. L'objectif principal de cette étude est de concevoir un contrôleur capable d'assurer la stabilité posturale et la locomotion du robot G1.

Pour y parvenir, deux approches complémentaires ont été développées et analysées :

L'Apprentissage par Renforcement (RL) : Utilisation de l'algorithme Proximal Policy Optimization (PPO) combiné à un travail d'ingénierie de récompense (Reward Shaping) pour permettre au robot d'apprendre de manière autonome à se maintenir debout et à réagir aux perturbations.

Le Contrôle Déterministe Bas Niveau (DDS) : Génération de trajectoires analytiques et cinématiques (marche sinusoïdale, séquences de tir, équilibrage statique) pour tester la réponse physique des actionneurs sous le middleware Unitree SDK2 à haute fréquence (200 Hz).

<img width="416" height="463" alt="image" src="https://github.com/user-attachments/assets/8b7de072-f61d-4b28-ab13-86e8460a1a91" />


# Unitree G1 Humanoid - PPO Reinforcement Learning & Control (MuJoCo)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![MuJoCo](https://img.shields.io/badge/Physics-MuJoCo-orange.svg)
![RL](https://img.shields.io/badge/Algorithm-PPO%20%28Stable--Baselines3%20%2F%20Gymnasium%29-green.svg)

Ce dépôt contient le contrôleur complet d'apprentissage par renforcement (**PPO**) et les générateurs de mouvement déterministes bas niveau pour le robot humanoïde **Unitree G1** (29 degrés de liberté) sous la plateforme de simulation **MuJoCo**.

---

## 📁 Architecture du Projet

```text
simulate_python/
├── g1_ppo_env.py             # Environnement Gymnasium (MuJoCo, observations 71D, reward shaping)
├── g1_train_ppo.py           # Script principal d'entraînement PPO (Stable-Baselines3)
├── enjoy_ppo.py              # Script d'évaluation visuelle et de rendu 3D
├── g1_walk_controller.py     # Contrôleur DDS de marche sinusoïdale déterministe (200 Hz)
├── g1_kick_controller.py     # Contrôleur DDS de coup de pied chronométré
├── g1_controller3.py         # Contrôleur DDS de stabilisation géométrique fixe
├── ppo_g1_stand_model.zip    # Poids du réseau de neurones PPO entraîné
└── ppo_g1_tensorboard/       # Logs d'apprentissage TensorBoard

## ⚙️ Configuration & Installation

### 1. Prérequis

- Python 3.10+
- Un environnement virtuel (recommandé)

### 2. Installation des dépendances

Activer l'environnement virtuel et installer les bibliothèques requises :

```bash
# Activation de l'environnement virtuel (.venv)
source .venv/bin/activate

# Installation des packages
pip install mujoco gymnasium stable-baselines3 tensorboard unitree_sdk2py
```

---

## 🚀 Utilisation

### 1. Lancer l'entraînement PPO (`g1_train_ppo.py`)

Le script initialise l'environnement `G1StandEnv` et exécute l'apprentissage PPO sur 100 000+ pas de temps.

```bash
python g1_train_ppo.py
```

Pour suivre les courbes d'apprentissage en temps réel via TensorBoard :

```bash
tensorboard --logdir=./ppo_g1_tensorboard/
```

### 2. Tester et visualiser la politique entraînée (`enjoy_ppo.py`)

Charge le modèle sauvegardé `ppo_g1_stand_model.zip` et ouvre l'interface graphique interactive de MuJoCo pour observer la stabilisation du G1.

```bash
mjpython enjoy_ppo.py
```

### 3. Exécuter les contrôleurs déterministes (Low-Level DDS)

Vous pouvez également tester les générateurs de mouvements analytiques bas niveau à 200 Hz :

```bash
# Générateur de marche sinusoïdale
python g1_walk_controller.py

# Séquence de coup de pied (Kick)
python g1_kick_controller.py
```

---

## 🧠 Modèle Mathématique & Reward Shaping (`g1_ppo_env.py`)

**Espace d'observation (O) — 71 dimensions**
Positions physiques (`qpos`), vitesses angulaires (`qvel`) et orientation spatiale de la base.

**Espace d'action (A) — 12 dimensions**
Consignes de couple/position pour les 12 moteurs des jambes.

**Fonction de récompense**

```
R = R_hauteur + P_chute + P_inclinaison + P_effort
```

| Terme | Description |
|---|---|
| `R_hauteur` | Maximise le maintien du tronc à la hauteur nominale (z ≈ 0.74 m) |
| `P_chute` | Pénalité si le robot perd de l'altitude |
| `P_inclinaison` | Pénalité sur les déviations en roulis/tangage pour garder le buste droit |
| `P_effort` | Pénalité d'énergie sur la somme des carrés des actions, pour lisser le contrôle |
