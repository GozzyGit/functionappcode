const { app } = require('@azure/functions');
const { DefaultAzureCredential } = require('@azure/identity');
const axios = require('axios');

app.http('costs', {
    methods: ['GET'],
    authLevel: 'anonymous',

    handler: async (request, context) => {

        try {

            const subscriptionId = '71e85381-5707-48bd-9e75-199a87e9705e';

            const credential = new DefaultAzureCredential();

            const token = await credential.getToken(
                'https://management.azure.com/.default'
            );

            const today = new Date();

            const startDate =
                `${today.getUTCFullYear()}-${String(today.getUTCMonth() + 1).padStart(2, '0')}-01`;

            const endDate =
                `${today.getUTCFullYear()}-${String(today.getUTCMonth() + 1).padStart(2, '0')}-${String(today.getUTCDate()).padStart(2, '0')}`;

            const url =
                `https://management.azure.com/subscriptions/${subscriptionId}` +
                `/providers/Microsoft.CostManagement/query` +
                `?api-version=2023-03-01`;

            const body = {
                type: 'ActualCost',
                timeframe: 'Custom',
                timePeriod: {
                    from: startDate,
                    to: endDate
                },
                dataset: {
                    granularity: 'Daily',
                    aggregation: {
                        totalCost: {
                            name: 'PreTaxCost',
                            function: 'Sum'
                        }
                    }
                }
            };

            const response = await axios.post(
                url,
                body,
                {
                    headers: {
                        Authorization: `Bearer ${token.token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            const rows =
                response.data?.properties?.rows || [];

            let totalCost = 0;

            rows.forEach(row => {
                totalCost += Number(row[0]);
            });

            const dayOfMonth = today.getUTCDate();

            const projectedCost =
                dayOfMonth > 0
                    ? (totalCost / dayOfMonth) * 30
                    : totalCost;

            return {
                jsonBody: {
                    subscriptionId,
                    monthToDateSpend: `£${totalCost.toFixed(2)}`,
                    projectedMonthEndSpend: `£${projectedCost.toFixed(2)}`,
                    currency: 'GBP',
                    daysElapsed: dayOfMonth
                }
            };

        } catch (err) {

            return {
                status: 500,
                jsonBody: {
                    error: err.message,
                    details: err.response?.data || null
                }
            };

        }
    }
});