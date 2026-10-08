import datetime as dt
import unittest
from hunter import analyze, pub_date, contains

TODAY = dt.date(2026, 10, 8)

class ClassificationTests(unittest.TestCase):
    def item(self, title, date='Wed, 07 Oct 2026 08:00:00 GMT'):
        return {'title': title, 'published': date, 'url': 'https://news.google.com/rss/articles/example', 'source': 'Example'}

    def test_current_target_job_is_priority_but_not_verified(self):
        row = analyze(self.item('東京 AI エンジニア インターン 募集'), TODAY, 30)
        self.assertEqual(row['review_status'], '优先人工核实')
        self.assertEqual(row['application_url'], '')
        self.assertIn('未找到', row['application_status'])

    def test_old_article_is_not_priority(self):
        row = analyze(self.item('東京 コンサル インターン 募集', 'Tue, 22 Dec 2020 14:18:37 GMT'), TODAY, 30)
        self.assertEqual(row['review_status'], '历史线索')

    def test_press_release_not_priority(self):
        row = analyze(self.item('東京 AI インターン 募集に関する調査結果発表'), TODAY, 30)
        self.assertEqual(row['review_status'], '新闻或非岗位')

    def test_unknown_location_not_guessed(self):
        row = analyze(self.item('IT エンジニア インターン 募集'), TODAY, 30)
        self.assertEqual(row['region'], '未确定')
        self.assertEqual(row['review_status'], '待人工核实')

    def test_missing_date_not_recent(self):
        row = analyze(self.item('横浜 商社 インターン 募集', ''), TODAY, 30)
        self.assertEqual(row['freshness'], '日期未知')
        self.assertNotEqual(row['review_status'], '优先人工核实')

    def test_paid_doesnt_trigger_ai(self):
        self.assertFalse(contains('paid internship', 'ai'))

    def test_pub_date(self):
        self.assertEqual(pub_date('Tue, 22 Dec 2020 14:18:37 GMT'), dt.date(2020, 12, 22))

if __name__ == '__main__':
    unittest.main()
