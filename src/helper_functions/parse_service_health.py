import json


def parse_service_health(alert_json):
    alert_context = alert_json.get('data', {}).get('alertContext', {})
    
    parsed_alert = f"""
    title: {alert_context.get('properties', {}).get('title')}
    service: {alert_context.get('properties', {}).get('service')}
    region: {alert_context.get('properties', {}).get('region')}
    communication: {alert_context.get('properties', {}).get('communication')}
    """
