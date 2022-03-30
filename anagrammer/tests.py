import unittest
import json
from anagrammer import app  # pylint: disable=cyclic-import


class TestLadderSearch(unittest.TestCase):
    def test_working(self):
        with app.test_client() as test_client:
            response = test_client.post(
                "/ladders/search/",
                json={"length": [4], "difficulty": [1, 2], "ladder_filter": "hi"},
            )
            parsed_data = {
                d["pair"]: d for d in json.loads(response.data).get("ladders", [])
            }
            self.assertTrue(parsed_data.get("born-this")["difficulty"] == 17448)

    def test_page_size(self):
        with app.test_client() as test_client:
            response = test_client.post(
                "/ladders/search/",
                json={"length": [3], "difficulty": [1, 2], "page_size": 23},
            )
            parsed_data = {
                d["pair"]: d for d in json.loads(response.data).get("ladders", [])
            }
            self.assertTrue(len(parsed_data.keys()) == 23)


if __name__ == "__main__":
    unittest.main()
