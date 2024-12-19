import azure.functions as func
import json
import logging
import requests
import os

app = func.FunctionApp()


def parse_service_health(alert_json):
    alert_context = alert_json.get('data', {}).get('alertContext', {})
    
    parsed_alert = f"""
title: {alert_context.get('properties', {}).get('title')}
currentHealthStatus: {alert_context.get('properties', {}).get('currentHealthStatus')}
type: {alert_context.get('properties', {}).get('type')}
cause: {alert_context.get('properties', {}).get('cause')}
    """

    return parsed_alert

def parse_resource_health(alert_json):
    alert_context = alert_json.get('data', {}).get('alertContext', {})
    
    parsed_alert = f"""
title: {alert_context.get('properties', {}).get('title')}
status: {alert_context.get('properties', {}).get('status')}
service: {alert_context.get('properties', {}).get('service')}
region: {alert_context.get('properties', {}).get('region')}
communication: {alert_context.get('properties', {}).get('communication')}
trackingId: {alert_context.get('properties', {}).get('trackingId')}
    """

    return parsed_alert

def parse_metric(alert_json):
    alert_context = alert_json.get('data', {}).get('alertContext', {})
    
    parsed_alert = f"""
title: {alert_context.get('conditionType')}
windowSize: {alert_context.get('windowSize')}

    """
    for condition in alert_context.get('conditions', []):
        parsed_alert += f"metricName: {condition.get('metricName')}\n"
        parsed_alert += f"operator: {condition.get('operator')}\n"
        parsed_alert += f"threshold: {condition.get('threshold')}\n"

    return parsed_alert

def parse_alert(req_body):
    if req_body['schemaId'] == 'azureMonitorCommonAlertSchema':
        alert = req_body.get('data', {}).get('essentials', {})
        message = ""

        if alert.get('description') != "":
            message += f"{alert.get('description')}\n\n"
        message += f"severity: {alert.get('severity')}\n"
        message += f"monitoringService: {alert.get('monitoringService')}\n\n"

        # Add specific fields based on the monitoring service
        if alert.get('monitoringService') == 'ServiceHealth':
            message += parse_service_health(req_body)

        elif alert.get('monitoringService') == 'Resource Health':
            message += parse_resource_health(req_body)

        elif alert.get('monitoringService') == 'Platform' and alert.get('Metric') == 'ServiceHealth':
            message += parse_metric(req_body)

        # finally if any CIs are present, add them to the message
        if alert.get('configurationItems'):
            message += "configurationItems:\n"
            for ci in alert.get('configurationItems', []):
                message += f"- {ci} \n"

        return alert, message

    else:
        logging.info('Schema not supported')
        return None, None

def send_pushover_notification(alert, message):
    # https://pushover.net/api#priority
    pushover_priority = {
        "Sev0": 1,
        "Sev1": 1,
        "Sev2": 0,
        "Sev3": -1,
        "Sev4": -2,
    }

    r = requests.post("https://api.pushover.net/1/messages.json", data={
        "token": os.environ['PUSHOVER_APP_TOKEN'],
        "user": os.environ['PUSHOVER_USER_KEY'],
        "title": alert.get('alertRule'),
        "message": message,
        "priority": pushover_priority.get(alert.get('severity')), 
    })
    r.raise_for_status()
    return r

@app.route(route="alert_parser", auth_level=func.AuthLevel.FUNCTION)
def alert_parser(req: func.HttpRequest) -> func.HttpResponse:# 
    logging.info('Alert Parser triggered')

    try:
        req_body = req.get_json()
        logging.info(json.dumps(req_body))
    except ValueError:
        return func.HttpResponse("Request body is not valid JSON", status_code=400)
    
    alert, message = parse_alert(req_body)
    if alert is None:
        return func.HttpResponse("Schema not supported", status_code=400)

    try:
        r = send_pushover_notification(alert, message)
        return func.HttpResponse(f"Alert sent to Pushover: {r.text}", status_code=200)
    except requests.RequestException as e:
        return func.HttpResponse(f"Failed to send alert to Pushover: {str(e)}", status_code=500)