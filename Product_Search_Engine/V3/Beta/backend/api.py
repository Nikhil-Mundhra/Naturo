from backend import config, search

class Api:
    def get_config(self):
        return config.load_config()

    def update_config(self, key, value):
        return config.update_config(key, value)

    def run_search(self, query):
        return search.execute(query)
