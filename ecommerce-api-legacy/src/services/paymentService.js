const { PaymentStatus } = require('../models/paymentModel');
const logger = require('../utils/logger');

// Simulated gateway: cards starting with this prefix are approved.
const APPROVED_CARD_PREFIX = '4';
const VISIBLE_CARD_DIGITS = 4;

class PaymentService {
    constructor({ gatewayKey }) {
        this.gatewayKey = gatewayKey;
    }

    charge({ cardNumber }) {
        logger.info(`Processando pagamento do cartão **** ${cardNumber.slice(-VISIBLE_CARD_DIGITS)}`);
        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;
    }
}

module.exports = { PaymentService };
