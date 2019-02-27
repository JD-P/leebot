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
        self.assertEqual(None, bot.check_feed(fake_feed,
                                              {"testfeed":"1"},
                                              bot.git_alert)[0])

    def test_message_if_different_head(self):
        self.assertTrue(bot.check_feed(fake_feed,
                                           {"testfeed":"2"},
                                           bot.git_alert))

    def test_updates_feed_heads_on_new(self):
        """Test that the callback updates the feed_heads dictionary on new entry."""
        self.assertEqual({"testfeed":"1"},
                         bot.check_feed(fake_feed,
                                            {"testfeed":"2"},
                                            bot.git_alert)[1])

class TestFeedValidation(unittest.TestCase):
    def test_returns_arguments_for_proper_command(self):
        self.assertEqual(("blog_feeds", "https://jdpressman.com"),
                         bot.validate_feed_add("/addfeed blog_feeds https://jdpressman.com"))
    
    def test_fails_on_improper_feed_type(self):
        self.assertRaises(ValueError, bot.validate_feed_add, "/addfeed admin https://jdpressman.com")

    def test_fails_on_improper_url(self):
        self.assertRaises(ValueError, bot.validate_feed_add, "/addfeed blog_feeds my-wrong-url")
        #self.assertRaises(ValueError, bot.validate_feed_add, "/addfeed blog_feeds htt://jdpressman.com")
        #self.assertRaises(ValueError, bot.validate_feed_add, "/addfeed blog_feeds https://jdpressman") 
    
        
if __name__ == '__main__':
    unittest.main()
