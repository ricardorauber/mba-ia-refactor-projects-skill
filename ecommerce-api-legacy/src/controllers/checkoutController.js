const { NotFoundError, PaymentDeniedError } = require('../errors');
const { PaymentStatus } = require('../models/paymentModel');
const { validateCheckout } = require('./validators');

class CheckoutController {
    constructor({ transaction, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService, passwordHasher }) {
        this.transaction = transaction;
        this.userModel = userModel;
        this.courseModel = courseModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
        this.auditLogModel = auditLogModel;
        this.paymentService = paymentService;
        this.passwordHasher = passwordHasher;
    }

    async checkout(body) {
        const input = validateCheckout(body);

        const course = await this.courseModel.findActive(input.courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const existingUser = await this.userModel.findByEmail(input.email);

        const status = this.paymentService.charge(input);
        if (status === PaymentStatus.DENIED) throw new PaymentDeniedError('Pagamento recusado');

        const passwordHash = existingUser
            ? null
            : await this.passwordHasher.hashPassword(input.password || this.passwordHasher.randomPassword());

        const enrollmentId = await this.transaction(async () => {
            const userId = existingUser
                ? existingUser.id
                : await this.userModel.create({ name: input.name, email: input.email, passwordHash });
            const newEnrollmentId = await this.enrollmentModel.create({ userId, courseId: course.id });
            await this.paymentModel.create({ enrollmentId: newEnrollmentId, amount: course.price, status });
            await this.auditLogModel.record(`Checkout curso ${course.id} por ${userId}`);
            return newEnrollmentId;
        });

        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    }
}

module.exports = { CheckoutController };
