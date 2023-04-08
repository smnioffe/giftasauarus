from flask import Flask, render_template, request, session
from redis import Redis
import os, json

app = Flask(__name__)
app.secret_key = os.urandom(24)
redis = Redis(host='localhost', port=6379)

GIFT_ATTRIBUTES = [
    {1: "Significant Other", 2: "Family", 3: "Friend", 4: "Myself"},
    {1: "Travel", 2: "Working Out", 3: "Watching TV/Movies", 4: "Spa"},
    {1: "$", 2: "$$", 3: "$$$", 4: "No preference"}
]

def set_step(session_id, step):
    redis.set(f"step:{session_id}", step)

def get_step(session_id):
    return int(redis.get(f"step:{session_id}"))

@app.before_first_request
def load_gift_data():
    # Load the gift data from the CSV file
    with open('gifts.csv') as f:
        gift_data = [line.strip().split(',') for line in f]

    # Convert the age and price fields to integers
    gift_data = [[name, int(age), int(price), category] for name, age, price, category in gift_data[1:]]

    # Store the gift data in Redis
    for i, gift in enumerate(gift_data):
        gift_dict = {'name': gift[0], 'age': gift[1], 'price': gift[2], 'category': gift[3]}
        redis.hset('gifts', i, json.dumps(gift_dict))

@app.route('/')
def index():
    session['session_id'] = os.urandom(16).hex()
    set_step(session['session_id'], 0)
    step = get_step(session['session_id'])

    attributes = GIFT_ATTRIBUTES[step] if step < len(GIFT_ATTRIBUTES) else []

    return render_template('index.html', step=step, attributes=attributes, gift_attributes=GIFT_ATTRIBUTES)

@app.route('/flip-tiles', methods=['POST'])
def flip_tiles():
    data = request.get_json()
    current_values = data['currentValues']
    clicked_number = data['clickedNumber']
    session_id = session['session_id']

    step = get_step(session_id)
    is_last_attribute = (step + 1) == len(GIFT_ATTRIBUTES)

    new_values = {}  # Initialize new_values here

    if not is_last_attribute:
        redis.hset(f"choices:{session_id}", f"step{step}", clicked_number)
        step += 1
        set_step(session_id, step)

        for key, _ in current_values.items():
            index = int(key[-1])
            new_values[key] = GIFT_ATTRIBUTES[step % len(GIFT_ATTRIBUTES)][index]
            redis.hset(f"tiles:{session_id}", key, GIFT_ATTRIBUTES[step % len(GIFT_ATTRIBUTES)][index])
    else:
        new_values = current_values

    return {'newValues': new_values if not is_last_attribute else {}, 'clicked_numbers': clicked_number, 'step': step, 'is_last_attribute': is_last_attribute}


# @app.route('/recommendations')
# def recommendations():
#     session_id = session['session_id']
#     choices = redis.hgetall(f"choices:{session_id}")
#     choices = {key.decode(): int(value.decode()) for key, value in choices.items()}
#     recommended_gifts = choices

#     return {'recommendedGifts': recommended_gifts}
@app.route('/recommendations')
def recommendations():
    session_id = session['session_id']
    choices = redis.hgetall(f"choices:{session_id}")
    choices = {key.decode(): int(value.decode()) for key, value in choices.items()}
    print(choices)

    # Fetch the gift data from Redis
    gift_data = []
    for i in range(redis.hlen('gifts')):
        gift_dict = json.loads(redis.hget('gifts', i))
        gift_data.append([gift_dict['name'], gift_dict['age'], gift_dict['price'], gift_dict['category']])

    # Filter the gift data based on the selected attributes
    for step, attribute in choices.items():
        attribute_index = int(step[-1]) - 1
        gift_data = [gift for gift in gift_data if gift[attribute_index] == attribute]

    # Sort the remaining gift data by price in ascending order
    gift_data.sort(key=lambda x: x[2])

    # Get the top 3 recommended products
    recommended_gifts = [gift[0] for gift in gift_data[:3]]

    # Store the recommended products in Redis
    redis.hset(f"recommendations:{session_id}", "products", json.dumps(recommended_gifts))

    return {'recommendedGifts': recommended_gifts}


if __name__ == '__main__':
    app.run(debug=True)
