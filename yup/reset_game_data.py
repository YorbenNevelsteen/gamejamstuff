import json

data = {
  "high_score": 0,
  "total_trash": 0,
  "sound_enabled": True,
  "owned_trash_colors": [],
  "owned_obstacle_colors": [],
  "selected_trash_color": "Standaard",
  "selected_obstacle_color": "Standaard",
  "owned_characters": ["Standaard"],
  "selected_character": "Standaard"
}

with open("patty_runner_data.json", 'w') as f:
    json.dump(data, f, indent=2)