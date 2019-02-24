import unittest
import bot

fake_feed = {"feed":
             {"id":"testfeed",
              "title":"Fake Feed to leebot"},
             "entries":[
                 {"id":"1",
                  "title":"Fake Entry",
                  "author":"jd",
                  "link":"https://duckduckgo.com"}]}

class TestRSSHandling(unittest.TestCase):
    """Test the functions associated with the RSS tracking in leebot."""
    
    def test_no_repeat_if_same_head(self):
        self.assertEqual(None, bot.check_git_feed(fake_feed, {"testfeed":"1"})[0])

    def test_message_if_different_head(self):
        self.assertTrue(bot.check_git_feed(fake_feed, {"testfeed":"2"}))

    def test_updates_feed_heads_on_new(self):
        """Test that the callback updates the feed_heads dictionary on new entry."""
        self.assertEqual({"testfeed":"1"}, bot.check_git_feed(fake_feed, {"testfeed":"2"})[1])
        
if __name__ == '__main__':
    unittest.main()
