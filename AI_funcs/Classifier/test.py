__author__ = 'Weiliang Guo'


def get_time_hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    result = str(h) + 'h' + str(m) + 'm' + str(s) + 's'
    return result

r = get_time_hms(244)
print(r)