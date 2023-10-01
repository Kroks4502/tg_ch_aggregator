import json


class DBJsonFieldEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, DBJsonField):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

    @staticmethod
    def json_dumper(obj):
        return json.dumps(obj, cls=DBJsonFieldEncoder)


class DBJsonField:
    pass
