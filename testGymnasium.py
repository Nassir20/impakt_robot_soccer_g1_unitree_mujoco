import gymnasium as gym
render_mode = "human"


env = gym.make('CartPole-v1', render_mode=render_mode)
observation, info = env.reset()

print(f"initial observation: {observation}")

episode_over = False
total_reward = 0
while not episode_over:
    action = env.action_space.sample()  # Take a random action
    observation, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    episode_over = terminated or truncated
print(f"Episode finished with total reward: {total_reward}")
env.close()