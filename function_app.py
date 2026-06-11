import azure.functions as func
import datetime
import requests
from azure.identity import DefaultAzureCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="costs")
def get_costs(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Get Azure access token from managed identity / local login
        credential = DefaultAzureCredential()
        token = credential.get_token("https://management.azure.com/.default").token

        # Replace with your subscription ID
        subscription_id = "71e85381-5707-48bd-9e75-199a87e9705e"

        today = datetime.date.today()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()

        url = (
            f"https://management.azure.com/subscriptions/"
            f"{subscription_id}/providers/Microsoft.CostManagement/query"
            f"?api-version=2023-03-01"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        body = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {
                "from": start,
                "to": end
            },
            "dataset": {
                "granularity": "Daily",
                "aggregation": {
                    "totalCost": {
                        "name": "PreTaxCost",
                        "function": "Sum"
                    }
                }
            }
        }

        response = requests.post(url, headers=headers, json=body)
        data = response.json()

        rows = data.get("properties", {}).get("rows", [])

        result = [
            {"date": r[0], "cost": r[1]}
            for r in rows
        ]

        return func.HttpResponse(
            str(result),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            f"Error fetching costs: {str(e)}",
            status_code=500
        )