import random

def random_delay(min_ms: int = 1000, max_ms: int = 3000) -> int:
    '''대기 시간 랜덤 생성성'''
    return random.randint(min_ms, max_ms)
