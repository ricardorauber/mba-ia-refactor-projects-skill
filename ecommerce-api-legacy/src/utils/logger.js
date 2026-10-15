const { logLevel } = require('../config/settings');

const LEVELS = { error: 0, warn: 1, info: 2, silent: -1 };
const threshold = LEVELS[logLevel] ?? LEVELS.info;

function write(level, stream, message) {
    if (threshold < LEVELS[level]) return;
    stream(`[${level.toUpperCase()}] ${new Date().toISOString()} ${message}`);
}

module.exports = {
    info: (message) => write('info', console.info, message),
    warn: (message) => write('warn', console.warn, message),
    error: (message) => write('error', console.error, message),
};
