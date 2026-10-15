const { AppError } = require('../errors');
const logger = require('../utils/logger');

const CLIENT_ERROR_MIN = 400;
const SERVER_ERROR_MIN = 500;

// Registered after the routes. Never sends stack traces or internal messages to the client.
function errorHandler(err, req, res, next) {
    if (res.headersSent) return next(err);
    if (err instanceof AppError) return res.status(err.statusCode).send(err.message);

    // Framework errors such as malformed JSON from express.json()
    const status = err.status || err.statusCode;
    if (status >= CLIENT_ERROR_MIN && status < SERVER_ERROR_MIN) return res.status(status).send('Bad Request');

    logger.error(err.stack || String(err));
    return res.status(500).send('Internal Server Error');
}

module.exports = { errorHandler };
