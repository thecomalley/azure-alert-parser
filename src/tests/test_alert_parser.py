import unittest
import azure.functions as func
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from function_app import alert_parser, parse_alert, send_pushover_notification


class TestAlertParser(unittest.TestCase):
    def load_payload(self, filename):
        with open(os.path.join('tests/payloads', filename), 'r') as file:
            return json.load(file)

    def invoke_function(self, filename):
        req_body = self.load_payload(filename)
        req = func.HttpRequest(
            method='POST',
            url='/api/alert_parser',
            body=json.dumps(req_body).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        resp = alert_parser(req)
        self.assertEqual(resp.status_code, 200)

    def test_activity_log_alert_rule(self):
        self.invoke_function('test-activityLogAlertRule.json')

    def test_budget_forecasted(self):
        self.invoke_function('test-budget-forecasted.json')

    def test_cost_budget_actual(self):
        self.invoke_function('test-cost-budget-actual.json')

    def test_dynamicMetricAlertRule(self):
        self.invoke_function('test-dynamicMetricAlertRule.json')

    def test_logAlertRule_v1_metricMeasurement(self):
        self.invoke_function('test-logAlertRule-v1-metricMeasurement.json')
    
    def test_logAlertRule_v1_numResults(self):
        self.invoke_function('test-logAlertRule-v1-numResults.json')
        
    def test_metricAlertRule(self):
        self.invoke_function('test-metricAlertRule.json')
        
    def test_ResourceHealthAlertRule(self):
        self.invoke_function('test-ResourceHealthAlertRule.json')
        
    def test_ServiceHealthAlertRule(self):
        self.invoke_function('test-ServiceHealthAlertRule.json')
        
    def test_SmartAlertRule(self):
        self.invoke_function('test-SmartAlertRule.json')

if __name__ == '__main__':
    unittest.main()