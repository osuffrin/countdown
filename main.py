import time, random
from tqdm import tqdm
from countdown import Countdown as countdown


recipients = ((1971, 6, 28, "elonmusk", 3), (1976, 11, 19, 'jack', 1))


while True:
    for i in recipients:
        countdown(*i).count()

    print('\n')

    for i in tqdm(range(24), desc="progress", colour="WHITE"):
        time.sleep((7200 / 24) + random.random())
