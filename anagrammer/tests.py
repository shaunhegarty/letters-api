import unittest
import json
from anagrammer import app  # pylint: disable=cyclic-import


class TestLadderSearch(unittest.TestCase):
    def test_working(self):
        with app.test_client() as test_client:
            response = test_client.post(
                "/ladders/search/",
                json={"length": 4, "difficulty": 2, "ladder_filter": "hi"},
            )
            self.assertTrue(
                json.loads(response.data).get("ladders")[0].get("pair") == "born-this"
            )


if __name__ == "__main__":
    unittest.main()
