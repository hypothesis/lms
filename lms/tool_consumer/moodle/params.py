class MoodleParams:
    @classmethod
    def extract_dict(cls, schema, kwargs):
        return cls.dict(schema().load(kwargs))

    @classmethod
    def dict(cls, options):
        moodle_format = []

        for key, value in options.items():
            if value is None:
                continue

            moodle_format.append({"name": key, "value": value})

        return moodle_format

    @classmethod
    def flatten(cls, data):
        flat = {}
        for path, value in cls._visit(data):
            head = path[0]
            tail = path[1:]

            key = head + "".join(f"[{item}]" for item in tail)

            flat[key] = value

        return flat

    @classmethod
    def _visit(cls, data, path=None):
        if path is None:
            path = []

        if isinstance(data, dict):
            for key, value in data.items():
                yield from cls._visit(value, path + [key])

            return
        elif isinstance(data, list):
            for pos, value in enumerate(data):
                yield from cls._visit(value, path + [pos])

            return

        yield path, data
