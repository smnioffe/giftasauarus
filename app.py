from flask import Flask, render_template, request, session
from redis import Redis
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
redis = Redis(host='localhost', port=6379)

GIFT_ATTRIBUTES = [
    {1: "Books", 2: "Electronics", 3: "Clothing", 4: "Home & Kitchen"},
    {1: "Under $25", 2: "$25 - $50", 3: "Above $50", 4: "Above $100"},
    {1: "Children", 2: "Teenagers", 3: "Adults", 4: "Elders"}
]

def set_step(session_id, step):
    redis.set(f"step:{session_id}", step)

def get_step(session_id):
    return int(redis.get(f"step:{session_id}"))

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


@app.route('/recommendations')
def recommendations():
    session_id = session['session_id']
    choices = redis.hgetall(f"choices:{session_id}")
    choices = {key.decode(): int(value.decode()) for key, value in choices.items()}
    recommended_gifts = choices

    return {'recommendedGifts': recommended_gifts}

if __name__ == '__main__':
    app.run(debug=True)
