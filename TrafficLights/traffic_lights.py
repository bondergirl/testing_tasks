import random
import time
from threading import Thread
from celery import Celery

# Инициализация Celery
app = Celery('traffic_optimization', broker='redis://localhost:6379/0')


# Класс светофора
class TrafficLight:
    def __init__(self, traffic_light_id, direction, light_states):
        self.id = traffic_light_id
        self.direction = direction
        self.light_states = light_states
        self.current_state_index = 0
        self.timer = None

    def change_state(self):
        self.current_state_index = (self.current_state_index + 1) % len(self.light_states)
        print(
            f"Traffic light {self.id} for {self.direction} changed to {self.light_states[self.current_state_index]}")

    def start_timer(self, duration):
        self.timer = Timer(duration, self.change_state)
        self.timer.start()

    def cancel_timer(self):
        if self.timer:
            self.timer.cancel()


# Класс таймера
class Timer:
    def __init__(self, duration, callback):
        self.duration = duration
        self.callback = callback
        self.thread = None

    def start(self):
        self.thread = Thread(target=self._run)
        self.thread.start()

    def _run(self):
        time.sleep(self.duration)
        self.callback()


# Функция симуляции оценки трафика
def evaluate_traffic():
    car_queues = {id: random.randint(0, 10) for _ in range(1, 5)}
    pedestrian_queues = {id: random.randint(0, 5) for _ in range(5, 13)}
    return car_queues, pedestrian_queues


# Задача Celery для обработки событий между светофорами
@app.task
def handle_traffic_events(sender_id, receiver_id, event_data):
    print(f"Received event from traffic light {sender_id} to {receiver_id}: {event_data}")
    # Здесь можно реализовать логику обработки событий, например, обновление состояния светофора


# Задача Celery для оптимизации трафика
@app.task
def optimize_traffic():
    car_queues, pedestrian_queues = evaluate_traffic()

    # Определение состояний светофоров
    car_light_states = ['red', 'yellow', 'green']
    pedestrian_light_states = ['red', 'green']

    # Оптимизация светофоров для автомобильного движения
    for car_id, queue_length in car_queues.items():
        light_state_duration = queue_length * 2
        traffic_light = TrafficLight(car_id, 'right-forward', car_light_states)
        traffic_light.start_timer(light_state_duration)

    # Оптимизация светофоров для пешеходного движения
    for pedestrian_id, queue_length in pedestrian_queues.items():
        light_state_duration = 10 if queue_length > 3 else 5
        traffic_light = TrafficLight(pedestrian_id, 'forward', pedestrian_light_states)
        traffic_light.start_timer(light_state_duration)

        # Отправка событий между светофорами
        for car_light_id in range(1, 5):
            handle_traffic_events.delay(car_light_id, id, {'car_queue_length': car_queues[car_light_id],
                                                           'pedestrian_queue_length': queue_length})


# Запуск оптимизации трафика через Celery
while True:
    optimize_traffic.delay()
    time.sleep(30)  # Оптимизировать трафик каждые 30 секунд
