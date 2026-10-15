const crypto = require('node:crypto');
const { promisify } = require('node:util');

const scrypt = promisify(crypto.scrypt);
const KEY_LENGTH = 64;
const SALT_BYTES = 16;

async function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const derived = await scrypt(password, salt, KEY_LENGTH);
    return `scrypt$${salt}$${derived.toString('hex')}`;
}

// Used when the client sends no password: the account gets an unguessable one
// instead of a fixed default.
function randomPassword() {
    return crypto.randomBytes(SALT_BYTES).toString('hex');
}

module.exports = { hashPassword, randomPassword };
