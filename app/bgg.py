import requests
import xml.etree.ElementTree as ET
import time
from .models import db, Game, User
from sqlalchemy.exc import SQLAlchemyError
import logging

BGG_COLLECTION_URL = "https://www.boardgamegeek.com/xmlapi2/collection"
BGG_THING_URL = "https://www.boardgamegeek.com/xmlapi2/thing"
MAX_RETRIES = 5  # Number of retries for rate limiting
RETRY_DELAY = 60  # Delay between retries in seconds when 429 is encountered
BATCH_SIZE = 20  # Max number of items that can be fetched in one request

def parse_bgg_collection(xml_data):
    """Parse the game IDs from the user's collection XML."""
    root = ET.fromstring(xml_data)
    game_ids = [item.attrib['objectid'] for item in root.findall('item') if item.attrib.get('subtype') == 'boardgame']
    return game_ids

def fetch_user_games(bgg_username):
    """Fetch game IDs for a user from BGG."""
    params = {
        'username': bgg_username,
        'own': 1,
        'stats': 1,
        'type': 'boardgame'
    }
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(BGG_COLLECTION_URL, params=params)
            response.raise_for_status()
            return parse_bgg_collection(response.content)
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 429:
                retries += 1
                logging.warning(f"Rate limited while fetching games for user {bgg_username}, retrying in {RETRY_DELAY} seconds... (Attempt {retries}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                raise http_err
    raise Exception(f"Failed to fetch user games for {bgg_username} after {MAX_RETRIES} retries due to rate limiting.")

def parse_game_details(item):
    """Parse the game details from an XML item."""
    if item is None:
        raise ValueError("Invalid XML: 'item' element is None")

    name_elem = item.find("name[@type='primary']")
    if name_elem is None:
        raise ValueError("Game has no primary name element")

    name = name_elem.attrib.get('value', 'Unknown Game')
    thumbnail = item.find('thumbnail').text if item.find('thumbnail') is not None else ''
    min_players = item.find('minplayers').attrib.get('value') if item.find('minplayers') is not None else None
    max_players = item.find('maxplayers').attrib.get('value') if item.find('maxplayers') is not None else None
    playing_time = item.find('playingtime').attrib.get('value') if item.find('playingtime') is not None else None
    average_rating = item.find('statistics/rating/average')
    difficulty = average_rating.attrib.get('value') if average_rating is not None else 'N/A'
    
    return {
        'name': name,
        'thumbnail': thumbnail,
        'min_players': int(min_players) if min_players else None,
        'max_players': int(max_players) if max_players else None,
        'playing_time': int(playing_time) if playing_time else None,
        'difficulty': difficulty
    }

def fetch_game_details_batch(bgg_ids):
    """Fetch game details for a batch of BGG IDs, handling rate limits."""
    retries = 0
    params = {
        'id': ','.join(bgg_ids),  # Fetch a batch of game details by passing multiple IDs
        'stats': 1
    }
    while retries < MAX_RETRIES:
        try:
            response = requests.get(BGG_THING_URL, params=params)
            response.raise_for_status()
            return response.content
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 429:
                retries += 1
                logging.warning(f"Rate limited while fetching game details for BGG IDs: {bgg_ids}, retrying in {RETRY_DELAY} seconds... (Attempt {retries}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                raise http_err
    raise Exception(f"Failed to fetch game details for BGG IDs: {bgg_ids} after {MAX_RETRIES} retries due to rate limiting.")

def update_games_for_user(user):
    """Update games owned by a user by fetching them from BGG."""
    logging.info(f"Fetching games for user: {user.name} ({user.bgg_username})")
    
    try:
        game_ids = fetch_user_games(user.bgg_username)
        logging.info(f"Found {len(game_ids)} games for user '{user.name}'.")
    except Exception as e:
        logging.error(f"Error fetching games for user '{user.name}': {e}")
        return

    for i in range(0, len(game_ids), BATCH_SIZE):
        batch_ids = game_ids[i:i + BATCH_SIZE]
        try:
            xml_data = fetch_game_details_batch(batch_ids)
            root = ET.fromstring(xml_data)
            for item in root.findall('item'):
                bgg_id = item.attrib.get('id')
                if not bgg_id:
                    logging.warning(f"Game item in batch {batch_ids} is missing an 'id'. Skipping.")
                    continue

                game = Game.query.filter_by(bgg_id=bgg_id).first()

                if not game:
                    try:
                        details = parse_game_details(item)
                        game = Game(
                            bgg_id=bgg_id,
                            name=details['name'],
                            thumbnail=details['thumbnail'],
                            min_players=details['min_players'],
                            max_players=details['max_players'],
                            playing_time=details['playing_time'],
                            difficulty=details['difficulty']
                        )
                        db.session.add(game)
                        db.session.commit()
                        logging.info(f"Added game: {game.name} (ID: {game.bgg_id})")
                    except ValueError as ve:
                        logging.error(f"Error parsing game details for BGG ID {bgg_id}: {ve}")
                        continue  # Skip this game if there was a parsing error
                
                if game not in user.owned_games:
                    user.owned_games.append(game)
                    db.session.commit()
                    logging.info(f"Associated game '{game.name}' with user '{user.name}'")
        except Exception as e:
            logging.error(f"Error fetching game details for user '{user.name}' in batch: {batch_ids}. Error: {e}")
            continue  # Continue to the next batch in case of failure

def update_all_games(app):
    """Update games for all users."""
    with app.app_context():
        users = User.query.all()
        logging.info(f"Starting update for all users. Total users: {len(users)}")
        for user in users:
            update_games_for_user(user)
        logging.info("Completed updating games for all users.")
