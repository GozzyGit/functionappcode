const { app } = require('@azure/functions');
const { DefaultAzureCredential } = require('@azure/identity');
const axios = require('axios');

app.http('costs', {
    methods: ['GET'],
    authLevel: 'anonymous',

    handler: async (req, context) => {

        const subscriptionId = process.env.SUBSCRIPTION_ID;

        const credential = new DefaultAzureCredential();
        const token = await credential.getToken(
            "https://management.azure.com/.default"
        );

        const today = new Date();
        const start = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-01`;
        const end = today.toISOString().split('T')[0];

        const url =
            `https://management.azure.com/subscriptions/${subscriptionId}` +
            `/providers/Microsoft.CostManagement/query?api-version=2023-03-01`;

        const body = {
            type: "ActualCost",
            timeframe: "Custom",
            timePeriod: {
                from: start,
                to: end
            },
            dataset: {
                granularity: "None",
                aggregation: {
                    totalCost: {
                        name: "PreTaxCost",
                        function: "Sum"
                    }
                }
            }
        };

        try {
            const response = await axios.post(url, body, {
                headers: {
                    Authorization: `Bearer ${token.token}`,
                    "Content-Type": "application/json"
                }
            });

            const rows = response.data?.properties?.rows || [];

            const total = rows.length ? rows[0][0] : 0;

            const day = today.getDate();
            const projected = (total / day) * 30;

            return {
                jsonBody: {
                    subscriptionId,
                    monthToDateSpend: `£${total.toFixed(2)}`,
                    projectedSpend: `£${projected.toFixed(2)}`
                }
            };

        } catch (err) {
            return {
                status: 500,
                jsonBody: {
                    error: err.message,
                    details: err.response?.data
                }
            };
        }
    }
});