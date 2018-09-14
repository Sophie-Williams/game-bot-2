# Overlord of Kazan

This is a telegram bot, aimed to mimic a popular King of Tokyo board game. Currently under development.

### Requirements
* Python    3.6+
* Docker    17.12.0+

### Deploying Local Version

1. Install Python dependencies: `pip install -r requirements.txt`
1. Create all required docker containers: `docker-compose up -d`
1. Change `TOKEN` in the `config.env`
1. Run the updater: `python updater.py`

To clean docker environment, run `docker-compose down`. This will delete all created containers. 