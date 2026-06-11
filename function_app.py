import azure.functions as func
import datetime
import requests
import json
from azure.identity import DefaultAzureCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="costs")
def get_costs(req: func.HttpRequest) -> func.HttpResponse:
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://management.azure.com/.default").token

        subscription_id = "71e85381-5707-48bd-9e75-199a87e9705e"

        today = datetime.date.today()
        start = today.replace(day=1).isoformat()

        url = (
            f"https://management.azure.com/subscriptions/{subscription_id}"
            f"/providers/Microsoft.CostManagement/query?api-version=2023-03-01"
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
                "to": today.isoformat()
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

        daily = []
        total = 0.0

        for r in rows:
            cost = float(r[1])
            total += cost
            daily.append({
                "date": str(r[0]),
                "cost": round(cost, 2)
            })

        # Simple projection
        days = len(daily)
        avg = total / days if days else 0

        days_in_month = (datetime.date(today.year, today.month % 12 + 1, 1)
                         - datetime.timedelta(days=1)).day

        projected = avg * days_in_month

        result = {
            "month_to_date_total": round(total, 2),
            "average_daily_cost": round(avg, 2),
            "projected_month_total": round(projected, 2),
            "daily_breakdown": daily
        }

        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500
        )