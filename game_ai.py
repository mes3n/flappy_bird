
def jump(player_y, tube_y, ground_level):
    buffer = 13
    if player_y <= tube_y + buffer:
        return True
    if player_y <= ground_level + buffer:
        return True
    return False
