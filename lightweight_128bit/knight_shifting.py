def knight_shifting(state):
    bytes_ = [(state >> (8 * i)) & 0xFF for i in range(16)]
    map_ = [9, 7, 4, 10, 2, 12, 15, 1, 14, 0, 3, 13, 5, 11, 8, 6]
    new_state = [bytes_[i] for i in map_]
    return sum(new_state[i] << (8 * (15 - i)) for i in range(16))