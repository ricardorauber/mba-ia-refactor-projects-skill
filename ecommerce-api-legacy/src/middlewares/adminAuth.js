const crypto = require('node:crypto');
const { UnauthorizedError, ForbiddenError } = require('../errors');

function adminAuth({ adminToken }) {
    const expected = Buffer.from(adminToken || '');
    return (req, res, next) => {
        const received = Buffer.from(req.get('X-Admin-Token') || '');
        if (received.length === 0) return next(new UnauthorizedError('Token de administrador ausente'));
        const valid = expected.length > 0 && expected.length === received.length && crypto.timingSafeEqual(received, expected);
        if (!valid) return next(new ForbiddenError('Token de administrador inválido'));
        return next();
    };
}

module.exports = { adminAuth };
