const { ValidationError } = require('../errors');

const BAD_REQUEST = 'Bad Request';

function isScalar(value) {
    return typeof value === 'string' || typeof value === 'number';
}

// Maps the public request fields (usr, eml, pwd, c_id, card) to internal names.
function validateCheckout(body) {
    const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = body || {};
    if (!name || !email || !courseId || !cardNumber) throw new ValidationError(BAD_REQUEST);
    if (![name, email, courseId, cardNumber].every(isScalar)) throw new ValidationError(BAD_REQUEST);
    if (password && !isScalar(password)) throw new ValidationError(BAD_REQUEST);

    return {
        name: String(name),
        email: String(email),
        password: password ? String(password) : null,
        courseId,
        cardNumber: String(cardNumber),
    };
}

module.exports = { validateCheckout };
