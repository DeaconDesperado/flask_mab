import json
import bandits

class JSONBanditStorage(object):
    def __init__(self,filepath):
        self.file_handle = open(filepath,'w')

    def save(self,bandits):
        json_bandits = json.dumps(bandits,indent=4)
        self.file_handle.write(json_bandits)

    def load(self):
        with self.file_handle as bandit_file:
            bandits = bandit_file.read()
        return json.loads(bandits)
