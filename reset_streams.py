import _pickle

with open('streamers.pkl', 'rb') as file_handle:
    STREAMERS = _pickle.load(file_handle)

for streamer in STREAMERS.keys():
    STREAMERS[streamer]['message_id'] = None
    STREAMERS[streamer]['live_status'] = False

with open('streamers.pkl', 'wb') as file_handle:
    _pickle.dump(STREAMERS, file_handle)