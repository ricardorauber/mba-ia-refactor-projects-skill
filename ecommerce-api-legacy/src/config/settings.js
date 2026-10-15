const crypto = require('node:crypto');

function secret(name) {
    if (process.env[name]) return process.env[name];
    console.warn(`[WARN] ${name} is not set; using an ephemeral value`);
    return crypto.randomBytes(32).toString('hex');
}

module.exports = Object.freeze({
    host: process.env.HOST || '0.0.0.0',
    port: Number(process.env.PORT || 3000),
    databasePath: process.env.DATABASE_PATH || ':memory:',
    adminToken: process.env.ADMIN_TOKEN || '',
    paymentGatewayKey: secret('PAYMENT_GATEWAY_KEY'),
    logLevel: process.env.LOG_LEVEL || 'info',
});
