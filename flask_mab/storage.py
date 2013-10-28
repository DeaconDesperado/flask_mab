import json
import bandits

class BanditEncoder(json.JSONEncoder):
    def default(self,obj):
        if isinstance(obj,bandits.Bandit):
            dict_repr = obj.__dict__
            dict_repr['bandit_type'] = obj.__class__.__name__
            return dict_repr
        return json.JSONEncoder.default(self,obj)

class BanditDecoder(json.JSONDecoder):
    def decode(self,obj):
        dict_repr = json.loads(obj)
        for key in dict_repr.keys():
            if 'bandit_type' not in dict_repr[key].keys():
                raise TypeError("Serialized object is not a valid bandit")
            dict_repr[key] = bandits.Bandit.fromdict(dict_repr[key])
        return dict_repr

class JSONBanditStorage(object):
    def __init__(self,filepath):
        self.file_handle = filepath

    def flush(self):
        open(self.file_handle,'w').truncate()

    def save(self,bandits):
        json_bandits = json.dumps(bandits,indent=4,cls=BanditEncoder)
        open(self.file_handle,'w').write(json_bandits)

    def load(self):
        try:
            with open(self.file_handle,'r') as bandit_file:
                bandits = bandit_file.read()

            return json.loads(bandits,cls=BanditDecoder)
        except (ValueError,IOError):
            return {}
